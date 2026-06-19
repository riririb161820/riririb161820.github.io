#!/usr/bin/env python3
"""블로그 카드 썸네일 생성기 (HTML → 헤드리스 Chrome PNG, 1200x630).

단일 생성:  python3 tools/gen_card.py --title "제목" --category 자동화 --slug my-post
전체 재생성: python3 tools/gen_card.py --all

카테고리(자동화/운영/트러블슈팅)에 따라 색·아이콘이 정해진다. 그 외는 회색.
출력: assets/img/cards/<slug>.png  (메인페이지 카드 전용. 본문 히어로 이미지는 별개)
"""
import argparse, html, os, re, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "assets", "img", "cards")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

THEME = {
    "자동화":     {"dot": "#2dd4a7", "pillbg": "rgba(45,212,167,0.16)",  "pilltext": "#5fe3c0",
                  "icon": '<path d="M13 2 5 13h6l-1 9 9-12h-6z"/>'},
    "운영":       {"dot": "#5ba3f0", "pillbg": "rgba(91,163,240,0.16)",  "pilltext": "#8cc2f7",
                  "icon": '<rect x="3" y="11" width="4" height="10" rx="1"/><rect x="10" y="5" width="4" height="16" rx="1"/><rect x="17" y="8" width="4" height="13" rx="1"/>'},
    "트러블슈팅":  {"dot": "#f0a93c", "pillbg": "rgba(240,169,60,0.16)",  "pilltext": "#f5c477",
                  "icon": '<path d="M12 7a4 4 0 0 1 4 4v3a4 4 0 0 1-8 0v-3a4 4 0 0 1 4-4z"/><rect x="10.5" y="2.5" width="3" height="4.5" rx="1.5"/>'},
}
DEFAULT = {"dot": "#8a97a8", "pillbg": "rgba(138,151,168,0.16)", "pilltext": "#aab4c2",
           "icon": '<circle cx="12" cy="12" r="7"/>'}

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{font-family:-apple-system,"Apple SD Gothic Neo","Pretendard",sans-serif}}
.c{{width:1200px;height:630px;background:#1b2533;padding:64px 72px;position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between}}
.mark{{font-family:"SF Mono",monospace;font-size:24px;color:#8a97a8;display:flex;align-items:center;gap:12px}}
.dot{{width:14px;height:14px;border-radius:50%;background:{dot}}}
.pill{{display:inline-block;font-size:24px;font-weight:600;padding:7px 20px;border-radius:12px;background:{pillbg};color:{pilltext};margin-bottom:22px}}
.ttl{{font-size:54px;font-weight:700;line-height:1.3;color:#f1f5f9;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.ic{{position:absolute;right:-16px;bottom:-44px;color:#fff;opacity:.10}}
</style></head><body>
<div class="c">
  <div class="mark"><span class="dot"></span>riririb.log</div>
  <div>
    <span class="pill">{category}</span>
    <div class="ttl">{title}</div>
  </div>
  <svg class="ic" viewBox="0 0 24 24" width="260" height="260" fill="currentColor">{icon}</svg>
</div></body></html>"""


def render(title, category, slug):
    t = THEME.get(category, DEFAULT)
    page = TEMPLATE.format(dot=t["dot"], pillbg=t["pillbg"], pilltext=t["pilltext"],
                           category=html.escape(category), title=html.escape(title), icon=t["icon"])
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, slug + ".png")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page)
        html_path = f.name
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=1200,630",
                    "--screenshot=" + out, "file://" + html_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(html_path)
    print("  ✓", os.path.basename(out))
    return out


def parse_front_matter(path):
    text = open(path, encoding="utf-8").read()
    title = re.search(r'^title:\s*(.+)$', text, re.M)
    cats = re.search(r'^categories:\s*\[(.+)\]', text, re.M)
    title = title.group(1).strip().strip('"').strip("'") if title else "(제목 없음)"
    category = ""
    if cats:
        parts = [c.strip() for c in cats.group(1).split(",")]
        category = parts[1] if len(parts) > 1 else parts[0]
    return title, category


def slug_from_filename(fn):
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', fn[:-3]) if fn.endswith(".md") else fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--category", default="")
    ap.add_argument("--slug")
    a = ap.parse_args()
    if a.all:
        posts = os.path.join(REPO, "_posts")
        for fn in sorted(os.listdir(posts)):
            if fn.endswith(".md"):
                title, category = parse_front_matter(os.path.join(posts, fn))
                render(title, category, slug_from_filename(fn))
    elif a.title and a.slug:
        render(a.title, a.category, a.slug)
    else:
        sys.exit("사용법: --all  또는  --title ... --category ... --slug ...")


if __name__ == "__main__":
    main()
