from __future__ import annotations

import zipfile
from pathlib import Path

from meslotendard import __version__
from meslotendard.packaging import create_release_assets


def test_release_package_contains_four_fonts_licenses_and_checksums(
    tmp_path: Path,
) -> None:
    fonts = tmp_path / "fonts" / "ttf"
    fonts.mkdir(parents=True)
    for suffix in ("Regular", "Bold", "Italic", "BoldItalic"):
        (fonts / f"Argontendard-{suffix}.ttf").write_bytes(suffix.encode("ascii"))

    assets = create_release_assets(
        fonts_dir=tmp_path / "fonts",
        dist_dir=tmp_path / "dist",
    )
    assert [path.name for path in assets] == ["Argontendard.zip", "SHA256SUMS.txt"]

    with zipfile.ZipFile(assets[0]) as archive:
        names = set(archive.namelist())
        assert archive.read("VERSION.txt") == f"{__version__}\n".encode("ascii")
        assert len(archive.read("SHA256SUMS.txt").decode("ascii").splitlines()) == 4

    for suffix in ("Regular", "Bold", "Italic", "BoldItalic"):
        assert f"Argontendard-{suffix}.ttf" in names
    assert "LICENSE" in names
    assert "FONTLOG.md" in names
    assert "licenses/THIRD_PARTY_NOTICES.md" in names
    assert "licenses/NERD_FONTS_LICENSE.txt" in names
    assert len(assets[1].read_text(encoding="ascii").splitlines()) == 1
