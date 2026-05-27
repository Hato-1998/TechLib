#!/usr/bin/env python3
"""TechLib 페이지 추가 도구.

대화형으로 새 페이지/섹션을 만들고 mkdocs.yml 및 섹션 인덱스를 자동 갱신한다.

사용:
    python tools/add_page.py                 # 대화형
    python tools/add_page.py --list          # 섹션 목록만 보기
    python tools/add_page.py --add ARGS...   # 비대화형 페이지 추가
    python tools/add_page.py --new-section ARGS...   # 비대화형 새 섹션

비대화형 예:
    python tools/add_page.py --add \
        --section "1. 자료구조" --title "해시 테이블" \
        --slug hash-table --summary "O(1) 평균 조회, 충돌 해결"

    python tools/add_page.py --new-section \
        --number 13 --folder 13-shader-programming \
        --title "셰이더 프로그래밍" --summary "HLSL/GLSL, 머티리얼 그래프"
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml  # mkdocs 의존성으로 이미 설치되어 있음

ROOT = Path(__file__).resolve().parent.parent
MKDOCS_YML = ROOT / "mkdocs.yml"
DOCS = ROOT / "docs"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


# ============================================================
# 기본 I/O
# ============================================================

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def prompt(label: str, default: Optional[str] = None, allow_empty: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        ans = input(f"{label}{suffix}: ").strip()
        if ans:
            return ans
        if default is not None:
            return default
        if allow_empty:
            return ""
        print("  값을 입력해 주세요.")


def confirm(label: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        ans = input(f"{label} [{d}]: ").strip().lower()
        if not ans:
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


# ============================================================
# mkdocs.yml 파싱·직렬화·교체
# ============================================================

class _OpaqueTag:
    """미지원 YAML 태그(예: !!python/name:...)를 그대로 보존하기 위한 placeholder."""

    def __init__(self, tag: str, value: object) -> None:
        self.tag = tag
        self.value = value


class _PermissiveLoader(yaml.SafeLoader):
    """mkdocs.yml에 있는 Python tag를 읽어들이기 위한 관대한 로더."""

    pass


def _construct_undefined(loader: yaml.Loader, node: yaml.Node) -> _OpaqueTag:
    return _OpaqueTag(str(node.tag), node.value)


_PermissiveLoader.add_constructor(None, _construct_undefined)


def load_config() -> dict:
    """mkdocs.yml을 dict로 읽는다.

    Python tag(!!python/name:...)는 _OpaqueTag로 감싸진다.
    nav 영역에는 그런 태그가 없으므로 우리 용도엔 영향 없음.
    """
    return yaml.load(read_text(MKDOCS_YML), Loader=_PermissiveLoader)


def get_sections(config: dict) -> list[tuple[str, object]]:
    """nav에서 '홈'을 제외한 [(이름, value)] 반환."""
    out = []
    for item in config.get("nav", []):
        if not isinstance(item, dict):
            continue
        for name, value in item.items():
            if name == "홈":
                continue
            out.append((name, value))
    return out


def section_folder(value) -> Path:
    """섹션의 docs/ 기준 폴더 경로."""
    if isinstance(value, str):
        return DOCS / Path(value).parent
    if isinstance(value, list):
        for sub in value:
            if isinstance(sub, dict):
                for v in sub.values():
                    if isinstance(v, str):
                        return DOCS / Path(v).parent
    raise ValueError(f"섹션 폴더 추출 실패: {value!r}")


def is_multipage(value) -> bool:
    return isinstance(value, list)


def serialize_nav(nav: list) -> str:
    """nav 리스트를 mkdocs.yml 들여쓰기 규약에 맞춰 직렬화."""
    lines = ["nav:"]
    for item in nav:
        if not isinstance(item, dict):
            continue
        for name, value in item.items():
            if isinstance(value, str):
                lines.append(f"  - {name}: {value}")
            elif isinstance(value, list):
                lines.append(f"  - {name}:")
                for sub in value:
                    if isinstance(sub, dict):
                        for sname, spath in sub.items():
                            lines.append(f"      - {sname}: {spath}")
    return "\n".join(lines)


def replace_nav_block(yml_text: str, new_nav: str) -> str:
    """yml_text의 nav: 블록을 통째로 new_nav로 교체."""
    lines = yml_text.split("\n")
    nav_start = None
    nav_end = None
    for i, line in enumerate(lines):
        if line.rstrip() == "nav:" and nav_start is None:
            nav_start = i
            continue
        if nav_start is not None and i > nav_start:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # 다음 top-level YAML 키 (들여쓰기 없음, ':' 포함)
            if line and not line[0].isspace() and ":" in stripped:
                nav_end = i
                break
    if nav_start is None:
        raise ValueError("mkdocs.yml에 nav: 섹션이 없습니다.")
    if nav_end is None:
        nav_end = len(lines)
    new_lines = lines[:nav_start] + new_nav.split("\n") + [""] + lines[nav_end:]
    return "\n".join(new_lines)


# ============================================================
# 섹션 index.md 표 갱신
# ============================================================

INDEX_TABLE_PATTERN = re.compile(
    r"(##\s*이 섹션에서 다루는 것[^\n]*\n+\|[^\n]+\|\n\|[\s\-:|]+\|\n)((?:\|[^\n]+\|\n)+)",
    re.MULTILINE,
)


def add_index_row(index_path: Path, title: str, slug: str, summary: str) -> str:
    """섹션 index.md의 '이 섹션에서 다루는 것' 표에 한 줄 추가."""
    if not index_path.exists():
        return "no-index"
    text = read_text(index_path)
    m = INDEX_TABLE_PATTERN.search(text)
    if not m:
        return "no-table"
    header = m.group(1)
    rows = m.group(2)
    if f"({slug}.md)" in rows:
        return "exists"
    new_row = f"| [{title}]({slug}.md) | {summary} |\n"
    updated = text.replace(header + rows, header + rows + new_row, 1)
    write_text(index_path, updated)
    return "ok"


# ============================================================
# docs/index.md (홈) 카드 추가
# ============================================================

def add_home_card(section_name: str, summary: str, index_link: str) -> bool:
    home = DOCS / "index.md"
    text = read_text(home)
    if f"]({index_link})" in text:
        return False  # 이미 있음
    new_card = f"- **{section_name}**\n\n    {summary}\n\n    [→ 시작하기]({index_link})\n\n"
    if "</div>" not in text:
        return False
    updated = text.replace("</div>", new_card + "</div>", 1)
    write_text(home, updated)
    return True


# ============================================================
# 템플릿 렌더링
# ============================================================

def render_page(title: str) -> str:
    template = read_text(TEMPLATES_DIR / "page.md")
    return template.replace("{{TITLE}}", title)


def render_section_index(
    section_name: str,
    first_title: str,
    first_slug: str,
    first_summary: str,
) -> str:
    template = read_text(TEMPLATES_DIR / "section_index.md")
    return (
        template
        .replace("{{SECTION_NAME}}", section_name)
        .replace("{{FIRST_TITLE}}", first_title)
        .replace("{{FIRST_SLUG}}", first_slug)
        .replace("{{FIRST_SUMMARY}}", first_summary)
    )


# ============================================================
# 편집기 자동 열기
# ============================================================

def open_in_editor(file_path: Path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(str(file_path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(file_path)])
        else:
            editor = os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(file_path)])
    except Exception as e:
        print(f"  ! 편집기 자동 실행 실패: {e}")
        print(f"    경로: {file_path}")


# ============================================================
# 명령 A: 기존 섹션에 페이지 추가
# ============================================================

def add_page_to_section(
    section_name: str,
    title: str,
    slug: str,
    summary: str,
    *,
    auto_confirm: bool = False,
    open_editor: bool = True,
) -> int:
    config = load_config()
    nav = config["nav"]

    # 섹션 찾기
    target = None
    for item in nav:
        if isinstance(item, dict) and section_name in item:
            target = item
            break
    if target is None:
        print(f"[에러] 섹션 '{section_name}'을 찾을 수 없습니다.")
        return 1

    current_value = target[section_name]
    folder = section_folder(current_value)
    folder_rel = folder.relative_to(DOCS)
    new_file = folder / f"{slug}.md"

    if new_file.exists():
        print(f"[에러] 파일이 이미 존재합니다: {new_file.relative_to(ROOT)}")
        return 1

    print(f"\n== '{section_name}'에 새 페이지 추가 ==")
    print(f"  생성:    docs/{folder_rel.as_posix()}/{slug}.md")
    print(f"  mkdocs.yml:  nav에 entry 추가")
    if (folder / "index.md").exists():
        print(f"  섹션 index:  '이 섹션에서 다루는 것' 표에 1행 추가")
    if not is_multipage(current_value):
        print(f"  변환:    '{section_name}'을 단일 → 다중 페이지 구조로 변환")
    print()

    if not auto_confirm and not confirm("진행할까요?", default=True):
        print("취소되었습니다.")
        return 0

    # nav 데이터 수정
    if isinstance(current_value, str):
        # 단일 → 다중 변환: 기존 페이지를 '개요'로 보존
        target[section_name] = [
            {"개요": current_value},
            {title: f"{folder_rel.as_posix()}/{slug}.md"},
        ]
    else:
        # 중복 체크
        flat = [list(s.values())[0] for s in current_value if isinstance(s, dict)]
        new_path = f"{folder_rel.as_posix()}/{slug}.md"
        if new_path in flat:
            print(f"[에러] 이미 nav에 같은 경로가 있습니다: {new_path}")
            return 1
        current_value.append({title: new_path})

    # 파일 생성
    write_text(new_file, render_page(title))
    print(f"  [OK] 파일 생성: {new_file.relative_to(ROOT)}")

    # mkdocs.yml 갱신
    new_nav_text = serialize_nav(nav)
    new_yml = replace_nav_block(read_text(MKDOCS_YML), new_nav_text)
    write_text(MKDOCS_YML, new_yml)
    print(f"  [OK] mkdocs.yml 업데이트")

    # 섹션 index 표 갱신
    index_path = folder / "index.md"
    result = add_index_row(index_path, title, slug, summary)
    if result == "ok":
        print(f"  [OK] 섹션 인덱스 표 업데이트")
    elif result == "no-table":
        print(f"  [skip] 섹션 index에 '이 섹션에서 다루는 것' 표가 없음")
    elif result == "no-index":
        print(f"  [skip] 섹션에 index.md 없음")
    elif result == "exists":
        print(f"  [skip] 표에 이미 해당 항목 존재")

    print(f"\n[성공] 편집할 파일: {new_file.relative_to(ROOT)}")
    if open_editor:
        if auto_confirm or confirm("지금 편집기로 열까요?", default=True):
            open_in_editor(new_file)

    return 0


# ============================================================
# 명령 B: 새 섹션 생성
# ============================================================

def create_new_section(
    section_number: str,
    folder_slug: str,
    section_title: str,
    summary: str,
    *,
    first_title: str = "",
    first_slug: str = "",
    first_summary: str = "",
    auto_confirm: bool = False,
    open_editor: bool = True,
) -> int:
    full_name = f"{section_number}. {section_title}"
    folder = DOCS / folder_slug
    multipage = bool(first_title and first_slug)

    if folder.exists():
        print(f"[에러] 폴더가 이미 존재합니다: {folder.relative_to(ROOT)}")
        return 1

    print(f"\n== 새 섹션: '{full_name}' ==")
    print(f"  생성:")
    print(f"    docs/{folder_slug}/index.md")
    if multipage:
        print(f"    docs/{folder_slug}/{first_slug}.md")
    print(f"  mkdocs.yml:  nav 끝에 새 섹션 추가")
    print(f"  docs/index.md:  홈 카드 그리드에 추가\n")

    if not auto_confirm and not confirm("진행할까요?", default=True):
        print("취소되었습니다.")
        return 0

    # 폴더 + index.md
    folder.mkdir(parents=True)
    index_path = folder / "index.md"
    if multipage:
        index_content = render_section_index(full_name, first_title, first_slug, first_summary)
    else:
        index_content = render_page(full_name)
    write_text(index_path, index_content)
    print(f"  [OK] 생성: {index_path.relative_to(ROOT)}")

    # 첫 하위 페이지
    if multipage:
        sub_path = folder / f"{first_slug}.md"
        write_text(sub_path, render_page(first_title))
        print(f"  [OK] 생성: {sub_path.relative_to(ROOT)}")

    # mkdocs.yml nav 추가
    config = load_config()
    nav = config["nav"]
    if multipage:
        new_entry = {full_name: [
            {"개요": f"{folder_slug}/index.md"},
            {first_title: f"{folder_slug}/{first_slug}.md"},
        ]}
    else:
        new_entry = {full_name: f"{folder_slug}/index.md"}
    nav.append(new_entry)

    new_nav_text = serialize_nav(nav)
    new_yml = replace_nav_block(read_text(MKDOCS_YML), new_nav_text)
    write_text(MKDOCS_YML, new_yml)
    print(f"  [OK] mkdocs.yml 업데이트")

    # 홈 카드
    if add_home_card(full_name, summary, f"{folder_slug}/index.md"):
        print(f"  [OK] docs/index.md 카드 추가")
    else:
        print(f"  [skip] docs/index.md 카드 (이미 있음 또는 그리드 없음)")

    edit_target = (folder / f"{first_slug}.md") if multipage else index_path
    print(f"\n[성공] 편집할 파일: {edit_target.relative_to(ROOT)}")
    if open_editor:
        if auto_confirm or confirm("지금 편집기로 열까요?", default=True):
            open_in_editor(edit_target)

    return 0


# ============================================================
# 명령 C: 페이지 제거
# ============================================================

def remove_page(
    section_name: str,
    slug: str,
    *,
    auto_confirm: bool = False,
) -> int:
    """기존 페이지를 nav·섹션 index에서 제거하고 파일을 삭제한다."""
    config = load_config()
    nav = config["nav"]

    target = None
    for item in nav:
        if isinstance(item, dict) and section_name in item:
            target = item
            break
    if target is None:
        print(f"[에러] 섹션 '{section_name}'을 찾을 수 없습니다.")
        return 1

    current = target[section_name]
    if not is_multipage(current):
        print(f"[에러] '{section_name}'은 단일 페이지 섹션입니다. 제거하려면 nav 직접 편집.")
        return 1

    folder = section_folder(current)
    folder_rel = folder.relative_to(DOCS)
    new_path = f"{folder_rel.as_posix()}/{slug}.md"
    target_file = folder / f"{slug}.md"

    # nav에서 제거
    new_list = []
    found = False
    for sub in current:
        if isinstance(sub, dict):
            (_name, _path), = sub.items()
            if _path == new_path:
                found = True
                continue
        new_list.append(sub)

    if not found:
        print(f"[에러] nav에서 '{new_path}'를 찾을 수 없습니다.")
        return 1

    print(f"\n== '{section_name}'에서 페이지 제거 ==")
    print(f"  삭제: docs/{new_path}")
    print(f"  업데이트: mkdocs.yml, 섹션 index 표\n")

    if not auto_confirm and not confirm("진행할까요?", default=False):
        print("취소되었습니다.")
        return 0

    target[section_name] = new_list

    # 파일 삭제
    if target_file.exists():
        target_file.unlink()
        print(f"  [OK] 파일 삭제: {target_file.relative_to(ROOT)}")

    # mkdocs.yml 갱신
    new_nav_text = serialize_nav(nav)
    new_yml = replace_nav_block(read_text(MKDOCS_YML), new_nav_text)
    write_text(MKDOCS_YML, new_yml)
    print(f"  [OK] mkdocs.yml 업데이트")

    # 섹션 index 표에서 행 제거
    index_path = folder / "index.md"
    if index_path.exists():
        text = read_text(index_path)
        # 해당 슬러그가 들어간 표 행 제거
        pattern = re.compile(rf"^\| \[[^\]]+\]\({re.escape(slug)}\.md\) \| [^\n]+\n", re.MULTILINE)
        new_text, n = pattern.subn("", text)
        if n > 0:
            write_text(index_path, new_text)
            print(f"  [OK] 섹션 인덱스 표에서 행 제거")

    print(f"\n[성공] 제거 완료")
    return 0


# ============================================================
# 대화형 메뉴
# ============================================================

def list_sections() -> None:
    config = load_config()
    sections = get_sections(config)
    print(f"\n== 섹션 목록 ==\n")
    for i, (name, value) in enumerate(sections, 1):
        kind = "여러 페이지" if is_multipage(value) else "단일 페이지"
        print(f"  {i:>2}. {name}  ({kind})")


def interactive_main() -> int:
    print("\n" + "=" * 42)
    print("  TechLib 페이지 추가 도구")
    print("=" * 42)

    config = load_config()
    sections = get_sections(config)

    print(f"\n== 섹션 목록 ==\n")
    for i, (name, value) in enumerate(sections, 1):
        kind = "여러 페이지" if is_multipage(value) else "단일 페이지"
        print(f"  {i:>2}. {name}  ({kind})")
    print(f"   N. 새 섹션 만들기")
    print(f"   Q. 종료")

    while True:
        ans = input("\n선택: ").strip().lower()
        if ans in ("q", "quit", "exit"):
            return 0
        if ans == "n":
            print("\n== 새 섹션 만들기 ==\n")
            num = prompt("섹션 번호 (예: 13)")
            slug = prompt(f"섹션 폴더명 (예: {num}-shader-programming)")
            title = prompt("섹션 표시명 (예: 셰이더 프로그래밍)")
            summary = prompt("홈 카드 한 줄 설명")
            if confirm("첫 하위 페이지도 만들까요?", default=True):
                fst_title = prompt("첫 하위 페이지 제목 (한국어)")
                fst_slug = prompt("첫 하위 페이지 슬러그 (영문)")
                fst_summary = prompt("첫 하위 페이지 한 줄 요약")
            else:
                fst_title = fst_slug = fst_summary = ""
            return create_new_section(
                num, slug, title, summary,
                first_title=fst_title, first_slug=fst_slug, first_summary=fst_summary,
            )
        if ans.isdigit():
            idx = int(ans) - 1
            if 0 <= idx < len(sections):
                name, value = sections[idx]
                print(f"\n== '{name}'에 새 페이지 추가 ==\n")
                title = prompt("페이지 제목 (한국어)")
                slug = prompt("영문 슬러그 (파일명, 예: hash-table)")
                summary = prompt("한 줄 요약 (섹션 인덱스 표용)")
                return add_page_to_section(name, title, slug, summary)
        print("  올바른 번호 또는 N/Q를 입력하세요.")


# ============================================================
# argparse
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="TechLib 페이지 추가 도구")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="섹션 목록 출력")

    p_add = sub.add_parser("add", help="기존 섹션에 페이지 추가 (비대화형)")
    p_add.add_argument("--section", required=True, help="섹션 이름 (예: '1. 자료구조')")
    p_add.add_argument("--title", required=True, help="페이지 제목")
    p_add.add_argument("--slug", required=True, help="영문 슬러그 (파일명)")
    p_add.add_argument("--summary", required=True, help="섹션 인덱스 표용 한 줄 요약")
    p_add.add_argument("--no-open", action="store_true", help="편집기 자동 실행 안 함")
    p_add.add_argument("--yes", action="store_true", help="모든 확인 건너뛰기")

    p_rm = sub.add_parser("remove", help="페이지 제거 (비대화형)")
    p_rm.add_argument("--section", required=True, help="섹션 이름 (예: '1. 자료구조')")
    p_rm.add_argument("--slug", required=True, help="제거할 페이지 슬러그")
    p_rm.add_argument("--yes", action="store_true", help="확인 건너뛰기")

    p_new = sub.add_parser("new-section", help="새 섹션 생성 (비대화형)")
    p_new.add_argument("--number", required=True)
    p_new.add_argument("--folder", required=True, help="폴더 슬러그 (예: 13-shader-programming)")
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--summary", required=True, help="홈 카드 한 줄 설명")
    p_new.add_argument("--first-title", default="", help="첫 하위 페이지 제목")
    p_new.add_argument("--first-slug", default="", help="첫 하위 페이지 슬러그")
    p_new.add_argument("--first-summary", default="", help="첫 하위 페이지 요약")
    p_new.add_argument("--no-open", action="store_true")
    p_new.add_argument("--yes", action="store_true")

    args = parser.parse_args()

    if args.cmd == "list":
        list_sections()
        return 0
    if args.cmd == "add":
        return add_page_to_section(
            args.section, args.title, args.slug, args.summary,
            auto_confirm=args.yes, open_editor=not args.no_open,
        )
    if args.cmd == "remove":
        return remove_page(args.section, args.slug, auto_confirm=args.yes)
    if args.cmd == "new-section":
        return create_new_section(
            args.number, args.folder, args.title, args.summary,
            first_title=args.first_title, first_slug=args.first_slug,
            first_summary=args.first_summary,
            auto_confirm=args.yes, open_editor=not args.no_open,
        )
    # 인자 없으면 대화형
    return interactive_main()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n중단되었습니다.")
        sys.exit(130)
