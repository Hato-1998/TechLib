# 메모리 관리 & 스트리밍 로딩

## 개요

게임은 대규모 월드를 로드하면서도 프레임 드롭 없이 부드러운 이동을 제공해야 한다. 가상 메모리(Virtual Memory), 페이지 폴트, 백그라운드 스트리밍이 핵심이다. Unreal의 Texture Streaming, Level Streaming, World Partition은 메모리 예산과 로딩 시간의 균형을 맞추는 고급 기법이다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **가상 메모리** | 논리 주소 → 물리 주소 매핑. 디스크 + RAM 합쳐 거대 주소 공간 제공 |
| **페이지 폴트** | 참조한 페이지가 물리 메모리 없음 → 디스크에서 페이지 로드. 수 ms의 히드 시크 |
| **심리스 로딩** | 플레이어가 느끼지 못하게 백그라운드에서 다음 영역 로드. 0-frame stall |
| **Texture Streaming** | 고해상도 텍스처 Mip level 동적 로드/언로드. 해상도↑ 메모리↓ |
| **Level Streaming** | 큰 월드를 구역(sublevel)으로 나눠 필요할 때만 로드 |
| **World Partition** | Unreal 5+. 월드를 공간 칼(Cell) 기준으로 자동 분할. Level Streaming 자동화 |
| **FStreamableManager** | Unreal의 비동기 로딩 API. 콜백 기반 의존성 체인 로드 |

## 페이지 폴트 메커니즘

```
논리 주소 참조
    ↓
TLB(Translation Lookaside Buffer) 조회
    ↓ (miss)
Page Table 조회
    ↓ (not in RAM)
[Page Fault 발생]
    ↓
Disk I/O: 디스크 페이지 읽기
    ↓ (~5-10ms, SSD 기준)
물리 메모리에 적재
    ↓
Page Table 업데이트
    ↓
명령 재실행
```

**게임 영향**: 
- 프레임 15ms 내에 페이지 폴트 → 프레임 드롭 (16.67ms@60fps 초과)
- 백그라운드 스트리밍 중 예측 불가 폴트 → 지터(jitter)

## Level Streaming 구조

```cpp
// 월드를 여러 Level로 분할
// Level_Main (persistent), Level_Forest, Level_Cave 등

// 플레이어 위치 기반 동적 로드
void AGameMode::Tick(float DeltaTime)
{
    FVector PlayerPos = GetPlayer()->GetActorLocation();
    
    // 거리 기반 로드/언로드
    if (FVector::Dist(PlayerPos, ForestCenter) < StreamingDistance)
    {
        // Level_Forest 로드 시작
        GetWorld()->StreamLevel(TEXT("Level_Forest"), true, false);
    }
    else
    {
        GetWorld()->StreamLevel(TEXT("Level_Forest"), false, false);
    }
}
```

## Texture Streaming (Mip Mapping)

```
원본 텍스처 (4K, 4MB)
    ↓
Mip 0: 4K (4MB)   - 가까이
Mip 1: 2K (1MB)   - 중거리
Mip 2: 1K (256KB) - 먼거리
Mip 3: 512 (64KB)
```

```cpp
// Unreal Texture Streaming 설정
UTexture2D* MyTexture = ...;

// Mip Bias 설정 (거리에 따라 자동 조정)
MyTexture->NeverStream = false;
MyTexture->LODGroup = TEXTUREGROUP_WorldNormalMap;

// 수동 Mip 강제 설정
MyTexture->SetForcedMipAndLimit(2, 2); // Mip 2만 로드
```

## FStreamableManager & 비동기 로딩

```cpp
// 단일 에셋 비동기 로드
FStreamableManager& Streamable = UAssetManager::GetStreamableManager();

FStreamableHandle Handle = Streamable.RequestAsyncLoad(
    FSoftObjectPath(TEXT("/Game/Materials/M_Ground")),
    [](const FSoftObjectPath& LoadedPath)
    {
        if (UMaterialInterface* Mat = Cast<UMaterialInterface>(LoadedPath.ResolveObject()))
        {
            // 로드 완료 콜백
            UE_LOG(LogTemp, Warning, TEXT("Material loaded: %s"), *Mat->GetName());
        }
    }
);

// 의존성 체인 (A로드 → B로드 → C로드)
TArray<FSoftObjectPath> AssetChain = {
    TEXT("/Game/Characters/Ch_Hero"),
    TEXT("/Game/Animations/Montage_Attack"),
    TEXT("/Game/Audio/SFX_Slash")
};

Streamable.RequestAsyncLoad(AssetChain, [](){ /* 모두 로드 완료 */ });
```

## World Partition (Unreal 5+)

```cpp
// World Partition: 월드 자동 분할 (Cell 기준)
// Editor에서 설정: World Settings → Enable World Partition

// 런타임에 특정 Cell 명시적 로드
AWorldPartitionSubsystem* WPS = GetWorld()->GetSubsystem<AWorldPartitionSubsystem>();

FWorldPartitionQuerySource QuerySource(GetPlayer());
WPS->UpdateStreamingState(QuerySource);

// 플레이어 근처 Cell만 자동 로드 (선언적)
```

## 메모리 예산 & 프로파일링

```cpp
// 메모리 상태 조회
FMemory::DumpStats();
FGenericMemoryStats MemStats;
FMemory::GetMemoryStats(MemStats);

UE_LOG(LogTemp, Warning, 
    TEXT("Used: %.2fMB, Available: %.2fMB"), 
    (double)MemStats.UsedPhysical / 1024 / 1024,
    (double)MemStats.AvailablePhysical / 1024 / 1024
);

// 텍스처 메모리 사용량
int32 TextureMemory = FTextureMemoryStats().AllocatedMemory / 1024 / 1024;

// 레벨 언로드 시 메모리 회수
GetWorld()->StreamLevel(TEXT("Level_Old"), false, true); // bShouldBeLoaded=false, bMakeVisibleAfterLoad=true
```

## 심리스 로딩 워크플로우

```
프레임 N: 플레이어 위치 업데이트
  ↓
백그라운드 스레드: 다음 구역 예측
  ↓
비동기 로드 시작 (FStreamableManager)
  ↓
프레임 N+k: 메인 스레드 차단 없이 로드 진행
  ↓
콜백: 에셋 준비 완료 → 월드에 Add
  ↓
프레임 N+m: 플레이어 도착 (이미 로드됨)
  → 부드러운 전환, 드롭 없음
```

## 심화 학습

- 키워드: Virtual Memory Paging, Prefetch Algorithms, Streaming Pool Management
- Unreal: `UAssetManager`, `FWorldPartitionSubsystem`, `ULevelStreamingDynamic`
- DirectStorage API (XboxSeriesX, PS5 I/O 가속)
- 관련 페이지: [07-os-scheduling](../07-os-scheduling/index.md), [10-profiling](../10-profiling/index.md)
