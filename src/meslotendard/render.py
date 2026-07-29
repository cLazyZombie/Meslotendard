"""실제 TTF로 1:2 셀 격자 검수 이미지를 만든다."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from meslotendard.builder import FAMILY_NAME

SIZES_TO_VERIFY = (12, 14, 16, 20, 24, 32)
MAX_RASTER_ROUNDING_ERROR = 1.0
SPECIMEN_STYLE_ORDER = ("Regular", "Italic", "Bold", "BoldItalic")
SPECIMEN_LINES = (
    "AB가CD나EF다GH한IJ글",
    "가나다라마바사아자차카타파하",
    "if (값 == 10) 결과 = 값 + 1;",
    "==  !=  ->  =>  <=  >=  &&  ||",
    "\ue0a0 \ue0b0  \uf00c \uf07c \uf126 \uf489 󰀁",
    "┌────────┬────────┐  ████",
)


def verify_rendered_ratio(font_path: Path) -> list[str]:
    """FreeType 정수 픽셀 반올림 오차가 한 픽셀 이내인지 검사한다."""
    errors: list[str] = []
    for size in SIZES_TO_VERIFY:
        font = ImageFont.truetype(font_path, size=size)
        latin = float(font.getlength("AB"))
        hangul = float(font.getlength("가"))
        if abs(latin - hangul) > MAX_RASTER_ROUNDING_ERROR:
            errors.append(
                f"{font_path.name} {size}px 렌더 폭 불일치: AB={latin}, 가={hangul}"
            )
    return errors


def _draw_style_specimen(
    canvas: Image.Image,
    font_path: Path,
    *,
    top: int,
    left: int,
    width: int,
) -> int:
    draw = ImageDraw.Draw(canvas)
    font_size = 30
    font = ImageFont.truetype(font_path, size=font_size)
    label_font = ImageFont.truetype(font_path, size=14)
    cell_width = float(font.getlength("A"))
    row_height = 48
    grid_top = top + 28
    grid_bottom = grid_top + row_height * len(SPECIMEN_LINES)

    draw.text(
        (left, top),
        f"{font_path.stem} · 영문 1칸 {cell_width:.2f}픽셀 · 한글 2칸",
        font=label_font,
        fill=(45, 52, 65),
    )
    for index in range(int(width / cell_width) + 1):
        x = left + round(index * cell_width)
        color = (184, 199, 225) if index % 2 == 0 else (221, 228, 240)
        draw.line((x, grid_top, x, grid_bottom), fill=color, width=1)
    for row in range(len(SPECIMEN_LINES) + 1):
        y = grid_top + row * row_height
        draw.line((left, y, left + width, y), fill=(225, 229, 236), width=1)
    for row, text in enumerate(SPECIMEN_LINES):
        y = grid_top + row * row_height + 6
        draw.text((left, y), text, font=font, fill=(25, 28, 34))
    return grid_bottom + 28


def render_specimen(
    font_dir: Path = Path("fonts/ttf"),
    output_path: Path = Path("assets/argontendard-preview.png"),
) -> Path:
    """네 스타일을 같은 1:2 격자에 그린 PNG를 생성한다."""
    font_paths = [
        font_dir / f"{FAMILY_NAME}-{suffix}.ttf" for suffix in SPECIMEN_STYLE_ORDER
    ]
    if any(not path.is_file() for path in font_paths):
        raise FileNotFoundError(
            f"검수 이미지에 필요한 TTF 네 종이 없습니다: {[path.name for path in font_paths]}"
        )

    width = 1440
    section_height = 360
    canvas = Image.new("RGB", (width, section_height * len(font_paths) + 60), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(
        font_dir / f"{FAMILY_NAME}-Regular.ttf",
        size=18,
    )
    draw.text(
        (36, 20),
        "Argontendard 실제 TTF 렌더링 · 세로선 한 칸은 영문 1자, 두 칸은 한글 1자",
        font=title_font,
        fill=(20, 24, 32),
    )
    top = 56
    for font_path in font_paths:
        top = _draw_style_specimen(
            canvas,
            font_path,
            top=top,
            left=36,
            width=width - 72,
        )
    cropped = canvas.crop((0, 0, width, min(canvas.height, top + 20)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(output_path, format="PNG", optimize=True)
    return output_path
