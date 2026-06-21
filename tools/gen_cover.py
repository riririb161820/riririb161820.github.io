#!/usr/bin/env python3
"""카드뉴스형 커버 생성기 (FLUX 일러스트 배경 + 텍스트 오버레이 → 1080x1080 PNG).
블로그 메인 카드 + 인스타 피드 겸용.

단일:  python3 tools/gen_cover.py --bg <flux.png> --slug <slug> --category 자동화 \
              --headline "DM 자동화의 벽" --highlight "벽"
전체:  python3 tools/gen_cover.py --all     (아래 MAP 일괄 렌더)

배지는 우상단 'riri.devlog' 하나로 통일. 헤드라인은 좌하단, 강조어는 카테고리색 박스.
출력: assets/img/covers/<slug>.png
"""
import argparse, html, os, subprocess, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "assets", "img", "covers")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FLUX = os.path.expanduser("~/ComfyUI/output")

THEME = {
    "자동화":    {"scrim": "8,22,18",  "hi": "#2dd4a7", "hitext": "#06382b", "dot": "#5fe3c0"},
    "운영":      {"scrim": "8,20,38",  "hi": "#5ba3f0", "hitext": "#08294d", "dot": "#8cc2f7"},
    "트러블슈팅": {"scrim": "28,12,6",  "hi": "#f0a93c", "hitext": "#3d2402", "dot": "#f5c477"},
}
DEFAULT = {"scrim": "20,22,28", "hi": "#aab4c2", "hitext": "#1b2025", "dot": "#cdd5df"}

TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
body{{font-family:-apple-system,"Apple SD Gothic Neo","Pretendard",sans-serif}}
.cover{{width:1080px;height:1080px;position:relative;overflow:hidden;display:flex;flex-direction:column;padding:58px}}
.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
.scrim{{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba({scrim},.20) 0%,rgba({scrim},.05) 38%,rgba({scrim},.86) 100%)}}
.mark{{position:relative;z-index:2;align-self:flex-end;display:inline-flex;align-items:center;gap:9px;font-family:"SF Mono",monospace;font-size:24px;font-weight:600;color:#fff;background:rgba(0,0,0,.28);padding:9px 18px;border-radius:40px}}
.mdot{{width:11px;height:11px;border-radius:50%;background:{dot}}}
.hl{{position:relative;z-index:2;margin-top:auto;font-size:82px;font-weight:800;line-height:1.26;color:#fff;letter-spacing:-1px;text-shadow:0 2px 20px rgba(0,0,0,.38)}}
.hi{{background:{hi};color:{hitext};padding:2px 20px;border-radius:16px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
</style></head><body>
<div class="cover">
  <img class="bg" src="file://{bg}">
  <div class="scrim"></div>
  <span class="mark"><span class="mdot"></span>riri.devlog</span>
  <div class="hl">{headline}</div>
</div></body></html>"""


def build_headline(headline, highlight):
    h = html.escape(headline)
    if highlight:
        hl = html.escape(highlight)
        if hl in h:
            h = h.replace(hl, f'<span class="hi">{hl}</span>', 1)
    return h


def render(bg, slug, category, headline, highlight):
    t = THEME.get(category, DEFAULT)
    page = TPL.format(scrim=t["scrim"], dot=t["dot"], hi=t["hi"], hitext=t["hitext"],
                      bg=bg, headline=build_headline(headline, highlight))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, slug + ".png")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page); hp = f.name
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--force-device-scale-factor=1",
                    "--window-size=1080,1080", "--screenshot=" + out, "file://" + hp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(hp)
    print("  ✓", slug + ".png")
    return out


MAP = [
    ("claude_gen_00024_.png", "claude-code-blog-automation-github-pages",            "자동화",    "블로그 자동 발행",   "자동 발행"),
    ("claude_gen_00025_.png", "website-analytics-goatcounter-ga4-search-console",    "운영",      "방문 통계 3종",     "3종"),
    ("claude_gen_00026_.png", "claude-code-skills-cross-machine-sync",               "자동화",    "스킬 PC 동기화",    "동기화"),
    ("claude_gen_00027_.png", "blog-to-instagram-automation-1-design",               "자동화",    "전체 설계",        "설계"),
    ("claude_gen_00029_.png", "blog-to-instagram-automation-2-card-generation",      "자동화",    "카드 자동 생성",    "자동"),
    ("claude_gen_00030_.png", "blog-to-instagram-automation-3-design",               "자동화",    "벤치마킹 ≠ 카피",   "≠ 카피"),
    ("claude_gen_00031_.png", "blog-to-instagram-automation-4-publish",              "자동화",    "심사 없이 자동 발행", "심사 없이"),
    ("claude_gen_00021_.png", "blog-to-instagram-automation-5-dm-wall",              "자동화",    "DM 자동화의 벽",    "벽"),
    ("claude_gen_00022_.png", "ig-cloudflare-wrangler-login-failed",                 "트러블슈팅", "wrangler login 실패", "실패"),
    ("claude_gen_00032_.png", "instagram-api-oauthexception-190-session-invalidated", "트러블슈팅", "OAuth 190 해결",   "해결"),
    ("claude_gen_00033_.png", "instagram-comment-webhook-not-working-dev-mode",      "트러블슈팅", "webhook이 안 올 때", "안 올 때"),
    ("claude_gen_00034_.png", "instagram-tester-invite-accept-error",                "트러블슈팅", "테스터 초대 실패",   "실패"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--bg"); ap.add_argument("--slug"); ap.add_argument("--category", default="")
    ap.add_argument("--headline"); ap.add_argument("--highlight", default="")
    a = ap.parse_args()
    if a.all:
        for bg, slug, cat, hl, hi in MAP:
            render(os.path.join(FLUX, bg), slug, cat, hl, hi)
    elif a.bg and a.slug and a.headline:
        render(a.bg, a.slug, a.category, a.headline, a.highlight)
    else:
        raise SystemExit("사용법: --all  또는  --bg .. --slug .. --category .. --headline .. --highlight ..")


if __name__ == "__main__":
    main()
