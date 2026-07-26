"""검증된 글꼴을 재현 가능한 Release 자산으로 묶는다."""

from __future__ import annotations

import base64
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

from monatendard.builder import FAMILY_NAME

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


def _write_specimen(woff2_path: Path, destination: Path, version: str) -> None:
    template = (PROJECT_ROOT / "specimen" / "Monatendard-Specimen.template.html").read_text(
        encoding="utf-8"
    )
    font_data = base64.b64encode(woff2_path.read_bytes()).decode("ascii")
    html = (
        template.replace("__FONT_DATA__", font_data)
        .replace("__MONATENDARD_VERSION__", version)
        .replace("__BUILD_DATE__", "재현 가능 빌드")
    )
    destination.write_text(html, encoding="utf-8")


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
    """Desktop/Web ZIP, specimen, SHA256SUMS를 생성한다."""
    normalized_version = version.removeprefix("v")
    ttf_paths = sorted((fonts_dir / "ttf").glob(f"{FAMILY_NAME}-*.ttf"))
    woff2_paths = sorted((fonts_dir / "webfont").glob(f"{FAMILY_NAME}-*.woff2"))
    if not ttf_paths or not woff2_paths:
        raise FileNotFoundError("패키징할 글꼴이 없습니다. 먼저 전체 빌드를 실행하세요.")

    dist_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{FAMILY_NAME}-v{normalized_version}"
    desktop_zip = dist_dir / f"{prefix}-Desktop.zip"
    web_zip = dist_dir / f"{prefix}-Web.zip"
    specimen_path = dist_dir / f"{prefix}-Specimen.html"

    temporary_root = PROJECT_ROOT / "build"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="monatendard-package-",
        dir=temporary_root,
    ) as temporary:
        root = Path(temporary)
        desktop = root / "desktop"
        web = root / "web"
        desktop_fonts = desktop / "fonts"
        web_fonts = web / "fonts"
        desktop_fonts.mkdir(parents=True)
        web_fonts.mkdir(parents=True)

        for path in ttf_paths:
            shutil.copy2(path, desktop_fonts / path.name)
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
        _copy_licenses(desktop / "LICENSES")
        _copy_licenses(web / "LICENSES")
        _zip_directory(desktop, desktop_zip)
        _zip_directory(web, web_zip)

    regular_webfont = fonts_dir / "webfont" / f"{FAMILY_NAME}-Regular.woff2"
    _write_specimen(regular_webfont, specimen_path, normalized_version)

    assets = [desktop_zip, web_zip, specimen_path]
    checksums = dist_dir / "SHA256SUMS.txt"
    checksums.write_text(
        "".join(f"{_file_sha256(path)}  {path.name}\n" for path in assets),
        encoding="ascii",
    )
    assets.append(checksums)
    return assets
