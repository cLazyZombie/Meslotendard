from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_specimen_has_three_comparisons_controls_and_reduced_motion() -> None:
    specimen = (ROOT / "specimen" / "Monatendard-Specimen.template.html").read_text(
        encoding="utf-8"
    )
    assert "face--90" in specimen
    assert "face--925" in specimen
    assert "JetBrains Mono" in specimen
    assert 'id="size"' in specimen
    assert 'id="leading"' in specimen
    assert "prefers-reduced-motion" in specimen


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
    assert "Monatendard-*.ttf" in uninstaller
