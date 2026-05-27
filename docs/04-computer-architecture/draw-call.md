# Draw Call

## 개요

Draw Call = "이 메시를 이 머티리얼로 그려라"라는 CPU → GPU 명령 한 건.
하나당 비용은 작지만, 수천 건이 모이면 **CPU(render thread)가 GPU를 못 따라가는 병목**이 된다.
대규모 씬 최적화의 거의 첫 번째 의제.

## 핵심 개념

### 비용 발생 지점

- **API 호출 자체** — DX12/Vulkan은 DX11보다 저렴하지만 0은 아님
- **상태 변경** — 머티리얼·셰이더·텍스처 바인딩 전환 비용이 큰 비중
- **드라이버 처리** — 명령 버퍼 구성, validation

### 줄이는 전략

| 전략 | 무엇을 합치나 | 제약 |
| --- | --- | --- |
| **Static Batching** | 같은 머티리얼의 정적 메시를 하나의 vertex buffer로 결합 | 메모리 증가, 라이트맵 처리 주의 |
| **Dynamic Batching** | 작은 동적 메시들을 매 프레임 결합 | CPU 비용 발생, 임계 폴리곤 이하만 |
| **GPU Instancing (ISM/HISM)** | 같은 메시를 위치만 바꿔 1번의 콜로 여러 개 그림 | 같은 메시·머티리얼 한정 |
| **Hierarchical LOD (HLOD)** | 거리 멀면 여러 메시를 하나의 단순 메시로 대체 | 사전 빌드 시간 |
| **Nanite** | 메시 단위 LOD를 GPU가 알아서. 사실상 드로우콜 무력화 | UE5+, 정적 메시 한정 (5.5에서 스켈레탈 확장) |

### Unreal 사례

- **ISM (Instanced Static Mesh)** — 같은 메시 N개를 한 컴포넌트로
- **HISM (Hierarchical ISM)** — ISM + 거리별 LOD + 컬링
- **Nanite** — 메시를 클러스터 단위로 GPU에서 LOD/컬링. 드로우콜 1개로 거대한 씬 처리
- **Material Slot 정리** — 메시당 머티리얼 슬롯 수가 곧 드로우콜 수 (메시당 1 slot = 1 draw call)

## C++ 예시: ISM으로 1,000개 풀잎 그리기

```cpp
// UWorld에 ISM 컴포넌트 추가
UInstancedStaticMeshComponent* ISM = NewObject<UInstancedStaticMeshComponent>(this);
ISM->SetStaticMesh(GrassMesh);
ISM->SetMaterial(0, GrassMat);
ISM->RegisterComponent();

for (int i = 0; i < 1000; ++i)
{
    const FVector Loc(FMath::FRandRange(-1000.f, 1000.f),
                      FMath::FRandRange(-1000.f, 1000.f),
                      0.f);
    ISM->AddInstance(FTransform(Loc));
}
// 결과: 풀잎 1,000개가 단일 드로우콜로 렌더링
```

- 개별 `UStaticMeshComponent` 1,000개를 두면 드로우콜 1,000개
- ISM이면 1개 (또는 LOD 단계별 소수)

### 드로우콜 측정

```
stat scenerendering
# 또는
stat rhi
```

`Mesh draw calls` 행을 본다.

## 면접/실무 포인트

- **Q1**: 드로우콜이 비싼 본질적 이유는? — API 호출보다 **state 전환과 드라이버 검증**이 크다. 같은 머티리얼이면 batching이 가능한 이유.
- **Q2**: Nanite가 모든 메시에 답인가? — 정적 메시·내부 deforming 없는 경우에 최적. 투명/half-transparent, WPO 변형, 일부 머티리얼은 fallback. UE5.5에서 스켈레탈 Nanite 도입되며 범위 확장.
- **Q3**: ISM vs HISM 선택? — 적은 수면 ISM, 수천+ 멀리까지 보이면 HISM(LOD·컬링 자동).
- **Q4**: DX12에서 드로우콜이 DX11보다 저렴한 이유? — 명령 버퍼를 미리 여러 스레드에서 작성, 드라이버 검증 감소. 하지만 PSO 관리·메모리 명시는 개발자 몫.
- **Q5**: Material Slot 수를 줄이는 게 왜 드로우콜에 영향? — 슬롯마다 별도 머티리얼 → 슬롯별 드로우콜. 슬롯 통합 + Material Function으로 분기.

## 안티패턴

- BP에서 매 Tick `SpawnActor`로 이펙트 생성 → 매 프레임 새 컴포넌트, 드로우콜 폭증
- Material Editor에서 머티리얼 인스턴스 대신 새 머티리얼 복제 → PSO 캐시 무효화

## 심화 학습

- Pipeline State Object (PSO) 캐싱 전략
- GPU-driven rendering (indirect draw, mesh shader)
- Bindless resource binding (DX12/Vulkan)
- 관련 페이지: [병목 현상 최소화](bottleneck.md), [배경 최적화](environment-optimization.md), [공간 분할](../01-data-structures/space-partitioning.md)
