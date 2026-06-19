---
title: "Instagram API OAuthException 190 'session has been invalidated' 해결"
date: 2026-06-19 09:35:00 +0900
categories: [개발, 트러블슈팅]
tags: [instagram, graph-api, oauth, troubleshooting, blog-to-insta]
image:
  path: /assets/img/posts/body-ts-oauth-190.png
  alt: Instagram API OAuthException 190 증상·원인·해결 다이어그램
description: Instagram Graph API 호출이 OAuthException code 190 'The session has been invalidated...'로 실패할 때의 원인(토큰 반복 재생성)과 해결(재연결·재생성 자제).
---

> 이 글은 [블로그→인스타 자동화 (4) 발행](/posts/blog-to-instagram-automation-4-publish/)·[(5) DM의 벽](/posts/blog-to-instagram-automation-5-dm-wall/) 작업 중 만난 문제입니다.

![OAuthException 190 — 증상·원인·해결](/assets/img/posts/body-ts-oauth-190.png)

## 증상

조금 전까지 잘 되던 토큰이 갑자기 이 에러로 막힌다.

```json
{
  "error": {
    "message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.",
    "type": "OAuthException",
    "code": 190
  }
}
```

비밀번호를 바꾼 적도 없는데 "세션이 무효화됐다"고 나온다.

## 원인

- **토큰을 새로 생성하면 같은 계정의 이전 세션/토큰이 무효화**된다.
- 개발 중 대시보드에서 토큰을 **여러 번 재생성**하거나, 같은 계정으로 다른 도구(예: Composio)와 자체 앱을 번갈아 연결하면, 한쪽을 새로 만들 때 다른 쪽 세션이 죽어 190이 뜬다.

## 해결

- 토큰은 **한 번만 발급하고 재생성하지 않는다.** 발급 후 그 값을 그대로 시크릿/`.env`에 보관해 쓴다.
- 이미 무효화됐다면 **다시 발급(또는 OAuth 재연결) 후 한 번에** 설정을 끝내고, 이후 재생성하지 않는다.
- 유효성은 간단히 확인할 수 있다:

```bash
curl -s "https://graph.instagram.com/v21.0/me?fields=username&access_token=$TOKEN"
# username이 나오면 유효, 190이면 무효
```

## 정리

- 190 "session invalidated"의 흔한 원인은 비번 변경이 아니라 **토큰 반복 재생성**.
- 한 번 발급 → 보관 → 재생성 자제. 죽었으면 재연결로 새 토큰을 받고 그걸로 고정.
