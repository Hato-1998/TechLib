# 추측 항법 & 보간

## 개요

**추측 항법(Dead Reckoning)**은 해상 항법 용어에서 온 개념이다. 배가 마지막으로 확인한 위치에서 속도와 시간을 이용해 현재 위치를 추정하는 것처럼, 게임에서는 네트워크 업데이트 사이에 엔티티의 속도/가속도를 이용해 위치를 외삽(extrapolation)한다. RPG, MOBA, 배틀로얄 같은 느린 게임에서 자주 사용되며, 원격 플레이어/NPC의 부드러운 이동 표현이 핵심이다.

## 핵심 개념

```
마지막 알려진 상태 (T0):
  위치 P0 = (100, 200)
  속도 V = (50, 0) m/s

현재 시간 (T1 = T0 + 0.5s), 서버 업데이트 미도착:

외삽(Extrapolation):
  P(T1) = P0 + V * (T1 - T0)
        = (100, 200) + (50, 0) * 0.5
        = (125, 200)

=> 서버 업데이트 없이 로컬에서 계산
```

| 개념 | 설명 |
|------|------|
| **Extrapolation (외삽)** | 마지막 데이터 기반 미래 값 추정. 선형/2차 다항식 |
| **Interpolation (보간)** | 알려진 두 점 사이의 값 추정. Lerp/Slerp |
| **Smoothing** | 보간 결과를 시간 축에 펴기 (부드러운 곡선) |
| **Snap Threshold** | 오차가 크면 즉시 스냅, 작으면 부드럽게 조정 |
| **Lag Compensation** | 네트워크 지연 고려한 동기화 |

## 추측 항법의 기본 공식

```
선형 추정 (1차):
  P(t) = P0 + V * Δt

2차 추정 (가속도 포함):
  P(t) = P0 + V * Δt + 0.5 * A * Δt²

예시 (캐릭터 속도 200 units/s, 가속도 50 units/s²):
  Δt = 1.0s 이후:
    선형: P = P0 + 200 * 1.0 = P0 + 200
    2차: P = P0 + 200 * 1.0 + 0.5 * 50 * 1.0² = P0 + 225
```

## Unreal 구현: 원격 플레이어 이동

```cpp
// 원격 플레이어 구조
class ARemoteCharacter : public ACharacter
{
public:
    UPROPERTY()
    FVector LastReceivedPosition;
    
    UPROPERTY()
    FVector LastReceivedVelocity;
    
    UPROPERTY()
    float LastUpdateTime;
    
    virtual void Tick(float DeltaTime) override;
    
    // 서버에서 받은 업데이트
    UFUNCTION()
    void OnNetworkUpdate(FVector NewPos, FVector NewVel);
};

void ARemoteCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    
    // 추측 항법으로 위치 계산
    float TimeSinceUpdate = GetWorld()->GetTimeSeconds() - LastUpdateTime;
    
    FVector ExtrapolatedPos = LastReceivedPosition + LastReceivedVelocity * TimeSinceUpdate;
    
    // 매번 즉시 이동 vs 부드럽게 이동?
    // 즉시: SetActorLocation(ExtrapolatedPos);
    // 부드럽게:
    FVector CurrentPos = GetActorLocation();
    FVector SmoothedPos = FMath::Lerp(CurrentPos, ExtrapolatedPos, 0.1f);
    SetActorLocation(SmoothedPos);
}

void ARemoteCharacter::OnNetworkUpdate(FVector NewPos, FVector NewVel)
{
    float Error = FVector::Dist(GetActorLocation(), NewPos);
    
    if (Error > 100.0f)
    {
        // 큰 오차 (서버 권한 변경, 추측 실패): 스냅
        SetActorLocation(NewPos);
    }
    else
    {
        // 작은 오차: 부드럽게 조정 (아래 참조)
    }
    
    LastReceivedPosition = NewPos;
    LastReceivedVelocity = NewVel;
    LastUpdateTime = GetWorld()->GetTimeSeconds();
}
```

## 보간 vs 외삽 트레이드오프

```cpp
// A. 보간 (Interpolation) - "과거 재생"
//    → 느린 게임, 일관성 중요
void InterpolateMovement(float DeltaTime)
{
    // T0, T0+TickRate 사이 보간
    // T1에는 항상 "이미 일어난 것" 재생
    float Alpha = (CurrentTime - LastPacketTime) / TickRate;
    
    FVector DisplayPos = Lerp(Pos[0], Pos[1], Alpha);
    SetActorLocation(DisplayPos);
    
    // 장점: 항상 안전 (서버 확인됨)
    // 단점: TickRate 지연 누적
}

// B. 외삽 (Extrapolation) - "미래 예측"
//    → 액션 게임, 반응성 중요
void ExtrapolateMovement(float DeltaTime)
{
    // 마지막 패킷 이후로 계속 진행
    float DeltaSincePacket = CurrentTime - LastPacketTime;
    
    FVector DisplayPos = LastPacketPos + LastPacketVel * DeltaSincePacket;
    SetActorLocation(DisplayPos);
    
    // 장점: 낮은 지연
    // 단점: 잘못된 예측 가능 (물리 변화, 매직 등)
}

// C. 혼합 (Hybrid)
void HybridMovement(float DeltaTime)
{
    float TimeSincePacket = CurrentTime - LastPacketTime;
    
    if (TimeSincePacket < TickRate * 0.5f)
    {
        // 신선한 패킷: 보간
        float Alpha = TimeSincePacket / TickRate;
        SetActorLocation(Lerp(OldPos, NewPos, Alpha));
    }
    else
    {
        // 오래된 패킷: 외삽
        SetActorLocation(NewPos + NewVel * (TimeSincePacket - TickRate));
    }
}
```

## 부드러운 조정 (Smoothing)

```cpp
struct FMovementState
{
    FVector Position;
    FVector Velocity;
    double LastUpdateTime;
};

void SmoothCorrection(FVector ServerPos, float CorrectionSpeed = 0.1f)
{
    FVector CurrentPos = GetActorLocation();
    FVector Error = ServerPos - CurrentPos;
    
    // 에러 크기에 따라 조정 속도 결정
    if (Error.Length() < 50.0f)
    {
        // 작은 오차: 느리게 조정 (플레이어 미감지)
        FVector CorrectedPos = CurrentPos + Error * CorrectionSpeed;
        SetActorLocation(CorrectedPos);
    }
    else if (Error.Length() < 150.0f)
    {
        // 중간 오차: 중속 조정
        FVector CorrectedPos = CurrentPos + Error * 0.5f;
        SetActorLocation(CorrectedPos);
    }
    else
    {
        // 큰 오차: 즉시 스냅 (명백한 이벤트)
        SetActorLocation(ServerPos);
    }
}
```

## Snap Threshold 설계

```cpp
enum class EMovementCorrectionType
{
    Smooth,  // 부드러운 보간
    Snap,    // 즉시 스냅
    Teleport // 명백한 텔레포트
};

EMovementCorrectionType GetCorrectionType(float ErrorDistance)
{
    // 게임마다 다르지만, 일반적인 기준:
    if (ErrorDistance < 50.0f)
        return EMovementCorrectionType::Smooth;    // 네트워크 지터 수준
    
    if (ErrorDistance < 200.0f)
        return EMovementCorrectionType::Snap;      // 조작 실패/기술 사용
    
    return EMovementCorrectionType::Teleport;      // 맵 이동/리스폰
}

void ApplyMovementCorrection(FVector ServerPos, float ErrorDistance)
{
    EMovementCorrectionType Type = GetCorrectionType(ErrorDistance);
    
    switch (Type)
    {
        case EMovementCorrectionType::Smooth:
            SmoothCorrection(ServerPos, 0.05f);  // 시간에 걸쳐 조정
            break;
        
        case EMovementCorrectionType::Snap:
            SetActorLocation(ServerPos);  // 한 프레임에 이동
            break;
        
        case EMovementCorrectionType::Teleport:
            PlayTeleportEffect();
            SetActorLocation(ServerPos);
            break;
    }
}
```

## 심화 학습

- 키워드: Lag-Compensated Movement, Angular Interpolation (Slerp/Quaternion)
- Unreal: `FMath::Lerp`, `FQuat::Slerp`, `FVector::Lerp`
- 관련 페이지: [09-network-sync/index.md](./index.md), [client-prediction](./client-prediction.md)
