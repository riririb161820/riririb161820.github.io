#!/usr/bin/env python3
"""블로그 글 → velog 발췌본 마크다운 생성기.

velog는 **트래픽을 빌리는 채널**이지 본진이 아니다. 원문을 통째로 복사하면
중복 콘텐츠가 되어 원문(riririb.com)의 검색 순위를 갉아먹으므로,
**도입부는 새로 쓰고 일부 섹션만 발췌한 뒤 원문 링크로 보내는** 방식을 쓴다.

이 스크립트가 맡는 건 기계적이고 틀리기 쉬운 부분이다:
  - 이미지 상대경로(/assets/...) → 절대 URL (velog에선 상대경로가 깨진다)
  - Chirpy 전용 kramdown IAL({: .prompt-tip } 등) 제거 (velog에선 그대로 노출된다)
  - 원문 링크 푸터 + 태그 목록 생성
  - **중복률 계산** — 원문 대비 재사용 비율이 높으면 경고

도입부 새로 쓰기와 섹션 선택은 사람(또는 작성 세션)이 판단한다.

사용법:
    # 1) 섹션 목록 확인
    python3 tools/velog_crosspost.py --slug <slug> --list

    # 2) 도입부를 파일로 쓴 뒤 발췌본 생성
    python3 tools/velog_crosspost.py --slug <slug> --sections 2,3 \
        --intro /tmp/intro.md --title "velog용 제목"

macOS·Windows 공용(표준 라이브러리만 사용).
"""

import argparse
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO, "_posts")
SITE_URL = "https://riririb.com"

# 재사용 비율이 이 값을 넘으면 중복 콘텐츠로 판정될 위험이 있어 경고한다.
DUPE_WARN_RATIO = 0.45


def read_post(slug: str) -> tuple[str, str, str]:
    """_posts에서 slug에 해당하는 글을 찾아 (경로, front matter, 본문)을 돌려준다."""
    hits = glob.glob(os.path.join(POSTS_DIR, f"*-{slug}.md"))
    if not hits:
        raise SystemExit(f"[!] _posts에서 '{slug}' 글을 찾지 못했습니다")
    path = sorted(hits)[-1]
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"[!] front matter를 파싱하지 못했습니다: {path}")
    return path, m.group(1), m.group(2).strip()


def front_matter_value(fm: str, key: str) -> str:
    """따옴표 유무·인라인 리스트를 모두 견디는 얕은 front matter 파서."""
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def split_sections(body: str) -> list[tuple[str, str]]:
    """본문을 '## ' 기준으로 쪼갠다. 코드펜스 안의 '## '는 제목이 아니므로 건너뛴다."""
    sections: list[tuple[str, str]] = []
    title, buf, in_fence = None, [], False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            if title is not None:
                sections.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        elif title is not None:
            buf.append(line)
    if title is not None:
        sections.append((title, "\n".join(buf).strip()))
    return sections


def clean_for_velog(text: str) -> str:
    """Chirpy 전용 문법을 걷어내고 링크·이미지를 절대 URL로 바꾼다."""
    # kramdown IAL — velog는 이 문법을 모르므로 '{: .prompt-tip }'이 본문에 그대로 찍힌다.
    text = re.sub(r"^\{:\s*\..+?\s*\}\s*$", "", text, flags=re.M)
    # 이미지·링크의 루트 상대경로는 velog 도메인 기준이 되어 깨진다 → 절대 URL로.
    text = re.sub(r"\]\((/(?!/)[^)]*)\)", rf"]({SITE_URL}\1)", text)
    # IAL을 지우면서 생긴 빈 줄 3개 이상을 2개로 정리.
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build(slug: str, fm: str, body: str, picked: list[int], intro: str,
          title: str | None) -> tuple[str, float]:
    sections = split_sections(body)
    canonical = f"{SITE_URL}/posts/{slug}/"
    out = [intro.strip(), ""]

    excerpt_len = 0
    for i in picked:
        if not 1 <= i <= len(sections):
            raise SystemExit(f"[!] 섹션 번호 {i}는 범위를 벗어납니다 (1~{len(sections)})")
        head, content = sections[i - 1]
        cleaned = clean_for_velog(content)
        excerpt_len += len(cleaned)
        out += [f"## {head}", "", cleaned, ""]

    out += [
        "---",
        "",
        "### 전체 내용은 원문에",
        "",
        f"이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.",
        "",
        f"👉 **[{front_matter_value(fm, 'title')}]({canonical})**",
        "",
    ]

    # 제목은 velog 에디터의 별도 입력란에 들어가므로 본문에 섞지 않는다.
    ratio = excerpt_len / max(len(body), 1)
    return "\n".join(out).strip() + "\n", ratio


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--list", action="store_true", help="섹션 목록만 출력")
    ap.add_argument("--sections", default="", help="발췌할 섹션 번호 (예: 2,3)")
    ap.add_argument("--intro", help="새로 쓴 도입부 마크다운 파일 경로")
    ap.add_argument("--title", help="velog용 제목 (원문과 다르게)")
    ap.add_argument("--out", help="출력 경로 (기본: /tmp/velog-<slug>.md)")
    a = ap.parse_args()

    path, fm, body = read_post(a.slug)
    sections = split_sections(body)

    if a.list or not a.sections:
        print(f"[원문] {os.path.relpath(path, REPO)}")
        print(f"[제목] {front_matter_value(fm, 'title')}")
        print(f"[태그] {front_matter_value(fm, 'tags')}")
        print(f"[본문] {len(body):,}자 · 섹션 {len(sections)}개\n")
        for i, (head, content) in enumerate(sections, 1):
            print(f"  {i:2}. {head}  ({len(content):,}자)")
        if not a.sections:
            print("\n→ --sections 2,3 --intro <파일> 로 발췌본을 생성하세요.")
        return 0

    if not a.intro:
        raise SystemExit("[!] --intro 로 새로 쓴 도입부 파일을 지정하세요 "
                         "(원문 도입부 복사는 중복 콘텐츠가 됩니다)")
    with open(a.intro, encoding="utf-8") as f:
        intro = f.read()

    picked = [int(x) for x in a.sections.split(",") if x.strip()]
    doc, ratio = build(a.slug, fm, body, picked, intro, a.title)

    out = a.out or f"/tmp/velog-{a.slug}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"[+] 발췌본 생성: {out}  ({len(doc):,}자)")
    if a.title:
        print(f"[+] velog 제목: {a.title}")
    print(f"[+] 원문 재사용 비율: {ratio:.0%}")
    if ratio > DUPE_WARN_RATIO:
        print(f"[!] 경고: 재사용 비율이 {DUPE_WARN_RATIO:.0%}를 넘습니다. "
              "섹션을 줄이지 않으면 원문이 중복 콘텐츠로 밀릴 수 있습니다.")
    print(f"[+] velog 태그: {front_matter_value(fm, 'tags')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
