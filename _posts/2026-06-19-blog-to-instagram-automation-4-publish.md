---
title: "블로그 글을 인스타그램에 자동 발행하기 (4) — Instagram API 심사 없이 자동 발행 (Composio)"
date: 2026-06-19 10:12:00 +0900
categories: [개발, 자동화]
tags: [instagram, automation, composio, api, blog-to-insta]
image:
  path: /assets/img/posts/blog-to-insta-4-publish.png
  alt: 블로그→인스타 자동화 시리즈 진행도 — 4편 자동 발행 단계 강조
description: 카드를 인스타에 자동 발행하기. Instagram Graph API를 직접 심사받지 않고 승인된 중개자 Composio로 캐러셀을 자동 게시한 5단계와 삽질(JPEG·호스팅·토큰·핸들·삭제 불가). (시리즈 4편)
---

> **🗺 시리즈: 블로그 → 인스타 자동화** — 지금은 **④ 발행**
>
> ← 이전 편: [(3) 벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
>
> ① 전체 설계 · ② 카드 자동 생성 · ③ 디자인 · **④** 발행 *(현재 글)* · ⑤ DM의 벽
{: .prompt-info }

## 문제

만든 카드를 인스타에 **자동으로 올리려면** Instagram Graph API가 필요하다. 그런데 직접 앱을 만들어 심사(App Review)를 받는 건 시간·서류 부담이 크다. "자동 발행" 하나 하려고 며칠~몇 주를 기다릴 순 없었다.

![Composio로 심사 없이 자동 발행하는 5단계](/assets/img/posts/body-blog-to-insta-4-publish.png)

## 원인 — 직접 발행의 장벽

Graph API로 게시하려면 권한 + 앱 심사 + 비즈니스 인증이 필요하다. 개인이 직접 받기엔 진입장벽이 높다.

## 해결 과정 — 승인된 중개자(Composio)로 우회

이미 Meta 승인을 받은 중개 서비스 **Composio**를 쓰면, 내 계정만 OAuth로 연결해 **심사 없이** 캐러셀을 발행할 수 있다. 단계별로 함정이 있었다.

### 1) 인스타를 비즈니스/크리에이터로 전환
개인 계정으론 API 발행이 안 된다. 프로페셔널 전환(무료)이 전제.

### 2) Composio 연결 (OAuth)
브라우저로 한 번 인증하면 연결된다. 단, **토큰을 대시보드에서 자꾸 새로 만들면 세션이 무효화**된다(OAuthException 190). [→ 트러블슈팅: OAuth 190](/posts/instagram-api-oauthexception-190-session-invalidated/)

### 3) 카드 PNG → JPEG 변환
인스타 API는 **JPEG + 공개 HTTPS URL만** 받는다. PNG는 거부된다. macOS `sips`로 변환했다.

```bash
sips -s format jpeg -s formatOptions 92 slide.png --out slide.jpg
```

### 4) 공개 URL 호스팅
API가 이미지를 가져갈 **공개 URL**이 필요하다. 이미 쓰던 GitHub Pages 저장소에 올려 URL을 확보했다(추가 비용 0).

### 5) 캐러셀 컨테이너 생성 → 발행
이미지 URL들로 캐러셀 컨테이너를 만들고 발행. 참고로 **게시물 삭제는 API가 지원하지 않아**(앱에서 수동), 계정 **핸들 표기**(예: 점/밑줄)도 발행 전에 카드와 일치시켜야 한다.

결과: 블로그 글 → 카드 6장 캐러셀이 **심사 없이 자동 발행**됐다.

## 사용한 기술

- **Composio MCP** — Meta 승인 중개자(심사 우회)
- **Instagram Graph API** — 캐러셀 컨테이너 생성·발행
- **sips**(PNG→JPEG) · **GitHub Pages**(공개 URL 호스팅)

> **🧭 기획자·사업자라면**
> - **심사·인증은 "빌릴 수 있는 것"**: 직접 앱 심사 대신 승인된 중개자를 쓰면 출시 시간을 크게 단축한다. 단 **중개자 의존 리스크**(요금제·정책 변경)를 인지하라.
> - **플랫폼 제약을 먼저 확인**: "JPEG만, 공개 URL만, 삭제 불가" 같은 제약은 기획 단계에서 알아야 일정·UX가 안 꼬인다.
{: .prompt-tip }

## 정리

- 직접 심사 대신 **승인된 중개자**로 우회하면 개인도 자동 발행 가능.
- 인스타 발행은 **JPEG + 공개 HTTPS URL**이 전제, 삭제는 수동.
- 토큰을 반복 재생성하면 세션이 깨지니 주의.

### 시리즈 목차

1. [전체 설계와 도구 선택](/posts/blog-to-instagram-automation-1-design/)
2. [카드뉴스 자동 생성](/posts/blog-to-instagram-automation-2-card-generation/)
3. [벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
4. **Composio로 자동 발행** (현재 글)
5. [DM 자동화의 벽](/posts/blog-to-instagram-automation-5-dm-wall/)

> 이 단계에서 막혔다면 → [Instagram API OAuthException 190](/posts/instagram-api-oauthexception-190-session-invalidated/)
{: .prompt-warning }
