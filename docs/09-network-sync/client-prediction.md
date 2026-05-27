# 클라이언트 예측 & 서버 보정

## 개요

네트워크 RTT가 100ms일 때, 플레이어는 버튼 누른 후 100ms 뒤에 반응을 본다. 이는 "느린" 조작감으로 이어진다. **클라이언트 예측(Client-Side Prediction)**은 클라이언트가 서버 응답을 기다리지 않고 로컬에서 먼저 상태를 진행한 후, 서버 응답이 오면 차이를 조정(Server Reconciliation)하는 기법이다. 격투 게임의 롤백 넷코드(Rollback Netcode)는 이 원리의 극단적 형태이다.

## 핵심 개념

```
전통 방식 (Delay 명백):
입력 발생 → [RTT 대기] → 서버 응답 → 화면 반영
           └─ ~100ms ─┘

예측 방식 (Delay 은닉):
입력 발생 → [로컬 즉시 진행] → 서버 응답 → 차이 보정
           (낙관적)          (조정)
```

| 개념 | 설명 |
|------|------|
| **Prediction** | 클라가 로컬에서 다음 상태 시뮬레이션 (물리, 입력) |
| **Server Authority** | 서버가 실제 상태 계산 → 클라와 차이 발생 |
| **Reconciliation** | 서버 상태와 클라 상태 일치시키기 (스냅/부드러운 보정) |
| **Replay** | 조정 후 이후 입력들 다시 시뮬레이션 |
| **Rollback Netcode** | 역사 프레임 저장 → 예측 실패 시 롤백 → 빠른 응답 (FPS/격투) |

## 클라이언트 예측 흐름 (Unreal)

```
프레임 N (로컬):
  1. 입력 수집: Move(100, 0)
  2. 로컬 상태 업데이트: Pos += Velocity * DT
  3. 입력 ID 저장: InputID = 42

  ↓ 네트워크 송신 (이후 프레임들)

프레임 N+6 (약 100ms 뒤):
  서버 응답 도착: ServerState = (Pos: 98, 0)
  
  예측 상태: (Pos: 102, 0)
  
  오차: 4 units
  
  보정:
  - 즉시 스냅: Pos = 98 (끊김 보임)
  - 부드러운 보정: Pos -= 4 / 8 per frame (8 프레임)

프레임 N+14:
  완전히 일치
```

## Unreal UCharacterMovementComponent 예측

```cpp
// 캐릭터 이동 예측 구현
void AMyCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    
    if (IsLocallyControlled())
    {
        // 로컬: 즉시 진행
        FVector InputDirection = GetInputVector();
        FVector NewLocation = GetActorLocation() + InputDirection * 600.0f * DeltaTime;
        SetActorLocation(NewLocation);
        
        // 입력 정보와 함께 서버로 전송
        ServerMove(NewLocation, InputDirection);
    }
}

// 서버: 권위있는 상태 계산
void AMyCharacter::ServerMove_Implementation(FVector ClientLocation, FVector InputDir)
{
    // 서버가 다시 시뮬레이션
    FVector ServerLocation = GetActorLocation() + InputDir * 600.0f * GetWorld()->GetDeltaSeconds();
    
    // 클라 위치와 크게 다르면 기본
    if (FVector::Dist(ServerLocation, ClientLocation) > 50.0f)
    {
        // 명백한 부정행위 또는 예측 오차
        SetActorLocation(ServerLocation);
    }
    
    // 보정 정보를 모든 클라에게 브로드캐스트
    MulticastCorrectPosition(ServerLocation);
}

// 모든 클라: 서버 보정 적용
void AMyCharacter::MulticastCorrectPosition_Implementation(FVector ServerPos)
{
    if (!IsLocallyControlled())
    {
        // 원격 클라: 스냅 또는 부드러운 보정
        SetActorLocation(ServerPos);
    }
    else
    {
        // 로컬: 미세 조정
        FVector Error = ServerPos - GetActorLocation();
        
        if (FMath::Abs(Error.Length()) > 100.0f)
        {
            // 큰 오차: 스냅
            SetActorLocation(ServerPos);
        }
        else
        {
            // 작은 오차: 부드럽게
            SetActorLocation(GetActorLocation() + Error * 0.1f);
        }
    }
}
```

## 롤백 넷코드 (Rollback Netcode)

격투 게임에서 사용. 예측 오류 발생 시 과거 프레임으로 되돌린 후 다시 시뮬레이션.

```
프레임 1-20: 로컬 입력 진행 (낙관적)
프레임 21: 상대 입력 도착 (RTT 이후)
         예측과 다름 → 롤백 필요

프레임 20으로 상태 복원
프레임 20: 상대 입력 적용 후 시뮬레이션
프레임 21-현재: 재계산 후 화면에 표시

결과: 끊김 없음 (대부분 유저 미감지)
```

```cpp
// 간단한 게임 상태 롤백 구조
struct FGameState
{
    FVector PlayerPos;
    float PlayerHealth;
    int32 Frame;
};

TArray<FGameState> HistoryBuffer;  // 최근 60프레임 저장

void SaveState(int32 Frame, const FGameState& State)
{
    if (HistoryBuffer.Num() > 60)
        HistoryBuffer.RemoveAt(0);  // 오래된 것 제거
    
    HistoryBuffer.Add(State);
}

void RollbackAndReplay(int32 TargetFrame)
{
    // 1. 타겟 프레임으로 복원
    FGameState& Target = HistoryBuffer[TargetFrame];
    CurrentState = Target;
    
    // 2. 이후 입력들 다시 재생
    for (int32 i = TargetFrame; i < CurrentFrame; ++i)
    {
        ApplyInput(StoredInputs[i]);
        SimulatePhysics(DeltaTime);
    }
}
```

## 예측 vs 부드러운 보정 (Interpolation)

```cpp
// A. 예측 기반 (FPS, 액션 게임)
// 장점: 낮은 지연, 반응성 높음
// 단점: 오류 누적, 시각적 버그 가능
void PredictiveMove()
{
    NewPos = LastPos + Velocity * DT;
    Velocity += Acceleration * DT;
}

// B. 보간 기반 (RPG, 느린 게임)
// 장점: 안정적, 예측 오류 없음
// 단점: 입력이 "늦은" 느낌
void InterpolateMove()
{
    NewPos = Lerp(LastServerPos, NextServerPos, Alpha);
    Alpha += DT / NetworkTickTime;
}

// C. 혼합 (최적)
void HybridMove(float DeltaTime)
{
    // 로컬: 예측
    PredictiveMove();
    
    // 이따금 서버 보정
    if (ErrorTooLarge())
    {
        // 부드럽게 조정
        SetActorLocation(Lerp(GetActorLocation(), ServerPos, 0.1f));
    }
}
```

## 면접/실무 포인트

- **Q1**: 예측이 항상 맞을 수 없다면, 왜 사용할까?
  - 대부분의 프레임(90%+)은 예측 맞음. 틀린 프레임만 보정.
  - 유저 입장: 즉각적 반응(낮은 지연) > 가끔 미세 조정(오류 보정).

- **Q2**: 격투 게임의 롤백 넷코드와 FPS 예측의 차이?
  - 격투: 프레임-perfect (60fps, 매 프레임 중요) → 롤백.
  - FPS: 연속 움직임 → 예측+보간.

- **Q3**: "저는 예측 오류를 보지 못한다"?
  - 좋은 신호: 예측이 대부분 맞고, 보정이 부드럽다는 뜻.
  - 검증: 서버 위치와 로컬 위치 디버그 표시 → 오차 크기 추적.

## 심화 학습

- 키워드: Deterministic Simulation, Frame Jitter Compensation, Netcode Rollback
- 논문: "GGPO: Good Game Peace Out" (P2P 격투 게임 표준)
- Unreal: `UCharacterMovementComponent::MaxNetworkUpdateRate`
- 관련 페이지: [09-network-sync/index.md](./index.md), [dead-reckoning](./dead-reckoning.md)
