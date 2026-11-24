#!/usr/bin/env python3
"""발행 후 검증 (하네스 3단계). 표준 라이브러리만.

    python3 tools/post_verify.py <slug 또는 _posts/파일.md> [--shot DIR] [--indexnow]

라이브 페이지(https://riririb.com/posts/<slug>/)를 받아서 확인한다:
  1. HTTP 200, <title>이 front matter title로 시작
  2. meta description이 front matter description과 일치
  3. 글 안 #앵커 링크가 전부 실제 id로 연결
  4. 본문 이미지·대표 이미지가 전부 200
  5. (--shot) Chrome 헤드리스로 전체 페이지 스크린샷 저장 → 사람이/Claude가 눈으로 확인
  6. (--indexnow) 통과하면 IndexNow 통보
배포 직후엔 CDN 캐시 때문에 옛 버전이 올 수 있어 쿼리스트링으로 캐시를 피한다.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://riririb.com"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_lint import split_front_matter  # noqa: E402


def fetch(url: str, method: str = "GET") -> tuple[int, str]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "riririb-post-verify"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, (r.read().decode("utf-8", "replace") if method == "GET" else "")
    except urllib.error.HTTPError as e:
        return e.code, ""


def norm(t: str) -> str:
    """Jekyll(kramdown smart quotes)이 바꾼 따옴표·공백을 되돌려 비교한다."""
    t = t.translate(str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " "}))
    return re.sub(r"\s+", " ", t).strip()


def find_post(arg: str) -> Path:
    p = Path(arg)
    if p.suffix == ".md" and p.exists():
        return p.resolve()
    hits = sorted((ROOT / "_posts").glob(f"*-{arg}.md"))
    if not hits:
        sys.exit(f"글을 찾을 수 없음: {arg}")
    return hits[0]


def chrome_path() -> str | None:
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if Path(mac).exists() else shutil.which("google-chrome")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("post")
    ap.add_argument("--shot", metavar="DIR", help="전체 페이지 스크린샷 저장 폴더")
    ap.add_argument("--indexnow", action="store_true", help="모두 통과하면 IndexNow 통보")
    a = ap.parse_args()

    path = find_post(a.post)
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    fm, _, _ = split_front_matter(path.read_text(encoding="utf-8"))
    url = f"{SITE}/posts/{slug}/"
    fails, notes = [], []

    status, body = fetch(f"{url}?v={int(time.time())}")
    if status != 200:
        print(f"[FAIL] {url} → HTTP {status}")
        return 1

    m = re.search(r"<title>(.*?)</title>", body, re.S)
    live_title = html.unescape(m.group(1)).strip() if m else ""
    if not norm(live_title).startswith(norm(fm.get("title", "\0"))):
        fails.append(f"title 불일치: 라이브='{live_title[:60]}'")
    m = re.search(r'<meta name="description" content="([^"]*)"', body)
    live_desc = html.unescape(m.group(1)) if m else ""
    want_desc = fm.get("description", "")
    if want_desc and norm(live_desc) != norm(want_desc):
        fails.append("description 불일치(배포 전 버전이 캐시됐을 수 있음 — 1~2분 뒤 재시도)")

    ids = set(re.findall(r'\bid="([^"]+)"', body))
    for href in sorted(set(re.findall(r'href="#([^"]+)"', body))):
        h = urllib.parse.unquote(href)
        if h not in ids:
            fails.append(f"끊긴 앵커: #{h}")

    imgs = set(re.findall(r'<img[^>]+src="([^"]+)"', body))
    img = fm.get("image")
    if isinstance(img, dict) and img.get("path"):
        imgs.add(img["path"])
    checked = 0
    for src in sorted(imgs):
        if src.startswith("data:"):
            continue
        full = urllib.parse.urljoin(url, src)
        if not full.startswith(SITE):
            continue
        st, _ = fetch(full, "HEAD")
        checked += 1
        if st != 200:
            fails.append(f"이미지 {st}: {src}")
    notes.append(f"이미지 {checked}개 확인")

    if a.shot:
        out = Path(a.shot).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        shot = out / f"verify-{slug}.png"
        chrome = chrome_path()
        if not chrome:
            notes.append("Chrome 없음 — 스크린샷 건너뜀")
        else:
            subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=1", "--window-size=1000,6000",
                            "--virtual-time-budget=6000", f"--screenshot={shot}", url],
                           capture_output=True, timeout=120)
            notes.append(f"스크린샷: {shot} (Read로 열어 눈으로 확인할 것 — 200은 '보인다'가 아님)")

    print(f"[{'FAIL' if fails else 'OK'}] {url}")
    for f in fails:
        print(f"  FAIL  {f}")
    for n in notes:
        print(f"  info  {n}")

    if a.indexnow and not fails:
        subprocess.run([sys.executable, str(ROOT / "tools" / "indexnow.py"), url])
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
