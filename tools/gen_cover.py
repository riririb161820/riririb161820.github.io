#!/usr/bin/env python3
"""카드뉴스형 커버 생성기 (FLUX 일러스트 배경 + 텍스트 오버레이 → 1080x1080 PNG).
블로그 메인 카드 + 인스타 피드 겸용.

단일:  python3 tools/gen_cover.py --slug <slug> --category 자동화 \
              --headline "DM 자동화의 벽" --highlight "벽"
       (배경은 assets/img/covers/_src/<slug>.png 를 기본 사용. --bg로 다른 경로 지정 가능)
전체:  python3 tools/gen_cover.py --all     (아래 MAP 일괄 렌더)

배지는 우상단 'riririb.dev' 하나로 통일 (2026-09-29 핸들 변경, 옛 riri.devlog는 없는 계정). 헤드라인은 좌하단, 강조어는 카테고리색 박스.
입력 일러스트(공유 소스): assets/img/covers/_src/<slug>.png  (insta-post 표지도 같은 소스 재사용)
출력: assets/img/covers/<slug>.png   (블로그 메인 카드 1:1)
"""
import argparse, glob, html, os, re, subprocess, tempfile
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "assets", "img", "covers")
SRC_DIR = os.path.join(OUT_DIR, "_src")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

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
  <img class="bg" src="{bg}">
  <div class="scrim"></div>
  <span class="mark"><span class="mdot"></span>riririb.dev</span>
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
    bg_uri = Path(bg).resolve().as_uri()  # '#' 등 특수문자 안전 인코딩 (file:// fragment 방지)
    page = TPL.format(scrim=t["scrim"], dot=t["dot"], hi=t["hi"], hitext=t["hitext"],
                      bg=bg_uri, headline=build_headline(headline, highlight))
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
    to_webp(out)
    return out


def to_webp(png_path: str) -> str | None:
    """블로그가 실제로 서빙하는 640² WebP를 함께 만든다.

    1080² PNG는 인스타 파이프라인이 계속 쓰므로 남겨두고, 웹에는 WebP만 건다
    (home.html이 .webp를 참조). 실측 약 97% 경량 — 534KB → 9KB.
    cwebp가 없으면 경고만 남기고 넘어간다(PNG는 이미 만들어져 있으므로 치명적이지 않다).
    """
    webp = os.path.splitext(png_path)[0] + ".webp"
    try:
        subprocess.run(["cwebp", "-quiet", "-q", "80", "-resize", "640", "640",
                        png_path, "-o", webp], check=True)
    except FileNotFoundError:
        print("  [!] cwebp 없음 — WebP 미생성. `brew install webp` 후 다시 실행하세요.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  [!] WebP 변환 실패({e.returncode}) — {png_path}")
        return None
    print("  ✓", os.path.basename(webp))
    return webp


def posts_with_covers() -> list[tuple[str, str, str, str]]:
    """_posts의 front matter에서 (slug, category, headline, highlight)를 읽는다.

    예전에는 이 목록을 MAP 상수로 손으로 들고 있었는데, 글이 늘면 금방 낡아서
    `--all`이 일부만 다시 만들었다(2026-09-29에 12/36건만 들어있는 걸 발견).
    **강조어(highlight)는 front matter가 정본이다** — 여기 없으면 커버를 다시 만들 때
    강조 박스가 통째로 사라지므로, 새 글에는 headline과 함께 반드시 넣는다.
    """
    out = []
    for path in sorted(glob.glob(os.path.join(REPO, "_posts", "*.md"))):
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(path)[:-3])
        if not os.path.exists(os.path.join(SRC_DIR, slug + ".png")):
            continue  # 배경 일러스트가 없는 글은 이 생성기 대상이 아니다
        fm = re.match(r"^---\n(.*?)\n---\n", open(path, encoding="utf-8").read(), re.S)
        if not fm:
            continue
        fm = fm.group(1)

        def field(name: str) -> str:
            m = re.search(rf'^{name}:\s*"?(.*?)"?\s*$', fm, re.M)
            return m.group(1) if m else ""

        headline = field("headline")
        if not headline:
            continue
        # categories: [개발, 트러블슈팅] → 테마 키는 뒤쪽(소분류)
        cats = [c.strip().strip('"\'') for c in field("categories").strip("[]").split(",") if c.strip()]
        category = cats[-1] if cats else ""
        out.append((slug, category, headline, field("highlight")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--bg"); ap.add_argument("--slug"); ap.add_argument("--category", default="")
    ap.add_argument("--headline"); ap.add_argument("--highlight", default="")
    a = ap.parse_args()
    if a.all:
        items = posts_with_covers()
        print(f"[대상] {len(items)}건")
        missing = [s for s, _, _, hi in items if not hi]
        if missing:
            print(f"  [!] highlight 없는 글 {len(missing)}건 — 강조 박스 없이 렌더됩니다: {missing}")
        for slug, cat, hl, hi in items:
            render(os.path.join(SRC_DIR, slug + ".png"), slug, cat, hl, hi)
    elif a.slug and a.headline:
        bg = a.bg or os.path.join(SRC_DIR, a.slug + ".png")
        render(bg, a.slug, a.category, a.headline, a.highlight)
    else:
        raise SystemExit("사용법: --all  또는  --slug .. --category .. --headline .. --highlight ..  (배경 기본 _src/<slug>.png)")


if __name__ == "__main__":
    main()
