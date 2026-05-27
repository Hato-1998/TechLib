# 배경 최적화

## 개요

게임 배경(레벨, 지형, 식생, 조명)은 메모리·드로우콜·셰이딩 비용을 가장 많이 차지하는 영역.
"카메라 한 컷이 한 프레임"이라는 전제 아래, **보이지 않을 만한 것을 미리 제거**하고 **보일 것은 거리에 맞게 단순화**하는 것이 전체 전략.

## 핵심 개념

### LOD (Level of Detail)

- 거리에 따라 메시·텍스처·머티리얼을 단순한 버전으로 교체
- 메시 LOD: 폴리곤 수 감소 (LOD0 → LOD3, 비율 보통 50%, 25%, 12.5%)
- 텍스처 MipMap: 해상도 절반씩
- Shader LOD: 거리 멀면 단순한 머티리얼 (Unreal `Quality Level`)

### HLOD (Hierarchical LOD)

- 여러 메시 + 머티리얼을 통째로 단순한 메시 하나로 사전 빌드
- 거리 멀면 도시 한 블록 → 하나의 박스 메시 + 통합 텍스처
- 드로우콜 대폭 감소

### Nanite (UE5+)

- 가상화된 지오메트리 — 메시 단위 LOD가 사실상 자동
- 클러스터 단위 GPU streaming + culling
- 작가가 LOD를 만들지 않아도 됨
- 한계: 투명 메시, WPO(World Position Offset) 변형, 일부 머티리얼은 fallback (5.4부터 점차 완화, 5.5 스켈레탈 지원)

### Lumen

- 동적 글로벌 일루미네이션 + 반사
- 사전 베이크 없이 실시간 GI → 라이트맵 의존 줄임
- Software vs Hardware Lumen 선택지: 후자는 RT 카드 필요, 더 정확

### World Partition (UE5+)

- 거대한 월드를 **Cell 그리드**로 분할
- 카메라 근처 Cell만 메모리에 로드 (스트리밍)
- 작가 협업: 한 레벨 파일 잠금 문제 해결 (Cell 단위 락)
- **Data Layers**: 시나리오·시간대별 컨텐츠 분리

### Texture Streaming

- 전체 텍스처가 아니라 필요한 mip만 메모리 적재
- 카메라 가까워지면 고해상도 mip 로드
- `r.Streaming.PoolSize`로 메모리 예산 설정

## C++ 예시: 거리 기반 Tick 최적화

```cpp
void AEnvActor::Tick(float Dt)
{
    Super::Tick(Dt);
    const float DistSq = FVector::DistSquared(GetActorLocation(),
                                              GetWorld()->GetFirstPlayerController()
                                                       ->GetPawn()->GetActorLocation());
    if (DistSq > FMath::Square(FarDistance))
    {
        // 멀면 거의 안 갱신
        SetActorTickInterval(0.5f);
        return;
    }
    SetActorTickInterval(0.f); // 매 프레임

    // ... 실제 갱신
}
```

`USignificanceManager`를 쓰면 같은 패턴을 거리·각도·우선순위 기준으로 자동화.

## Foliage / 식생

- **Instanced Foliage Actor** — 같은 풀잎·나무 수천 개를 ISM/HISM로
- **Procedural Foliage Volume** — 절차적 배치 + 거리 기반 LOD
- **Imposter Sprite** — 멀리 보이는 나무를 2D 판으로 대체 (드로우콜·폴리곤 절감)
- Nanite + Foliage 조합이 UE5의 표준 방향

## 라이팅 최적화

- 동적 라이트는 비싸다 — Lumen이 일부 완화하지만 라이트 수 자체가 곧 비용
- **Stationary Light** + 라이트맵 베이크 = 실내 환경의 전통적 정답
- **Distance Field Shadow** — 거리 멀면 shadow map 대신 distance field로 그림자

## 면접/실무 포인트

- **Q1**: HLOD가 있는데 Nanite도 필요? — Nanite는 메시 자체의 자동 LOD. HLOD는 여러 메시를 묶는 단계. 큰 도시는 Nanite로 가도 머티리얼·라이팅 단순화 위해 HLOD가 의미.
- **Q2**: World Partition vs Level Streaming(레거시) 차이? — Streaming은 명시적 sublevel 단위, Partition은 자동 Cell 단위. Partition이 협업·자동화 면에서 우수.
- **Q3**: Lumen의 software vs hardware 트레이드? — software는 distance field 기반(어디서나 동작, 비용 중간). hardware는 RT, 더 정확하지만 GPU 요구 높음.
- **Q4**: 라이트맵 해상도를 어떻게 정하나? — 표면 면적 × 시각적 중요도. 캐릭터 가까이 가는 벽은 높게, 천장은 낮게.
- **Q5**: 메모리 예산이 빠듯한 모바일에서 무엇부터? — 텍스처 압축 포맷(ASTC), mip streaming, 라이트맵 해상도 하향, Nanite 미사용.

## 안티패턴

- 모든 라이트를 Movable로 설정 → 그림자 비용 폭증
- LOD 없이 거대 메시 통째 사용 → 가까이 갈 때 vertex shader 폭주
- Foliage를 `UStaticMeshComponent`로 하나씩 → 드로우콜 수천 개

## 심화 학습

- Virtual Texturing (Runtime/Streaming Virtual Texture)
- Mesh Shader 기반 클러스터 컬링
- Substrate (UE5.4+) — 머티리얼 표현력과 비용 트레이드
- 관련 페이지: [Draw Call](draw-call.md), [메모리 관리 & 심리스 로딩](../08-memory-management/index.md), [PBR](../11-advanced-rendering/pbr.md)
