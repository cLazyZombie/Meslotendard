"""생성 글꼴의 이름, 폭, 글리프, 리게이처와 재현성을 검증한다."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont

from monatendard.builder import ASCII_SAMPLE, FAMILY_NAME, REQUIRED_HANGUL, build_font
from monatendard.sources import VARIANTS_BY_SUFFIX

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TABLES = {"cmap", "glyf", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post"}
LIGATURE_FEATURES = {"liga", "calt", *(f"ss{number:02d}" for number in range(1, 11))}


def _name_values(font: TTFont, name_id: int) -> set[str]:
    values: set[str] = set()
    for record in font["name"].names:
        if record.nameID == name_id:
            values.add(record.toUnicode())
    return values


def verify_font(path: Path) -> list[str]:
    """한 글꼴을 검사하고 실패 사유를 반환한다."""
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

        for name_id, label in ((1, "Family"), (4, "Full"), (6, "PostScript")):
            values = _name_values(font, name_id)
            if not values or any(FAMILY_NAME not in value for value in values):
                errors.append(f"{label} name이 Monatendard 규칙과 다릅니다: {sorted(values)}")

        licenses = _name_values(font, 13)
        if not licenses or not any("SIL Open Font License" in value for value in licenses):
            errors.append("name ID 13에 SIL OFL 고지가 없습니다.")

        cmap = font.getBestCmap() or {}
        hmtx = font["hmtx"].metrics
        ascii_widths = {
            hmtx[cmap[codepoint]][0]
            for codepoint in ASCII_SAMPLE
            if codepoint in cmap and cmap[codepoint] in hmtx
        }
        if len(ascii_widths) != 1:
            errors.append(f"대표 영문 advance가 단일 값이 아닙니다: {sorted(ascii_widths)}")
        else:
            latin_advance = next(iter(ascii_widths))
            for codepoint in REQUIRED_HANGUL:
                glyph_name = cmap.get(codepoint)
                if glyph_name is None:
                    errors.append(f"필수 한글 글리프 누락: U+{codepoint:04X}")
                elif hmtx[glyph_name][0] != latin_advance * 2:
                    errors.append(
                        f"U+{codepoint:04X} advance={hmtx[glyph_name][0]}, "
                        f"expected={latin_advance * 2}"
                    )

        if "GSUB" not in font:
            errors.append("Monaspace 리게이처를 위한 GSUB 테이블이 없습니다.")
        else:
            feature_list = font["GSUB"].table.FeatureList
            tags = (
                {record.FeatureTag for record in feature_list.FeatureRecord}
                if feature_list is not None
                else set()
            )
            if not tags & LIGATURE_FEATURES:
                errors.append(f"리게이처 feature가 없습니다: {sorted(tags)}")

        if not cast_fixed_pitch(font):
            errors.append("고정폭 메타데이터가 설정되지 않았습니다.")
    finally:
        font.close()
    return errors


def cast_fixed_pitch(font: TTFont) -> bool:
    """일반적인 두 고정폭 플래그가 모두 설정됐는지 확인한다."""
    return bool(font["post"].isFixedPitch) and font["OS/2"].panose.bProportion == 9


def verify_directory(font_dir: Path) -> dict[Path, list[str]]:
    """디렉터리의 모든 TTF를 검사한다."""
    paths = sorted(font_dir.glob("Monatendard-*.ttf"))
    if not paths:
        return {font_dir: ["검사할 Monatendard TTF가 없습니다."]}
    return {path: errors for path in paths if (errors := verify_font(path))}


def verify_reproducible(variant_name: str = "Regular") -> tuple[bool, str, str]:
    """같은 입력을 두 번 빌드해 TTF SHA256이 같은지 확인한다."""
    from monatendard.sources import sha256

    variant = VARIANTS_BY_SUFFIX[variant_name]
    temporary_root = PROJECT_ROOT / "build"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="monatendard-repro-",
        dir=temporary_root,
    ) as temporary:
        root = Path(temporary)
        first = build_font(variant, output_dir=root / "first").output_path
        second = build_font(variant, output_dir=root / "second").output_path
        first_hash = sha256(first)
        second_hash = sha256(second)
    return first_hash == second_hash, first_hash, second_hash
