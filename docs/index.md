# 게임 프로그래밍 기술 위키

게임 프로그래머가 알아야 할 핵심 주제를 한곳에 정리한 개인 학습 위키.
각 페이지는 **개요 → 핵심 개념 → C++ 예시 → 면접/실무 포인트 → 심화 학습** 구조를 따른다.

## 누구를 위한 자료인가

- **게임 프로그래머 지망생** — 면접 단골 주제(자료구조, 캐시, 렌더링 파이프라인)를 빠르게 훑고 싶을 때
- **현업 1~4년차** — 자기 분야 외 인접 지식(네트워크 동기화, 물리, ECS)을 보강할 때
- **5년차 이상** — 최신 트렌드(Nanite/Lumen, Iris Networking, Mass Entity) 정리와 시니어 시선 체크리스트

## 학습 로드맵

```mermaid
flowchart LR
    DS[1. 자료구조] --> Math[2. 선형대수학]
    Math --> Cache[3. 캐시 메모리]
    Cache --> Arch[4. 컴퓨터 아키텍처]
    Arch --> Thread[5. 스레드]
    Thread --> Mem[6. 동적 할당]
    Mem --> OS[7. OS 스케줄링]
    OS --> Stream[8. 메모리 관리]
    Stream --> Net[9. 네트워크]
    Net --> Prof[10. 프로파일링]
    Prof --> Adv[11. 물리·렌더링 심화]
    Adv --> ECS[12. OOP vs DOD/ECS]
    ECS --> Senior[시니어 지식]
```

## 섹션 안내

<div class="grid cards" markdown>

- **1. 자료구조**

    Tree, Graph, 공간 분할, 충돌, 길찾기

    [→ 시작하기](01-data-structures/index.md)

- **2. 선형대수학**

    행렬 변환, 내·외적, 시야각/백페이스 컬링

    [→ 시작하기](02-linear-algebra/index.md)

- **3. 캐시 메모리**

    L1/L2/L3, false sharing, 프리페치

    [→ 시작하기](03-cache-memory/index.md)

- **4. 컴퓨터 아키텍처**

    Draw Call, 병목 분석, 배경 최적화

    [→ 시작하기](04-computer-architecture/index.md)

- **5. 스레드 & 동기화**

    멀티스레딩, 메인/렌더/물리 분리, 병렬 처리

    [→ 시작하기](05-threading/index.md)

- **6. 동적 할당 & 단편화**

    메모리 풀링, Arena/Slab Allocator

    [→ 시작하기](06-memory-allocation/index.md)

- **7. OS 스케줄링**

    컨텍스트 스위치, frame pacing, fiber

    [→ 시작하기](07-os-scheduling/index.md)

- **8. 메모리 관리**

    심리스 로딩, 스트리밍, World Partition

    [→ 시작하기](08-memory-management/index.md)

- **9. 네트워크 동기화**

    클라이언트 예측, 추측 항법, 롤백

    [→ 시작하기](09-network-sync/index.md)

- **10. 프로파일링 & 최적화 도구**

    Unreal Insights, RenderDoc, Tracy

    [→ 시작하기](10-profiling/index.md)

- **11. 물리·렌더링 심화**

    물리 엔진, PBR, WFC 알고리즘

    [→ 시작하기](11-advanced-rendering/index.md)

- **12. OOP vs DOD/ECS**

    패러다임 비교, Mass Entity, Unity DOTS

    [→ 시작하기](12-oop-vs-dod-ecs/index.md)

- **시니어 지식 (5년차+)**

    디버깅, 코드 리뷰, 디자인 패턴, 최신 트렌드

    [→ 시작하기](senior-knowledge/index.md)

</div>

## 작성 원칙

- **추론 금지, 출처 확인** — 엔진 API/매크로는 실제 소스로 검증
- **수치는 대략적 범위** — "L1 약 4사이클" 같은 표현 사용. 절대값 단정 회피
- **Unreal Engine 5.4+ 기준** — 코드 예시는 가능하면 UE의 `F-/U-` 타입을 사용
- **하드코딩 지양** — 코드 예시는 개념 설명용 최소 스니펫
