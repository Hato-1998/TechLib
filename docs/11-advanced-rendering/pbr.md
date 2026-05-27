# Physically Based Rendering (PBR)

## 개요

**Physically Based Rendering**은 현실의 빛과 물질 상호작용 물리 법칙을 게임에 적용하는 렌더링 철학이다. 마이크로 페셋(microfacet) 모델 기반 BRDF(Bidirectional Reflectance Distribution Function), 에너지 보존, 메탈릭/러프니스 워크플로우를 통해 다양한 재질을 일관성 있게 표현한다. Unreal의 Material Editor는 이러한 개념을 노드 기반으로 구현하며, 최신 버전의 Substrate 시스템은 더욱 유연한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **BRDF** | 들어오는 빛이 표면에서 어느 방향으로 반사되는지 확률 함수 |
| **Cook-Torrance Model** | 현대 PBR 표준. Specular + Diffuse 분리 |
| **Fresnel Effect** | 각도에 따라 반사율 변화 (수면, 극도로 빛나는 표면) |
| **Microfacet** | 표면은 미시적 凹凸. Roughness ↑ = 난반사 ↑ |
| **Metallic** | 0~1. 금속(1)은 diffuse ↓, specular(색상 유지) ↑ |
| **Roughness** | 0~1. 0=거울같음, 1=반투명 |
| **Normal Map** | 피크셀 단위 기울기 정보. 세밀한 표면 표현 |
| **Energy Conservation** | 반사 + 흡수 = 1. 에너지 "생성" 금지 |

## Cook-Torrance BRDF

```
f(l, v) = k_d * c / π + k_s * DFG / (4(N·L)(N·V))

여기서:
  k_d = diffuse fraction (1 - metallic)
  k_s = specular fraction (metallic)
  
  D(h) = Distribution Function (Roughness)
  F(l, h) = Fresnel (시야각 의존)
  G(l, v, h) = Geometry Function (Shadowing)
```

## Unreal Material 노드 매핑

```
Material 프로퍼티               노드 입력
┌─────────────────────────────┬──────────────────┐
│ BaseColor                   │ Main surface RGB │
│ Metallic (0~1)              │ 금속 여부        │
│ Roughness (0~1)             │ 미세면 거칠기    │
│ Normal Map                  │ 표면 기울기      │
│ AmbientOcclusion (0~1)      │ 음영 영역        │
│ Emissive                    │ 자체 발광        │
│ Opacity (Alpha)             │ 투명도           │
└─────────────────────────────┴──────────────────┘
```

## Unreal Material Editor 구현

```cpp
// C++ 콜백으로 동적 머티리얼 생성
UMaterialInstanceDynamic* CreatePBRMaterial(
    float InMetallic, 
    float InRoughness,
    const FLinearColor& InBaseColor)
{
    // 마스터 머티리얼 로드
    static UMaterial* MasterMat = LoadObject<UMaterial>(
        nullptr, 
        TEXT("/Game/Materials/M_PBR_Master")
    );
    
    // 동적 인스턴스 생성
    UMaterialInstanceDynamic* MatInst = UMaterialInstanceDynamic::Create(
        MasterMat, 
        nullptr
    );
    
    // 파라미터 설정
    MatInst->SetScalarParameterValue(TEXT("Metallic"), InMetallic);
    MatInst->SetScalarParameterValue(TEXT("Roughness"), InRoughness);
    MatInst->SetVectorParameterValue(TEXT("BaseColor"), InBaseColor);
    
    return MatInst;
}
```

## 메탈릭 vs 러프니스 워크플로우

```
Metallic Workflow (Unreal 기본):
  BaseColor    → [RGB] 물질 색상 (빛 에너지)
  Metallic     → [0~1] 금속성
  Roughness    → [0~1] 표면 거칠기
  
결과:
  Metallic=0 (비금속): BaseColor = diffuse 색상
  Metallic=1 (금속):   BaseColor = specular 색상 (금속 톤)

예시:
  강철:       Metallic=1, Roughness=0.3, BaseColor=밝은회색
  녹슨철:     Metallic=1, Roughness=0.8, BaseColor=갈색
  나무:       Metallic=0, Roughness=0.6, BaseColor=갈색
  자기:       Metallic=0, Roughness=0.2, BaseColor=흰색
```

## 노멀맵 & 에너지 보존

```cpp
void ApplyNormalMap(inout float3 WorldNormal, float3 TangentNormal)
{
    // 탄젠트 스페이스 → 월드 스페이스 변환
    // (TBN 행렬 사용)
    
    float3 WorldN = normalize(mul(TangentNormal, TBN));
    
    // 정규화 중요! 부정확한 법선 = 조명 오류
}

// Energy Conservation 검증
float Diffuse = (1.0 - Metallic);          // 비금속만 diffuse
float Specular = (Metallic);               // 금속만 specular

float Total = Diffuse + Specular;  // ≈ 1.0 (에너지 보존)
```

## IBL (Image-Based Lighting)

```
환경맵(Cubemap) 기반 조명:
  1. Specular Irradiance Cubemap (각 러프니스마다)
  2. Diffuse Irradiance Cubemap (1회 사전계산)
  3. BRDF Lookup Table

결과: 간접 반사, 확산 조명 모두 표현
```

```cpp
// Unreal: Sky Light (IBL 자동)
ASkylightActor::ASkylightActor()
{
    USkyLightComponent* SkyLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLight"));
    
    // 환경맵 설정
    SkyLight->SourceType = SLS_SpecifiedCubemap;
    SkyLight->Cubemap = LoadObject<UTextureCube>(nullptr, TEXT("/Game/Textures/EnvironmentCube"));
    
    // 간접 조명 강도
    SkyLight->Intensity = 1.5f;
}
```

## Substrate (UE 5.4+)

기존 Material 시스템의 한계 극복:
- 여러 레이어 재질 (페인트 + 금속, 먼지 + 유리)
- 복잡한 BRDF (헝겊, 피부 등)
- 재질 혼합

```cpp
// Substrate Material 선언
UCLASS()
class UMySubstrateMaterial : public UMaterialInterface
{
    GENERATED_BODY()
    
    // 레이어별 프로퍼티
    UPROPERTY()
    float BaseMetallic;
    
    UPROPERTY()
    float TopCoatRoughness;
};
```

## 실시간 vs 사전계산

```
사전계산 (Offline):
  ├─ 환경맵 필터링 (Mipmap BRDF)
  ├─ Ambient Occlusion 맵 생성
  └─ 조명 맵
  
  장점: 빠름, 고품질
  단점: 정적, 업데이트 어려움

실시간 (Runtime):
  ├─ 동적 라이트
  ├─ 실시간 shadows
  └─ 지형 변형
  
  장점: 상호작용성
  단점: 계산 비용
```

## 심화 학습

- 키워드: Microfacet Theory, Fresnel Equations, Ambient Occlusion Baking
- Unreal: Material Function, Material Layer System
- 관련 페이지: [11-advanced-rendering/index.md](./index.md), [physics-engine.md](./physics-engine.md)
