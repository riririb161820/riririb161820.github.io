---
title: "네이버 카페 글쓰기 API 뚫기 (2) — Callback URL 하나 때문에 막혀 있었다"
headline: "카페 API 글쓰기 성공"
date: 2026-09-02 22:20:00 +0900
categories: [개발, 자동화]
tags: [naver-buddy-automation, 네이버카페, openapi, oauth, 네이버로그인]
description: "네이버 카페 글쓰기 공식 API는 존재하는데 쓰지 못하고 있었다. 원인은 앱 설정의 Callback URL 미등록. 콜백 서버 없이 인가 코드를 회수하는 방법과 문서에 적힌 MS949 이중 인코딩의 실체까지 실측으로 정리했다."
image:
  path: /assets/img/posts/naver-buddy-automation-2-cafe-api-callback-url-hero.png
  alt: 앱 설정에서 Callback URL 등록, OAuth 인증, 인가 코드 회수, 토큰 교환, 글쓰기 POST로 이어지는 5단계 흐름
---

> **시리즈 「네이버 서이추 자동화」**
> [1편 JS click이 안 먹히는 버튼](/posts/naver-buddy-automation-1-js-vs-real-click/) · **2편 (현재 글)** · [3편 웹훅은 없다](/posts/naver-buddy-automation-3-no-webhook-polling/) · [4편 토큰 99% 줄이기](/posts/naver-buddy-automation-4-browser-token-diet/) · [5편 자동화 티는 어디서 나는가](/posts/naver-buddy-automation-5-automation-tell/)
{: .prompt-info }

## 문제

[1편](/posts/naver-buddy-automation-1-js-vs-real-click/)에서 카페 글쓰기를 **스마트에디터에 실제 키보드로 타이핑**해서 해결했다. 동작은 했지만 취약했다. 스냅샷으로 문단 uid를 찾고, 캐럿을 옮기고, 한 글자씩 넣는다. 에디터 DOM이 조금만 바뀌어도 깨진다.

그런데 공식 API 카탈로그를 다시 보니 이런 게 있었다.

```
POST https://openapi.naver.com/v1/cafe/{clubid}/menu/{menuid}/articles
```

**네이버 카페 게시글 등록 API가 공식으로 존재한다.** 로그인 방식 오픈API다.

처음엔 "쓸 수 없다"고 결론 냈다. 앱 설정을 열어보니 **OAuth 인증을 시작할 수가 없었기** 때문이다.

## 원인

앱 설정 화면을 뜯어보니 상태가 이랬다.

- **사용 API**: 네이버 로그인 · **카페** · 캡차 → 카페 권한은 **이미 켜져 있었다**
- **비로그인 오픈 API 서비스 환경**: WEB 설정 등록됨
- **로그인 오픈 API 서비스 환경**: **비어 있음** ← 여기가 문제

그리고 화면 하단에 빨간 경고가 떠 있었다.

```
[로그인 오픈 API 서비스 환경] 설정을 확인해 주세요.
```

**로그인 방식 오픈API는 Callback URL이 등록돼 있어야 한다.** OAuth 인증(`authorize`)은 인증이 끝난 뒤 사용자를 되돌려 보낼 주소가 필요한데, 그게 없으면 `authorize` 자체를 시작할 수 없다. → 인가 코드를 못 받는다 → access token을 못 받는다 → **로그인 방식 API 전부 사용 불가.**

카페 권한은 켜져 있는데, 그 권한을 쓸 수 있는 **입구가 닫혀 있던 상태**였다. 기술적 한계가 아니라 **설정 한 줄**이 빠져 있었다.

## 해결 과정

### 1. 로그인 오픈 API 서비스 환경 추가

앱 → `API 설정` → **로그인 오픈 API 서비스 환경** → `환경 추가` → **PC 웹**

| 항목 | 값 |
|---|---|
| 서비스 URL | `http://localhost` |
| Callback URL | `http://localhost:8080/callback` |

저장하니 내부 상태가 이렇게 바뀌고, 빨간 경고가 사라졌다.

```json
serviceEnvUrlList      : {"openapi_web":"http://localhost","pcweb":"http://localhost"}
serviceEnvCallbackList : {"pcweb":["http://localhost:8080/callback"], ...}
```

> 실서비스가 아니라 로컬 자동화용이면 `localhost`로 충분하다. 다만 **여기 적은 주소와 실제 `redirect_uri`가 정확히 일치**해야 한다. 다르면 인증이 거부된다.
{: .prompt-tip }

### 2. OAuth 인증

```
https://nid.naver.com/oauth2.0/authorize
  ?response_type=code
  &client_id={CLIENT_ID}
  &redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback
  &state={임의문자열}
```

동의 화면에 **`[선택] 카페가입, 글쓰기`** 항목이 포함돼 있다. 이게 체크돼야 글쓰기 API를 쓸 수 있다.

### 3. 콜백 서버 없이 인가 코드 회수하기

여기가 이 글의 핵심이다.

`redirect_uri`를 `http://localhost:8080/callback`으로 잡았지만 **거기엔 아무 서버도 안 띄웠다.** 당연히 리다이렉트는 실패한다.

```
GET http://localhost:8080/callback?code=XXXXXXXX&state=XXXX
→ net::ERR_CONNECTION_REFUSED
```

**그런데 실패한 요청의 URL에 인가 코드가 그대로 들어 있다.** DevTools 네트워크 로그에서 그 요청을 찾으면 `?code=...` 를 바로 읽을 수 있다.

즉 **콜백을 받아줄 서버를 만들 필요가 없다.** 로컬 자동화 목적이라면 Express 띄우고 라우트 만들 이유가 없었다.

![리다이렉트가 ERR_CONNECTION_REFUSED로 실패해도 네트워크 로그에 남은 요청 URL에서 인가 코드를 회수하는 흐름](/assets/img/posts/naver-buddy-automation-2-cafe-api-callback-url-code.png)
_실패한 리다이렉트가 인가 코드를 그대로 실어 나른다_

### 4. 토큰 교환

```
https://nid.naver.com/oauth2.0/token
  ?grant_type=authorization_code
  &client_id={ID}&client_secret={SECRET}
  &code={회수한 코드}&state={같은 값}
```

`access_token`(유효 1시간)과 `refresh_token`을 받는다.

### 5. 실제 글쓰기 — 첫 시도에 200

```python
def enc2(s):                                   # 문서 규칙 = 이중 URL 인코딩
    return quote_plus(quote_plus(s))

url  = f"https://openapi.naver.com/v1/cafe/{clubid}/menu/{menuid}/articles"
body = f"subject={enc2(subject)}&content={enc2(content)}".encode()
req  = Request(url, data=body, method="POST")
req.add_header("Authorization", "Bearer " + token)
req.add_header("Content-Type", "application/x-www-form-urlencoded")
```

```json
{"result":{"msg":"Success","articleId":XXXXXX,"articleUrl":"https://cafe.naver.com/..."}}
```

### 인코딩 함정 — "MS949 재인코딩"의 실체

문서에는 이렇게 적혀 있다.

> 해당 string은 UTF-8로 encode 후 MS949로 재 encode를 수행한 값

자바 코드로는 `URLEncoder.encode(URLEncoder.encode(s, "UTF-8"), "MS949")` 다. 처음엔 실제로 MS949 코덱을 써야 하는 줄 알았는데, 뜯어보면 그렇지 않다.

첫 번째 `URLEncoder.encode`의 결과는 `%EC%95%88...` 처럼 **순수 ASCII**다. ASCII에는 UTF-8과 MS949 차이가 없다. 그러니 두 번째 인코딩은 `%` 를 `%25` 로 바꾸는 일만 한다. 즉 **그냥 이중 URL 인코딩**이다.

```python
quote_plus(quote_plus(s))   # 이걸로 그대로 동작했다
```

### 렌더 검증 — `·` 이 깨진 줄 알았다

발행된 글을 API로 다시 읽어보니 본문이 이랬다.

```
좋은 얘기만 쓰지 않고 등&middot;어깨 통증 같은 부작용도 …
```

가운뎃점이 `&middot;` 로 저장돼 있었다. 깨진 줄 알았는데, **HTML 엔티티라 화면에서는 `·` 로 정상 렌더**된다. 실제 페이지를 눈으로 확인해서 문제없음을 확인했다.

> 저장된 원문(`contentHtml`)만 보고 판단하지 말 것. **렌더된 화면**을 봐야 한다.
{: .prompt-warning }

### 6. 무인 자동화의 조건 — refresh_token

`access_token`은 1시간짜리다. 예약 작업이 매번 사람 손을 빌릴 순 없다.

```
grant_type=refresh_token → 새 access_token 발급 (expires_in 3600)
```

**정상 동작을 확인했다.** 이걸로 무인 자동화가 가능해졌다.

### 자격증명 취급

`client_secret`은 개발자센터 화면에서 `보기`를 눌러야 나온다. 이걸 대화 로그나 터미널 출력에 흘리지 않으려고, **브라우저에서 곧바로 로컬 파일로 떨어뜨리고** 셸에서만 읽어 썼다.

```
.naver-oauth.json   (chmod 600, .gitignore 등재)
  client_id / client_secret / refresh_token / access_token
```

## 사용한 기술

- **네이버 카페 API** — `POST /v1/cafe/{clubid}/menu/{menuid}/articles` (로그인 방식 오픈API)
- **OAuth 2.0 Authorization Code Grant** — authorize → code → token → refresh
- **DevTools 네트워크 로그** — 실패한 리다이렉트에서 인가 코드 회수. 콜백 서버 대체
- **이중 URL 인코딩** — 문서의 "MS949 재인코딩"이 실제로 뜻하는 것

> **🧭 기획자·사업자라면**
> - **"안 된다"의 상당수는 설정 한 줄이다.** 권한은 켜져 있는데 입구(Callback URL)가 닫혀 있어서 못 쓰는 상태였다. 기능 불가로 판단하기 전에 **콘솔의 경고 문구부터 읽어야** 한다. 여기서 며칠이 갈릴 수 있다.
> - **공식 API가 있으면 우회 자동화보다 항상 낫다.** 1편의 실키보드 방식은 DOM이 바뀌면 깨지지만, API는 계약이라 스펙이 유지된다. **처음부터 공식 경로를 확인하는 게 총비용이 싸다.**
> - **무인 운영의 진짜 관문은 토큰 갱신이다.** access token만 되고 refresh가 안 되면 그건 자동화가 아니라 "사람이 매시간 붙어야 하는 반자동"이다. 견적에 반드시 포함할 항목.
{: .prompt-tip }

## 정리

- 카페 글쓰기 공식 API는 존재한다. 못 쓰고 있었던 건 **로그인 오픈 API 서비스 환경(Callback URL) 미등록** 때문이었다.
- **콜백 서버는 안 띄워도 된다.** 리다이렉트가 실패해도 DevTools 네트워크 로그에 `?code=` 가 남는다.
- 문서의 "MS949 재인코딩"은 사실상 **이중 URL 인코딩**이다. `quote_plus(quote_plus(s))` 로 동작한다.
