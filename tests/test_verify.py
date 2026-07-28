from __future__ import annotations

from pathlib import Path

from meslotendard.verify import (
    MINIMUM_NERD_GLYPHS,
    OPERATOR_SEQUENCES,
    REQUIRED_NERD_CODEPOINTS,
    is_private_use,
    verify_directory,
)


def test_required_prompt_icons_are_private_use_codepoints() -> None:
    assert MINIMUM_NERD_GLYPHS >= 10_000
    assert {0xE0A0, 0xE0B0, 0xF00C, 0xF07C, 0xF126, 0xF489, 0xF0001}.issubset(
        REQUIRED_NERD_CODEPOINTS
    )
    assert all(is_private_use(codepoint) for codepoint in REQUIRED_NERD_CODEPOINTS)
    assert not is_private_use(ord("A"))
    assert not is_private_use(0xAC00)


def test_operator_regression_set_covers_common_coding_sequences() -> None:
    assert {"==", "!=", "->", "=>", "<=", ">=", "&&", "||"}.issubset(
        OPERATOR_SEQUENCES
    )


def test_directory_verification_requires_exactly_four_styles(tmp_path: Path) -> None:
    (tmp_path / "Meslotendard-Regular.ttf").write_bytes(b"not enough")
    failures = verify_directory(tmp_path)
    assert tmp_path in failures
    assert "TTF 네 종" in failures[tmp_path][0]
