from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_surfaces_link_to_official_website() -> None:
    official_url = "https://monatendard.github.io/"
    paths = [
        ROOT / "README.ko.md",
        ROOT / "pyproject.toml",
        ROOT / "packaging" / "windows" / "설치방법.txt",
        ROOT / "packaging" / "windows" / "Nerd-설치방법.txt",
    ]
    for path in paths:
        assert official_url in path.read_text(encoding="utf-8")


def test_windows_scripts_support_dry_run_and_user_install() -> None:
    installer = (ROOT / "packaging" / "windows" / "Install-Monatendard.ps1").read_text(
        encoding="utf-8"
    )
    uninstaller = (ROOT / "packaging" / "windows" / "Uninstall-Monatendard.ps1").read_text(
        encoding="utf-8"
    )
    for script in (installer, uninstaller):
        assert "SupportsShouldProcess" in script
        assert "HKCU:" in script
        assert "WM_FONTCHANGE" not in script or "0x001D" in script
    assert "LOCALAPPDATA" in installer
    assert "-Value $destination" in installer
    assert "-Value $font.Name" not in installer
    assert "GetFileName([string]$property.Value)" in uninstaller
    assert "Monatendard-*.ttf" in uninstaller


def test_nerd_windows_scripts_are_isolated_from_standard_family() -> None:
    installer = (
        ROOT / "packaging" / "windows" / "Install-Monatendard-Nerd.ps1"
    ).read_text(encoding="utf-8")
    uninstaller = (
        ROOT / "packaging" / "windows" / "Uninstall-Monatendard-Nerd.ps1"
    ).read_text(encoding="utf-8")
    for script in (installer, uninstaller):
        assert "SupportsShouldProcess" in script
        assert "HKCU:" in script
        assert "MonatendardNFM-*.ttf" in script
        assert "Monatendard Nerd Font Mono" in script
    assert "-Value $destination" in installer
    assert "GetFileName([string]$property.Value)" in uninstaller
