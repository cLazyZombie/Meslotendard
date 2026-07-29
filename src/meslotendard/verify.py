"""Argontendard의 이름, 폭, 아이콘, 리게이처 부재와 재현성을 검증한다."""

from __future__ import annotations

import tempfile
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from meslotendard.builder import (
    FAMILY_NAME,
    REQUIRED_HANGUL,
    _glyph_bounds,
    build_font,
    is_cjk,
    is_double_cell,
)
from meslotendard.render import verify_rendered_ratio
from meslotendard.sources import VARIANTS_BY_SUFFIX, sha256

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TABLES = {"cmap", "glyf", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post"}
FORBIDDEN_LAYOUT_TABLES = {"GSUB", "GPOS", "GDEF", "morx", "mort", "kern", "PfEd"}
MINIMUM_NERD_GLYPHS = 10_000
REQUIRED_NERD_CODEPOINTS = (
    0xE0A0,
    0xE0B0,
    0xF00C,
    0xF07C,
    0xF126,
    0xF489,
    0xF0001,
)
OPERATOR_SEQUENCES = (
    "==",
    "===",
    "!=",
    "!==",
    "->",
    "=>",
    "<=",
    ">=",
    "::",
    "&&",
    "||",
    "++",
    "--",
)
EDGE_JOIN_REQUIREMENTS = {
    0x2500: (True, True),
    0x2588: (True, True),
    0xE0B0: (True, False),
    0xE0B2: (False, True),
}


def is_private_use(codepoint: int) -> bool:
    """Unicode 사적 사용 영역인지 판단한다."""
    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )


def _name_values(font: TTFont, name_id: int) -> set[str]:
    values: set[str] = set()
    for record in font["name"].names:
        if record.nameID == name_id:
            values.add(record.toUnicode())
    return values


def _verify_shaping(path: Path, font: TTFont, latin_advance: int) -> list[str]:
    """기본 shaping에서도 연산자 글리프와 폭이 바뀌지 않는지 검사한다."""
    errors: list[str] = []
    cmap = font.getBestCmap() or {}
    face = hb.Face(path.read_bytes())
    shaped_font = hb.Font(face)
    shaped_font.scale = (face.upem, face.upem)

    for text in OPERATOR_SEQUENCES:
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.direction = "ltr"
        buffer.script = "Latn"
        buffer.language = "en"
        hb.shape(shaped_font, buffer)

        expected_glyphs = [
            font.getGlyphID(cmap[ord(character)])
            for character in text
            if ord(character) in cmap
        ]
        actual_glyphs = [info.codepoint for info in buffer.glyph_infos]
        if actual_glyphs != expected_glyphs:
            errors.append(
                f"연산자 shaping이 글리프를 바꿉니다: {text!r}, "
                f"expected={expected_glyphs}, actual={actual_glyphs}"
            )
        advances = [position.x_advance for position in buffer.glyph_positions]
        if advances != [latin_advance] * len(text):
            errors.append(
                f"연산자 shaping이 셀 폭을 바꿉니다: {text!r}, advances={advances}"
            )
    return errors


def verify_font(path: Path) -> list[str]:
    """한 Argontendard TTF를 검사하고 실패 사유를 반환한다."""
    errors: list[str] = []
    try:
        font = TTFont(path)
        font.ensureDecompiled()
    except Exception as exc:
        return [f"글꼴을 열 수 없습니다: {exc}"]

    try:
        missing_tables = REQUIRED_TABLES - set(font.keys())
        if missing_tables:
            errors.append(f"필수 테이블 누락: {', '.join(sorted(missing_tables))}")

        families = _name_values(font, 16) or _name_values(font, 1)
        if families != {FAMILY_NAME}:
            errors.append(f"패밀리 이름이 다릅니다: {sorted(families)}")
        for name_id, label in ((4, "Full"), (6, "PostScript")):
            values = _name_values(font, name_id)
            if not values or any(FAMILY_NAME not in value for value in values):
                errors.append(f"{label} name이 Argontendard 규칙과 다릅니다: {sorted(values)}")

        licenses = _name_values(font, 13)
        required_license_words = ("SIL Open Font License", "Apache", "MIT", "modified")
        for word in required_license_words:
            if not any(word in value for value in licenses):
                errors.append(f"name ID 13 라이선스 고지에 {word!r}가 없습니다.")

        cmap = font.getBestCmap() or {}
        hmtx = font["hmtx"].metrics
        ascii_codepoints = range(0x20, 0x7F)
        missing_ascii = [codepoint for codepoint in ascii_codepoints if codepoint not in cmap]
        if missing_ascii:
            errors.append(
                "ASCII 글리프 누락: "
                + ", ".join(f"U+{codepoint:04X}" for codepoint in missing_ascii)
            )
            latin_advance = None
        else:
            ascii_widths = {hmtx[cmap[codepoint]][0] for codepoint in ascii_codepoints}
            if len(ascii_widths) != 1:
                errors.append(f"ASCII advance가 단일 값이 아닙니다: {sorted(ascii_widths)}")
                latin_advance = None
            else:
                latin_advance = next(iter(ascii_widths))

        for codepoint in REQUIRED_HANGUL:
            if codepoint not in cmap:
                errors.append(f"필수 한글 글리프 누락: U+{codepoint:04X}")

        if latin_advance is not None:
            wrong_single_cell_widths = [
                (codepoint, hmtx[glyph_name][0])
                for codepoint, glyph_name in cmap.items()
                if not is_double_cell(codepoint)
                and glyph_name in hmtx
                and hmtx[glyph_name][0] != latin_advance
            ]
            if wrong_single_cell_widths:
                sample = ", ".join(
                    f"U+{codepoint:04X}={width}"
                    for codepoint, width in wrong_single_cell_widths[:10]
                )
                errors.append(
                    f"비 CJK 글리프 advance가 한 칸이 아닙니다: {sample} "
                    f"(총 {len(wrong_single_cell_widths)}개)"
                )

            wrong_cjk_widths = [
                (codepoint, hmtx[glyph_name][0])
                for codepoint, glyph_name in cmap.items()
                if is_double_cell(codepoint)
                and glyph_name in hmtx
                and hmtx[glyph_name][0] != latin_advance * 2
            ]
            if wrong_cjk_widths:
                sample = ", ".join(
                    f"U+{codepoint:04X}={width}"
                    for codepoint, width in wrong_cjk_widths[:10]
                )
                errors.append(
                    f"한글/CJK advance가 영문 두 칸이 아닙니다: {sample} "
                    f"(총 {len(wrong_cjk_widths)}개)"
                )

            private_use_codepoints = [
                codepoint for codepoint in cmap if is_private_use(codepoint)
            ]
            if len(private_use_codepoints) < MINIMUM_NERD_GLYPHS:
                errors.append(
                    f"Nerd 아이콘 수가 너무 적습니다: {len(private_use_codepoints)} "
                    f"(최소 {MINIMUM_NERD_GLYPHS})"
                )

            missing_icons = [
                codepoint for codepoint in REQUIRED_NERD_CODEPOINTS if codepoint not in cmap
            ]
            for codepoint in missing_icons:
                errors.append(f"필수 Nerd 아이콘 누락: U+{codepoint:04X}")

            wrong_icon_widths = [
                (codepoint, hmtx[glyph_name][0])
                for codepoint in private_use_codepoints
                if (glyph_name := cmap[codepoint]) in hmtx
                and hmtx[glyph_name][0] != latin_advance
            ]
            if wrong_icon_widths:
                sample = ", ".join(
                    f"U+{codepoint:04X}={width}"
                    for codepoint, width in wrong_icon_widths[:10]
                )
                errors.append(
                    f"Nerd 아이콘 advance가 한 칸이 아닙니다: {sample} "
                    f"(총 {len(wrong_icon_widths)}개)"
                )

            glyph_set = font.getGlyphSet()
            for codepoint, (joins_left, joins_right) in EDGE_JOIN_REQUIREMENTS.items():
                glyph_name = cmap.get(codepoint)
                bounds = (
                    _glyph_bounds(glyph_set, glyph_name) if glyph_name is not None else None
                )
                if bounds is None:
                    errors.append(f"셀 접합 글리프 누락: U+{codepoint:04X}")
                    continue
                xmin, _, xmax, _ = bounds
                if joins_left and xmin > 0:
                    errors.append(f"U+{codepoint:04X} 왼쪽 셀 경계 미접합: xmin={xmin:g}")
                if joins_right and xmax < latin_advance:
                    errors.append(
                        f"U+{codepoint:04X} 오른쪽 셀 경계 미접합: "
                        f"xmax={xmax:g}, expected>={latin_advance}"
                    )

            hhea = font["hhea"]
            clipped_cjk = []
            for codepoint, glyph_name in cmap.items():
                if not is_cjk(codepoint):
                    continue
                bounds = _glyph_bounds(glyph_set, glyph_name)
                if bounds is not None and (
                    bounds[1] < hhea.descent or bounds[3] > hhea.ascent
                ):
                    clipped_cjk.append(codepoint)
            if clipped_cjk:
                errors.append(
                    "세로 메트릭을 벗어난 한글/CJK: "
                    + ", ".join(f"U+{codepoint:04X}" for codepoint in clipped_cjk[:10])
                )

            errors.extend(_verify_shaping(path, font, latin_advance))
            errors.extend(verify_rendered_ratio(path))

        present_layout_tables = FORBIDDEN_LAYOUT_TABLES & set(font.keys())
        if present_layout_tables:
            errors.append(
                "치환/위치 조정/편집기 테이블이 남아 있습니다: "
                + ", ".join(sorted(present_layout_tables))
            )

        if not font["post"].isFixedPitch or font["OS/2"].panose.bProportion != 9:
            errors.append("고정폭 메타데이터가 설정되지 않았습니다.")
    finally:
        font.close()
    return errors


def verify_directory(font_dir: Path) -> dict[Path, list[str]]:
    """디렉터리의 모든 Argontendard TTF를 검사한다."""
    paths = sorted(font_dir.glob(f"{FAMILY_NAME}-*.ttf"))
    expected_names = {
        f"{FAMILY_NAME}-{suffix}.ttf"
        for suffix in ("Regular", "Bold", "Italic", "BoldItalic")
    }
    actual_names = {path.name for path in paths}
    if actual_names != expected_names:
        return {
            font_dir: [
                "검사할 TTF 네 종이 정확히 필요합니다: "
                f"expected={sorted(expected_names)}, actual={sorted(actual_names)}"
            ]
        }
    return {path: errors for path in paths if (errors := verify_font(path))}


def verify_reproducible(variant_name: str = "Regular") -> tuple[bool, str, str]:
    """같은 입력을 두 번 빌드해 TTF SHA256이 같은지 확인한다."""
    variant = VARIANTS_BY_SUFFIX[variant_name]
    temporary_root = PROJECT_ROOT / "build"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="argontendard-repro-",
        dir=temporary_root,
    ) as temporary:
        root = Path(temporary)
        first = build_font(variant, output_dir=root / "first").output_path
        second = build_font(variant, output_dir=root / "second").output_path
        first_hash = sha256(first)
        second_hash = sha256(second)
    return first_hash == second_hash, first_hash, second_hash
