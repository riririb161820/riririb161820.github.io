// 인스타 시리즈 캐러셀 자동 발행 (GitHub Actions용, graph.instagram.com 직접)
// 사용: EP=2 DRY_RUN=0 IG_ACCESS_TOKEN=... node tools/insta_publish.mjs
//   EP=auto 면 현재 UTC 날짜로 편을 매핑(21→2, 23→3, 25→4, 27→5).
//   DRY_RUN=1 이면 컨테이너만 만들고 발행은 안 함(검증용).
import fs from "node:fs";

const TOKEN = process.env.IG_ACCESS_TOKEN;
const BASE = "https://graph.instagram.com/v21.0";
const HOST = "https://riririb161820.github.io/assets/insta";
const DRY = process.env.DRY_RUN === "1";
if (!TOKEN) { console.error("IG_ACCESS_TOKEN 없음"); process.exit(1); }

let ep = (process.env.EP || "auto").trim();
if (ep === "auto" || ep === "") {
  const day = new Date().getUTCDate();
  const map = { 21: "2", 23: "3", 25: "4", 27: "5" };
  ep = map[day];
  if (!ep) { console.error(`UTC ${day}일에 매핑된 편 없음 — 종료`); process.exit(1); }
}

const manifest = JSON.parse(fs.readFileSync(new URL("./insta-series.json", import.meta.url)));
const item = manifest[ep];
if (!item) { console.error(`매니페스트에 ep ${ep} 없음`); process.exit(1); }
const { slug, caption } = item;
const urls = [1, 2, 3, 4, 5, 6].map((i) => `${HOST}/${slug}/slide-0${i}.jpg`);

async function post(path, params) {
  const body = new URLSearchParams({ ...params, access_token: TOKEN });
  const r = await fetch(`${BASE}/${path}`, { method: "POST", body });
  const j = await r.json();
  if (j.error) throw new Error(`${path}: ${JSON.stringify(j.error)}`);
  return j;
}
async function getJson(path, params) {
  const body = new URLSearchParams({ ...params, access_token: TOKEN });
  const r = await fetch(`${BASE}/${path}?${body}`);
  return r.json();
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  console.log(`[insta-publish] ep${ep} (${slug}) DRY_RUN=${DRY}`);

  // 1) 이미지 URL 6개 200 확인
  for (const u of urls) {
    const r = await fetch(u, { method: "HEAD" });
    if (!r.ok) throw new Error(`이미지 URL ${r.status}: ${u}`);
  }
  console.log("이미지 6장 200 확인");

  // 2) 자식 컨테이너
  const children = [];
  for (const u of urls) {
    const j = await post("me/media", { image_url: u, is_carousel_item: "true" });
    children.push(j.id);
  }
  console.log("자식:", children.join(","));

  // 3) 캐러셀 부모
  const parent = await post("me/media", {
    media_type: "CAROUSEL",
    children: children.join(","),
    caption,
  });
  console.log("부모 컨테이너:", parent.id);

  if (DRY) { console.log("DRY_RUN — 발행 생략(컨테이너 자동 만료)"); return; }

  // 4) 발행 (컨테이너 준비될 때까지 폴링)
  let pub;
  for (let i = 0; i < 24; i++) {
    try { pub = await post("me/media_publish", { creation_id: parent.id }); break; }
    catch (e) {
      const m = String(e);
      if (m.includes("not ready") || m.includes("not available") || m.includes("Media ID")) {
        await sleep(5000); continue;
      }
      throw e;
    }
  }
  if (!pub) throw new Error("발행 실패: 컨테이너가 준비되지 않음");
  console.log("발행 media id:", pub.id);

  const media = await getJson(pub.id, { fields: "permalink" });
  console.log("PERMALINK:", media.permalink || "(조회 실패)");
})().catch((e) => { console.error("실패:", e.message); process.exit(1); });
