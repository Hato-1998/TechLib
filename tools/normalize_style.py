"""한국어 ~합니다체 → ~다체 일괄 변환.

Agent 2가 작성한 파일들의 문체를 plain form으로 통일.
규칙:
- 동사 합니다/한다 (action)
- 형용사·서술 입니다/이다, 있습니다/있다, 없습니다/없다
- ~ㅂ니다 (vowel stem) → ~ㄴ다
- ~습니다 (consonant stem) → ~는다 또는 ~다

순서 중요: 더 긴/구체적 패턴부터.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# (pattern, replacement) — order matters: longer/more specific first
RULES: list[tuple[str, str]] = [
    # Descriptive (be/exist)
    ("입니다", "이다"),
    ("있습니다", "있다"),
    ("없습니다", "없다"),
    ("같습니다", "같다"),
    ("쉽습니다", "쉽다"),
    ("어렵습니다", "어렵다"),
    ("좋습니다", "좋다"),
    ("나쁩니다", "나쁘다"),
    ("적습니다", "적다"),
    ("많습니다", "많다"),
    ("작습니다", "작다"),
    ("큽니다", "크다"),
    ("높습니다", "높다"),
    ("낮습니다", "낮다"),
    ("필요합니다", "필요하다"),
    ("중요합니다", "중요하다"),
    ("가능합니다", "가능하다"),
    ("유리합니다", "유리하다"),
    ("불리합니다", "불리하다"),
    ("간단합니다", "간단하다"),
    ("복잡합니다", "복잡하다"),
    ("적합합니다", "적합하다"),
    ("느립니다", "느리다"),
    ("빠릅니다", "빠르다"),
    ("강합니다", "강하다"),
    ("약합니다", "약하다"),
    ("어색합니다", "어색하다"),
    ("자연스럽습니다", "자연스럽다"),
    # Become / state change
    ("됩니다", "된다"),
    ("이어집니다", "이어진다"),
    ("바뀝니다", "바뀐다"),
    # Action verbs (specific stems before generic 합니다)
    ("봅니다", "본다"),
    ("옵니다", "온다"),
    ("갑니다", "간다"),
    ("줍니다", "준다"),
    ("씁니다", "쓴다"),
    ("씁시다", "쓰자"),
    ("듭니다", "든다"),
    ("만듭니다", "만든다"),
    ("시킵니다", "시킨다"),
    ("받습니다", "받는다"),
    ("찾습니다", "찾는다"),
    ("듣습니다", "듣는다"),
    ("걸립니다", "걸린다"),
    ("올립니다", "올린다"),
    ("내립니다", "내린다"),
    ("열립니다", "열린다"),
    ("닫힙니다", "닫힌다"),
    ("처리됩니다", "처리된다"),
    ("표시됩니다", "표시된다"),
    ("발생합니다", "발생한다"),
    ("사용됩니다", "사용된다"),
    ("선호됩니다", "선호된다"),
    ("사용합니다", "사용한다"),
    ("적용합니다", "적용한다"),
    ("선택합니다", "선택한다"),
    ("제공합니다", "제공한다"),
    ("수행합니다", "수행한다"),
    ("관리합니다", "관리한다"),
    ("처리합니다", "처리한다"),
    ("계산합니다", "계산한다"),
    ("측정합니다", "측정한다"),
    ("실행합니다", "실행한다"),
    ("동작합니다", "동작한다"),
    ("작동합니다", "작동한다"),
    ("호출합니다", "호출한다"),
    ("반환합니다", "반환한다"),
    ("표현합니다", "표현한다"),
    ("의미합니다", "의미한다"),
    ("나타냅니다", "나타낸다"),
    ("결정합니다", "결정한다"),
    ("판단합니다", "판단한다"),
    ("탐색합니다", "탐색한다"),
    ("순회합니다", "순회한다"),
    ("확인합니다", "확인한다"),
    ("검증합니다", "검증한다"),
    ("정리합니다", "정리한다"),
    ("권장합니다", "권장한다"),
    ("추천합니다", "추천한다"),
    ("초래합니다", "초래한다"),
    ("발전합니다", "발전한다"),
    ("진화합니다", "진화한다"),
    ("개선합니다", "개선한다"),
    ("최적화합니다", "최적화한다"),
    ("저장합니다", "저장한다"),
    ("로드합니다", "로드한다"),
    ("렌더링합니다", "렌더링한다"),
    ("동기화합니다", "동기화한다"),
    ("이해합니다", "이해한다"),
    ("의도합니다", "의도한다"),
    ("요구합니다", "요구한다"),
    ("요청합니다", "요청한다"),
    ("기다립니다", "기다린다"),
    ("기억합니다", "기억한다"),
    ("정의합니다", "정의한다"),
    ("구현합니다", "구현한다"),
    ("설계합니다", "설계한다"),
    ("디자인합니다", "디자인한다"),
    ("추구합니다", "추구한다"),
    ("갖춥니다", "갖춘다"),
    ("가집니다", "가진다"),
    ("나뉩니다", "나뉜다"),
    ("나눕니다", "나눈다"),
    ("합칩니다", "합친다"),
    ("쪼갭니다", "쪼갠다"),
    ("쪼개집니다", "쪼개진다"),
    ("연결합니다", "연결한다"),
    ("분리합니다", "분리한다"),
    ("교환합니다", "교환한다"),
    ("전송합니다", "전송한다"),
    ("전달합니다", "전달한다"),
    ("수신합니다", "수신한다"),
    ("기록합니다", "기록한다"),
    ("출력합니다", "출력한다"),
    ("로그합니다", "로그한다"),
    ("디버깅합니다", "디버깅한다"),
    ("재현합니다", "재현한다"),
    ("재시작합니다", "재시작한다"),
    ("종료합니다", "종료한다"),
    ("시작합니다", "시작한다"),
    ("진행합니다", "진행한다"),
    ("진단합니다", "진단한다"),
    ("분석합니다", "분석한다"),
    ("프로파일링합니다", "프로파일링한다"),
    # Generic catch-all (must come AFTER specific verbs)
    ("합니다", "한다"),
    ("됬습니다", "되었다"),  # potential typo
    # Past tense
    ("했습니다", "했다"),
    ("됐습니다", "되었다"),
    ("있었습니다", "있었다"),
    ("없었습니다", "없었다"),
    # Generic ~습니다 fallback (most action verbs handled above; this catches anything left)
    # Skip this — too risky without context. Manual review for leftovers.
]


def transform(text: str) -> tuple[str, int]:
    count = 0
    for pat, rep in RULES:
        new_text, n = re.subn(re.escape(pat), rep, text)
        count += n
        text = new_text
    return text, count


def main(paths: list[Path]) -> None:
    total = 0
    for p in paths:
        original = p.read_text(encoding="utf-8")
        new, n = transform(original)
        if n > 0:
            p.write_text(new, encoding="utf-8")
            print(f"{p}: {n} substitutions")
            total += n
    print(f"\nTotal: {total} substitutions across {len(paths)} files")


if __name__ == "__main__":
    docs = Path("E:/Git_Project/TechLib/docs")
    targets = [
        docs / "07-os-scheduling/index.md",
        docs / "08-memory-management/index.md",
        docs / "09-network-sync/index.md",
        docs / "09-network-sync/client-prediction.md",
        docs / "09-network-sync/dead-reckoning.md",
        docs / "10-profiling/index.md",
        docs / "11-advanced-rendering/index.md",
        docs / "11-advanced-rendering/physics-engine.md",
        docs / "11-advanced-rendering/pbr.md",
        docs / "11-advanced-rendering/wfc.md",
        docs / "12-oop-vs-dod-ecs/index.md",
        docs / "senior-knowledge/index.md",
        docs / "senior-knowledge/debugging-mindset.md",
        docs / "senior-knowledge/code-review.md",
        docs / "senior-knowledge/design-patterns.md",
        docs / "senior-knowledge/git-workflow.md",
        docs / "senior-knowledge/tech-trends-2026.md",
    ]
    main(targets)
