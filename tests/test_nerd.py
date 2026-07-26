from __future__ import annotations

from monatendard.nerd import (
    NERD_FAMILY_NAME,
    NERD_FILE_PREFIX,
    NERD_ICON_VERTICAL_OFFSET_EM,
    REQUIRED_NERD_CODEPOINTS,
    _vertical_center_shift,
    is_private_use,
)


def test_nerd_family_and_files_are_separate_from_standard_family() -> None:
    assert NERD_FAMILY_NAME == "Monatendard Nerd Font Mono"
    assert NERD_FILE_PREFIX == "MonatendardNFM"


def test_required_prompt_icons_are_private_use_codepoints() -> None:
    assert {0xE0A0, 0xE0B0, 0xF00C, 0xF07C, 0xF126, 0xF489, 0xF0001}.issubset(
        REQUIRED_NERD_CODEPOINTS
    )
    assert all(is_private_use(codepoint) for codepoint in REQUIRED_NERD_CODEPOINTS)
    assert not is_private_use(ord("A"))
    assert not is_private_use(0xAC00)


def test_nerd_icon_vertical_center_uses_optical_offset_above_x_height() -> None:
    bounds = (1, -182, 2049, 1410)
    scale = 1101 / 2048
    target_center = 513.5 + 2000 * NERD_ICON_VERTICAL_OFFSET_EM
    shift = _vertical_center_shift(bounds, scale=scale, target_center=target_center)
    transformed_center = ((bounds[1] + bounds[3]) / 2) * scale + shift
    assert transformed_center == target_center
