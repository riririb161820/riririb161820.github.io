---
title: "Instagram 테스터 초대 수락 안 될 때 (manage_access '문제가 발생했습니다')"
date: 2026-06-19 09:45:00 +0900
categories: [개발, 트러블슈팅]
tags: [instagram, meta-developers, troubleshooting, blog-to-insta]
image:
  path: /assets/img/posts/body-ts-tester-invite.png
  alt: Instagram 테스터 초대 수락 에러 증상·원인·해결 다이어그램
description: Meta 앱의 Instagram 테스터 초대가 Pending에서 안 풀리고, instagram.com 앱·웹사이트 관리 페이지가 '문제가 발생했습니다'로 열리지 않을 때의 우회법.
---

> 이 글은 [블로그→인스타 자동화 (5) DM의 벽](/posts/blog-to-instagram-automation-5-dm-wall/) 작업 중 만난 문제입니다.

![테스터 초대 수락 에러 — 증상·원인·해결](/assets/img/posts/body-ts-tester-invite.png)

## 증상

Meta 앱에서 Instagram **테스터**를 추가했는데 상태가 **Pending**에서 안 풀린다. 수락하려고 `instagram.com` → 설정 → **앱 및 웹사이트(manage_access)** 페이지에 들어가면:

```text
문제가 발생했습니다
문제가 발생하여 페이지를 읽어들이지 못했습니다.
```

다른 브라우저(시크릿 포함)로 해도 같은 에러가 난다.

## 원인

- 테스터 역할은 **초대받은 인스타 계정이 직접 수락**해야 활성화된다(그전엔 Pending).
- 그런데 `instagram.com`의 **앱·웹사이트 관리 페이지가 특정 계정에서 버그**로 안 열리는 경우가 있다(브라우저 문제가 아니라 그 페이지·계정 조합 이슈).

## 해결

1. **모바일 인스타 앱**에서 수락 — 설정 및 활동 → "앱 및 웹사이트" → **테스터 초대** → 수락. (웹이 깨져도 앱은 별개라 열리는 경우가 많다)
2. 그래도 안 되면 **다른/새 계정**을 테스터로 추가해 수락 — 깨끗한 새 계정은 그 버그 페이지를 잘 타지 않는다. (테스트용 댓글 계정은 *아무 테스터 계정*이면 된다)
3. 잠시 후 재시도(일시적 장애일 때도 있음)

## 정리

- 테스터 Pending은 **수락이 안 끝난 상태** — 수락은 인스타 쪽에서 한다.
- 웹 manage_access가 에러나면 **모바일 앱 / 다른 계정**으로 우회.
