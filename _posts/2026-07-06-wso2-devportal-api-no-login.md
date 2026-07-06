---
title: "Kuehne+Nagel API 포털, 회원가입 없이 스펙 전부 받아내기 (WSO2 Devportal)"
headline: "가입 없이 스펙 확보"
date: 2026-07-06 15:00:00 +0900
categories: [개발, 트러블슈팅]
tags: [kuehne-nagel, wso2, api-manager, devportal, openapi, swagger]
description: 글로벌 물류기업 Kuehne+Nagel(쿠네+나겔)의 개발자 API 포털은 WSO2 API Manager 기반이다. 회원가입·로그인이 막혔을 때 익명 REST 엔드포인트로 API 21개 목록과 OpenAPI(Swagger) 스펙 전문을 받아내는 방법. 포털의 'MCP Servers' 메뉴 정체도 함께 정리했다.
image:
  path: /assets/img/posts/wso2-devportal-api-no-login-hero.png
  alt: WSO2 개발자 포털 - 화면은 잠겨도 REST 데이터 API는 열려 있다
---

## 문제

글로벌 물류기업 **Kuehne+Nagel(쿠네+나겔)**의 배송 추적 API를 연동해야 하는
프로젝트였다. Kuehne+Nagel은 개발자 API 포털(`portal.api.kuehne-nagel.com`)을
운영하고 있어서 들어가 봤더니, 화면에 보이는 건 로그인 폼뿐이었다.

- 포털 첫 화면 타이틀: `[DevPortal]WSO2 APIM`
- 회원가입을 시도했지만 진행이 막혔다 (승인제인지 오류인지조차 알 수 없는 상태)
- 계정이 언제 발급될지 모르는데, 연동 개발 일정은 이미 잡혀 있었다

API 스펙 없이는 연동 모듈의 요청·응답 타입 설계 자체를 시작할 수 없다. 계정을
하염없이 기다리는 것 말고 방법이 없을까?

## 원인 (이라기보다 구조)

포털 타이틀의 `WSO2 APIM`이 결정적인 힌트였다. Kuehne+Nagel의 이 포털은
처음부터 만든 자체 웹앱이 아니라, **WSO2 API Manager**라는 오픈소스 API 관리
플랫폼의 개발자 포털(Devportal) 컴포넌트를 그대로 띄운 것이었다.

WSO2 Devportal은 **화면(프론트엔드 SPA)과 데이터(백엔드 REST API)가 분리**돼
있다. 그리고 이 데이터 쪽 REST API는 공개(PUBLISHED) API의 목록·문서를
**익명으로 조회할 수 있게 열려 있는 경우가 많다.** 카탈로그를 검색엔진이나
비로그인 방문자에게도 보여주려는 기본 설계 때문이다.

즉, 브라우저 화면은 로그인을 요구해도 **화면이 데이터를 가져가는 뒷문은 열려
있을 수 있다**는 것. 위 대표 이미지가 그 구조다.

## 해결 과정

### 1. API 목록 익명 조회

WSO2 API Manager의 Devportal REST API는 경로가 표준으로 고정돼 있다
(`/api/am/devportal/v3/`). 로그인 절차를 건너뛰고 목록 엔드포인트를 바로
호출했다.

```bash
curl -s "https://portal.api.kuehne-nagel.com/api/am/devportal/v3/apis?limit=100" \
  -H "Accept: application/json"
```

응답이 왔다. **로그인 없이, 공개 상태의 API 21개 전체 목록이.**

```json
{
  "count": 21,
  "list": [
    {
      "id": "6b98ae4c-ef06-4f72-acba-616584ee7f0f",
      "name": "ShipmentTracking",
      "version": "v2",
      "lifeCycleStatus": "PUBLISHED",
      "description": "Find and show details of the consumer's shipments. Contents are basically reflecting visibility in myKN."
    }
  ]
}
```

목록에는 API 이름·버전·설명·비즈니스 오너까지 들어 있었다. 이것만으로도
"우리 유스케이스(배송 추적·해상 이벤트)에 어떤 API를 쓰면 되는지"를 바로
추릴 수 있었다.

![WSO2 Devportal에서 계정 없이 스펙 전문까지 받아내는 3단계 흐름](/assets/img/posts/wso2-devportal-api-no-login-flow.png)

### 2. OpenAPI(Swagger) 스펙 전문 다운로드

목록에서 얻은 `id`를 그대로 스펙 엔드포인트에 넣으면 OpenAPI 문서 전문이
내려온다.

```bash
curl -s "https://portal.api.kuehne-nagel.com/api/am/devportal/v3/apis/6b98ae4c-ef06-4f72-acba-616584ee7f0f/swagger" \
  -H "Accept: application/json" -o shipment-tracking-v2.json
```

핵심 API 4개(배송 추적, 컨테이너 추적, 해상 이벤트, 실시간 가시성)의 스펙을
전부 받았다. 합계 약 200KB. 스키마 정의까지 완전한 OpenAPI 문서라, 이 시점부터
연동 어댑터의 요청·응답 타입을 **실제 스펙 기준으로** 설계할 수 있었다.
계정 발급을 기다리는 동안 개발이 멈추지 않게 된 것 — 이것이 이 작업의 실질
가치였다.

### 3. 함정: 익명 스펙의 서버 URL은 믿지 말 것

익명으로 받은 스펙의 `servers` 값은 내부용 주소였다.

```json
"servers": [{ "url": "https://internal.api.kuehne-nagel.com/track-trace/shipment/v2" }]
```

나중에 계정이 발급된 뒤 **로그인 상태로 받은 같은 API의 스펙**에는 실제
게이트웨이 주소가 들어 있었다.

```json
"servers": [{ "url": "https://gateway.api.kuehne-nagel.com/track-trace/shipment/v2" }]
```

`internal.api...`로 호출하면 당연히 닿지 않는다. **익명 스펙은 "타입·구조
설계"에만 쓰고, 실제 호출 주소는 로그인 후 포털 화면의 Endpoint 표기를
우선하자.** (이 URL 함정 때문에 토큰까지 발급받고도 400 에러를 만난 디버깅은
곧 별도 글로 정리할 예정이다.)

### 보너스: 포털의 "MCP Servers" 메뉴 정체

포털 메뉴에 `MCP Servers`가 있어서 "혹시 AI 에이전트용 MCP 연결을 이미
제공하나?" 기대하고 같은 방식으로 확인해 봤다.

```bash
curl -s "https://portal.api.kuehne-nagel.com/api/am/devportal/v3/mcp-servers?limit=50"
# {"count":0,"list":[],"pagination":{"offset":0,"limit":50,"total":0}}
```

**발행된 MCP 서버 0개.** 이 메뉴는 WSO2 API Manager 최신 버전이 플랫폼 차원에서
제공하는 기능 — "REST API를 클릭 몇 번으로 MCP 서버로 변환·노출하는" MCP Hub —
의 빈 진열대였다. 포털에 메뉴가 보인다고 운영사가 실제로 뭔가를 올려뒀다는
뜻은 아니다. `count`부터 확인하자.

## 사용한 기술

- **WSO2 API Manager Devportal REST API v3** — 포털 화면이 내부적으로 쓰는
  공개 데이터 API. 표준 경로: `/api/am/devportal/v3/apis`,
  `/apis/{id}/swagger`, `/mcp-servers`
- **curl + Python** — 목록 파싱, 스펙 파일 저장
- **OpenAPI 3.0** — 받은 스펙으로 연동 어댑터 타입·목업 설계
- **WSO2 MCP Hub** — API Manager가 REST API를 MCP 서버로 노출하는 기능
  (메뉴만 있고 실제 발행은 별개)

> **🧭 기획자·사업자라면**
> 1. 파트너 API 연동에서 **계정 발급 리드타임은 코드가 아니라 계약·심사 대기열**이라 개발팀이 통제할 수 없다. "스펙 확보"와 "호출 권한 확보"를 분리해두면, 승인을 기다리는 동안에도 연동 설계·목업 개발을 병렬로 굴릴 수 있다. 일정 리스크가 크게 줄어든다.
> 2. 반대로 **우리 회사가 API 포털을 운영하는 입장**이라면 점검거리다 — 로그인 게이트가 화면(SPA)에만 걸려 있고 데이터 API는 익명으로 열려 있지 않은지. 카탈로그 공개는 의도일 수도 있지만, 내부용 엔드포인트 주소나 비즈니스 오너 정보까지 노출된다면 의도치 않은 정보 유출이다.
{: .prompt-tip }

## 정리

1. WSO2 기반 API 포털은 화면이 로그인으로 막혀 있어도 `/api/am/devportal/v3/apis`가 익명으로 열려 있는 경우가 있다 — 목록부터 OpenAPI 스펙 전문까지 받을 수 있다.
2. 단, 익명 스펙의 `servers` URL은 내부 주소일 수 있다. 타입 설계용으로만 쓰고 실제 게이트웨이 주소는 로그인 후 값으로 확정하자.
3. 포털의 `MCP Servers` 메뉴는 플랫폼 기능일 뿐 — `count:0`이면 아무것도 없는 빈 진열대다.
