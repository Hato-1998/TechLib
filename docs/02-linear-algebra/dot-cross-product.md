# 내적·외적

## 개요

두 벡터 연산만으로 **각도, 투영, 면적, 법선, 회전축** 을 얻을 수 있다.
게임 코드에서 `if (FVector::DotProduct(...) > 0)` 한 줄이 시야 판정·라이팅·백페이스 컬링 등 수많은 결정을 처리한다.

## 내적 (Dot Product)

### 정의

`A · B = |A| * |B| * cos θ`

- 결과는 **스칼라**
- `A · B = Ax*Bx + Ay*By + Az*Bz`

### 의미와 용도

| 결과 | 의미 |
| --- | --- |
| `A · B > 0` | 같은 방향 (예각) |
| `A · B = 0` | 수직 (90°) |
| `A · B < 0` | 반대 방향 (둔각) |

- **각도 계산**: `θ = acos((A·B) / (|A||B|))`
- **투영(projection)**: A를 B 방향으로 정사영한 길이 = `(A·B) / |B|`
- **NPC 시야 판정**: 시선 벡터와 적 방향 벡터의 내적이 cos(시야각 절반)보다 크면 시야 내
- **라이팅**: `N · L` (표면 법선과 광원 방향) — Lambertian 디퓨즈
- **백페이스 컬링**: 카메라 방향과 면 법선의 내적 부호로 면이 카메라를 향하는지 판단

## 외적 (Cross Product)

### 정의

`A × B = (Ay*Bz - Az*By, Az*Bx - Ax*Bz, Ax*By - Ay*Bx)`

- 결과는 **벡터** (A, B 모두에 수직)
- 크기: `|A × B| = |A| * |B| * sin θ`
- 방향: 오른손 법칙(Unreal 좌표계 기준)

### 의미와 용도

- **면 법선 계산**: 삼각형 (V0, V1, V2)의 법선 = `(V1-V0) × (V2-V0)` 정규화
- **회전축 찾기**: 두 벡터 사이를 회전시키는 축은 `A × B` 방향
- **평행사변형 면적**: `|A × B|` 가 두 벡터로 이루어진 평행사변형 면적
- **방향성(좌/우 판정)**: 2D에서 외적 z성분의 부호로 시계/반시계 판정 (CCW vs CW)

## C++ 예시

### 시야 판정 (Dot Product)

```cpp
bool IsInFOV(const AActor* Viewer, const AActor* Target, float HalfFOVDeg)
{
    const FVector Forward = Viewer->GetActorForwardVector();
    const FVector ToTarget = (Target->GetActorLocation() - Viewer->GetActorLocation())
                              .GetSafeNormal();

    const float Threshold = FMath::Cos(FMath::DegreesToRadians(HalfFOVDeg));
    return FVector::DotProduct(Forward, ToTarget) >= Threshold;
}
```

- 정규화한 두 벡터의 내적은 `cos θ`
- `acos` 호출 없이 비교 가능 (성능 이득)

### 삼각형 법선 (Cross Product)

```cpp
FVector ComputeTriangleNormal(const FVector& V0, const FVector& V1, const FVector& V2)
{
    return FVector::CrossProduct(V1 - V0, V2 - V0).GetSafeNormal();
}
```

정점 순서가 법선 방향을 결정한다 — 시계/반시계 규약을 통일해야 컬링이 일관된다.

### 두 벡터 사이 회전축

```cpp
FQuat RotationBetween(const FVector& From, const FVector& To)
{
    const FVector Axis = FVector::CrossProduct(From, To).GetSafeNormal();
    const float Angle = FMath::Acos(FVector::DotProduct(From.GetSafeNormal(), To.GetSafeNormal()));
    return FQuat(Axis, Angle);
}
```

## 면접/실무 포인트

- **Q1**: 내적이 음수면 무엇을 의미? — 두 벡터 각이 90°보다 크다. 시야 밖, 또는 면이 카메라 반대편.
- **Q2**: 외적의 결과 벡터 방향은 어떻게 결정? — 오른손 법칙 (또는 좌표계 따라 왼손). 정점 순서를 바꾸면 법선이 뒤집힌다.
- **Q3**: `acos` 없이 각도 비교를 어떻게? — 정규화한 벡터의 내적을 `cos(임계각)`과 직접 비교. trig 함수 호출 회피.
- **Q4**: 2D 게임에서 외적이 의미 있나? — z 성분 부호만 본다 (좌/우 판정, 폴리곤 winding).
- **Q5**: 라이팅에서 `max(0, N·L)`은 왜? — 빛이 표면 뒤에서 오면 음수가 나오는데, 음의 밝기가 없으므로 0으로 클램프.

## 심화 학습

- 그램-슈미트 직교화
- 외적의 일반화 (Wedge product, 외대수)
- 내적의 BRDF/마이크로페싯 모델에서의 등장
- 관련 페이지: [행렬 변환](matrix-transform.md), [시야각 & 백페이스 컬링](frustum-culling.md), [PBR](../11-advanced-rendering/pbr.md)
