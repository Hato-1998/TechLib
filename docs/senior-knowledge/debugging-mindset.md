# 디버깅 마인드셋

## 개요

**"제가 버그를 본 적이 없어요"**라고 말하는 시니어는 없다. 대신 시니어는 **버그를 빠르게 찾고, 원인을 정확히 파악하고, 근본 해결책을 구현**한다. 이는 디버깅 도구의 숙련도보다는 **문제 분해 능력**, **가설 검증 체계**, **결정성 재현(deterministic reproduction)**의 중요성을 이해하는 마인드셋에서 나온다.

## 핵심 원칙

```
디버깅 주기:
  1. 현상 관찰 (What)
  2. 가설 수립 (Why)
  3. 가설 검증 (Test)
  4. 근본 원인 파악 (Root Cause)
  5. 수정 및 재현 (Fix & Verify)
```

| 원칙 | 의미 |
|------|------|
| **결정성 첫 번째** | 재현 불가능하면 수정 불가능. "가끔" 뜬다? → 먼저 재현성 확보 |
| **격리 (Isolation)** | 한 번에 한 가지만 변경. 변수 많으면 원인 추적 어려움 |
| **가설 기반** | 무작정 코드 읽지 말고, "여기가 문제"라는 가설 세운 후 확인 |
| **도구 선택** | 로그 vs 디버거 vs 프로파일러, 상황에 맞게 |
| **최소 재현** | 전체 게임 재현 vs 단위 테스트 → 최소화하기 |

## 결정성 재현 (Deterministic Repro)

```
문제: "게임이 가끔 크래시"
↓ (나쁜 접근)
전체 게임 플레이 → "크래시 안 네?" → 반복 시도 (시간 낭비)

↓ (좋은 접근)
1. 언제 크래시? → 특정 시나리오
2. 재현 가능? → 매번 재현되는지 확인
3. 조건 단순화 → 최소 케이스
4. 단위 테스트 작성 → 자동화
```

```cpp
// 크래시 재현 최소화 예시
void TestCharacterDeath()
{
    ACharacter* Char = World->SpawnActor<ACharacter>();
    Char->SetHealth(0);  // 직접 사망 조건 재현
    
    // 크래시 발생 시점까지만 실행
    Char->OnDeath();
    
    // 결과 검증
    check(Char->GetHealth() == 0);
}

// 장점: 게임 30분 플레이 → 1초 테스트
```

## 디버거 vs 프로파일러 vs 로그

| 상황 | 최적 도구 | 이유 |
| --- | --- | --- |
| 변수 값 추적 | 디버거 | 중단점, 스택·로컬 변수 검사 |
| 프레임 드롭 | 프로파일러 | 타임라인, 핫스팟 시각화 |
| 논리 흐름 오류 | 로그 | 조건부 마크 지점, 시간 압박 없음 |
| 메모리 누수 | 프로파일러 / 로그 | 메모리 증가 추적 |
| 다중스레드 경합 | 디버거 + 로그 | 경쟁 조건 기록 (TSAN 보조) |
| 네트워크 문제 | 로그 | RPC 순서·타이밍 추적 |

### 디버거 (Breakpoint)
```cpp
// 언제 써야 하나?
// - 변수 상태를 "보고 싶을 때"
// - 콜스택 확인 필요
// - 한 줄씩 실행

int32 HP = 100;
Char->TakeDamage(50);  // ← 여기서 중단점
// 스택 보기: TakeDamage(50)
//   → OnDamageTaken(50)
//   → SetHealth(-50)  ← 버그! 마이너스?
```

### 프로파일러 (Timeline)
```cpp
// 언제 써야 하나?
// - "어디가" 느린지 알고 싶을 때
// - 프레임 전체 흐름 이해
// - 성능 최적화

stat startfile
for (int i = 0; i < 100; ++i)
{
    SCOPE_CYCLE_COUNTER(STAT_HeavyOperation);
    DoWork();
}
stat stopfile
// → Insights: HeavyOperation이 전체의 70%? 병목 확인됨
```

### 로그 (UE_LOG)
```cpp
// 언제 써야 하나?
// - 조건부 흐름 추적
// - 실시간 게임 플레이 중 (디버거 일시정지 불가)
// - 네트워크/멀티스레드 (동시성)

void ACharacter::TakeDamage(float Amount)
{
    UE_LOG(LogDamage, Warning, TEXT("Before Health: %f"), GetHealth());
    Health -= Amount;
    UE_LOG(LogDamage, Warning, TEXT("After Health: %f"), GetHealth());
    
    if (Health < 0)
    {
        UE_LOG(LogDamage, Error, TEXT("Health went negative! Clamping."));
        Health = 0;  // 버그 수정
    }
}

// 장점: 재현 후 로그 파일 검토 (시간 압박 없음)
```

## 다중스레드 문제 (Race Condition, Heisenbug)

```
Heisenbug = 디버거로 찾으면 나타나지 않는 버그
원인: 디버거 중단점 → 다른 스레드 대기 → 타이밍 변함
```

```cpp
// 문제 코드
class ANetworkActor
{
    float Value;
};

// 메인 스레드
void Tick(float DeltaTime)
{
    Value = 42;  // 쓰기
}

// 백그라운드 스레드
void BackgroundWork()
{
    float Temp = Value;  // 읽기
    // 동시 실행 → Race condition
}

// 해결
void Tick(float DeltaTime)
{
    FScopeLock Lock(&Mutex);
    Value = 42;
}

void BackgroundWork()
{
    FScopeLock Lock(&Mutex);
    float Temp = Value;  // 안전
}
```

## Crash Dump 분석

Windows에서 .dmp 파일 분석 (WinDbg 또는 Visual Studio):

```
1. .dmp 파일 + PDB (디버그 심볼) 준비
2. Visual Studio: File → Open → Crash dump
3. 스택 트레이스 확인
   │
   ├─ Frame 0: GetActorLocation() + 0x12
   ├─ Frame 1: UpdatePosition() + 0x45
   ├─ Frame 2: Tick() + 0x78
   └─ Frame 3: FTickableGameObject::TickMe()

4. 가장 낮은 프레임 = 크래시 지점
   "GetActorLocation()에서 nullptr 접근?"
```

```cpp
// 방어적 코딩 + 로그
FVector AMyActor::GetSafeLocation()
{
    if (!this)
    {
        UE_LOG(LogTemp, Error, TEXT("GetSafeLocation called on nullptr!"));
        return FVector::ZeroVector;
    }
    
    if (!IsValidLowLevel())
    {
        UE_LOG(LogTemp, Error, TEXT("GetSafeLocation called on destroyed actor!"));
        return FVector::ZeroVector;
    }
    
    return GetActorLocation();
}
```

## Bisect로 회귀 찾기

언제 버그가 생겼는지 추적:

```
버그 발견: 어제 빌드는 OK, 오늘 NG

1. 커밋 이력 확인 (Git)
   │
   ├─ A (2일 전, OK로 알고 있음)
   ├─ B (어제)
   ├─ C (어제)
   ├─ D (오늘) ← 버그 시작?
   └─ E (오늘)

2. Bisect 실행
   git bisect start
   git bisect good <A-hash>
   git bisect bad <E-hash>
   
3. 자동으로 중간값 체크아웃 → 테스트 → 나쁨/좋음 표시
4. 반복 → 원인 커밋 특정
```

## 면접/실무 포인트

- **Q1**: "버그 못 찾겠어요"?
  - 첫 질문: 재현 가능한가?
  - 재현 불가 = 진행 불가. 먼저 재현성 확보.

- **Q2**: 디버거로 찾은 버그인데 프로덕션에서 안 나타난다?
  - Heisenbug 의심. 로그로 재추적.
  - 타이밍/멀티스레드 이슈 검토.

- **Q3**: Crash dump가 스택 표시 안 함?
  - PDB 파일 경로 확인 (Symbol path 설정).
  - 난독화/릴리스 빌드 → 디버그 정보 손실.

## 심화 학습

- 키워드: Binary Search, Symbol Resolution, Call Stack Unwinding
- Unreal: `UE_LOG`, `check()`, `ensure()` 매크로 활용
- 도구: WinDbg, Visual Studio Debugger, Unreal Insights
- 관련 페이지: [code-review](./code-review.md), [design-patterns](./design-patterns.md)
