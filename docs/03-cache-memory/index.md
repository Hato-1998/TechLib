# 3. 캐시 메모리

## 개요

현대 CPU는 메인 메모리 접근 한 번에 수백 사이클을 쓴다.
같은 시간에 CPU는 수십~수백 개의 명령을 실행할 수 있다.
**캐시 친화적 코드 = 게임에서 가장 큰 단일 최적화 레버**.
ECS·DOD 패러다임이 부상한 것도 캐시 때문이다.

## 핵심 개념

### 메모리 계층

| 계층 | 대략 크기 | 대략 레이턴시 (사이클) |
| --- | --- | --- |
| **레지스터** | ~수십 byte | < 1 |
| **L1 캐시** | 32~64 KB / core | ~4 |
| **L2 캐시** | 256 KB ~ 2 MB / core | ~12 |
| **L3 캐시** | 수 MB ~ 수십 MB / chip | ~40 |
| **DRAM** | 수 GB ~ 수십 GB | ~200+ |

*수치는 CPU 세대마다 다르며 대략적인 비율로 이해하자. 정확한 값은 `lscpu`, Intel ARK 등에서 확인.*

### Cache Line

- CPU가 한 번에 가져오는 메모리 단위. 보통 **64 byte** (일부 ARM은 128)
- 4 byte float 하나를 읽어도 64 byte가 통째로 캐시에 적재됨
- → **연속 메모리를 순회하면 첫 접근만 비용, 나머지 15개 float는 거의 공짜**

### Locality

| 종류 | 의미 |
| --- | --- |
| **Temporal locality** | 같은 데이터를 가까운 시간에 다시 접근 |
| **Spatial locality** | 가까운 주소를 함께 접근 |

`std::vector` 순회는 spatial locality 극대화. `std::list`는 노드가 흩어져 있어 캐시 미스 빈발.

### False Sharing

여러 스레드가 **같은 cache line의 다른 변수**를 동시에 수정하면 CPU 캐시 일관성 프로토콜이 매번 line을 무효화하며 충돌. 멀티스레드 성능이 단일 스레드보다 나빠질 수 있음.

해결: 변수를 cache line 크기로 정렬·패딩.

### Prefetch

CPU는 접근 패턴을 학습해 미리 적재(hardware prefetch). 명시적으로 `__builtin_prefetch` 또는 `_mm_prefetch` 호출 가능. **순차 접근이면 자동 prefetch가 잘 작동**, 무작위 접근이면 수동 prefetch 고려.

## AoS vs SoA

```cpp
// AoS (Array of Structs) — 객체 지향 직관
struct FParticle { FVector Pos; FVector Vel; float Life; };
TArray<FParticle> Particles;

// SoA (Struct of Arrays) — 캐시 친화
struct FParticleSoA
{
    TArray<FVector> Positions;
    TArray<FVector> Velocities;
    TArray<float>   Lives;
};
```

**Pos만 업데이트하는 루프**라면 SoA는 캐시 라인에 Position만 가득 차서 효율 극대화.
AoS는 매 객체마다 사용 안 하는 Vel/Life까지 적재 → 캐시 낭비.

이게 ECS의 핵심 아이디어.

## C++ 예시: False Sharing 회피

```cpp
struct alignas(64) FPaddedCounter
{
    std::atomic<int64_t> Value;
    char Padding[64 - sizeof(std::atomic<int64_t>)];
};

// 스레드별로 독립된 cache line 보장
FPaddedCounter Counters[16];

void ThreadWork(int ThreadIdx)
{
    for (int i = 0; i < 1'000'000; ++i)
    {
        Counters[ThreadIdx].Value.fetch_add(1, std::memory_order_relaxed);
    }
}
```

패딩 없으면 두 카운터가 같은 line에 → 성능 크게 떨어짐.

### Unreal에서의 cache line 상수

```cpp
// Unreal 내부에 PLATFORM_CACHE_LINE_SIZE 정의됨
alignas(PLATFORM_CACHE_LINE_SIZE) FMyHotData Hot;
```

## 측정 도구

- **perf** (Linux) — cache miss 카운터 (`cache-misses`, `LLC-load-misses`)
- **Intel VTune** — top-down 분석, 백엔드 바운드 원인 파악
- **Tracy** — 가벼운 in-process 프로파일러, lock contention 시각화

## 심화 학습

- Cache 일관성 프로토콜 (MESI)
- Branch predictor, speculative execution
- Data-Oriented Design 원리
- 관련 페이지: [OOP vs DOD/ECS](../12-oop-vs-dod-ecs/index.md), [멀티스레딩 기초](../05-threading/multi-threading.md), [동적 할당 & 단편화](../06-memory-allocation/index.md)
