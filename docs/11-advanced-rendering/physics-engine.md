# 물리 엔진 & 경직체 동역학

## 개요

게임의 물리 엔진은 현실의 뉴턴 역학을 디지털로 재현한다. 경직체(Rigid Body)의 위치, 회전, 속도, 각속도 계산부터 충돌 감지, 제약 조건(joint) 해결까지 복잡한 계산이 필요하다. Unreal Engine 5는 PhysX에서 자체 개발 엔진 Chaos로 전환했으며, 이는 더 나은 성능, 확장성, 게임 피드백을 제공한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **경직체 (Rigid Body)** | 변형하지 않는 물체. 질량, 위치, 회전으로 표현 |
| **힘과 토크** | Force = m*a, Torque = I*α (각 가속도) |
| **충돌 감지** | Continuous vs Discrete. 고속 물체는 CCD 필요 |
| **제약 솔버** | 조인트 조건 만족시키는 반발력 계산 (Sequential Impulse) |
| **동역학 vs 운동학** | 동역학: 힘 기반 (리얼). 운동학: 직접 이동 (빠름) |
| **소프트바디** | 변형 가능 (cloth, jello). 복잡도↑ |

## 경직체 동역학 기초

```
상태 벡터:
  r = [x, y, z]           (위치)
  v = [vx, vy, vz]        (선속도)
  ω = [ωx, ωy, ωz]        (각속도)
  q = [qx, qy, qz, qw]    (회전, 쿼터니언)

힘의 적분:
  a = F / m
  v = v + a * dt
  r = r + v * dt
  
  α = I^-1 * τ  (τ = 토크, I = 관성 텐서)
  ω = ω + α * dt
  q = q + 0.5 * ω_quat * q * dt
```

## Unreal Chaos 물리 설정

```cpp
// Actor 물리 활성화
AMyRigidBody::AMyRigidBody()
{
    // 메시 컴포넌트
    UStaticMeshComponent* Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    
    // 물리 활성화
    Mesh->SetSimulatePhysics(true);
    Mesh->SetPhysicsEnabled(true);
    
    // 질량 설정
    Mesh->SetMassOverrideInKg(NAME_None, 10.0f, true);
    
    // 중력 적용
    Mesh->AddForce(FVector(0, 0, -980) * 10.0f);  // m * g
    
    RootComponent = Mesh;
}

// 런타임 힘 적용
void AMyRigidBody::ApplyForce()
{
    UPrimitiveComponent* Comp = Cast<UPrimitiveComponent>(RootComponent);
    
    // 선형 힘
    Comp->AddForce(FVector(1000, 0, 0));
    
    // 각 력 (토크)
    Comp->AddTorque(FVector(0, 0, 500));
}
```

## 제약 솔버: Sequential Impulse

```
제약 조건 (예: Distance Constraint):
  ||r_A - r_B|| = L  (고정 거리 L)

위반 시 보정:
  1. 반발력(impulse) J 계산
  2. 각 바디에 -J, +J 적용
  3. 속도 업데이트: v += J / m
  4. 반복 (여러 iteration)

예시 (거리 조인트):
  Body A ←──── 10 units ────→ Body B
  
  오차: 15 units (멀어짐)
  
  보정력 계산 → 서로에게 끌어당기는 임펄스
  여러 iteration 후 → 10 units로 복귀
```

```cpp
// Unreal: 물리 제약 컴포넌트
UPhysicsConstraintComponent* Constraint = NewObject<UPhysicsConstraintComponent>();

// Distance constraint 설정
Constraint->ConstraintInstance.SetLinearXLimit(LCM_Limited, 50.0f);  // X축 50cm 범위
Constraint->ConstraintInstance.SetLinearYLimit(LCM_Limited, 50.0f);
Constraint->ConstraintInstance.SetLinearZLimit(LCM_Limited, 50.0f);

// 두 바디 연결
Constraint->SetConstrainedComponents(BodyA, NAME_None, BodyB, NAME_None);

// 경성도(stiffness) 조절 (0~1, 1이 더 경직)
Constraint->ConstraintInstance.ProfileInstance.LinearLimit.Stiffness = 0.8f;
Constraint->ConstraintInstance.ProfileInstance.LinearLimit.Damping = 0.1f;
```

## 연속 충돌 감지 (CCD)

```
문제: 고속 물체가 얇은 벽 "통과" 가능
  ├─ Frame N: 위치 = x
  └─ Frame N+1: 위치 = x+1000 (한 프레임에 1000 units)
  → 충돌 검사 안 함 (이미 벽 너머)

해결: CCD (Continuous Collision Detection)
  ├─ 스윕 테스트: x → x+1000 경로에서 충돌 확인
  ├─ 충돌 시점 t ∈ [0,1] 계산
  └─ t 위치에서 이동 중단
```

```cpp
// CCD 활성화
UPrimitiveComponent* Mesh = ...;
Mesh->SetUseCCD(true);  // 연속 충돌 감지 활성화

// 추가 설정
Mesh->SetRigidBodyResponseToChannels(ECC_Pawn, ECR_Block);  // 폰과 충돌

// CCD는 계산 비용 증가하므로, 필요한 객체에만 활성화
// (예: 총알, 고속 캐릭터)
```

## 소프트바디 & 천 물리

```cpp
// Cloth 컴포넌트 (Chaos Cloth)
AClothActor::AClothActor()
{
    USkeletalMeshComponent* SkeletalMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
    
    // 천 시뮬레이션 활성화 (머티리얼 설정 필요)
    // 시뮬레이션 프로퍼티: 중력, 댐핑, 바람, 충돌
}

// 파괴 가능 메시
ADestructibleActor::ADestructibleActor()
{
    UGeometryCollectionComponent* Collection = CreateDefaultSubobject<UGeometryCollectionComponent>(TEXT("Geometry"));
    Collection->SetSimulatePhysics(true);
    
    // 손상 또는 폭발 시 자동 파괴됨
}
```

## 충돌 채널 & 응답

```cpp
// 커스텀 충돌 채널 설정
enum ECC_GameTraceChannel1 = 32,  // 게임 채널 (물리 > 충돌)

// Actor 충돌 응답 설정
void AMyActor::SetCollisionChannels()
{
    UPrimitiveComponent* Comp = Cast<UPrimitiveComponent>(RootComponent);
    
    // 이 객체의 채널
    Comp->SetObjectType(ECC_GameTraceChannel1);
    
    // 다른 채널과의 상호작용
    Comp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);     // 폰 무시
    Comp->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block); // 월드와 충돌
}
```

## 성능 최적화

```
물리 시뮬레이션 비용 감소:
  1. 불필요한 바디 비활성화 (Sleep 상태)
  2. Simple collision 사용 (복잡한 메시 대신)
  3. CCD는 필요한 것에만 활성화
  4. 제약 solver iteration 감소 (4→2)
  5. SubStepping 비활성화 (필요한 경우만)
```

```cpp
// 바디 Sleep 상태 (충돌 없으면 자동)
Comp->PutRigidBodyToSleep();

// Solver iteration (낮을수록 빠름, 정확도↓)
GetWorld()->GetPhysicsScene()->SetPhysicsConstraintIterations(2);  // Default 4

// Substepping 설정 (프레임 더 세분화)
Comp->SetPhysicsMaxAngularVelocity(1000.0f, false, false);
```

## 면접/실무 포인트

- **Q1**: PhysX vs Chaos, 어떤 게 나을까?
  - Chaos: UE5 기본, 더 나은 성능, 게임 친화적.
  - PhysX: 레거시 지원, 외부 프로젝트와 호환.

- **Q2**: 물리 시뮬레이션이 프레임을 먹는다?
  - Actor 개수 감소 (Pool 사용).
  - Collision complexity 낮춤 (Simple → Complex).
  - Tick 빈도 감소 (고정 rate 시뮬레이션).

- **Q3**: 고속 총알이 벽을 통과한다?
  - CCD 활성화.
  - Mesh collision 복잡도 확인.

## 심화 학습

- 키워드: Constraint Graphs, Island Management, Broad-Phase Collision
- Unreal: `FPhysicsCommand`, `FPhysScene`
- 논문: "Real-Time Physics Simulation" (NVIDIA GTC)
- 관련 페이지: [11-advanced-rendering/index.md](./index.md), [pbr.md](./pbr.md)
