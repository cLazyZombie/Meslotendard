"""검증된 Argontendard TTF를 재현 가능한 Release 자산으로 묶는다."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

from meslotendard.builder import FAMILY_NAME
from meslotendard.sources import load_lock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def create_release_assets(
    *,
    version: str | None = None,
    fonts_dir: Path = Path("fonts"),
    dist_dir: Path = Path("dist"),
) -> list[Path]:
    """TTF 네 종과 라이선스를 단일 고정 이름 ZIP으로 만든다."""
    project_version = str(load_lock()["project"]["version"])
    normalized_version = (version or project_version).removeprefix("v").strip()
    if normalized_version != project_version:
        raise ValueError(
            f"Release 버전과 sources.lock.toml이 다릅니다: "
            f"release={normalized_version}, project={project_version}"
        )

    ttf_paths = sorted((fonts_dir / "ttf").glob(f"{FAMILY_NAME}-*.ttf"))
    expected_names = {
        f"{FAMILY_NAME}-Regular.ttf",
        f"{FAMILY_NAME}-Bold.ttf",
        f"{FAMILY_NAME}-Italic.ttf",
        f"{FAMILY_NAME}-BoldItalic.ttf",
    }
    actual_names = {path.name for path in ttf_paths}
    if actual_names != expected_names:
        raise FileNotFoundError(
            "패키징할 TTF 네 종이 없습니다: "
            f"expected={sorted(expected_names)}, actual={sorted(actual_names)}"
        )

    dist_dir.mkdir(parents=True, exist_ok=True)
    archive_path = dist_dir / f"{FAMILY_NAME}.zip"
    temporary_root = PROJECT_ROOT / "build"
    temporary_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="argontendard-package-",
        dir=temporary_root,
    ) as temporary:
        package_root = Path(temporary)
        for path in ttf_paths:
            shutil.copy2(path, package_root / path.name)

        shutil.copy2(PROJECT_ROOT / "README.md", package_root / "README.md")
        shutil.copy2(PROJECT_ROOT / "LICENSE", package_root / "LICENSE")
        shutil.copy2(PROJECT_ROOT / "FONTLOG.md", package_root / "FONTLOG.md")
        shutil.copytree(PROJECT_ROOT / "licenses", package_root / "licenses")
        (package_root / "VERSION.txt").write_text(
            normalized_version + "\n",
            encoding="ascii",
        )
        (package_root / "SHA256SUMS.txt").write_text(
            "".join(f"{_file_sha256(path)}  {path.name}\n" for path in ttf_paths),
            encoding="ascii",
        )
        _zip_directory(package_root, archive_path)

    checksums_path = dist_dir / "SHA256SUMS.txt"
    checksums_path.write_text(
        f"{_file_sha256(archive_path)}  {archive_path.name}\n",
        encoding="ascii",
    )
    return [archive_path, checksums_path]
