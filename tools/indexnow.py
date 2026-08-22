#!/usr/bin/env python3
"""IndexNow로 빙·네이버·Yandex에 URL 변경을 통보한다.

구글은 IndexNow에 참여하지 않는다(2023년 sitemap ping 폐지 후 Search Console
색인 요청만 가능). 이 스크립트는 빙·네이버용이다.

사용법:
    python3 tools/indexnow.py                      # sitemap.xml의 모든 URL
    python3 tools/indexnow.py <url> [<url> ...]    # 지정한 URL만
    python3 tools/indexnow.py --posts-only         # /posts/ 글만

macOS·Windows 공용(표준 라이브러리만 사용).
"""

import json
import re
import sys
import urllib.request
import urllib.error

HOST = "riririb161820.github.io"
KEY = "5768935f2adfde244257b38d96dddc03"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP = f"https://{HOST}/sitemap.xml"
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000  # IndexNow 1회 요청 상한


def fetch_sitemap_urls(posts_only: bool = False) -> list[str]:
    with urllib.request.urlopen(SITEMAP, timeout=30) as r:
        raw = r.read().decode("utf-8", "replace")
    # 정규식으로 <loc>만 뽑는다 — 일부 환경의 파이썬은 pyexpat이 깨져 있어
    # xml.etree를 쓰면 import 단계에서 죽는다. 사이트맵은 형식이 고정이라 안전하다.
    urls = [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", raw, re.S)]
    if posts_only:
        urls = [u for u in urls if "/posts/" in u]
    return urls


def submit(urls: list[str]) -> bool:
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[+] IndexNow {r.status} — {len(urls)}개 URL 통보 완료")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        # 200/202 외 상태는 사유가 본문에 담긴다 (403=키 불일치, 422=URL 불일치 등)
        print(f"[!] IndexNow 실패 {e.code}: {body}")
        return False
    except urllib.error.URLError as e:
        print(f"[!] IndexNow 연결 실패: {e.reason}")
        return False


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--posts-only"]
    posts_only = "--posts-only" in sys.argv

    urls = args if args else fetch_sitemap_urls(posts_only=posts_only)
    if not urls:
        print("[!] 통보할 URL이 없습니다")
        return 1

    ok = True
    for i in range(0, len(urls), BATCH):
        ok = submit(urls[i:i + BATCH]) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
