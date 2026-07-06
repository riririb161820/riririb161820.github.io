---
title: "B2B API 연동 검증에서 HTTP 400이 반가운 신호인 이유 (401 vs 400 vs 200)"
headline: "400이 반가운 신호"
date: 2026-07-07 07:00:00 +0900
categories: [개발, 트러블슈팅]
tags: [api, oauth, http-status, client-credentials, kuehne-nagel, integration]
description: 파트너 API에 첫 호출을 던졌더니 HTTP 400 Bad Request. 인증 실패인 줄 알았지만, 400은 오히려 인증을 통과해 백엔드까지 도달했다는 신호였다. OAuth Client Credentials 토큰 발급부터 200 빈 배열까지, 연동 검증의 상태코드 읽는 법.
image:
  path: /assets/img/posts/b2b-api-http-400-good-signal-hero.png
  alt: API 첫 호출 상태코드 - 401 인증 실패, 400 백엔드 도달, 200 연동 성공
---

## 문제

글로벌 물류기업 Kuehne+Nagel의 배송 추적 API를 연동하려고, 개발자 포털에서
OAuth 애플리케이션을 만들고 Client Credentials 방식으로 액세스 토큰을 발급받았다.
발급까지는 순조로웠다. 그리고 첫 API 호출을 던졌다.

```bash
curl -H "Authorization: Bearer <access_token>" \
  "https://gateway.api.kuehne-nagel.com/track-trace/shipment/v2/shipments"
```

돌아온 건 이거였다.

```json
{"timestamp":"...","status":400,"error":"Bad Request","path":"/tracking-overviews/external/api/knite/track-trace/shipments"}
```

**HTTP 400 Bad Request.** 순간 "토큰이 잘못됐나? 인증이 안 먹었나?" 싶었다.
그런데 여기서 400을 인증 실패로 오해하고 토큰 발급부터 다시 파면, 멀쩡한 걸
붙잡고 시간을 버리게 된다.

## 원인

400은 인증 실패가 아니다. **인증을 통과했다는 증거**다. 상태코드가 어디서
막혔는지를 알려준다고 보면 된다.

- **401**이면 토큰 문제 — API 게이트웨이 문턱조차 못 넘은 것.
- **403**이면 인증은 됐지만 구독·권한 문제.
- **400**이면 인증·권한 다 통과하고 **백엔드 서비스까지 요청이 도달**한 뒤,
  요청 형식(필수 파라미터 등)이 틀렸다는 것.

결정적 단서는 400 응답 본문의 `path`였다. 내가 호출한 건
`/track-trace/shipment/v2/shipments`인데, 에러에 찍힌 경로는
`/tracking-overviews/external/api/knite/...`로 **내부 서비스 주소로 치환돼**
있었다. 게이트웨이가 요청을 내부로 라우팅했다는 뜻 — 즉 인증·구독·라우팅이
전부 정상 작동했다는 증거다.

그럼 왜 400인가? 스펙을 확인하니 `GET /shipments`는 `reference`(고객 참조번호)
쿼리 파라미터가 **필수**였다. 파라미터 없이 불러서 400이 난 것이다.

## 해결 과정

### 1. 토큰 발급 (Client Credentials)

```bash
curl -X POST "https://portal.api.kuehne-nagel.com/oauth2/token" \
  -u "<ConsumerKey>:<ConsumerSecret>" \
  -d "grant_type=client_credentials"
```

응답의 `access_token`이 Bearer 토큰. 여기서 **콘솔의 Key Configuration 화면은
그냥 Generate Keys만 누르면 된다** — Client Credentials 방식은 Callback URL도,
별도 입력도 필요 없다. 이 단계가 됐다면 인증 자체는 성공이다.

### 2. 필수 파라미터 없는 엔드포인트로 연결 검증

`GET /shipments`는 `reference`가 필수라 검증용으로는 번거롭다. 그래서 필수
필드가 없는 **검색 엔드포인트**로 연결만 확인했다.

```bash
curl -X POST "https://gateway.api.kuehne-nagel.com/track-trace/shipment/v2/shipments-search" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"pagination":{"pageNumber":1,"pageSize":10},"filters":{}}'
```

결과:

```json
{"shipments":[],"page":{"totalElements":0,"totalPages":0,"currentPage":0,"size":20,"hasNext":false,"hasPrevious":false}}
```

**HTTP 200 + 빈 배열.** 이게 연동 검증의 결승선이다. 우리 계정에 아직 운송
건이 없으니 **빈 배열이 정답**이고, 이 응답을 받은 순간 인증·구독·게이트웨이
라우팅·요청 형식이 전 구간 검증된 것이다.

### 3. 함정: 익명 스펙의 서버 URL

한 가지 더 삽질 포인트. 로그인 없이 받은 OpenAPI 스펙의 `servers`에는
`https://internal.api.kuehne-nagel.com/...` 내부 주소가 적혀 있었다. 실제
호출 주소는 로그인 후 포털에서 받은 스펙의 `https://gateway.api.kuehne-nagel.com/...`
였다. 내부 주소로 쏘면 당연히 안 닿는다. (이 익명 스펙 이야기는
[회원가입 없이 스펙 받아내기](/posts/wso2-devportal-api-no-login/)에 정리했다.)

## 사용한 기술

- **OAuth 2.0 Client Credentials** — 서버 간(machine-to-machine) 인증. 사용자
  로그인 없이 Consumer Key/Secret으로 액세스 토큰 발급
- **HTTP 상태코드** — 401(인증)·403(권한)·400(요청 형식)·200(성공)으로 실패
  지점 진단
- **curl** — 토큰 발급·API 호출 검증

> **🧭 기획자·사업자라면**
> 1. 외부 API 연동에서 "인증까지 됐나 / 데이터 권한까지 열렸나 / 실호출이 되나"는 **다른 단계**다. 200 빈 배열이라도 "연결은 검증됐다"는 마일스톤으로 잡으면, 실데이터가 없는 초기에도 연동 완료 여부를 명확히 보고할 수 있다.
> 2. 파트너와 API 연동 일정을 잡을 때 "토큰 발급"과 "실데이터 조회"를 같은 칸에 두지 말 것 — 토큰은 며칠, 실데이터는 계약·운송 데이터가 실제로 쌓여야 나온다. 이 둘을 분리하지 않으면 "API 연동 완료"의 정의가 흐려진다.
{: .prompt-tip }

## 정리

1. B2B API 첫 호출의 400은 인증 실패가 아니라 **인증 통과 + 백엔드 도달** 신호다. 401(토큰)·403(권한)과 구분하자.
2. 400 응답 본문의 `path`가 내부 주소로 바뀌어 있으면 게이트웨이 라우팅이 정상 작동한 것 — 필수 파라미터를 확인하면 된다.
3. 연결 검증은 필수 파라미터 없는 엔드포인트로 `200 + 빈 배열`을 받으면 끝. 빈 배열은 실패가 아니다.
