from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

import pytest

from meslotendard import __version__
from meslotendard.sources import (
    VARIANTS,
    VARIANTS_BY_SUFFIX,
    load_lock,
    make_variant,
    verify_archive,
)


def test_variant_matrix_has_two_real_weights_and_two_styles() -> None:
    assert len(VARIANTS) == 4
    assert set(VARIANTS_BY_SUFFIX) == {"Regular", "Italic", "Bold", "BoldItalic"}


def test_regular_italic_source_name_matches_monaspace_archive() -> None:
    variant = make_variant("Regular", "italic")
    assert variant.latin_filename == "MonaspaceArgonFrozen-Italic.ttf"
    assert variant.upright_latin_filename == "MonaspaceArgonFrozen-Regular.ttf"
    assert variant.cjk_filename == "Pretendard-Regular.ttf"
    assert variant.output_suffix == "Italic"


def test_unknown_variant_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="weight"):
        make_variant("Medium", "normal")
    with pytest.raises(ValueError, match="style"):
        make_variant("Regular", "oblique")


def test_lock_pins_sources_metrics_and_sha256() -> None:
    lock = load_lock()
    with (Path(__file__).parents[1] / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert lock["project"]["version"] == __version__ == pyproject["project"]["version"]
    assert lock["project"]["family"] == "Argontendard"
    assert lock["project"]["latin_horizontal_scale"] == 0.925
    assert lock["project"]["latin_advance_em"] == 0.595
    assert lock["sources"]["monaspace"]["name"] == "Monaspace Argon Frozen"
    assert lock["sources"]["monaspace"]["version"] == "1.400"
    assert lock["sources"]["pretendard"]["version"] == "1.3.9"
    assert lock["sources"]["nerd_fonts"]["version"] == "3.4.0"
    for source in lock["sources"].values():
        assert len(source["sha256"]) == 64
        int(source["sha256"], 16)


def test_archive_verification_detects_mismatch(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    archive.write_bytes(b"locked source")
    expected = hashlib.sha256(b"locked source").hexdigest()
    verify_archive(archive, expected)
    with pytest.raises(ValueError, match="SHA256"):
        verify_archive(archive, "0" * 64)
