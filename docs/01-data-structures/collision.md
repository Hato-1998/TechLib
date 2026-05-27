# 충돌 연산

## 개요

물리 시뮬레이션·트리거·히트스캔 등 게임의 거의 모든 인터랙션이 충돌 판정으로 귀결된다.
충돌 처리는 **broad phase(개략 후보 추출)** → **narrow phase(정밀 판정)** → **응답(impulse/penetration resolve)** 의 3단계로 분리한다.

## 핵심 개념

### 두 단계 분리

| 단계 | 목적 | 자료구조/알고리즘 |
| --- | --- | --- |
| **Broad phase** | 명백히 안 부딪힐 쌍 제거 | BVH, Spatial Hash, Sweep-and-Prune |
| **Narrow phase** | 후보 쌍의 정확한 충돌 판정 | AABB-AABB, SAT, GJK |

### 충돌 볼륨 종류

| 볼륨 | 특징 | 사용처 |
| --- | --- | --- |
| **AABB** (Axis-Aligned BB) | 가장 빠른 검사 (6 비교) | 컬링, broad-phase |
| **OBB** (Oriented BB) | 회전 가능 | 정밀한 박스 형태 |
| **Sphere** | 거리만 비교, 가장 단순 | 캐릭터 시야, 폭발 범위 |
| **Capsule** | 캐릭터 콜리전 표준 | UE Character 기본 |
| **Convex Hull** | 임의 볼록 다면체 | 정적 메시 단순화 |

### 알고리즘

#### SAT (Separating Axis Theorem)

> "두 볼록 다각형이 분리 축을 가지면 충돌하지 않는다."

- 두 도형 각 면의 법선을 후보 축으로 삼아 투영(projection) 비교
- OBB-OBB, 다각형-다각형에 직관적

#### GJK (Gilbert–Johnson–Keerthi)

- 두 볼록체의 **민코프스키 차(A ⊖ B)**가 원점을 포함하면 충돌
- 심플렉스를 점점 키우며 원점 포함 여부 갱신
- 임의의 볼록체에 대해 동작하며 거리(가장 가까운 점) 계산까지 확장 가능

#### CCD (Continuous Collision Detection)

- 빠른 객체가 한 프레임에 벽을 통과(tunneling)하는 문제 해결
- **swept volume** 또는 **conservative advancement**로 시작-끝 사이의 궤적을 함께 검사
- Unreal: `UPrimitiveComponent::SweepComponent`, `CCD` 옵션

## C++ 예시

```cpp
// AABB-AABB 검사: 가장 단순한 narrow phase
FORCEINLINE bool TestAABB(const FBox& A, const FBox& B)
{
    if (A.Max.X < B.Min.X || A.Min.X > B.Max.X) return false;
    if (A.Max.Y < B.Min.Y || A.Min.Y > B.Max.Y) return false;
    if (A.Max.Z < B.Min.Z || A.Min.Z > B.Max.Z) return false;
    return true;
}

// Unreal: 캐릭터의 sweep 이동 (CCD)
FHitResult Hit;
const bool bBlocked = GetWorld()->SweepSingleByChannel(
    Hit,
    StartLocation,
    EndLocation,
    FQuat::Identity,
    ECC_Pawn,
    FCollisionShape::MakeCapsule(Radius, HalfHeight)
);
```

한 프레임에 멀리 이동해도 sweep이 도중 충돌을 포착한다.

## 면접/실무 포인트

- **Q1**: 캐릭터에 Sphere 대신 Capsule을 쓰는 이유? — 보행자처럼 위아래로 길고 360° 회전해도 형태가 동일. 계단 처리와 슬라이딩이 자연스러움.
- **Q2**: Broad phase 자료구조 선택 기준? — 정적이면 grid/octree, 동적이면 BVH 또는 Sweep-and-Prune.
- **Q3**: CCD를 모든 객체에 켜지 않는 이유? — 비용이 크다(궤적 검사). 빠른 발사체·캐릭터에만 선택적으로 적용.
- **Q4**: 두 메시가 정확히 한 점에서 만나는 경우의 부동소수점 함정은? — epsilon 비교, 거리 0 처리, contact manifold 흔들림. impulse가 진동.
- **Q5**: PhysX와 Chaos의 broad phase 차이? — 둘 다 BVH 기반이지만 Chaos는 멀티스레드 친화 설계, GPU broad-phase 옵션도 존재.

## 심화 학습

- EPA(Expanding Polytope Algorithm) — GJK 충돌 시 침투 깊이 계산
- Contact Manifold와 안정성
- Persistent Manifold (프레임 간 접촉점 재사용)
- 관련 페이지: [공간 분할](space-partitioning.md), [물리 엔진 심화](../11-advanced-rendering/physics-engine.md)
