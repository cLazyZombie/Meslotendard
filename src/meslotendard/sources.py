"""고정된 Meslotendard 원본 글꼴을 내려받고 검증·추출한다."""

from __future__ import annotations

import hashlib
import shutil
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = PROJECT_ROOT / "sources.lock.toml"
UPSTREAM_DIR = PROJECT_ROOT / "upstream"
ARCHIVE_DIR = UPSTREAM_DIR / "_archives"
MESLO_DIR = UPSTREAM_DIR / "meslo"
PRETENDARD_DIR = UPSTREAM_DIR / "pretendard"

WEIGHTS = ("Regular", "Bold")
STYLES = ("normal", "italic")
WEIGHT_TO_CSS = {"Regular": 400, "Bold": 700}


@dataclass(frozen=True)
class Variant:
    """하나의 빌드 가능한 weight/style 조합."""

    weight_name: str
    css_weight: int
    style: str
    source_suffix: str
    output_suffix: str
    subfamily_name: str

    @property
    def is_italic(self) -> bool:
        return self.style == "italic"

    @property
    def latin_filename(self) -> str:
        return f"MesloLGMNerdFontMono-{self.source_suffix}.ttf"

    @property
    def upright_latin_filename(self) -> str:
        return f"MesloLGMNerdFontMono-{self.weight_name}.ttf"

    @property
    def cjk_filename(self) -> str:
        return f"Pretendard-{self.weight_name}.ttf"


def make_variant(weight_name: str, style: str) -> Variant:
    """weight/style을 Meslo 원본 및 Meslotendard 출력 이름으로 변환한다."""
    if weight_name not in WEIGHT_TO_CSS:
        raise ValueError(f"지원하지 않는 weight입니다: {weight_name}")
    if style not in STYLES:
        raise ValueError(f"지원하지 않는 style입니다: {style}")

    if style == "italic":
        suffix = "Italic" if weight_name == "Regular" else "BoldItalic"
        subfamily = "Italic" if weight_name == "Regular" else "Bold Italic"
    else:
        suffix = weight_name
        subfamily = weight_name

    return Variant(
        weight_name=weight_name,
        css_weight=WEIGHT_TO_CSS[weight_name],
        style=style,
        source_suffix=suffix,
        output_suffix=suffix,
        subfamily_name=subfamily,
    )


VARIANTS = tuple(make_variant(weight, style) for weight in WEIGHTS for style in STYLES)
VARIANTS_BY_SUFFIX = {variant.output_suffix: variant for variant in VARIANTS}


def load_lock(path: Path = LOCK_PATH) -> dict:
    """TOML 잠금 파일을 읽는다."""
    with path.open("rb") as handle:
        return tomllib.load(handle)


def sha256(path: Path) -> str:
    """파일 SHA256을 소문자 16진수로 반환한다."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(path: Path, expected_sha256: str) -> None:
    """아카이브 해시가 잠금 값과 같은지 확인한다."""
    actual = sha256(path)
    if actual != expected_sha256.lower():
        raise ValueError(
            f"{path.name} SHA256 불일치: expected={expected_sha256}, actual={actual}"
        )


def download(url: str, destination: Path) -> None:
    """URL을 임시 파일로 받은 뒤 원자적으로 교체한다."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    request = urllib.request.Request(url, headers={"User-Agent": "Meslotendard-builder"})
    try:
        with (
            urllib.request.urlopen(request, timeout=180) as response,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _extract_member(archive: zipfile.ZipFile, member_name: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        member = archive.getinfo(member_name)
    except KeyError as exc:
        raise FileNotFoundError(
            f"아카이브에 필요한 파일이 없습니다: {member_name}"
        ) from exc
    with archive.open(member) as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target)


def extract_sources(meslo_archive: Path, pretendard_archive: Path) -> None:
    """빌드에 필요한 Meslo Nerd Mono와 Pretendard TTF를 추출한다."""
    with zipfile.ZipFile(meslo_archive) as archive:
        for variant in VARIANTS:
            _extract_member(
                archive,
                variant.latin_filename,
                MESLO_DIR / variant.latin_filename,
            )
        _extract_member(archive, "LICENSE.txt", MESLO_DIR / "LICENSE.txt")
        _extract_member(archive, "README.md", MESLO_DIR / "README.md")

    with zipfile.ZipFile(pretendard_archive) as archive:
        for weight in WEIGHTS:
            filename = f"Pretendard-{weight}.ttf"
            _extract_member(
                archive,
                f"public/static/alternative/{filename}",
                PRETENDARD_DIR / filename,
            )


def write_sources_note(lock: dict) -> None:
    """추출한 입력과 변환 기준을 사람이 읽을 수 있게 기록한다."""
    project = lock["project"]
    meslo = lock["sources"]["meslo"]
    pretendard = lock["sources"]["pretendard"]
    lines = [
        "# Meslotendard 빌드 입력",
        "",
        f"- {meslo['name']}: {meslo['version']}",
        f"- Pretendard: {pretendard['version']}",
        f"- 영문 윤곽 가로 배율: {project['latin_horizontal_scale']:.6f}",
        f"- 영문 셀 너비: {project['latin_advance_em']:.12f}em",
        f"- 한글/CJK 가로 배율: {project['cjk_horizontal_scale']:.6f}",
        f"- 한글/CJK 세로 배율: {project['cjk_vertical_scale']:.6f}",
        f"- 한글/CJK X 오프셋: {project['cjk_horizontal_offset_em']:.6f}em",
        f"- 한글/CJK Y 오프셋: {project['cjk_vertical_offset_em']:.6f}em",
        "- 무결성 기준: 저장소 루트 `sources.lock.toml`",
        "",
        "이 디렉터리는 자동 생성되며 Git에 커밋하지 않습니다.",
        "",
    ]
    (UPSTREAM_DIR / "SOURCES.md").write_text("\n".join(lines), encoding="utf-8")


def fetch_sources(lock_path: Path = LOCK_PATH) -> list[Path]:
    """잠금된 원본을 준비하고 검증한다."""
    lock = load_lock(lock_path)
    archives: list[Path] = []
    for key in ("meslo", "pretendard"):
        source = lock["sources"][key]
        archive_path = ARCHIVE_DIR / source["archive"]
        if archive_path.exists():
            try:
                verify_archive(archive_path, source["sha256"])
            except ValueError:
                archive_path.unlink()
        if not archive_path.exists():
            download(source["url"], archive_path)
        verify_archive(archive_path, source["sha256"])
        archives.append(archive_path)

    extract_sources(archives[0], archives[1])
    write_sources_note(lock)
    return archives
