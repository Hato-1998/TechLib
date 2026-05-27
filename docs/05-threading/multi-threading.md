# 멀티스레딩 기초

## 개요

여러 스레드가 같은 메모리를 만지면, 한 줄짜리 코드도 두 단계 이상의 기계 명령으로 깨져 race condition이 발생한다.
정합성을 보장하는 도구는 **lock**, **atomic**, **memory ordering** 세 가지 축으로 정리된다.

## 핵심 개념

### Race Condition

```cpp
int Counter = 0;
// 두 스레드가 동시에:
Counter++;
// 내부: load Counter → +1 → store Counter
// 중간에 다른 스레드가 끼어들면 한 번의 증가가 사라짐
```

원인: **읽기-수정-쓰기(read-modify-write)** 가 원자적이지 않기 때문.

### 동기화 도구

| 도구 | 의미 |
| --- | --- |
| **Mutex** | 한 번에 한 스레드만 진입 (배타) |
| **RW Lock** | 다수 reader 또는 단일 writer |
| **Atomic** | 단일 변수에 대한 원자적 read/write/RMW |
| **Spinlock** | 짧은 구간 busy-wait. 컨텍스트 스위치 비용 회피 |
| **Condition Variable** | 어떤 조건이 충족될 때까지 대기 |

### Memory Ordering (C++)

| 옵션 | 의미 |
| --- | --- |
| `memory_order_relaxed` | 순서 보장 없음, 원자성만 |
| `memory_order_acquire` | 이 연산 전 read/write가 이 시점 이후로 안 옮겨짐 |
| `memory_order_release` | 이 연산 이후 read/write가 이 시점 이전으로 안 옮겨짐 |
| `memory_order_seq_cst` | 가장 엄격 (전역 순서) |

대부분의 경우 `seq_cst`로 시작하고, 성능이 중요한 곳만 acquire/release로 완화.

### Deadlock 발생 조건 (Coffman conditions)

1. 상호 배제 (Mutual Exclusion)
2. 점유 대기 (Hold and Wait)
3. 비선점 (No Preemption)
4. 순환 대기 (Circular Wait)

→ **락 획득 순서를 전역적으로 통일**하면 #4 깨짐.

## C++ 예시

### atomic 카운터

```cpp
#include <atomic>
std::atomic<int64_t> Counter{0};

void Worker()
{
    Counter.fetch_add(1, std::memory_order_relaxed);
}
```

단순 카운터는 락 불필요. `relaxed`로 충분 (값의 정확한 누적만 필요).

### Unreal: FCriticalSection

```cpp
FCriticalSection Mutex;
TArray<int32> Shared;

void Producer(int32 V)
{
    FScopeLock Lock(&Mutex);
    Shared.Add(V);
}
```

`FScopeLock`은 RAII — 예외 안전, 락 누락 방지.

### Lock-Free Queue (단일 producer/consumer)

```cpp
// Unreal TQueue, 기본 모드가 SPSC
TQueue<FCommand, EQueueMode::Spsc> Queue;

// Producer
Queue.Enqueue(Command);
// Consumer
FCommand C;
while (Queue.Dequeue(C)) { /* 처리 */ }
```

여러 producer면 `EQueueMode::Mpsc`. lock-free 큐는 메모리 ordering 내부 처리.

## 안티패턴

- 락 안에서 또 다른 함수 호출 → 내부에서 같은 락 시도하면 deadlock (재귀 락 아닌 한)
- `volatile`로 동기화 시도 → C++에서 volatile은 동기화 의미 아님. atomic 써야 함
- "그냥 락 한 번 더 잡으면 되겠지" — 디버깅 가능한 코드가 못 됨

## 심화 학습

- Happens-before, sequenced-before
- Compare-And-Swap (CAS)
- ABA problem과 hazard pointer
- 관련 페이지: [캐시 메모리](../03-cache-memory/index.md), [병렬 처리](parallel-processing.md)
