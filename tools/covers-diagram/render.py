#!/usr/bin/env python3
"""다이어그램형 커버 렌더러 (template.html → 1080² PNG + 640² WebP).

gen_cover.py는 FLUX 배경이 있는 글에 쓰고, 구조를 그림으로 보여줘야 하는 글은 이쪽을 쓴다.
컷 정의는 아래 COVERS에 둔다 — **소스를 여기 남겨야 나중에 마크나 문구를 바꿀 때 다시 그릴 수 있다.**

사용: python3 tools/covers-diagram/render.py            # 전체
      python3 tools/covers-diagram/render.py <slug>     # 하나만
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(REPO, "assets", "img", "covers")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ARROW_G = "#2dd4bf"   # 성공 방향
ARROW_R = "#f2536a"   # 끊긴 방향


def arrows_svg() -> str:
    """두 노드 사이의 화살표 3개: 질문(→) / 회신 실패(✗ ←) / 이름 붙인 뒤 회신(✓ ←)."""
    return f"""
    <svg width="300" height="152" viewBox="0 0 300 152" style="overflow:visible">
      <defs>
        <marker id="g" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
          <path d="M0,0 L9,4.5 L0,9 z" fill="{ARROW_G}"/></marker>
        <marker id="r" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
          <path d="M0,0 L9,4.5 L0,9 z" fill="{ARROW_R}"/></marker>
      </defs>
      <line x1="10" y1="26" x2="280" y2="26" stroke="{ARROW_G}" stroke-width="3" marker-end="url(#g)"/>
      <line x1="290" y1="76" x2="45" y2="76" stroke="{ARROW_R}" stroke-width="3" marker-end="url(#r)"/>
      <text x="14" y="86" fill="{ARROW_R}" font-size="30" font-weight="700">✕</text>
      <line x1="290" y1="126" x2="20" y2="126" stroke="{ARROW_G}" stroke-width="3" marker-end="url(#g)"/>
      <text x="252" y="136" fill="{ARROW_G}" font-size="28" font-weight="700">✓</text>
    </svg>"""


COVERS = {
    "ai-business-team-1-subagent-cannot-reply": {
        "headline": '서브에이전트 협업,<br><span class="hi">이름 하나</span>로 되살렸다',
        "stage": f"""
          <div style="display:flex;align-items:center;gap:34px;margin-top:-90px">
            <div class="node"><span class="ico">🗂️</span><span class="lb">src-desk</span></div>
            {arrows_svg()}
            <div class="node hot"><span class="ico">⚖️</span><span class="lb">gate-desk</span></div>
          </div>""",
    },
    "subagent-no-agent-reachable-reply-failure": {
        "headline": '답이 안 돌아올 땐<br><span class="hi">이름</span>부터 확인한다',
        "stage": """
          <div style="display:flex;flex-direction:column;align-items:center;gap:60px;margin-top:-90px">
            <div class="errbox">No agent named
'general-purpose' is reachable</div>
            <div style="display:flex;align-items:center;gap:46px">
              <div class="node"><span class="ico">🤖</span></div>
              <svg width="150" height="40" style="overflow:visible">
                <defs><marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
                  <path d="M0,0 L9,4.5 L0,9 z" fill="#f2536a"/></marker></defs>
                <line x1="145" y1="20" x2="40" y2="20" stroke="#f2536a" stroke-width="3" marker-end="url(#r2)"/>
                <text x="6" y="31" fill="#f2536a" font-size="28" font-weight="700">✕</text>
              </svg>
              <div class="node hot"><span class="ico">🤖</span></div>
            </div>
          </div>""",
    },
}


def render(slug: str, cfg: dict) -> str:
    tpl = Path(os.path.join(HERE, "template.html")).read_text(encoding="utf-8")
    # 설정 주입: 템플릿이 읽는 window.__CFG__ 를 <script> 앞에 심는다
    page = tpl.replace("<script>", f"<script>window.__CFG__={json.dumps(cfg, ensure_ascii=False)};</script>\n<script>", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        hp = f.name
    out = os.path.join(OUT_DIR, slug + ".png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    "--allow-file-access-from-files", "--force-device-scale-factor=1",
                    "--window-size=1080,1080", "--virtual-time-budget=6000",
                    "--screenshot=" + out, Path(hp).as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(hp)
    print("  ✓", slug + ".png")
    webp = out[:-4] + ".webp"
    try:
        subprocess.run(["cwebp", "-quiet", "-q", "80", "-resize", "640", "640", out, "-o", webp], check=True)
        print("  ✓", os.path.basename(webp))
    except FileNotFoundError:
        print("  [!] cwebp 없음 — WebP 미생성")
    return out


def main() -> int:
    want = sys.argv[1:] or list(COVERS)
    for slug in want:
        if slug not in COVERS:
            print(f"  [!] 모르는 slug: {slug}")
            return 1
        render(slug, COVERS[slug])
    return 0


if __name__ == "__main__":
    sys.exit(main())
