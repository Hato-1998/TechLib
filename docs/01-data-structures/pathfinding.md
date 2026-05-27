# 길찾기 알고리즘

## 개요

NPC가 장애물을 피해 목표로 가는 경로를 찾는 문제.
가중치 그래프 위의 최단 경로 문제로 환원되며, **그래프 표현(Navmesh, Grid)** + **탐색 알고리즘** + **경로 후처리(스무딩)** 의 조합으로 구성된다.

## 핵심 개념

### 알고리즘 진화

| 알고리즘 | 휴리스틱 | 특징 | 사용 |
| --- | --- | --- | --- |
| **BFS** | 없음 | 가중치 1 가정, 큐 기반 | 미로 |
| **Dijkstra** | 없음 | 가중치 그래프 최단경로, 우선순위 큐 | 거리 기반 |
| **A\*** | 사용 | f(n) = g(n) + h(n) | 표준 길찾기 |
| **JPS** | 사용 | Grid에서 점프로 가지치기 | 대규모 grid |
| **HPA\*** | 사용 | 계층 클러스터, 거시-미시 분리 | 오픈월드 |
| **Theta\*** | 사용 | Any-angle 경로 (대각 외 임의 각도) | 자연스러운 경로 |

### A\* 핵심

- `g(n)` = 시작에서 n까지 실제 비용
- `h(n)` = n에서 목표까지 휴리스틱 예측 비용 (admissible: 실제 비용 이하)
- `f(n) = g + h`가 작은 노드부터 확장
- 휴리스틱이 정확할수록 탐색 노드 수 감소. 그리드에서 보통 맨해튼 또는 옥타일 거리

### Navmesh

- 워킹 가능한 표면을 **볼록 다각형 메시**로 표현
- 다각형 인접 그래프 위에서 A* 수행
- 다각형 단위로 그래프가 단순 → 그리드 대비 노드 수 대폭 감소
- Unreal의 `RecastNavMesh` (Recast/Detour 라이브러리)

### 계층화: HPA\*

```mermaid
flowchart LR
    Start[시작] --> A1[클러스터 A 경계]
    A1 -. 거시 A* .-> B1[클러스터 B 경계]
    B1 -. 거시 A* .-> C1[클러스터 C 경계]
    C1 --> Goal[목표]
    A1 -. 미시 A* .-> Start
    Goal -. 미시 A* .-> C1
```

- 큰 그리드를 클러스터로 나누고 경계 포털 그래프로 거시 경로 탐색
- 진입/탈출 시에만 클러스터 내부 정밀 탐색

## C++ 예시

```cpp
// Unreal: 가장 단순한 navmesh 길찾기
UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld());
UNavigationPath* Path = NavSys->FindPathToLocationSynchronously(
    GetWorld(),
    GetActorLocation(),
    TargetLocation,
    /*PathfindingContext=*/ nullptr
);

if (Path && Path->IsValid())
{
    for (const FVector& Point : Path->PathPoints)
    {
        // 경로 따라 이동 로직
    }
}
```

비동기 경로 요청이 필요하면 `FindPathAsync` 사용. 대규모 NPC는 동기 호출 금지.

## 동적 장애물 처리

- **Navmesh Invoker / Dirty Area** — 변경된 영역만 부분 재빌드
- **RVO (Reciprocal Velocity Obstacles)** — NPC끼리 동적 회피
- **Detour Crowd** — Recast의 동적 군중 회피 모듈

## 면접/실무 포인트

- **Q1**: 휴리스틱이 admissible하지 않으면? — 최적 경로 보장 안 됨(과대평가 시 일찍 종료). 게임에서는 약간 과대평가해 속도-품질 트레이드.
- **Q2**: NPC 5,000마리 동시 길찾기를 어떻게 처리? — 매 프레임 분산(time-slicing), HPA*로 거시 경로 캐시, 동일 목표는 flow field 공유.
- **Q3**: Navmesh vs Grid 선택 기준? — 자유로운 3D 지형이면 Navmesh, 일정한 셀 단위(타워디펜스, 보드게임)면 Grid.
- **Q4**: A* 우선순위 큐 구현은? — 이진 힙이 일반적. Fibonacci heap은 이론적 우위지만 상수 커서 게임에선 거의 안 씀.
- **Q5**: 경로 스무딩이 필요한 이유? — Navmesh 다각형 중심을 잇는 경로는 지그재그. **Funnel algorithm**으로 string-pulling 후 시각적 자연스러움 확보.

## 심화 학습

- D\* Lite (변화하는 그래프에서의 재탐색)
- Flow Field Pathfinding (RTS, 다수 유닛 동일 목표)
- Hierarchical Navmesh, Off-Mesh Link (점프·사다리)
- 관련 페이지: [Tree & Graph](tree-graph.md), [공간 분할](space-partitioning.md)
