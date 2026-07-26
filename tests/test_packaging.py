from __future__ import annotations

import zipfile
from pathlib import Path

from monatendard.packaging import create_release_assets


def test_release_package_contains_installer_fonts_licenses_and_checksums(
    tmp_path: Path,
) -> None:
    fonts = tmp_path / "fonts"
    (fonts / "ttf").mkdir(parents=True)
    (fonts / "webfont").mkdir()
    (fonts / "ttf" / "Monatendard-Regular.ttf").write_bytes(b"ttf")
    (fonts / "webfont" / "Monatendard-Regular.woff2").write_bytes(b"woff2")
    (fonts / "webfont" / "monatendard.css").write_text("@font-face {}", encoding="utf-8")

    assets = create_release_assets(
        version="0.1.0-beta.1",
        fonts_dir=fonts,
        dist_dir=tmp_path / "dist",
    )
    assert [path.name for path in assets] == [
        "Monatendard-v0.1.0-beta.1-Desktop.zip",
        "Monatendard-v0.1.0-beta.1-Web.zip",
        "SHA256SUMS.txt",
    ]

    with zipfile.ZipFile(assets[0]) as archive:
        names = set(archive.namelist())
    assert "fonts/Monatendard-Regular.ttf" in names
    assert "Install-Monatendard.ps1" in names
    assert "Uninstall-Monatendard.ps1" in names
    assert "설치방법.txt" in names
    assert "LICENSES/LICENSE" in names
    assert "LICENSES/THIRD_PARTY_NOTICES.md" in names

    assert len(assets[2].read_text(encoding="ascii").splitlines()) == 2
