---
title: "블로그 글을 인스타그램에 자동 발행하기 (5) — 사업자 없으면 인스타 DM 자동화 못 합니다 (Meta App Review 벽)"
headline: "DM 자동화의 벽"
date: 2026-06-19 10:14:00 +0900
categories: [개발, 자동화]
tags: [instagram, automation, meta-app-review, cloudflare, blog-to-insta]
image:
  path: /assets/img/posts/blog-to-insta-5-dm.png
  alt: 블로그→인스타 자동화 시리즈 진행도 — 5편 DM 자동화의 벽 단계 강조
description: 댓글→DM follow-gate 봇을 완성했지만, 사업자등록이 없으면 Meta Advanced Access(App Review)를 못 받아 공개 팔로워 대상 DM 자동화가 막힌 실패담과 우회법. (시리즈 5편)
---

> **🗺 시리즈: 블로그 → 인스타 자동화** — 지금은 **⑤ DM의 벽** (마지막 편)
>
> ← 이전 편: [(4) Composio로 자동 발행](/posts/blog-to-instagram-automation-4-publish/)
>
> ① 전체 설계 · ② 카드 자동 생성 · ③ 디자인 · ④ 발행 · **⑤** DM의 벽 *(현재 글)*
{: .prompt-info }

## 문제

마지막 욕심은 DM 자동화였다. 게시물 댓글에 키워드("링크")를 달면 **자동으로 DM**을 보내고, 그 사람이 팔로우했는지 확인해 글 링크를 주는 **follow-gate 봇**을 만들고 싶었다.

![follow-gate 봇 구조와 사업자등록의 벽](/assets/img/posts/body-blog-to-insta-5-dm.png)

## 원인 — 타인 데이터 = Advanced Access = 사업자등록

공개 팔로워의 댓글·DM은 **타인의 데이터**다. 이걸 처리하려면 Instagram 권한을 **Advanced Access**로 받아야 하고, 그러려면 **App Review + business verification**이 필요하다.

문제는 business verification이 **등록된 사업체(법인/개인사업자)** 를 전제로 한다는 것. **개인 신분증·개인 명의 서류로는 인증이 안 된다**(인정 서류가 전부 사업체 명의). 게다가 개발 모드에서는 **테스터로 등록된 계정의 이벤트만** webhook이 오므로, 일반 팔로워의 실제 댓글로는 봇이 반응하지 않는다.

## 해결 과정 — 봇은 완성, 그러나 벽

봇 자체는 끝까지 만들고 검증했다. **Cloudflare Worker**(서버리스·무료)로:

1. 댓글 webhook 수신 → 키워드 매칭
2. **Private Reply**로 DM 발송 + "팔로우했어요" 버튼
3. 버튼 클릭 시 **`is_user_follow_business`** 로 팔로우 여부 확인
4. 팔로우했으면 링크 전달, 아니면 재안내

Meta가 보낸 **테스트 webhook이 워커에 정상 도착**하는 것까지 확인했다. 코드·인프라는 완성. 그런데 **사업자등록이 없어 공개 발행이 막혔다.** Meta 상담도 "사업자등록 후 App Review를 받거나, **공식 파트너(ManyChat 등)** 를 쓰라"고 확인해줬다.

결론적으로 길은 둘이다.

- (a) **개인사업자 등록** 후 App Review → 자체 봇 부활
- (b) **ManyChat 같은 인증된 중개자** 사용 (자기들이 이미 승인돼 있어 내 인증 불필요)

## 사용한 기술

- **Cloudflare Workers** — 서버리스 webhook 봇(무료 티어)
- **Instagram Messaging API** — Private Replies, `is_user_follow_business`(팔로우 확인)
- **Meta App Review / business verification** — 바로 이 단계가 벽

> **🧭 기획자·사업자라면**
> - **"개인 vs 사업자"는 기술이 아니라 자격의 문제**: 타인 데이터를 다루는 자동화는 본질적으로 사업자 인증을 요구한다. 사업화 의지가 있으면 등록이 오히려 모든 걸 푸는 열쇠.
> - **무료로 가려면 "인증된 중개자"**: ManyChat처럼 이미 승인된 도구를 쓰면 내 인증 없이 가능(단 무료 한도·기능 제약). 직접 구축 ROI와 비교해 결정.
> - **시작 전에 자격 요건부터 확인**: "이거 하려면 사업자등록이 필요하구나"를 먼저 알면 헛고생을 줄인다.
{: .prompt-tip }

## 정리

- **사업자등록이 없으면 자체 앱으로는 공개 팔로워 DM 자동화가 불가능하다**(Meta 정책).
- 봇 코드는 완성돼 있어, 등록만 하면 부활한다. 무료 대안은 ManyChat 같은 공식 파트너.
- 같은 길을 가려는 사람은 "DM 자동화 = 사업자등록 필요"를 **먼저 알고** 시작하길.

### 시리즈 목차

1. [전체 설계와 도구 선택](/posts/blog-to-instagram-automation-1-design/)
2. [카드뉴스 자동 생성](/posts/blog-to-instagram-automation-2-card-generation/)
3. [벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
4. [Composio로 자동 발행](/posts/blog-to-instagram-automation-4-publish/)
5. **DM 자동화의 벽** (현재 글)

> 봇을 만들다 막혔다면 — 트러블슈팅:
> [Cloudflare wrangler login 실패](/posts/ig-cloudflare-wrangler-login-failed/) · [OAuth 190 세션 무효](/posts/instagram-api-oauthexception-190-session-invalidated/) · [댓글 webhook 안 옴](/posts/instagram-comment-webhook-not-working-dev-mode/) · [테스터 초대 수락 에러](/posts/instagram-tester-invite-accept-error/)
{: .prompt-warning }
