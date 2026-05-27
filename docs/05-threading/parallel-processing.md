# 병렬 처리

## 개요

스레드를 직접 만들고 관리하는 시대는 끝났다.
현대 엔진은 **잡(Job)**을 만들어 **태스크 그래프(Task Graph) / 잡 시스템(Job System)** 에 넘기고,
스케줄러가 코어 수에 맞춰 자동 분배·**work stealing**으로 부하 균등화한다.

## 핵심 개념

### 데이터 병렬 vs 작업 병렬

| 구분 | 예 | 도구 |
| --- | --- | --- |
| **Data parallel** | 1만 개 객체에 같은 연산 | ParallelFor |
| **Task parallel** | 서로 다른 N개 작업 동시 | Task Graph, Async |
| **Pipeline parallel** | 단계가 다른 N개 객체 연쇄 | Producer/Consumer 큐 |

### Task Graph (Unreal)

- 잡 = 콜백 + 의존성 + 실행 스레드 선호
- 그래프로 의존성 표현 → 스케줄러가 가능한 만큼 동시 실행
- DAG가 깊지 않게(병렬도 확보), 너무 잘게 쪼개지도 않게(스케줄링 오버헤드)

### Work Stealing

- 각 워커 스레드가 자기 큐를 가짐
- 자기 큐가 비면 다른 워커 큐 끝에서 잡을 훔침
- 부하 분배 자동화 → 잡 크기 균일성에 덜 민감

### Unity DOTS Job System

- `IJob`, `IJobParallelFor`, `IJobParallelForTransform`
- **Burst Compiler** + ECS와 결합: SoA 데이터 → SIMD 자동
- 의존성 명시 → 안전한 race 방지

### 잡 크기의 황금률

- 너무 작음 (μs 단위) → 스케줄링 오버헤드가 본업보다 큼
- 너무 큼 (수십 ms) → 한 코어에 묶여 부하 불균등
- 보통 **수십~수백 μs** 가 적정. ParallelFor의 `MinBatchSize` 튜닝

## C++ 예시

### ParallelFor

```cpp
// 1만 개 파티클을 모든 코어에 분산
ParallelFor(Particles.Num(), [&](int32 Index)
{
    FParticle& P = Particles[Index];
    P.Position += P.Velocity * DeltaTime;
});
```

- 람다 안에서 같은 `Particles[Index]`만 만진다면 race 없음
- 옆 인덱스를 만지면 false sharing 가능 → 인덱스 격리 보장

### Task Graph

```cpp
FGraphEventRef HeavyTask = FFunctionGraphTask::CreateAndDispatchWhenReady(
    []()
    {
        // 무거운 계산
        DoComputation();
    },
    TStatId(), nullptr, ENamedThreads::AnyBackgroundThreadNormalTask);

// 결과 의존 잡 연결
FFunctionGraphTask::CreateAndDispatchWhenReady(
    []()
    {
        ApplyResult();
    },
    TStatId(), HeavyTask, ENamedThreads::GameThread);
```

`HeavyTask` 완료 후 두 번째 잡이 Game Thread에서 실행.

### 동시 컨테이너 접근 회피

```cpp
// 잘못된 예: 같은 TArray에 멀티 스레드 push
ParallelFor(N, [&](int32 i)
{
    Results.Add(Compute(i)); // RACE
});

// 좋은 예: per-thread 누적 후 합침
TArray<TArray<FResult>> Buckets;
Buckets.SetNum(FTaskGraphInterface::Get().GetNumWorkerThreads());

ParallelFor(N, [&](int32 i)
{
    const int32 Tid = FPlatformTLS::GetCurrentThreadId(); // 또는 워커 인덱스
    Buckets[Tid % Buckets.Num()].Add(Compute(i));
});

for (auto& B : Buckets) Results.Append(B);
```

## 면접/실무 포인트

- **Q1**: ParallelFor가 항상 빨라지지 않는 이유? — 잡 크기가 너무 작거나 메모리 액세스 패턴이 캐시 미스 유발이면 단일 스레드보다 느릴 수 있음.
- **Q2**: Work stealing이 단순 라운드로빈보다 나은 점? — 잡 크기가 불균등할 때 자동 균등화. 짧은 잡 워커가 긴 잡 워커 큐를 도와줌.
- **Q3**: Burst Compiler가 빠른 이유? — IL2CPP 대비 더 공격적 LLVM 최적화 + SIMD intrinsic 자동 생성. ECS의 SoA가 burst와 시너지.
- **Q4**: Task Graph DAG가 깊으면 어떤 문제? — 직렬 경로 길어져 병렬도↓. 의존성 줄여 wide DAG로 만든다.
- **Q5**: GPU compute로 보낼지, CPU 병렬로 풀지 기준? — 데이터가 크고 동질적 계산이면 GPU(transfer 비용 회수 가능). 적은 데이터·다양한 분기면 CPU.

## 안티패턴

- ParallelFor 안에서 락 사용 — 병렬도 무효화
- 한 워커 잡이 자기보다 큰 동기 잡을 기다림 → 데드락 위험
- 잡 안에서 새 잡을 만들어 wait — 재귀적 wait 패턴 주의

## 심화 학습

- Cilk-style work stealing 원리
- Coroutines로 잡 시스템 단순화 (C++20)
- ECS + Burst + Job 패턴 (DOTS)
- 관련 페이지: [멀티스레딩 기초](multi-threading.md), [캐시 메모리](../03-cache-memory/index.md), [OOP vs DOD/ECS](../12-oop-vs-dod-ecs/index.md)
