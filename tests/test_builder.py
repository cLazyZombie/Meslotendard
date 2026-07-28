from __future__ import annotations

import pytest

from meslotendard.builder import (
    _fit_cjk_transform_xy,
    _fit_latin_metrics,
    is_cell_connecting,
    is_cjk,
    is_double_cell,
)


@pytest.mark.parametrize("codepoint", [0x1100, 0x3131, 0xAC00, 0xD7A3, 0x4E00, 0xFF01])
def test_cjk_ranges_are_selected(codepoint: int) -> None:
    assert is_cjk(codepoint)


@pytest.mark.parametrize("codepoint", [0x20, 0x41, 0x391, 0x1F600])
def test_non_cjk_ranges_are_not_selected(codepoint: int) -> None:
    assert not is_cjk(codepoint)


@pytest.mark.parametrize("codepoint", [0x1100, 0x3131, 0xAC00, 0x4E00, 0xFF01])
def test_fullwidth_cjk_uses_two_cells(codepoint: int) -> None:
    assert is_double_cell(codepoint)


@pytest.mark.parametrize("codepoint", [0x41, 0xFF61, 0xFF9F, 0xFFA0, 0xFFDC, 0xFFE8])
def test_latin_and_halfwidth_forms_use_one_cell(codepoint: int) -> None:
    assert not is_double_cell(codepoint)


def test_cjk_transform_supports_independent_horizontal_and_vertical_scale() -> None:
    scale_x, scale_y, shift = _fit_cjk_transform_xy(
        (100, -200, 900, 800),
        normalized_scale_x=2.24,
        normalized_scale_y=2.16,
        target_advance=2220,
        safe_ymin=-1000,
        safe_ymax=2000,
    )
    transformed_center = ((100 + 900) / 2) * scale_x + shift
    assert transformed_center == pytest.approx(1110)
    assert scale_x == pytest.approx(2.24)
    assert scale_y == pytest.approx(2.16)


def test_latin_outline_is_centered_in_wider_advance() -> None:
    advance, left_side_bearing, shift = _fit_latin_metrics(
        1233,
        100,
        outline_scale=1.0,
        advance_scale=1.0,
    )
    assert advance == 1233
    assert shift == pytest.approx(0)
    assert left_side_bearing == 100


@pytest.mark.parametrize(
    "codepoint",
    [0x2500, 0x257F, 0x2580, 0x259F, 0xE0B0, 0xE0D4],
)
def test_cell_connecting_ranges_are_selected(codepoint: int) -> None:
    assert is_cell_connecting(codepoint)


@pytest.mark.parametrize("codepoint", [0x249F, 0x25A0, 0xE0A3, 0xE0D5])
def test_non_connecting_ranges_are_not_selected(codepoint: int) -> None:
    assert not is_cell_connecting(codepoint)


def test_connecting_outline_keeps_source_overlap_at_target_cell_edges() -> None:
    advance_scale = 1190 / 1240
    target_advance, _, shift = _fit_latin_metrics(
        1240,
        -10,
        outline_scale=advance_scale,
        advance_scale=advance_scale,
    )
    transformed_xmin = -10 * advance_scale + shift
    transformed_xmax = 1250 * advance_scale + shift

    assert target_advance == 1190
    assert transformed_xmin < 0
    assert transformed_xmax > target_advance
