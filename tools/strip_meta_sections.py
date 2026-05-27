"""비기술 섹션(메타·면접·로드맵) 일괄 제거.

다음 H2 헤딩과 그 본문을 제거한다 (다음 H2 또는 EOF까지):
- ## 학습 로드맵
- ## 누구를 위한 자료인가
- ## 작성 원칙
- ## 왜 이 순서인가
- ## 면접 빈출 주제
- ## 면접/실무 포인트
- ## 자주 묻는 질문        # 일부 페이지에서 같은 의도로 작성됨

부수 효과로 생기는 연속 빈 줄은 한 줄로 정리.
"""
from __future__ import annotations
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

SECTIONS_TO_REMOVE = [
    "학습 로드맵",
    "누구를 위한 자료인가",
    "작성 원칙",
    "왜 이 순서인가",
    "면접 빈출 주제",
    "면접/실무 포인트",
    "자주 묻는 질문",
]


def strip_section(text: str, heading: str) -> tuple[str, int]:
    """## {heading} 부터 다음 ## (또는 EOF)까지 제거."""
    # 그룹: 시작 헤딩 라인 + 내용 + (다음 ## 헤딩 직전까지)
    pattern = re.compile(
        rf"^##\s*{re.escape(heading)}\s*\n(?:(?!^##\s).*\n?)*",
        re.MULTILINE,
    )
    new_text, n = pattern.subn("", text)
    return new_text, n


def collapse_blank_lines(text: str) -> str:
    """연속된 3개 이상의 \\n을 2개로 줄임."""
    return re.sub(r"\n{3,}", "\n\n", text)


def process_file(p: Path) -> int:
    text = p.read_text(encoding="utf-8")
    total = 0
    for h in SECTIONS_TO_REMOVE:
        text, n = strip_section(text, h)
        total += n
    if total > 0:
        text = collapse_blank_lines(text)
        # 파일 끝에 빈 줄 보장
        if not text.endswith("\n"):
            text += "\n"
        p.write_text(text, encoding="utf-8")
    return total


def main() -> None:
    targets = sorted(DOCS.rglob("*.md"))
    grand_total = 0
    for p in targets:
        n = process_file(p)
        if n > 0:
            rel = p.relative_to(DOCS.parent)
            print(f"{rel}: -{n} section(s)")
            grand_total += n
    print(f"\nTotal: -{grand_total} sections across {len(targets)} files")


if __name__ == "__main__":
    main()
