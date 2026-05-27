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

## 심화 학습 키워드

- Spatial Hashing, Uniform Grid
- R-Tree (DB에서 게임으로 역수입)
- Behavior Tree, Decision Tree (AI 분야)
