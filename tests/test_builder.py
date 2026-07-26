from __future__ import annotations

import pytest

from monatendard.builder import _fit_cjk_transform, is_cjk


@pytest.mark.parametrize("codepoint", [0x1100, 0x3131, 0xAC00, 0xD7A3, 0x4E00, 0xFF01])
def test_cjk_ranges_are_selected(codepoint: int) -> None:
    assert is_cjk(codepoint)


@pytest.mark.parametrize("codepoint", [0x20, 0x41, 0x391, 0x1F600])
def test_non_cjk_ranges_are_not_selected(codepoint: int) -> None:
    assert not is_cjk(codepoint)


def test_cjk_transform_centers_outline_in_two_cell_advance() -> None:
    scale, shift = _fit_cjk_transform(
        (100, -200, 900, 800),
        normalized_scale=2.0,
        target_advance=2220,
        safe_ymin=-500,
        safe_ymax=1600,
    )
    transformed_center = ((100 + 900) / 2) * scale + shift
    assert transformed_center == pytest.approx(1110)
    assert 0 < scale <= 2.0
