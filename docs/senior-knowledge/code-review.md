# 코드 리뷰 문화

## 개요

효과적인 코드 리뷰는 버그 조기 발견, 지식 공유, 일관성 유지의 핵심이다. 시니어는 리뷰어로서 **건설적 피드백**을 제공하고, 리뷰이(작성자)의 의도를 존중하며, **기술적 정확성**과 **실행 가능성**을 균형 맞춰야 한다. 게임 코드는 일반 소프트웨어와 달리 메모리 할당 핫패스, 네트워크 동기화, 렌더링 성능 같은 특수한 관심사가 있다.

## 리뷰어의 역할과 톤

```
기준                     학부생/주니어     시니어 리뷰어
────────────────────────────────────────────────
피드백 형태              지시적           질문형 + 근거
코드 변경 제안           직접 수정         옵션 제시
성능 검토               포괄적           실측 기반
커뮤니케이션 톤          판사           멘토
```

### 좋은 리뷰 코멘트 vs 나쁜 리뷰 코멘트

```
[나쁜 예]
"이건 비효율적이다. 개선하세요."
→ 이유 없고, 무엇을 어떻게 하는지 불명확

[좋은 예]
"이 코드는 매 프레임마다 new를 호출하므로
메모리 할당 오버헤드가 발생한다.
대신 Object Pool 패턴을 고려하면
프레임 타임 10ms 절약 가능할 것 같다."
→ 근거, 대안, 예상 효과 명시
```

## 게임 코드 리뷰 체크리스트

| 항목 | 확인 내용 | 예시 |
|------|---------|------|
| **메모리 할당** | Tick/Update에서 new/malloc? | 루프 내 new → Object Pool 제안 |
| **가상함수 빈도** | 핫패스에서 동적 디스패치? | 매 프레임 100K 호출 → 구조 변경 제안 |
| **네트워크** | Replication/RPC 안전성? | 클라 검증 누락 → 서버 권한 강화 |
| **멀티스레드** | Lock/Race condition? | 데이터 경합 → FScopeLock 제안 |
| **타입 안전성** | Cast 오류 가능성? | UObject 캐스트 → IsA<> 검증 |
| **스타일 일관성** | 프로젝트 컨벤션 준수? | Unreal naming rule 위반 |

## Lyra 패턴 참조

Unreal의 Lyra Starter Game은 업계 모범 사례 집합이다. 리뷰 시 참조:

```cpp
// Lyra 패턴 1: Subsystem 활용 (전역 상태)
// [GOOD]
UGameInstanceSubsystem* GameSystem = GetGameInstance()->GetSubsystem<UMyGameSystem>();

// [AVOID]
extern UMyGameSystem* GGameSystem;  // 전역 변수

// Lyra 패턴 2: GameplayMessage 기반 이벤트
// [GOOD]
UGameplayMessageSubsystem::Get()->BroadcastMessage<FPlayerDeadMessage>(Message);

// [AVOID]
AGameMode::OnPlayerDead.Broadcast(Player);  // 강한 결합


// Lyra 패턴 3: Feature Plugins로 기능 분리
// [GOOD]
// /Plugins/MyFeature/
//   Source/MyFeature/
//   MyFeature.uplugin

// [AVOID]
// Source/MyGame/Features/MyFeature/  // 모노리식
```

## 네트워크 동기화 리뷰 포인트

```cpp
// [BAD] 클라가 직접 자신의 상태 변경
void ACharacter::Jump_Implementation()
{
    // 클라가 jump 판단 → 치팅 위험
    SetActorLocation(GetActorLocation() + FVector(0, 0, 500));
    bIsJumping = true;
}

// [GOOD] 서버 권한
void ACharacter::Jump_Implementation()
{
    if (IsLocallyControlled() && !bIsJumping)
    {
        ServerRequestJump();
    }
}

void ACharacter::ServerRequestJump_Implementation()
{
    // 서버만 판단
    if (!bIsJumping && GetCharacterMovement()->IsMovingOnGround())
    {
        bIsJumping = true;
        // 모든 클라에 복제
    }
}
```

## 리뷰 프로세스 최적화

```
1회 리뷰 사이클:
  ├─ 제출자: PR 설명 + diff 준비 (5분)
  ├─ 리뷰어: 코드 읽기 (15-30분)
  ├─ 리뷰어: 코멘트 작성 (5-10분)
  ├─ 제출자: 피드백 회신 (5-15분)
  ├─ 재검토 (5-10분)
  └─ Merge (1분)

좋은 리뷰 요약:
  ├─ 핵심 이슈: 2-3개 (과다 요구 피하기)
  ├─ 개선 제안: 구체적 (공중에 떠 있지 않게)
  ├─ 승인 신호: 명확 (Approve vs Pending)
  └─ 예상 영향도: 명시 (낮음/중간/높음)
```

## 코멘트 예시

```
리뷰 코멘트 (Line 42):

// 현재 코드
for (FVector& Pos : Positions)
{
    Pos += Velocity * DeltaTime;  // ← 매 프레임 1M번 호출
}

// 리뷰
가능하면 SIMD 최적화를 고려하면 좋을 것 같다:

for (int32 i = 0; i < Num; i += 4)
{
    __m128 Pos = _mm_loadu_ps(&Positions[i]);
    __m128 Vel = _mm_loadu_ps(&Velocities[i]);
    __m128 Result = _mm_add_ps(Pos, _mm_mul_ps(Vel, DT_vec));
    _mm_storeu_ps(&Positions[i], Result);
}

벤치마크: 단순 루프 vs SIMD ~3배 가속
테스트 방법:
  - CPU 프로파일러에서 이 함수 시간 측정
  - 1M 벡터로 비교 테스트

(선택사항, 현재 성능 문제 없으면 미연기 가능)
```

## 승인 기준

```
[Approve] 합병 가능:
  - 기능 정확
  - 성능 만족 (측정 또는 논의 완료)
  - 스타일 일관
  - 테스트 통과

[Pending] 재검토 필요:
  - 성능 우려 (추가 최적화 필요)
  - 스타일 문제 (rebase 요청)
  - 논리 버그 (수정 필요)

[Request Changes] 강한 피드백:
  - 아키텍처 문제 (재설계 필요)
  - 보안 우려 (서버 검증 누락)
  - 명백한 버그
```

## 면접/실무 포인트

- **Q1**: 리뷰에서 성능 지적할 때 근거는?
  - 추측 금지. 측정 또는 문헌 인용.
  - "1M 반복에서 malloc 호출 → 10ms 오버헤드" (구체적).

- **Q2**: 리뷰 코멘트 너무 많으면?
  - 핵심 3개만. 나머지는 "nice-to-have".
  - "개선하면 좋겠지만 blocking은 아니다" 표시.

- **Q3**: 작성자가 반박하면?
  - 토론 환영. 근거 있으면 입장 변경 (열린 자세).
  - "맞다, 내가 놓쳤다" — 시니어일수록 빨리 인정.

## 심화 학습

- 키워드: Constructive Feedback, Code Quality Metrics, Pull Request Best Practices
- Unreal: Lyra Learning Sample 코드 분석
- 관련 페이지: [debugging-mindset](./debugging-mindset.md), [design-patterns](./design-patterns.md)
