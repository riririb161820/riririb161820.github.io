---
title: "Cloudflare wrangler login 실패 해결 (Timed out / consent already used / localhost 연결 거부)"
headline: "wrangler login 실패"
date: 2026-06-19 09:30:00 +0900
categories: [개발, 트러블슈팅]
tags: [cloudflare, wrangler, oauth, troubleshooting, blog-to-insta]
image:
  path: /assets/img/posts/body-ts-wrangler-login.png
  alt: wrangler login 실패 증상·원인·해결 다이어그램
description: wrangler login이 'Timed out waiting for authorization code', 'consent verifier has already been used', localhost ERR_CONNECTION_REFUSED로 실패할 때, API 토큰 방식으로 우회하는 해결법.
---

> 이 글은 [블로그→인스타 자동화 (5) DM의 벽](/posts/blog-to-instagram-automation-5-dm-wall/) 작업 중 Cloudflare Workers 배포에서 만난 문제입니다.

## 증상

`wrangler login`이 브라우저 인증 후 이런 에러로 실패한다.

```text
✘ [ERROR] Timed out waiting for authorization code, please try again.
```
또는 재시도 시:
```text
▲ [WARNING] Received query string parameter doesn't match the one sent! Possible malicious activity somewhere.
```
콜백 화면에는 `localhost:8976/oauth/callback?error=access_denied ... The consent verifier has already been used` + **ERR_CONNECTION_REFUSED**.

## 원인

- 로그인 OAuth는 **로컬 콜백 서버(localhost:8976)** 가 떠 있는 동안 승인을 받아야 한다.
- 백그라운드/반복 실행으로 **state가 어긋나거나**, 승인 시점에 **콜백 서버가 이미 종료**돼 있으면 위 에러가 난다(consent 재사용·연결 거부).

## 해결 — OAuth 대신 API 토큰

브라우저 콜백을 아예 쓰지 않는 **Cloudflare API 토큰** 방식이 확실하다.

1. Cloudflare 대시보드 → My Profile → **API Tokens** → Create Token → **"Edit Cloudflare Workers"** 템플릿
2. 발급된 토큰을 환경변수로 사용:

```bash
export CLOUDFLARE_API_TOKEN="발급받은_토큰"
npx wrangler deploy   # 이제 브라우저 로그인 없이 동작
```

서브도메인 등록 등도 API로 가능하다(`PUT /accounts/{id}/workers/subdomain`). localhost 콜백 이슈가 원천 차단된다.

## 정리

- `wrangler login` 콜백 에러는 **state 충돌 + 콜백 서버 미가동**이 원인.
- **API 토큰(CLOUDFLARE_API_TOKEN)** 으로 우회하면 브라우저 OAuth 없이 배포된다.
