---
title: "블로그 글을 인스타그램에 자동 발행하기 (4) — Instagram API 심사 없이 자동 발행 (Composio)"
date: 2026-06-19 10:12:00 +0900
categories: [개발, 자동화]
tags: [instagram, automation, composio, api, blog-to-insta]
image:
  path: /assets/img/posts/blog-to-insta-4-publish.png
  alt: 블로그→인스타 자동화 시리즈 진행도 — 4편 자동 발행 단계 강조
description: 카드를 인스타에 자동 발행하기. Instagram Graph API를 직접 심사받지 않고, 이미 승인된 중개자 Composio로 캐러셀을 자동 게시한 방법과 삽질(JPEG·호스팅·토큰). (시리즈 4편)
---

> **🗺 시리즈: 블로그 → 인스타 자동화** — 지금은 **④ 발행**
>
> ← 이전 편: [(3) 벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
>
> ① 전체 설계 · ② 카드 자동 생성 · ③ 디자인 · **④** 발행 *(현재 글)* · ⑤ DM의 벽
{: .prompt-info }

## 문제

만든 카드를 인스타에 **자동으로 올리려면** Instagram Graph API가 필요하다. 그런데 직접 앱을 만들어 심사(App Review)를 받는 건 시간이 오래 걸린다.

## 원인 — 직접 발행의 장벽

Graph API로 게시하려면 권한 + **앱 심사** + 비즈니스 인증이 필요하다. 개인이 직접 받기엔 서류·대기 부담이 크다. "자동 발행" 하나 하려고 며칠~몇 주 심사를 기다릴 순 없었다.

## 해결 과정 — 승인된 중개자(Composio)로 우회

이미 Meta 승인을 받은 중개 서비스 **Composio**를 쓰면, 내 계정만 OAuth로 연결해 **심사 없이** 캐러셀을 자동 발행할 수 있다. (블로그를 GitHub Pages로 우회했던 것과 같은 원리 — 승인된 인프라에 올라타기)

흐름:

1. 인스타를 **비즈니스/크리에이터**로 전환
2. **Composio 연결**(OAuth)
3. 카드 PNG → **JPEG 변환** — 인스타 API는 JPEG + 공개 HTTPS URL만 받는다 (PNG 거부)
4. **GitHub Pages**에 올려 공개 URL 확보
5. **캐러셀 컨테이너 생성 → 발행**

삽질 포인트(같은 길 가는 사람용):

- **PNG는 거부됨** → `sips`로 JPEG 변환 필수
- 대시보드에서 **토큰을 자꾸 새로 만들면 세션이 무효화**된다 (한 번 만들고 재생성 자제)
- **게시물 삭제는 API 미지원** → 앱에서 수동 삭제

## 사용한 기술

- **Composio MCP** — Meta 승인 중개자(심사 우회)
- **Instagram Graph API** — 캐러셀 컨테이너 생성·발행
- **sips** — PNG → JPEG 변환(macOS 기본)
- **GitHub Pages** — 공개 이미지 호스팅(발행에 필요한 공개 URL)

## 정리

- 직접 심사 대신 **승인된 중개자**로 우회하면 개인도 자동 발행 가능.
- 인스타 발행은 **JPEG + 공개 HTTPS URL**이 전제.
- 토큰을 반복 재생성하면 세션이 깨지니 주의.

### 시리즈 목차

1. [전체 설계와 도구 선택](/posts/blog-to-instagram-automation-1-design/)
2. [카드뉴스 자동 생성](/posts/blog-to-instagram-automation-2-card-generation/)
3. [벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
4. **Composio로 자동 발행** (현재 글)
5. [DM 자동화의 벽](/posts/blog-to-instagram-automation-5-dm-wall/)
