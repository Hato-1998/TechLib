# 게임 프로그래밍 기술 위키

구현 중 만난 문제를 골라 관련 개념을 찾아보세요. C++ 필기 문제와 UE5 사례를 차례로 공부하려면 [학습실](study/index.md)에서 시작할 수 있습니다.

## 게임에서 마주친 문제로 찾기

| 궁금한 점 | 먼저 읽을 개념 | 게임에 적용하기 |
|---|---|---|
| 적이 많아지면 표적 탐색이 느려진다 | [공간 분할과 자료구조](01-data-structures/index.md), [캐시 메모리](03-cache-memory/index.md) | 탐색 후보 수와 메모리 접근 비용을 나눠 측정합니다. |
| 화면에 보이는 물체를 줄였는데 프레임 시간이 그대로다 | [컬링과 선형대수](02-linear-algebra/index.md), [렌더링 병목](04-computer-architecture/index.md) | CPU와 GPU 중 어느 쪽이 프레임을 제한하는지 확인합니다. |
| 레벨 경계에서 화면이 잠깐 멈춘다 | [스트리밍](08-memory-management/index.md), [동적 할당](06-memory-allocation/index.md), [프로파일링](10-profiling/index.md) | 최초 로딩과 반복되는 할당을 서로 다른 구간에서 비교합니다. |
| 부하가 낮아도 프레임 간격이 불규칙하다 | [스레드 동기화](05-threading/index.md), [OS 스케줄링](07-os-scheduling/index.md) | 게임 스레드가 일하는 시간과 대기하는 시간을 구분합니다. |
| 중간에 합류하면 미션 HUD가 비어 있다 | [네트워크 동기화](09-network-sync/index.md), [UE5 학습서 3·7장](study/UE5_Content_Programming_Workbook.md) | 현재 상태가 도착한 순간과 화면이 알림을 구독한 순간을 비교합니다. |
| 결과 창을 열 때마다 보상음이 한 번씩 늘어난다 | [디버깅과 코드 리뷰](senior-knowledge/index.md), [UE5 학습서 10장](study/UE5_Content_Programming_Workbook.md) | 지급·통지·재생 횟수를 같은 미션 ID로 추적합니다. |

## 분야별 기술 문서

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

