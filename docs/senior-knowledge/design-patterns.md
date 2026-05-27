# 게임 디자인 패턴

## 개요

디자인 패턴은 반복되는 설계 문제의 재사용 가능한 해결책이다. 게임 개발은 메모리 효율, 유연한 엔티티 구성, 느슨한 결합, 상태 관리 같은 독특한 요구사항이 있어서, 일반적인 GoF 패턴보다 **게임 특화 패턴**이 더 유용한다.

## 게임 필수 패턴 7가지

| 패턴 | 문제 | 해결책 |
|------|------|--------|
| **Object Pool** | 런타임 메모리 할당 비용 | 미리 객체 준비, 재사용 |
| **Component** | 엔티티 다양한 기능 조합 | 컴포넌트 기반 구성 |
| **State Machine** | 상태 전이 복잡도 | 명확한 상태 정의 |
| **Observer/Event Bus** | 엔티티 간 강한 결합 | 비동기 이벤트 중개 |
| **Service Locator** | 전역 싱글톤 남용 | 서비스 레지스트리 |
| **Command** | Undo/Replay 구현 | 명령 객체화 |
| **Flyweight** | 대량 작은 객체 메모리 | 공유 상태 분리 |

### 1. Object Pool

```cpp
// 문제: 매 프레임 100개 탄환 생성/삭제
for (int32 i = 0; i < 100; ++i)
{
    new ABullet();  // ← malloc 오버헤드
}

// 해결: 미리 객체 준비
class ABulletPool
{
    TArray<ABullet*> AvailableBullets;
    TArray<ABullet*> ActiveBullets;
    
public:
    ABullet* GetBullet()
    {
        if (AvailableBullets.Num() > 0)
        {
            ABullet* B = AvailableBullets.Pop();
            ActiveBullets.Add(B);
            return B;  // 기존 객체 재사용
        }
        return nullptr;  // 풀 부족
    }
    
    void ReturnBullet(ABullet* Bullet)
    {
        ActiveBullets.Remove(Bullet);
        AvailableBullets.Add(Bullet);
        Bullet->Reset();
    }
};

// 사용
ABullet* B = BulletPool->GetBullet();
if (B) B->Fire(Direction);
// 나중에
BulletPool->ReturnBullet(B);
```

**효과**: 메모리 할당 0 → 프레임 타임 일정.

### 2. Component (Composition)

```cpp
// 문제: 상속 구조 복잡화
class ACharacter : public APawn {}
class AEnemy : public ACharacter {}
class AEnemyFlyingType : public AEnemy {}  // 깊은 상속
class AEnemyMeleeType : public AEnemy {}

// 해결: 컴포넌트 조합
class UMovementComponent : public UActorComponent
{
    virtual void Move(FVector Direction) = 0;
};

class UWalkComponent : public UMovementComponent
{
    void Move(FVector Direction) override { /* 걷기 */ }
};

class UFlyComponent : public UMovementComponent
{
    void Move(FVector Direction) override { /* 날기 */ }
};

// 엔티티 정의
ACharacter* Enemy = CreateActor();
Enemy->AddComponent(NewObject<UWalkComponent>());  // 또는 UFlyComponent
Enemy->AddComponent(NewObject<UAttackComponent>());
Enemy->AddComponent(NewObject<UHealthComponent>());

// 유연성: 같은 Actor도 구성 다르게
```

### 3. State Machine

```cpp
class ACharacterStateMachine
{
    enum EState { Idle, Running, Jumping, Falling, Dead };
    EState CurrentState = Idle;
    
    void Update(float DeltaTime)
    {
        switch (CurrentState)
        {
            case Idle:
                HandleIdleInput();
                break;
            case Running:
                UpdateRunning(DeltaTime);
                break;
            case Jumping:
                UpdateJumping(DeltaTime);
                break;
            case Dead:
                // 상태 전이 불가
                break;
        }
    }
    
    void TransitionTo(EState NewState)
    {
        // 유효한 전이만 허용
        if (CanTransition(CurrentState, NewState))
        {
            ExitState(CurrentState);
            CurrentState = NewState;
            EnterState(CurrentState);
        }
    }
    
    bool CanTransition(EState From, EState To)
    {
        // Dead → 다른 상태 불가
        if (From == Dead) return false;
        // Jumping → Running 불가 (공중)
        if (From == Jumping && To == Running) return false;
        return true;
    }
};
```

### 4. Observer / Event Bus (Unreal GameplayMessage)

```cpp
// 문제: 플레이어 사망 → 10개 시스템 업데이트
// 각 시스템이 PlayerController 참조 필요 → 강한 결합

// 해결: 이벤트 중개소
struct FPlayerDeadMessage
{
    ACharacter* DeadCharacter;
    ACharacter* Killer;
};

// 발행
void ACharacter::Die()
{
    FPlayerDeadMessage Message;
    Message.DeadCharacter = this;
    Message.Killer = LastDamageInstigator;
    
    UGameplayMessageSubsystem::Get()->BroadcastMessage<FPlayerDeadMessage>(Message);
    // 모든 리스너에게 비동기 전달
}

// 구독
void AUIManager::PostInitializeComponents()
{
    Super::PostInitializeComponents();
    
    UGameplayMessageSubsystem::Get()->ListenForMessages<FPlayerDeadMessage>(
        this,
        [this](FGameplayMessageHandle Handle, const FPlayerDeadMessage& Message)
        {
            UpdateDeadScreen(Message.DeadCharacter);
        }
    );
}

// 장점: UI 매니저, Audio 매니저, Score 시스템 모두 독립적
```

### 5. Service Locator (Subsystem)

```cpp
// 문제: 전역 싱글톤
class AGameMode* GGameMode = nullptr;
void SomeFunction() { GGameMode->OnPlayerKilled(); }

// 해결: Subsystem (Unreal 표준)
class UGameplaySubsystem : public UWorldSubsystem
{
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    void OnPlayerKilled(ACharacter* Killer);
};

// 접근
UGameplaySubsystem* GameSys = GetWorld()->GetSubsystem<UGameplaySubsystem>();
GameSys->OnPlayerKilled(Instigator);

// 또는 GameInstance subsystem (전역 수준)
UGlobalGameSystem* Global = GetGameInstance()->GetSubsystem<UGlobalGameSystem>();
```

### 6. Command (Undo/Replay)

```cpp
class FCommand
{
public:
    virtual void Execute() = 0;
    virtual void Undo() = 0;
};

class FMoveCommand : public FCommand
{
    AActor* Actor;
    FVector OldLocation, NewLocation;
    
    void Execute() override { Actor->SetActorLocation(NewLocation); }
    void Undo() override { Actor->SetActorLocation(OldLocation); }
};

// 커맨드 히스토리
TArray<FCommand*> CommandHistory;
int32 HistoryIndex = -1;

void ExecuteCommand(FCommand* Cmd)
{
    Cmd->Execute();
    CommandHistory.Add(Cmd);
    HistoryIndex++;
}

void Undo()
{
    if (HistoryIndex >= 0)
    {
        CommandHistory[HistoryIndex]->Undo();
        HistoryIndex--;
    }
}

// Replay: 같은 커맨드 순서대로 Execute
```

### 7. Flyweight (메모리 공유)

```cpp
// 문제: 1000개 나무, 각각 텍스처/메시 메모리
struct ATree
{
    UStaticMesh* TreeMesh;  // 1000개 포인터 (모두 동일)
    UTexture* Bark;
    UTexture* Leaves;
};

// 해결: 공유 리소스
struct FTreeType
{
    UStaticMesh* Mesh;
    UTexture* Bark;
    UTexture* Leaves;
};

struct ATree
{
    FTreeType* Type;  // 공유
    FVector Position;  // 고유
    FRotator Rotation;
};

// 메모리: 1000 * sizeof(FVector + FRotator) + 1 * FTreeType
// vs
// 1000 * (3 포인터 + Vector + Rotator)
```

## 안티패턴 (피해야 할 것)

| 안티패턴 | 문제 | 해결책 |
|---------|------|--------|
| **God Object** | AGameMode/APlayerController에 모든 로직 | 기능 분산 (Subsystem) |
| **Singleton 남용** | 전역 상태, 테스트 어려움 | Service Locator / Subsystem |
| **강한 결합** | ClassA → ClassB → ClassC 참조 | 이벤트 버스 중개 |
| **Deep Inheritance** | 3단계 이상 상속 | Component 조합 |

## 심화 학습

- 키워드: Behavioral Pattern, Structural Pattern, Real-Time Constraints
- 관련 페이지: [12-oop-vs-dod-ecs](../12-oop-vs-dod-ecs/index.md), [code-review](./code-review.md)
