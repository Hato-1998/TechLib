# 1. 자료구조

## 개요

게임은 매 프레임 수많은 객체의 상태를 갱신하고, 그들 사이의 관계(공간적·논리적)를 빠르게 질의해야 한다.
잘못된 자료구조 선택은 곧 프레임 드랍으로 이어진다.
**탐색 O(log N), 삽입/삭제 O(1)** 같은 빅오 차이가 16.6ms 예산 안에서 결정적인 차이를 만든다.

## 이 섹션에서 다루는 것

| 주제 | 핵심 |
| --- | --- |
| [Tree & Graph](tree-graph.md) | BST/AVL/RB, 인접 리스트/행렬, 게임 내 그래프 사례 |
| [공간 분할](space-partitioning.md) | BVH, Octree, Quadtree, BSP, KD-Tree 비교 |
| [충돌 연산](collision.md) | Broad/Narrow phase, SAT, GJK, CCD |
| [길찾기](pathfinding.md) | Dijkstra → A* → JPS → HPA*, Navmesh |

## 왜 이 순서인가

1. **Tree/Graph** — 모든 공간 분할·길찾기의 기반
2. **공간 분할** — O(N²) 충돌 검사를 O(N log N)으로 줄이는 핵심
3. **충돌 연산** — 공간 분할로 후보를 추린 뒤의 정밀 판정
4. **길찾기** — 그래프 + 휴리스틱의 응용

## 면접 빈출 주제

- "총알이 100,000개 있을 때 충돌 검사를 어떻게 줄일 것인가?" → 공간 분할
- "오픈월드에서 NPC 5,000마리가 길찾기를 동시에 한다면?" → HPA*, Navmesh 계층화
- "쿼터니언과 트리(Scene Graph)의 관계는?" → 변환 누적 시 부동소수점 오차

## 심화 학습 키워드

- Spatial Hashing, Uniform Grid
- R-Tree (DB에서 게임으로 역수입)
- Behavior Tree, Decision Tree (AI 분야)
