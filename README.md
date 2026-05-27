# TechLib — 게임 프로그래밍 기술 위키

[![Live Site](https://img.shields.io/badge/site-live-brightgreen)](https://hato-1998.github.io/TechLib/)
[![Deploy](https://github.com/Hato-1998/TechLib/actions/workflows/deploy.yml/badge.svg)](https://github.com/Hato-1998/TechLib/actions/workflows/deploy.yml)
[![MkDocs Material](https://img.shields.io/badge/built%20with-mkdocs--material-526CFE)](https://squidfunk.github.io/mkdocs-material/)

> **사이트:** <https://hato-1998.github.io/TechLib/>

게임 프로그래밍 기술 자료를 정리한 개인 기술 위키.
자료구조·수학·메모리·렌더링·네트워크·동시성·렌더링 파이프라인 등의 핵심 개념과 C++ 예시를 모은다.

## 로컬 실행

```bash
pip install -r requirements.txt
mkdocs serve
```

브라우저에서 `http://127.0.0.1:8000` 접속.

## GitHub Pages 배포

```bash
mkdocs gh-deploy
```

`gh-pages` 브랜치에 빌드 결과를 푸시하고 Pages를 자동으로 활성화한다.

## 디렉토리 구조

```
TechLib/
├── mkdocs.yml                  # 사이트 설정 + 네비게이션
├── requirements.txt            # mkdocs-material 등
├── README.md
└── docs/
    ├── index.md                # 홈
    ├── 01-data-structures/     # Tree/Graph, 공간분할, 충돌, 길찾기
    ├── 02-linear-algebra/      # 행렬, 내적/외적, 컬링
    ├── 03-cache-memory/        # L1/L2/L3, false sharing
    ├── 04-computer-architecture/  # Draw Call, 병목, 배경 최적화
    ├── 05-threading/           # 멀티스레딩, 렌더/물리 분리
    ├── 06-memory-allocation/   # 풀링, 단편화
    ├── 07-os-scheduling/       # 컨텍스트 스위치, frame pacing
    ├── 08-memory-management/   # 심리스 로딩, 스트리밍
    ├── 09-network-sync/        # 예측, 추측 항법
    ├── 10-profiling/           # Unreal Insights, RenderDoc, Tracy
    ├── 11-advanced-rendering/  # 물리 엔진, PBR, WFC
    ├── 12-oop-vs-dod-ecs/      # 패러다임 비교
    └── senior-knowledge/       # 5년차 이상 추가 지식
```

## 기여 방법

각 페이지는 `개요 → 핵심 개념 → C++ 예시 → 심화 학습 키워드` 4단 구조를 따른다.

### 페이지 추가 도구 (권장)

수동으로 `mkdocs.yml`·섹션 index·파일을 따로 만지지 말고 도구를 쓴다.

```bash
# 대화형 (추천)
python tools/add_page.py

# 비대화형: 기존 섹션에 페이지 추가
python tools/add_page.py add \
    --section "1. 자료구조" \
    --title "해시 테이블" \
    --slug hash-table \
    --summary "O(1) 평균 조회, 충돌 해결"

# 비대화형: 새 섹션 생성
python tools/add_page.py new-section \
    --number 13 --folder 13-shader-programming \
    --title "셰이더 프로그래밍" \
    --summary "HLSL, GLSL, 머티리얼 그래프" \
    --first-title "HLSL 기초" --first-slug hlsl-basics \
    --first-summary "문법, 셰이더 단계"

# 페이지 제거
python tools/add_page.py remove --section "1. 자료구조" --slug hash-table

# 섹션 목록 확인
python tools/add_page.py list
```

도구가 자동으로:

1. 템플릿(`tools/templates/page.md`) 기반으로 파일 생성
2. `mkdocs.yml`의 nav에 entry 삽입
3. 섹션 `index.md`의 "이 섹션에서 다루는 것" 표에 행 추가
4. 새 섹션이면 홈(`docs/index.md`) 카드 그리드에도 카드 추가
5. 편집기 자동 실행 (Windows: 기본 연결 앱)

이후 사용자는 **생성된 파일의 본문만 채우면** 된다. 작성 완료 후 `python -m mkdocs build --strict`로 검증.
