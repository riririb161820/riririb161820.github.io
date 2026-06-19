---
title: "Instagram 댓글 webhook이 안 올 때 (개발 모드·comments 구독·권한 체크)"
headline: "webhook이 안 올 때"
date: 2026-06-19 09:40:00 +0900
categories: [개발, 트러블슈팅]
tags: [instagram, webhook, graph-api, troubleshooting, blog-to-insta]
image:
  path: /assets/img/posts/body-ts-comment-webhook.png
  alt: Instagram 댓글 webhook 미수신 증상·원인·해결 다이어그램
description: 실제 댓글을 달아도 Instagram comments webhook이 서버에 안 올 때 점검 순서 — 개발 모드(테스터만), comments 필드 subscribed_apps 누락, 권한 미추가, Live 전환.
---

> 이 글은 [블로그→인스타 자동화 (5) DM의 벽](/posts/blog-to-instagram-automation-5-dm-wall/) 작업 중 follow-gate 봇을 만들며 만난 문제입니다.

## 증상

게시물에 실제로 댓글을 달았는데도 **서버(webhook 엔드포인트)에 이벤트가 0건** 들어온다. 반면 Meta 대시보드의 **"Test" 버튼으로 보낸 샘플 webhook은 정상 도착**한다. → 전달 경로(콜백)는 멀쩡한데, *실제 댓글 이벤트*만 안 생기는 상황.

## 원인 (점검 순서대로)

1. **개발 모드 제약** — 개발 모드에서는 **앱에 역할이 있는 계정(테스터/개발자/관리자)** 의 이벤트만 webhook이 발생한다. 비(非)테스터의 댓글은 오지 않는다.
2. **comments 필드 미구독** — 계정-앱 구독(`subscribed_apps`)에 `messages`만 있고 `comments`가 빠진 경우.
3. **권한 미추가** — `instagram_business_manage_comments` 권한이 토큰에 없으면 댓글 이벤트 접근 불가(권한 추가 후 **토큰 재발급** 필요).

## 해결

- 권한 3종 추가: `instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_manage_messages` → **토큰 재발급**
- 계정-앱 구독에 **comments 포함** 확인:

```bash
# 구독 설정
curl -s -X POST "https://graph.instagram.com/v21.0/me/subscribed_apps?subscribed_fields=comments,messages&access_token=$TOKEN"
# 확인 (['comments','messages'] 나와야 정상)
curl -s "https://graph.instagram.com/v21.0/me/subscribed_apps?access_token=$TOKEN"
```

- 테스트는 **테스터로 등록·수락된 계정**으로 댓글 달기
- **일반 공개 팔로워**까지 받으려면 → 앱을 **Live로 전환 + App Review(Advanced Access)** 필요 (이건 사업자 인증이 전제다)

## 정리

- 댓글 webhook 미수신은 보통 **개발 모드 + comments 구독/권한 누락** 조합.
- Test 버튼은 되는데 실제 댓글이 안 오면 = **이벤트 생성 단계(역할/구독)** 문제. 공개 사용자는 Live·심사가 필요.
