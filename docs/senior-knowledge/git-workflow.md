# Git 워크플로우 & 협업 관리

## 개요

게임 프로젝트는 단순 코드 리포지토리가 아니다. 바이너리 에셋(텍스처, 메시, 레벨), 거대한 소스 트리, 수십 명의 동시 작업자를 다뤄야 한다. Git LFS, Perforce, Trunk-based flow vs Git Flow, 빌드 팜 연동 같은 실전 기술을 이해하는 것이 팀 생산성을 좌우한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **Trunk-based** | main/master만 존재. 모든 개발자가 짧은 브랜치로 자주 푸시 |
| **Git Flow** | develop/main + feature 브랜치. 구조적, 느린 머지 사이클 |
| **Git LFS** | 큰 파일 외부 저장소. 동기화 간편 |
| **Perforce** | 중앙집중형 VCS. 게임 규모 회사 표준 (EA, Ubisoft) |
| **Monorepo** | 한 저장소에 전체 프로젝트. 스케일링 도전과제 |
| **Pre-commit Hook** | 커밋 전 자동 검증 (포맷, 금지 파일 등) |

## Trunk-based vs Git Flow

```
Trunk-based:
  main ──●──●──●──●  (매 커밋이 배포 가능)
         ↙↙↙↙↙↙↙  (기능 브랜치, 하루 이내)

  장점: 빠른 피드백, 충돌 최소화, CI/CD 간편
  단점: main 안정성 필수, 엄격한 테스트 문화

Git Flow:
  main ──●────────●  (릴리스)
         ↑        ↑
  release ────────●  (릴리스 후보)
         ↑
  develop ──●──●──●  (개발 중심)
            ↑↑↑  (기능 브랜치)

  장점: 명확한 버전 관리, 병렬 개발
  단점: 머지 사이클 길어짐, 충돌 증가
```

### Trunk-based 권장 (모던 팀)

```
1. main에서 feature 브랜치 생성
   git checkout -b feature/player-jumping

2. 빠르게 작업 (하루 이내)
   git add ...
   git commit -m "feat: implement double jump"

3. PR 작성 → 리뷰 → 승인
   CI 자동 실행

4. main에 머지 (rebase 또는 squash)
   git merge feature/player-jumping
   (또는 GitHub "Squash and merge")

5. 브랜치 삭제
   git branch -D feature/player-jumping
```

## PR 사이즈 가이드라인

```
코드 라인 수      리뷰 난도    승인 시간    추천
─────────────────────────────────────────────
0-100 lines       쉬움         ~30분       최고
100-300 lines     중간         1시간       좋음
300-500 lines     어려움       2시간+      주의
500+ lines        매우어려움   3시간+      회피

예:
  [GOOD] "Add footstep audio system" (250줄)
  [BAD]  "Refactor entire character subsystem" (1500줄)
```

## Git LFS (Large File Storage)

```
문제: 텍스처(4K=20MB) 커밋 → .git 폭증 → clone 느림

해결:
1. .gitattributes 설정
   *.uasset filter=lfs diff=lfs merge=lfs -text
   *.umap filter=lfs diff=lfs merge=lfs -text
   *.png filter=lfs diff=lfs merge=lfs -text

2. LFS 추적 활성화
   git lfs install
   git lfs track "*.uasset"

3. 커밋 (투명)
   git add Textures/T_Ground.uasset
   git commit -m "Add ground texture"
   (내부: 포인터만 저장, 실제 파일 LFS 서버)

4. 다른 개발자 clone
   git clone <repo>  (자동 LFS 파일 다운)
```

## Perforce vs Git (게임 회사)

```
조건                   Git                    Perforce
──────────────────────────────────────────────────────
프로젝트 크기        <100GB                  100GB+
팀 규모              <50명                   50명+
에셋 버전링          Git LFS 필요            기본 지원
병렬 개발            브랜치 기반             스트림 기반
클라이언트           일반 Git               P4 클라이언트

게임 회사 현황:
  EA Frostbite: Perforce (매우 큰 규모)
  Ubisoft: Perforce
  Epic (Unreal): Perforce + Git (규모별)
  Indie: Git + LFS
```

## Pre-commit Hook (자동 검증)

```bash
# .git/hooks/pre-commit
#!/bin/bash

# 금지 파일 체크
git diff --cached --name-only | while read file
do
    # .env, credentials 차단
    if [[ $file =~ \.(env|key|credential)$ ]]; then
        echo "ERROR: Sensitive file detected: $file"
        exit 1
    fi
done

# 코드 포맷 검증 (선택)
if ! clang-format --dry-run $(git diff --cached --name-only *.cpp); then
    echo "ERROR: Code format violation. Run clang-format."
    exit 1
fi

exit 0
```

```bash
# 설정
chmod +x .git/hooks/pre-commit

# 테스트
git commit  (훅 자동 실행)

# 강제 무시 (금지!)
git commit --no-verify  # ← 절대 하지 말 것
```

## 모노레포 (Unreal 규모)

```
폴더 구조:
/
├─ Source/          (엔진 소스)
├─ Engine/          (엔진 리소스)
├─ Games/
│  ├─ ShooterGame/
│  └─ StrategyGame/
└─ Plugins/
   ├─ UMG/
   └─ Niagara/

문제:
  - 리포 크기: 100GB+
  - Clone 시간: 1시간+
  - Merge conflict 빈번

해결:
  - 부분 clone (sparse-checkout)
  - Git worktree (병렬 브랜치)
  - Shallow clone: git clone --depth 1
```

```bash
# 부분 clone (선택 폴더만)
git clone --sparse <repo>
git sparse-checkout add Source/MyGame
git sparse-checkout add Games/ShooterGame
# (다른 폴더는 다운로드 안 함)
```

## 브랜치 명명 규칙

```
패턴: <type>/<short-description>

type:
  feature/  - 새 기능
  bugfix/   - 버그 수정
  hotfix/   - 긴급 수정 (main)
  refactor/ - 코드 개선 (기능 변경 X)
  chore/    - 설정, 문서

예:
  feature/player-animation
  bugfix/network-replication-crash
  hotfix/critical-memory-leak
  refactor/character-subsystem
  chore/update-build-config

나쁜 예:
  new-feature           (type 불명확)
  fix-stuff             (너무 모호)
  my-changes            (팀 기여도 추적 어려움)
```

## CI/CD 빌드 팜

```
개발자 push
  ↓
GitHub Actions (또는 Jenkins, Unreal Automation)
  ├─ Compile (모든 플랫폼)
  ├─ Run Tests (unit + integration)
  ├─ Static Analysis (코드 검사)
  ├─ Performance Baseline (프레임타임 회귀)
  └─ 결과 → PR 코멘트 (자동)

예:
  [PASS] Compile: All platforms OK (2분)
  [PASS] Tests: 150/150 passed
  [WARN] Performance: Frametime +5% (이전 vs 현재)
  [FAIL] Analysis: 3 new warnings (casting)

→ 리뷰어 판단 용이
```

## 면접/실무 포인트

- **Q1**: 대규모 팀(50명+), 어떤 워크플로우?
  - Trunk-based + 강한 CI/CD.
  - 또는 Perforce (중앙집중형).

- **Q2**: Git LFS 프로젝트, clone이 느려진다?
  - Shallow clone 고려.
  - 부분 LFS 다운로드: `git lfs install --skip-smudge`

- **Q3**: main 브랜치를 잘못 건드렸다?
  - 커밋하지 않았으면: `git reset --hard HEAD`
  - 커밋했으면: `git revert <hash>` (새 커밋으로 되돌림)
  - Force push 금지! (협업 규칙 위반)

## 심화 학습

- 키워드: Branching Strategy, Distributed VCS, Merge Conflict Resolution
- 도구: Git LFS, Perforce, GitHub Actions
- 관련 페이지: [debugging-mindset](./debugging-mindset.md), [code-review](./code-review.md)
