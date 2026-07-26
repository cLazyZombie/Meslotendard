"""검증된 글꼴을 재현 가능한 Release 자산으로 묶는다."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

from monatendard.builder import FAMILY_NAME
from monatendard.nerd import NERD_FILE_PREFIX

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _zip_directory(source: Path, destination: Path) -> None:
    """정렬된 파일명과 고정 timestamp로 ZIP을 만든다."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)


def _copy_licenses(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / "LICENSE", destination / "LICENSE")
    for path in sorted((PROJECT_ROOT / "licenses").glob("*")):
        if path.is_file():
            shutil.copy2(path, destination / path.name)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_release_assets(
    *,
    version: str,
    fonts_dir: Path = Path("fonts"),
    dist_dir: Path = Path("dist"),
) -> list[Path]:
    """일반 Desktop, Nerd Desktop, Web ZIP과 SHA256SUMS를 생성한다."""
    normalized_version = version.removeprefix("v")
    ttf_paths = sorted((fonts_dir / "ttf").glob(f"{FAMILY_NAME}-*.ttf"))
    nerd_ttf_paths = sorted((fonts_dir / "nerd-ttf").glob(f"{NERD_FILE_PREFIX}-*.ttf"))
    woff2_paths = sorted((fonts_dir / "webfont").glob(f"{FAMILY_NAME}-*.woff2"))
    if not ttf_paths or not nerd_ttf_paths or not woff2_paths:
        raise FileNotFoundError("패키징할 글꼴이 없습니다. 먼저 전체 빌드를 실행하세요.")

    dist_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{FAMILY_NAME}-v{normalized_version}"
    desktop_zip = dist_dir / f"{prefix}-Desktop.zip"
    nerd_zip = dist_dir / f"{prefix}-Desktop-Nerd.zip"
    web_zip = dist_dir / f"{prefix}-Web.zip"

    temporary_root = PROJECT_ROOT / "build"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="monatendard-package-",
        dir=temporary_root,
    ) as temporary:
        root = Path(temporary)
        desktop = root / "desktop"
        nerd = root / "nerd"
        web = root / "web"
        desktop_fonts = desktop / "fonts"
        nerd_fonts = nerd / "fonts"
        web_fonts = web / "fonts"
        desktop_fonts.mkdir(parents=True)
        nerd_fonts.mkdir(parents=True)
        web_fonts.mkdir(parents=True)

        for path in ttf_paths:
            shutil.copy2(path, desktop_fonts / path.name)
        for path in nerd_ttf_paths:
            shutil.copy2(path, nerd_fonts / path.name)
        for path in woff2_paths:
            shutil.copy2(path, web_fonts / path.name)
        shutil.copy2(fonts_dir / "webfont" / "monatendard.css", web / "monatendard.css")

        windows_dir = PROJECT_ROOT / "packaging" / "windows"
        shutil.copy2(windows_dir / "Install-Monatendard.ps1", desktop / "Install-Monatendard.ps1")
        shutil.copy2(
            windows_dir / "Uninstall-Monatendard.ps1",
            desktop / "Uninstall-Monatendard.ps1",
        )
        shutil.copy2(windows_dir / "설치방법.txt", desktop / "설치방법.txt")
        shutil.copy2(
            windows_dir / "Install-Monatendard-Nerd.ps1",
            nerd / "Install-Monatendard-Nerd.ps1",
        )
        shutil.copy2(
            windows_dir / "Uninstall-Monatendard-Nerd.ps1",
            nerd / "Uninstall-Monatendard-Nerd.ps1",
        )
        shutil.copy2(windows_dir / "Nerd-설치방법.txt", nerd / "설치방법.txt")
        _copy_licenses(desktop / "LICENSES")
        _copy_licenses(nerd / "LICENSES")
        _copy_licenses(web / "LICENSES")
        _zip_directory(desktop, desktop_zip)
        _zip_directory(nerd, nerd_zip)
        _zip_directory(web, web_zip)

    assets = [desktop_zip, nerd_zip, web_zip]
    checksums = dist_dir / "SHA256SUMS.txt"
    checksums.write_text(
        "".join(f"{_file_sha256(path)}  {path.name}\n" for path in assets),
        encoding="ascii",
    )
    assets.append(checksums)
    return assets
