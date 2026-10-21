---
title: "인스타 자동화 봇이 막히는 네 지점 — OAuth 190·테스터 Pending·댓글 webhook·wrangler login"
headline: "인스타 봇 4대 벽"
highlight: "4대 벽"
date: 2026-10-21 17:40:00 +0900
categories: [개발, 트러블슈팅]
tags: [instagram, graph-api, webhook, oauth, cloudflare, meta-developers]
description: "인스타그램 댓글·DM 자동화 봇을 Meta 플랫폼에 올리다 막힌 네 지점을 한 편에 모았다. OAuthException 190 'session has been invalidated', 테스터 초대 Pending, 댓글 webhook 0건, wrangler login 콜백 실패 — 네 개 모두 에러 메시지가 진짜 원인을 가리키지 않았다."
image:
  path: /assets/img/posts/instagram-bot-four-blockers-hero.webp
  alt: 인스타 자동화 봇 구축에서 막힌 네 지점의 증상과 실제 원인을 대조한 다이어그램
---

## 문제 — 에러 메시지가 원인을 가리키지 않는다

인스타그램 댓글에 반응해 DM을 보내는 봇을 만들었다. 발행 파이프라인([블로그→인스타 자동화 (4) 발행](/posts/blog-to-instagram-automation-4-publish/))까지는 순탄했는데, 댓글·DM 영역([(5) DM의 벽](/posts/blog-to-instagram-automation-5-dm-wall/))에 들어가자 네 군데에서 연달아 막혔다.

네 개를 따로 적어뒀다가 한 편으로 합쳤다. 따로 보면 제각각인데, 모아놓으니 **공통점이 하나 있었다. 넷 다 에러 메시지가 엉뚱한 곳을 가리켰다.**

| 플랫폼이 말한 것 | 실제 원인 |
|---|---|
| "비밀번호를 변경했기 때문에 세션이 무효화됨" | 토큰을 **여러 번 재생성**함 |
| 테스터 상태 `Pending` (이유 없음) | 수락 페이지가 **그 계정에서 안 열림** |
| webhook 이벤트 **0건** (에러 없음) | 개발 모드 제약 + `comments` **구독 누락** |
| "Timed out waiting for authorization code" | 콜백 서버가 **이미 종료**됨 |

메시지를 그대로 믿고 쫓아가면 전부 헛수고로 끝나는 구조다. 하나씩 본다.

## ① "비밀번호를 바꾼 적 없는데" — OAuthException 190

![OAuthException 190의 증상·원인·해결 다이어그램](/assets/img/posts/body-ts-oauth-190.png)

조금 전까지 잘 되던 토큰이 갑자기 막힌다.

```json
{
  "error": {
    "message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.",
    "type": "OAuthException",
    "code": 190
  }
}
```

비밀번호를 바꾼 적이 없는데 "세션이 무효화됐다"고 나온다.

**원인은 토큰 재생성이다.** 같은 계정의 토큰을 새로 만들면 **이전 세션·토큰이 무효화**된다. 개발 중에 대시보드에서 토큰을 몇 번 다시 뽑거나, 같은 계정을 자체 앱과 다른 도구(예: Composio)에 번갈아 연결하면, 한쪽을 새로 만드는 순간 다른 쪽이 죽어 190이 뜬다.

메시지에 적힌 "changed their password"는 190이 뜨는 여러 경우 중 하나일 뿐인데, Meta가 **코드 하나에 안내 문구 하나를 붙여둔 탓**에 늘 비밀번호 이야기가 나온다.

해결은 단순하다.

- 토큰은 **한 번만 발급하고 재생성하지 않는다.** 발급 즉시 시크릿·`.env`에 넣고 그대로 쓴다.
- 이미 죽었으면 **재발급(또는 OAuth 재연결) 후 설정을 한 번에 끝내고**, 이후 손대지 않는다.
- 유효성은 한 줄로 확인한다.

```bash
curl -s "https://graph.instagram.com/v21.0/me?fields=username&access_token=$TOKEN"
# username이 나오면 유효, 190이면 무효
```

## ② 테스터 초대가 Pending에서 안 풀린다

![테스터 초대 수락 에러의 증상·원인·해결 다이어그램](/assets/img/posts/body-ts-tester-invite.png)

개발 모드에서 테스트하려면 인스타 계정을 앱의 **테스터**로 등록해야 한다. 추가했는데 상태가 **Pending**에서 멈춘다. 수락하려고 `instagram.com` → 설정 → **앱 및 웹사이트**(manage_access) 페이지에 들어가면 이렇게 나온다.

```text
문제가 발생했습니다
문제가 발생하여 페이지를 읽어들이지 못했습니다.
```

다른 브라우저로, 시크릿 창으로 해도 같다.

원인은 두 겹이다.

1. 테스터 역할은 **초대받은 계정이 직접 수락**해야 활성화된다. 그전까지는 Pending이 정상 상태다 — 즉 Pending 자체는 고장이 아니다.
2. 그런데 `instagram.com`의 앱·웹사이트 관리 페이지가 **특정 계정에서 열리지 않는다.** 브라우저 문제가 아니라 그 페이지·계정 조합의 문제다. 즉 **수락을 할 수 없어서** Pending이 안 풀린다.

우회 순서는 이렇다.

1. **모바일 인스타 앱**에서 수락 — 설정 및 활동 → "앱 및 웹사이트" → 테스터 초대 → 수락. 웹이 깨져도 앱은 별개 경로라 열리는 경우가 많다.
2. 그래도 안 되면 **다른 계정·새 계정**을 테스터로 추가해 수락한다. 깨끗한 새 계정은 그 버그를 잘 타지 않는다. 테스트용 댓글 계정은 *아무 테스터 계정*이면 되므로 이 우회로 충분하다.
3. 일시적 장애일 수도 있으니 시간을 두고 재시도한다.

## ③ Test 버튼은 되는데 실제 댓글 webhook은 안 온다

![댓글 webhook 미수신의 점검 순서 다이어그램](/assets/img/posts/body-ts-comment-webhook.png)

게시물에 실제로 댓글을 달았는데 **서버에 들어온 이벤트가 0건**이다. 반면 Meta 대시보드의 **"Test" 버튼으로 보낸 샘플 webhook은 정상 도착**한다.

이 조합이 중요한 단서다. **전달 경로(콜백 URL·서명 검증)는 멀쩡하고, 실제 댓글 이벤트만 생성되지 않는 상황**이라는 뜻이다. 콜백 쪽을 아무리 뒤져도 답이 없다.

점검 순서는 이렇다.

1. **개발 모드 제약** — 개발 모드에서는 **앱에 역할이 있는 계정**(테스터·개발자·관리자)의 이벤트만 webhook이 발생한다. 역할 없는 계정이 단 댓글은 오지 않는다. ②에서 테스터 수락을 끝내야 하는 이유가 여기 있다.
2. **`comments` 필드 미구독** — 계정-앱 구독(`subscribed_apps`)에 `messages`만 있고 `comments`가 빠진 경우.
3. **권한 미추가** — 토큰에 `instagram_business_manage_comments`가 없으면 댓글 이벤트에 접근할 수 없다. 권한을 추가한 뒤에는 **토큰을 다시 발급**해야 반영된다.

해결은 셋을 차례로 맞추는 것이다.

```bash
# 구독 설정 (comments 포함)
curl -s -X POST "https://graph.instagram.com/v21.0/me/subscribed_apps?subscribed_fields=comments,messages&access_token=$TOKEN"

# 확인 — ['comments','messages']가 나와야 정상
curl -s "https://graph.instagram.com/v21.0/me/subscribed_apps?access_token=$TOKEN"
```

권한은 `instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_manage_messages` 3종을 추가하고 토큰을 재발급한다. 테스트는 **테스터로 등록·수락이 끝난 계정**으로 댓글을 달아야 한다.

> **여기서 ①과 충돌한다.** ③은 권한 추가 후 "토큰 재발급"을 요구하고, ①은 "토큰을 재생성하지 말라"고 한다. 그래서 **권한을 먼저 다 맞춘 뒤 토큰을 마지막에 한 번 발급**하는 순서가 된다. 반대로 하면 190을 다시 만든다.
{: .prompt-warning }

**일반 공개 팔로워의 댓글까지 받으려면** 앱을 Live로 전환하고 App Review(Advanced Access)를 통과해야 한다. 그리고 이건 사업자 인증이 전제다 — 개발 모드로는 영원히 테스터 계정만 다룰 수 있다.

## ④ wrangler login이 localhost 콜백에서 죽는다

![wrangler login 실패의 증상·원인·해결 다이어그램](/assets/img/posts/body-ts-wrangler-login.png)

봇을 Cloudflare Workers에 올리려는데 `wrangler login`이 브라우저 인증 후 실패한다.

```text
✘ [ERROR] Timed out waiting for authorization code, please try again.
```

재시도하면 메시지가 바뀐다.

```text
▲ [WARNING] Received query string parameter doesn't match the one sent! Possible malicious activity somewhere.
```

콜백 화면에는 `localhost:8976/oauth/callback?error=access_denied ... The consent verifier has already been used`와 **ERR_CONNECTION_REFUSED**가 같이 뜬다.

원인은 **로컬 콜백 서버**다. `wrangler login`은 `localhost:8976`에 임시 서버를 띄워 승인 코드를 받는다. 백그라운드 실행이나 반복 시도로 **state가 어긋나거나**, 승인하는 시점에 **그 서버가 이미 종료**돼 있으면 위 에러들이 난다. consent 재사용·연결 거부는 모두 그 결과다.

해결은 브라우저 콜백을 아예 쓰지 않는 것이다.

1. Cloudflare 대시보드 → My Profile → **API Tokens** → Create Token → **"Edit Cloudflare Workers"** 템플릿으로 발급
2. 환경변수로 넘긴다.

```bash
export CLOUDFLARE_API_TOKEN="발급받은_토큰"
npx wrangler deploy   # 브라우저 로그인 없이 동작
```

서브도메인 등록 같은 작업도 API로 된다(`PUT /accounts/{id}/workers/subdomain`). localhost 콜백 이슈가 원천 차단된다.

## 네 가지의 공통 패턴

모아보고 나서야 보인 것이 두 가지 있다.

**① 에러 메시지를 믿지 말고 상태를 조회한다.** 190은 거짓 원인을 적어줬고, Pending은 이유를 안 적어줬고, webhook 0건은 "고장"인지 "정상"인지 구분조차 안 됐다. 세 경우 모두 해결의 출발점이 **플랫폼의 현재 상태를 직접 찍어보는 `curl` 한 줄**이었다 — 토큰이 유효한지, 구독 필드에 무엇이 들어 있는지. 추측으로 설정을 바꾸는 것보다 조회가 훨씬 빠르다.

**② 로컬 콜백에 의존하는 CLI 로그인은 자동화와 상성이 나쁘다.** ④는 성격이 다른 문제였다. `wrangler login` 같은 OAuth 흐름은 사람이 터미널 앞에 앉아 있다고 가정한다. 비대화형으로 돌리면 깨진다. **토큰 방식이 제공되는 도구는 처음부터 토큰으로 가는 게 맞다.**

> **🧭 기획자·사업자라면**
> **개발 모드에서 되는 것과 서비스가 되는 것은 전혀 다른 범위다.** ③에서 확인했듯 개발 모드 봇은 **앱에 역할이 있는 계정의 이벤트만** 받는다. 즉 테스터 몇 명으로 하는 데모는 끝까지 되지만, 일반 사용자 한 명도 못 받는다. 그 선을 넘으려면 Live 전환 + App Review이고, **그 전제가 사업자 인증**이다. 기능 개발이 아니라 **자격 요건**이라서 일정으로 당길 수 없다.
> **그래서 플랫폼 의존 기능의 일정 추정에는 "심사 리드타임"을 따로 적어야 한다.** 코드 완성일과 서비스 개시일이 같다고 적는 순간 계획이 틀린다. 반대로 데모·검증 단계라면 개발 모드만으로 충분하니, **심사를 언제 거는 게 가장 싼가**를 먼저 정하는 쪽이 낫다.
{: .prompt-tip }

## 사용한 기술

- **Instagram Graph API (`graph.instagram.com`)** — 토큰 유효성 확인(`/me`), 계정-앱 webhook 구독(`/me/subscribed_apps`).
- **Meta 앱 역할(테스터·개발자·관리자)** — 개발 모드에서 이벤트가 발생하는 범위를 정하는 설정. 초대는 받는 계정이 수락해야 한다.
- **Instagram 권한** — `instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_manage_messages`. 추가 후 토큰 재발급이 필요하다.
- **App Review / Advanced Access** — 역할 없는 일반 사용자의 이벤트를 받기 위한 심사. 사업자 인증이 전제다.
- **Cloudflare API 토큰(`CLOUDFLARE_API_TOKEN`)** — `wrangler`의 브라우저 OAuth를 대체. "Edit Cloudflare Workers" 템플릿으로 발급한다.

## 정리

- 네 에러 모두 **메시지가 가리키는 곳에 원인이 없었다.** 190은 비밀번호가 아니라 토큰 재생성, Pending은 수락 페이지 장애, webhook 0건은 개발 모드·구독, 타임아웃은 콜백 서버 종료였다.
- 권한을 먼저 다 맞추고 **토큰은 마지막에 한 번만** 발급한다. 순서를 바꾸면 190을 스스로 만든다.
- `Test` 버튼은 되는데 실제 이벤트가 안 오면 **전달 경로가 아니라 이벤트 생성 조건**(역할·구독)을 본다.
- CLI 로그인이 `localhost` 콜백을 쓴다면, **토큰 방식이 있는지 먼저 확인**한다.
