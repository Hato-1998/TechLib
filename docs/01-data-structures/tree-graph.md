# Tree & Graph

## 개요

트리는 계층(부모-자식)을, 그래프는 임의 관계를 표현한다.
게임에서는 **Scene Graph(트랜스폼 계층)**, **퀘스트 의존성**, **스킬 트리**, **NPC 관계망**, **다이얼로그 분기** 등 거의 모든 구조적 데이터가 둘 중 하나로 환원된다.

## 핵심 개념

### 트리 변종 비교

| 자료구조 | 탐색 | 삽입 | 균형 보장 | 게임에서의 쓰임 |
| --- | --- | --- | --- | --- |
| **BST** | O(log N) 평균 | O(log N) 평균 | 없음 | 단순 정렬 컬렉션 |
| **AVL** | O(log N) | O(log N) | 엄격 균형 | 잦은 탐색·드문 삽입 |
| **Red-Black** | O(log N) | O(log N) | 느슨한 균형 | `std::map`, 일반 목적 |
| **B-Tree** | O(log N) | O(log N) | 균형 | DB, 디스크 I/O 최소화 |
| **Trie** | O(L) | O(L) | — | 채팅 욕설 필터, 자동완성 |

### 그래프 표현

- **인접 리스트**: 희소 그래프(노드 N개, 간선 E개에서 E << N²)에 유리. 메모리 O(N+E)
- **인접 행렬**: 밀집 그래프에 유리. 두 노드 간 연결 확인 O(1), 메모리 O(N²)

### 게임 내 사례

- **Scene Graph** — Unreal의 `USceneComponent` 계층, 부모 트랜스폼이 자식에 누적
- **Behavior Tree** — AI 의사결정 트리, Selector/Sequence 노드
- **퀘스트 그래프** — DAG(방향성 비순환 그래프), 위상 정렬로 진행 가능 퀘스트 추출
- **스킬 트리** — 종종 트리지만 실제로는 그래프(여러 선행조건)
- **소셜 그래프** — 친구 추천, 길드 관계망

## C++ 예시

```cpp
// Unreal: 인접 리스트 기반 퀘스트 의존 그래프
USTRUCT()
struct FQuestNode
{
    GENERATED_BODY()

    UPROPERTY() FName QuestId;
    UPROPERTY() TArray<FName> Prerequisites;
};

UCLASS()
class UQuestGraph : public UObject
{
    GENERATED_BODY()
public:
    bool CanStart(FName QuestId, const TSet<FName>& Completed) const
    {
        const FQuestNode* Node = Nodes.Find(QuestId);
        if (!Node) return false;
        for (const FName& Pre : Node->Prerequisites)
        {
            if (!Completed.Contains(Pre)) return false;
        }
        return true;
    }

private:
    UPROPERTY() TMap<FName, FQuestNode> Nodes;
};
```

`TMap`은 내부적으로 해시 기반이므로 평균 O(1) 조회. 정렬이 필요하면 `TSortedMap` 사용.

## 심화 학습

- B+ Tree, LSM Tree (저장소 자료구조)
- Persistent Data Structure (함수형 게임 상태 관리)
- Disjoint Set Union (영역 병합, MST 알고리즘)
- 관련 페이지: [공간 분할](space-partitioning.md), [길찾기](pathfinding.md)
