#!/usr/bin/env python3
"""블로그 글 검사기 (하네스 1단계).

글(.md)을 넣으면 발행 전에 잡아야 할 문제를 찾는다. 표준 라이브러리만 쓴다(mac/win 공용).

    python3 tools/post_lint.py _posts/2026-09-02-foo.md [...]
    python3 tools/post_lint.py --changed      # git에서 바뀐(스테이징 포함) 글만
    python3 tools/post_lint.py --staged       # 커밋 대기 글만(pre-commit 훅이 사용)
    python3 tools/post_lint.py --all          # 전체

ERROR가 하나라도 있으면 종료코드 1. WARN은 보고만 한다.

기밀 금칙어: 저장소에 넣지 않는다. 환경변수 BLOG_LINT_TERMS(파일 경로, 여러 개면 os.pathsep 구분)
또는 git config blog.lintTerms <경로>(기계별 로컬 설정, 푸시 안 됨)로 지정한 파일을 읽는다. 한 줄에 단어 하나, '#'으로 시작하면 주석. 지정이 없으면 기밀 검사는 건너뛰고 WARN.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

MIN_BODY_ERROR = 1500   # 이보다 짧으면 ERROR
MIN_BODY_WARN = 3000    # 이보다 짧으면 WARN
DESC_WARN = 160         # description이 이보다 길면 검색결과에서 잘릴 수 있음(WARN)

REQUIRED_FM = ["title", "date", "categories", "tags", "description"]

OWN_PATH_RE = re.compile(r"(?:https?://(?:www\.)?riririb\.com)?/(?:posts|assets)/[^\s)\"']*")
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.items: list[tuple[str, int, str]] = []

    def error(self, line: int, msg: str):
        self.items.append(("ERROR", line, msg))

    def warn(self, line: int, msg: str):
        self.items.append(("WARN", line, msg))

    @property
    def errors(self):
        return [i for i in self.items if i[0] == "ERROR"]


# ---------- 파싱 ----------

def split_front_matter(text: str):
    """(front matter dict, fm 줄 수, 본문 줄 목록[(줄번호, 내용)])"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 0, list(enumerate(lines, 1))
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = parse_simple_yaml(lines[1:i])
            body = list(enumerate(lines[i + 1:], i + 2))
            return fm, i + 1, body
    return None, 0, list(enumerate(lines, 1))


def parse_simple_yaml(lines: list[str]) -> dict:
    """Chirpy front matter 수준의 단순 YAML(최상위 키 + 한 단계 중첩)만 읽는다."""
    out: dict = {}
    parent = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^(\s*)([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if not m:
            out.setdefault("__bad__", []).append(raw)
            continue
        indent, key, val = m.groups()
        val = unquote(val)
        if indent and parent is not None:
            if not isinstance(out.get(parent), dict):
                out[parent] = {}
            out[parent][key] = val
        else:
            out[key] = val if val != "" else {}
            parent = key
    return out


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def strip_code(body: list[tuple[int, str]]):
    """코드펜스 밖 줄과 코드블록 목록을 돌려준다."""
    prose, blocks = [], []
    in_code, fence, lang, start, buf = False, "", "", 0, []
    for no, line in body:
        m = FENCE_RE.match(line)
        if not in_code and m:
            in_code, fence, lang, start, buf = True, m.group(2)[0] * 3, m.group(3).strip(), no, []
            continue
        if in_code and m and m.group(2).startswith(fence) and not m.group(3).strip():
            blocks.append({"line": start, "lang": lang, "code": "\n".join(buf)})
            in_code = False
            continue
        (buf if in_code else prose).append(line if in_code else (no, line))
    if in_code:
        blocks.append({"line": start, "lang": lang, "code": "\n".join(buf), "unclosed": True})
    return prose, blocks


def heading_id(text: str) -> str:
    """kramdown이 이 블로그에서 만드는 heading id 규칙(라이브 HTML로 확인, 2026-11-18)."""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # 링크는 텍스트만
    t = t.lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def collect_ids(prose: list[tuple[int, str]]) -> set[str]:
    ids, seen = set(), {}
    for _, line in prose:
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        base = heading_id(m.group(2))
        n = seen.get(base, 0)
        ids.add(base if n == 0 else f"{base}-{n}")
        seen[base] = n + 1
    return ids


# ---------- 사이트 색인 ----------

_site_cache: dict | None = None


def site_index() -> dict:
    """슬러그 → 글 파일, 그 밖의 존재하는 경로."""
    global _site_cache
    if _site_cache is not None:
        return _site_cache
    posts = {}
    for p in POSTS.glob("*.md"):
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
        posts[slug] = p
    permalinks = set()
    for p in list(ROOT.glob("_tabs/*.md")) + list(ROOT.glob("redirects/*.html")) + list(ROOT.glob("*.md")) + list(ROOT.glob("*.html")):
        try:
            head = p.read_text(encoding="utf-8")[:2000]
        except Exception:
            continue
        m = re.search(r"^permalink:\s*(\S+)", head, re.M)
        if m:
            permalinks.add(m.group(1).strip("\"'").rstrip("/") + "/")
        if p.parent.name == "_tabs":
            permalinks.add(f"/{p.stem}/")
    _site_cache = {"posts": posts, "permalinks": permalinks}
    return _site_cache


def ids_of_post(path: Path) -> set[str]:
    _, _, body = split_front_matter(path.read_text(encoding="utf-8"))
    prose, _ = strip_code(body)
    return collect_ids(prose)


# ---------- 금칙어 ----------

def load_terms() -> list[str] | None:
    spec = os.environ.get("BLOG_LINT_TERMS", "")
    if not spec:  # 기계별 로컬 설정: git config blog.lintTerms <경로> (.git/config라 푸시되지 않음)
        spec = subprocess.run(["git", "-C", str(ROOT), "config", "--get", "blog.lintTerms"],
                              capture_output=True, text=True).stdout.strip()
    if not spec:
        return None
    terms = []
    for f in spec.split(os.pathsep):
        p = Path(f).expanduser()
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    terms.append(line)
    return terms


# ---------- 검사 ----------

def lint(path: Path, terms: list[str] | None) -> Report:
    r = Report(path)
    text = path.read_text(encoding="utf-8")
    fm, fm_end, body = split_front_matter(text)

    # front matter
    if fm is None:
        r.error(1, "front matter(--- ... ---)가 없거나 닫히지 않음")
        fm = {}
    for bad in fm.get("__bad__", []):
        r.error(1, f"front matter 해석 불가 줄: {bad[:60]}")
    for k in REQUIRED_FM:
        if not fm.get(k):
            r.error(1, f"front matter 필수 필드 누락: {k}")
    if not fm.get("headline"):
        r.warn(1, "headline 없음 — 메인 카드 커버 문구가 비게 됨")
    desc = fm.get("description") or ""
    if isinstance(desc, str) and len(desc) > DESC_WARN:
        r.warn(1, f"description {len(desc)}자 — {DESC_WARN}자 넘으면 검색결과에서 잘릴 수 있음")
    date_s = fm.get("date")
    if isinstance(date_s, str) and date_s:
        try:
            d = dt.datetime.strptime(date_s, "%Y-%m-%d %H:%M:%S %z")
            if d > dt.datetime.now(dt.timezone.utc):
                r.error(1, f"date가 미래({date_s}) — Jekyll이 빌드에서 빼서 404가 됨")
            if not path.name.startswith(d.strftime("%Y-%m-%d")):
                r.warn(1, f"파일명 날짜와 front matter date({date_s[:10]})가 다름")
        except ValueError:
            r.error(1, f"date 형식 오류: {date_s} (예: 2026-11-18 10:00:00 +0900)")
    img = fm.get("image")
    if isinstance(img, dict) and img.get("path"):
        if not (ROOT / img["path"].lstrip("/")).exists():
            r.error(1, f"대표 이미지 파일 없음: {img['path']}")
        if not img.get("alt"):
            r.warn(1, "대표 이미지 alt 없음")

    prose, blocks = strip_code(body)

    # 코드블록
    for b in blocks:
        if b.get("unclosed"):
            r.error(b["line"], "코드블록(```)이 닫히지 않음")
        if not b["lang"]:
            r.warn(b["line"], "코드블록 언어 표시 없음 (예: ```bash, ```text)")
        if b["lang"].split()[0:1] == ["json"]:
            try:
                json.loads(b["code"])
            except json.JSONDecodeError as e:
                r.warn(b["line"], f"```json 블록이 유효한 JSON이 아님({e.msg}) — 렌더 시 빨간 오류 표시 가능. 유효 JSON으로 고치거나 언어를 text로")

    # Liquid: raw 밖의 {{ (코드블록 포함 전체 본문 기준)
    in_raw = False
    for no, line in body:
        pos = 0
        while pos < len(line):
            if not in_raw:
                i_raw = line.find("{% raw %}", pos)
                i_tpl = line.find("{{", pos)
                if i_tpl != -1 and (i_raw == -1 or i_tpl < i_raw):
                    r.error(no, "{% raw %} 밖의 '{{' — Liquid가 먹어서 사라짐. {% raw %}…{% endraw %}로 감쌀 것")
                    break
                if i_raw == -1:
                    break
                in_raw, pos = True, i_raw + len("{% raw %}")
            else:
                i_end = line.find("{% endraw %}", pos)
                if i_end == -1:
                    break
                in_raw, pos = False, i_end + len("{% endraw %}")
    if in_raw:
        r.error(len(text.split("\n")), "{% raw %}가 {% endraw %}로 닫히지 않음")

    # 본문 길이(코드 제외)
    plain = "\n".join(l for _, l in prose)
    plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", plain)
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = re.sub(r"^\{:.*\}\s*$", "", plain, flags=re.M)
    n = len(plain.strip())
    if n < MIN_BODY_ERROR:
        r.error(1, f"본문(코드 제외) {n}자 — {MIN_BODY_ERROR}자 미만, 얇은 글")
    elif n < MIN_BODY_WARN:
        r.warn(1, f"본문(코드 제외) {n}자 — {MIN_BODY_WARN}자 미만")

    # 링크·이미지
    ids = collect_ids(prose)
    site = site_index()
    for no, line in prose:
        for m in re.finditer(r"(!?)\[[^\]]*\]\(([^)\s]+)[^)]*\)", line):
            is_img, url = m.group(1) == "!", m.group(2)
            if url.startswith("#"):
                if url[1:] not in ids:
                    r.error(no, f"글 안 앵커 없음: {url}")
                continue
            if url.startswith(("http://", "https://")):
                m2 = re.match(r"https?://(?:www\.)?riririb\.com(/.*)?$", url)
                if not m2:
                    continue
                url = m2.group(1) or "/"
            if not url.startswith("/"):
                continue
            path_part, _, frag = url.partition("#")
            if is_img or path_part.startswith("/assets/"):
                if not (ROOT / path_part.lstrip("/")).exists():
                    r.error(no, f"파일 없음: {path_part}")
                continue
            pm = re.match(r"^/posts/([^/]+)/?$", path_part)
            if pm:
                target = site["posts"].get(pm.group(1))
                if target is None:
                    norm = path_part.rstrip("/") + "/"
                    if norm not in site["permalinks"]:
                        r.error(no, f"없는 글 링크: {path_part}")
                    continue
                if frag and frag not in ids_of_post(target):
                    r.error(no, f"링크한 글에 앵커 없음: {path_part}#{frag}")
                continue
            norm = path_part.rstrip("/") + "/"
            if path_part not in ("/",) and norm not in site["permalinks"] and not (ROOT / path_part.lstrip("/")).exists():
                r.warn(no, f"확인 못 한 내부 링크: {path_part}")

    # 기밀 금칙어 (front matter 포함 전체)
    if terms is None:
        r.warn(1, "기밀 금칙어 검사 건너뜀 — BLOG_LINT_TERMS 미설정")
    else:
        for no, line in enumerate(text.split("\n"), 1):
            # 이 사이트의 기존 URL·파일 경로는 바꾸면 색인·링크가 깨지므로 예외(2026-11-19 사용자 결정)
            low = OWN_PATH_RE.sub("", line).lower()
            for t in terms:
                if t.lower() in low:
                    r.error(no, "기밀 금칙어 포함 (단어는 출력하지 않음 — 사전 대조 필요)")
                    break
    return r


def staged_posts() -> list[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                         capture_output=True, text=True).stdout
    return [ROOT / p for p in out.splitlines() if p.startswith("_posts/") and p.endswith(".md") and (ROOT / p).exists()]


def changed_posts() -> list[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout
    files = []
    for line in out.splitlines():
        p = line[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ")[1]
        if p.startswith("_posts/") and p.endswith(".md") and (ROOT / p).exists():
            files.append(ROOT / p)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="블로그 글 검사기")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--changed", action="store_true", help="git에서 바뀐 글만")
    ap.add_argument("--staged", action="store_true", help="커밋 대기(스테이징)된 글만 — pre-commit용")
    ap.add_argument("--all", action="store_true", help="_posts 전체")
    ap.add_argument("--quiet", action="store_true", help="WARN 숨김")
    a = ap.parse_args(argv)

    if a.all:
        files = sorted(POSTS.glob("*.md"))
    elif a.staged:
        files = staged_posts()
    elif a.changed:
        files = changed_posts()
    else:
        files = [Path(f).resolve() for f in a.files]
    if not files:
        print("검사할 글 없음")
        return 0

    terms = load_terms()
    total_err = 0
    for f in files:
        rep = lint(f, terms)
        shown = [i for i in rep.items if not (a.quiet and i[0] == "WARN")]
        status = "FAIL" if rep.errors else "OK"
        print(f"[{status}] {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
        for level, line, msg in sorted(shown, key=lambda x: (x[0] != "ERROR", x[1])):
            print(f"  {level:5} L{line}: {msg}")
        total_err += len(rep.errors)
    print(f"\n{len(files)}편 검사, ERROR {total_err}건")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
