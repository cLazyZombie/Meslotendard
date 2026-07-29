# Argontendard 작업 규칙

- 이 저장소는 `younjungpark/Monatendard`의 포크다.
- `argon` 브랜치의 결과물은 `Argontendard` 패밀리의 Regular, Bold, Italic,
  BoldItalic TTF 네 개뿐이다.
- 모든 결과물에 Nerd Font 아이콘을 포함한다. 일반판, 웹폰트, Windows 설치 스크립트,
  GitHub Pages 파일은 다시 추가하지 않는다.
- 영문·Nerd·유니코드 반각 문자는 한 칸, 한글·전각 CJK는 두 칸이어야 한다.
- `GSUB`, `GPOS`, `GDEF`, `morx`, `mort`, `kern` 테이블을 결과 폰트에 넣지 않는다.
- 원본 버전·URL·SHA256·배율은 `sources.lock.toml`을 기준으로 한다.
- 문서는 한국어로 작성한다. 단, 원문 보존이 필요한 라이선스 전문은 번역하지 않는다.
- 원본 저작권·Reserved Font Name·라이선스 고지를 삭제하거나 축약하지 않는다.
- 버전을 바꿀 때 `sources.lock.toml`, `pyproject.toml`,
  `src/meslotendard/__init__.py`를 함께 맞춘다.
- macOS/Linux 전체 검증은 `./build.sh`로 실행한다. 릴리스 태그 검증은 버전을 첫 인자로
  넘긴다.
- `upstream/`, `fonts/`, `dist/`, `build/`, 가상환경과 캐시는 커밋하지 않는다.
- 렌더 시편은 실제 네 TTF를 다시 만든 뒤 눈으로 확인한 결과만 갱신한다.
