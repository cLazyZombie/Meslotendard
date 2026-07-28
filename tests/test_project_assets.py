from __future__ import annotations

from pathlib import Path
from stat import S_IXUSR

ROOT = Path(__file__).resolve().parents[1]
IGNORED_SCAN_PARTS = {
    ".git",
    ".pytest_cache",
    ".pytest_tmp",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "fonts",
    "upstream",
}


def test_readme_is_short_korean_fork_documentation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "younjungpark/Monatendard" in readme
    assert "https://github.com/younjungpark/Monatendard" in readme
    assert "Meslotendard" in readme
    assert "Nerd Font" in readme
    assert "한글" in readme
    assert len(readme.splitlines()) < 160
    assert not (ROOT / "README.ko.md").exists()


def test_agents_file_keeps_only_project_invariants() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for required in (
        "younjungpark/Monatendard",
        "Meslotendard",
        "Nerd Font",
        "한글·전각 CJK는 두 칸",
        "./build.sh",
        "라이선스",
    ):
        assert required in agents
    assert len(agents.splitlines()) < 40


def test_local_build_script_is_executable_and_cross_platform() -> None:
    script = ROOT / "build.sh"
    contents = script.read_text(encoding="utf-8")
    assert script.stat().st_mode & S_IXUSR
    assert "Darwin | Linux" in contents
    assert "verify --reproducible" in contents
    assert "meslotendard package" in contents


def test_removed_web_and_windows_surfaces_stay_removed() -> None:
    assert not (ROOT / "packaging" / "windows").exists()
    tracked_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROOT.rglob("*")
        if path.is_file()
        and not IGNORED_SCAN_PARTS.intersection(path.parts)
        and path.suffix in {".py", ".sh", ".toml", ".md", ".yml", ".yaml", ".txt"}
        and path.name not in {"uv.lock"}
    )
    forbidden = (
        "monatendard" + ".github.io",
        "woff" + "2",
        "@font" + "-face",
        "Install-" + "Monatendard",
    )
    for text in forbidden:
        assert text.lower() not in tracked_text.lower()


def test_license_and_change_documents_are_packaged_sources() -> None:
    required = (
        ROOT / "LICENSE",
        ROOT / "FONTLOG.md",
        ROOT / "licenses" / "MESLO_APACHE-2.0.txt",
        ROOT / "licenses" / "NERD_FONTS_LICENSE.txt",
        ROOT / "licenses" / "THIRD_PARTY_NOTICES.md",
    )
    for path in required:
        assert path.is_file(), path
