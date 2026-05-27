# 행렬 변환

## 개요

3D 객체의 위치·회전·크기 변경은 모두 **4x4 행렬 곱**으로 통일된다.
"이동(T) → 회전(R) → 크기(S)"를 합쳐 TRS 행렬을 만들고, 부모-자식으로 누적해 최종 월드 행렬을 얻는다.
GPU의 정점 셰이더가 매 정점마다 수행하는 핵심 연산이다.

## 핵심 개념

### TRS 분해

월드 행렬 = T × R × S (열 우선 기준, 점이 오른쪽)

- **Translation (이동)**: 4x4의 마지막 열(또는 행)에 dx, dy, dz
- **Rotation (회전)**: 회전축 + 각도. 3x3 부분 행렬
- **Scale (크기)**: 대각선 sx, sy, sz

곱 순서가 결과를 바꾼다. **`T*R*S`와 `S*R*T`는 다른 결과**.

### 행 우선 vs 열 우선

| 표기 | 점/벡터 위치 | 곱 방향 |
| --- | --- | --- |
| **행 우선 (Row-Major)** | 왼쪽 (행벡터) | `v * M1 * M2` → M1이 먼저 적용 |
| **열 우선 (Column-Major)** | 오른쪽 (열벡터) | `M2 * M1 * v` → M1이 먼저 적용 |

DirectX 셰이더 코드는 보통 행 우선, OpenGL/Unreal HLSL/수학적 표기는 열 우선이 일반적.
**메모리 레이아웃과 수학적 표기는 별개**라는 점에 주의.

### 회전 표현

| 방식 | 메모리 | 짐벌락 | 보간 |
| --- | --- | --- | --- |
| **오일러각** (Yaw/Pitch/Roll) | 3 float | 발생 | 비선형, 어색 |
| **회전 행렬** | 9 float | 없음 | 어려움 |
| **쿼터니언** | 4 float | 없음 | Slerp 가능 |

게임 내부 표현은 거의 항상 쿼터니언. UI 노출(에디터 입력)만 오일러각.

### 짐벌락 (Gimbal Lock)

오일러각으로 90도 회전 시 두 축이 겹쳐 자유도 1개 손실. 카메라/스켈레톤 애니메이션에서 특히 문제.

## C++ 예시

```cpp
// Unreal: FTransform이 TRS를 모두 보관
FTransform Local;
Local.SetLocation(FVector(100, 0, 0));
Local.SetRotation(FQuat(FVector::UpVector, FMath::DegreesToRadians(45.f)));
Local.SetScale3D(FVector(1, 1, 2));

// 부모-자식 누적
FTransform World = Local * Parent->GetActorTransform();

// 행렬로 변환
const FMatrix M = World.ToMatrixWithScale();
// GPU에 전달할 때 보통 전치(transpose) 필요 (셰이더 규약에 따라)
```

`FTransform`은 내부적으로 SIMD 친화. 행렬 직접 곱보다 빠르고 안정적.

### 쿼터니언 보간

```cpp
FQuat A = ...;
FQuat B = ...;
const float Alpha = 0.5f;

// 짧은 호로 보간 (정상 방향)
FQuat Smooth = FQuat::Slerp(A, B, Alpha);
// 성능 우선이면 Nlerp + 정규화
FQuat Fast = FQuat::FastLerp(A, B, Alpha); // 내부적으로 정규화 포함
```

## 심화 학습

- 듀얼 쿼터니언 (스키닝의 트위스트 보존)
- LookAt 행렬 유도와 카메라 좌표계
- SLERP 미분 가능 형태 (애니메이션 블렌딩)
- 관련 페이지: [내적·외적](dot-cross-product.md), [시야각 & 백페이스 컬링](frustum-culling.md)
