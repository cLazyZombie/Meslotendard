# Monatendard

Monatendard는 **Monaspace Neon 1.400의 영문 폭을 92.5%로 조정**하고
**Pretendard 1.3.9의 한글 글리프를 결합**한 재현 가능한 코딩 글꼴 프로젝트입니다.
한글 한 글자의 advance는 영문 두 칸과 정확히 같습니다.

일반 사용자는 GitHub Release의 `Monatendard-v*-Desktop.zip`만 내려받아 압축을 풀고
`Install-Monatendard.ps1`을 실행하면 됩니다. Python, uv, Make는 필요하지 않습니다.

## 일반 사용자 설치

1. Release의 Desktop ZIP을 내려받아 압축을 풉니다.
2. PowerShell에서 `Install-Monatendard.ps1`을 실행합니다.
3. 사용 중인 편집기나 터미널을 다시 시작하고 글꼴을 `Monatendard`로 선택합니다.
4. 제거할 때는 같은 폴더의 `Uninstall-Monatendard.ps1`을 실행합니다.

스크립트는 관리자 권한 없이 현재 사용자 영역에 설치합니다.

## 개발자 빌드

필요 조건은 Python 3.11 이상과 [uv](https://docs.astral.sh/uv/)입니다.

```powershell
uv sync --all-groups
uv run monatendard fetch
uv run monatendard build --variants Regular
uv run monatendard verify
```

전체 14개 weight/style 조합은 다음 명령으로 빌드합니다.

```powershell
uv run monatendard build --all
```

생성 파일은 `fonts/ttf`, `fonts/webfont`에 저장되며 Git에는 포함되지 않습니다.
원본 아카이브도 `upstream/` 아래에만 저장되고 Git에서 제외됩니다.

## 명령

- `monatendard fetch`: 잠금 파일의 URL에서 원본을 받고 SHA256을 확인합니다.
- `monatendard build`: 92.5% 변환과 Pretendard 글리프 병합을 수행합니다.
- `monatendard verify`: 이름, 폭, 한글 글리프, 리게이처, 테이블 무결성을 확인합니다.
- `monatendard package --version 0.1.0`: Desktop/Web ZIP, 단일 specimen, 체크섬을 만듭니다.

`Makefile`은 개발자용 단축 명령일 뿐이며 사용자 설치 과정에는 필요하지 않습니다.

## 고정 메타데이터

| 항목 | 값 |
|---|---|
| Monatendard | 0.1.0 |
| Monaspace Neon | 1.400 |
| Pretendard | 1.3.9 |
| 영문 가로 배율 | 92.5% |
| 한글 advance | 영문 2칸 |

원본 URL과 아카이브 SHA256은 `sources.lock.toml`이 유일한 기준입니다. 같은 잠금 파일과
도구 버전으로 만든 결과의 바이트 재현성도 테스트합니다.

## 저장소 운영

- `main`에는 빌드 코드, 테스트, 문서, 워크플로만 둡니다.
- 원본 폰트, 생성 폰트, `dist/`는 커밋하지 않습니다.
- 버전은 SemVer 태그로 관리합니다. 하이픈이 있는 태그는 GitHub 사전 릴리스가 됩니다.
- Release workflow는 고정 원본 검증, 전체 빌드, 자동 테스트, 패키징, 체크섬 검증 후
  GitHub Release 자산을 게시합니다.

## 라이선스

Monaspace와 Pretendard는 SIL Open Font License 1.1로 배포됩니다. Monatendard는 원본의
Reserved Font Name을 사용하지 않는 별도 패밀리 이름입니다. 자세한 저작권과 고지는
`licenses/`를 확인해 주세요.
