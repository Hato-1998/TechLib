# Wave Function Collapse (파동 함수 붕괴)

## 개요

**Wave Function Collapse(WFC)**는 양자 역학에서 영감을 받은 절차적 콘텐츠 생성 알고리즘이다. 제약 조건(인접 규칙)에 따라 타일 또는 패턴을 배치하여 그럴듯한 콘텐츠를 생성한다. 던전 맵, 지형, 건축 배치, 심지어 픽셀 아트도 생성 가능하다. 계산 비용이 높아 보통 에디터/프리컴퓨테이션 단계에서 실행되며, 극소수 게임만 런타임 생성을 시도한다.

## 핵심 개념

```
Quantum Analogy (양자역학 비유):
  파동 함수 = {가능한 타일 상태들}
  붕괴 = 하나의 상태로 결정
  제약 전파 = 이웃 상태 업데이트
```

| 개념 | 설명 |
|------|------|
| **Tile (타일)** | 최소 단위 (16x16 텍셀, 맵 피스 등) |
| **Overlapping Model** | 패턴 (NxN) 기반 (이미지 분석) |
| **Tile Model** | 명시적 타일 세트 + 인접 규칙 |
| **Entropy** | 가능한 상태 개수. 0 = 결정됨 |
| **Constraint Propagation** | 한 타일 결정 → 이웃 가능성 제거 |
| **Backtracking** | 모순 발생 시 이전 상태 복원 |

## WFC 알고리즘 단계

```
Step 1: 초기화
  모든 셀: 가능한 모든 타일 상태 포함
  Entropy(cell) = | possible_tiles |
  
Step 2: 반복 루프
  a) 엔트로피 최소 셀 선택 (0 제외)
  b) 확률적 붕괴 (가능한 타일 중 랜덤 선택)
  c) 제약 전파 (이웃 상태 필터링)
  d) 모순 발생 → Backtrack
  e) 완료 → 출력
```

```
예시 (Tile Model):
초기 상태:           결정(결과):
┌─┬─┬─┐             ┌─┬─┬─┐
│?│?│?│             │A│B│B│
├─┼─┼─┤             ├─┼─┼─┤
│?│?│?│  collapse   │A│B│B│
├─┼─┼─┤   ─────→    ├─┼─┼─┤
│?│?│?│             │C│C│B│
└─┴─┴─┘             └─┴─┴─┘

(A, B, C = 타일 타입)
```

## Tile Model 구현 (간단한 예)

```cpp
// 타일 정의
enum ETileType
{
    Tile_Empty,
    Tile_Wall,
    Tile_Floor,
    Tile_Door
};

// 인접 규칙 (어떤 타일이 이웃할 수 있는가?)
bool CanBeAdjacent(ETileType Left, ETileType Right)
{
    // Wall은 Wall 옆에 올 수 있음
    if (Left == Tile_Wall && Right == Tile_Wall) return true;
    
    // Floor는 Floor 또는 Door 옆에
    if (Left == Tile_Floor && (Right == Tile_Floor || Right == Tile_Door)) return true;
    
    // Door는 Floor와 연결
    if (Left == Tile_Door && Right == Tile_Floor) return true;
    
    return false;
}

// WFC 상태 구조
struct FWFCCell
{
    TSet<ETileType> PossibleTiles;  // 아직 가능한 타일들
    ETileType ResolvedTile;          // 결정된 타일 (결정 후)
    bool bResolved = false;
};

// 간단한 WFC 구현
class FWaveFunction
{
public:
    TArray<TArray<FWFCCell>> Grid;
    int32 GridWidth, GridHeight;
    
    FWaveFunction(int32 W, int32 H) : GridWidth(W), GridHeight(H)
    {
        Grid.SetNum(H);
        for (auto& Row : Grid)
        {
            Row.SetNum(W);
            for (auto& Cell : Row)
            {
                // 모든 타일이 처음엔 가능
                Cell.PossibleTiles = {Tile_Empty, Tile_Wall, Tile_Floor, Tile_Door};
            }
        }
    }
    
    bool Collapse()
    {
        while (true)
        {
            // Step 1: 엔트로피 최소 미결정 셀 찾기
            FWFCCell* MinCell = nullptr;
            int32 MinX = -1, MinY = -1;
            int32 MinEntropy = INT_MAX;
            
            for (int32 Y = 0; Y < GridHeight; ++Y)
            {
                for (int32 X = 0; X < GridWidth; ++X)
                {
                    FWFCCell& Cell = Grid[Y][X];
                    if (!Cell.bResolved && Cell.PossibleTiles.Num() < MinEntropy)
                    {
                        MinCell = &Cell;
                        MinX = X;
                        MinY = Y;
                        MinEntropy = Cell.PossibleTiles.Num();
                    }
                }
            }
            
            // 모두 결정됨 → 완료
            if (MinCell == nullptr) return true;
            
            // 가능한 타일이 없음 → 모순 → Backtrack 필요
            if (MinEntropy == 0) return false;
            
            // Step 2: 확률적 붕괴
            TArray<ETileType> PossibleArray = MinCell->PossibleTiles.Array();
            int32 RandomIdx = FMath::Rand() % PossibleArray.Num();
            MinCell->ResolvedTile = PossibleArray[RandomIdx];
            MinCell->bResolved = true;
            
            // Step 3: 제약 전파
            if (!PropagatConstraints(MinX, MinY))
            {
                return false;  // 모순 발생
            }
        }
    }
    
    bool PropagatConstraints(int32 X, int32 Y)
    {
        // BFS로 이웃들의 가능성 줄이기
        ETileType CenterTile = Grid[Y][X].ResolvedTile;
        
        // 상하좌우 이웃
        int32 DX[] = {-1, 1, 0, 0};
        int32 DY[] = {0, 0, -1, 1};
        
        for (int32 i = 0; i < 4; ++i)
        {
            int32 NX = X + DX[i];
            int32 NY = Y + DY[i];
            
            if (NX >= 0 && NX < GridWidth && NY >= 0 && NY < GridHeight)
            {
                FWFCCell& Neighbor = Grid[NY][NX];
                
                // 인접 불가능한 타일 제거
                for (auto Iter = Neighbor.PossibleTiles.CreateIterator(); Iter; ++Iter)
                {
                    if (!CanBeAdjacent(CenterTile, *Iter))
                    {
                        Iter.RemoveCurrent();
                    }
                }
                
                // 가능한 타일이 없으면 모순
                if (Neighbor.PossibleTiles.Num() == 0)
                {
                    return false;
                }
            }
        }
        
        return true;
    }
};
```

## 게임 적용 예

```
던전 생성:
  1. 타일: Empty, Wall, Floor, Door, Treasure
  2. 규칙: Wall은 연결되어야 함, Door는 Floor와 인접
  3. 실행: 50x50 던전 생성
  
지형:
  1. 타일: Water, Sand, Grass, Mountain
  2. 규칙: Water는 Grass와 Sand 경계, Mountain은 Grass 위
  3. 실행: 맵 자동 생성

픽셀 아트:
  1. 참조 이미지에서 NxN 패턴 추출
  2. 패턴 인접 규칙 학습
  3. 생성: 새로운 이미지 합성
  
  유명 예: Caves of Qud, Townscaper, Bad North
```

## 오버래핑 모델 vs Tile Model

```
Tile Model (명시적):
  장점: 제어 용이, 명확한 규칙
  단점: 매뉴얼 규칙 정의 필요, 타일 개수↑
  
Overlapping Model (이미지 기반):
  장점: 이미지 패턴 자동 학습
  단점: 규칙 이해 어려움, 아티팩트 가능
```

## 성능 최적화

```
WFC 성능 문제:
  1. 백트래킹 → 지수 시간 가능
  2. 해결: 
     - 빠른 실패 (모순 조기 감지)
     - 제약 사전 간소화
     - 병렬화 (독립 구역 동시 생성)

예시:
  100x100 그리드 생성: ~1-5초 (CPU 기준)
  엔디탄스: 프리컴퓨테이션 또는 별도 스레드
```

## 면접/실무 포인트

- **Q1**: WFC가 보장하는 것은?
  - 제약 조건 만족.
  - 완성 보장 아님 (모순 가능 → backtrack).
  - 유일한 해 아님 (여러 결과 가능).

- **Q2**: 왜 대부분 게임이 WFC를 런타임에 안 쓸까?
  - 계산 비용 (1-5초/생성).
  - 프로덕션 문제 (불확정성, 디버깅 어려움).
  - 에디터에서 프리컴퓨테이션 후 에셋화 선호.

- **Q3**: WFC 모순 다루기?
  - Backtrack: 이전 상태 복원 후 다른 선택 시도.
  - Timeout: N초 이상 걸리면 중단, 재시도.

## 심화 학습

- 키워드: Constraint Satisfaction Problems (CSP), Backtracking Algorithms
- 오픈소스: "WFC" (Maxim Gumin 원저, 다양한 구현)
- 관련 페이지: [11-advanced-rendering/index.md](./index.md)
