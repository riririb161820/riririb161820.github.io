---
title: "왓츠앱 알림 도입 전에 알아야 할 것 — Meta 직접 vs Twilio, 2025 과금 개편 기준"
headline: "Meta냐 Twilio냐"
date: 2026-07-08 07:00:00 +0900
categories: [개발, 운영]
tags: [whatsapp, twilio, meta-cloud-api, notification, sms, bsp]
description: 글로벌 고객에게 왓츠앱으로 배송·주문 알림을 보내려 할 때 Meta Cloud API 직접 연동과 Twilio(BSP) 중 무엇을 고를까. 2025년 7월 건당 과금 개편, 템플릿 사전승인, 비즈니스 인증, SMS 폴백까지 의사결정 기준을 정리했다.
image:
  path: /assets/img/posts/whatsapp-notification-meta-vs-twilio-hero.png
  alt: 왓츠앱 알림 도입 - Meta Cloud API 직접 연동 vs Twilio BSP 비교
---

## 문제

글로벌 고객에게 주문·배송 상태를 왓츠앱으로 알리는 기능을 설계하다 벽에
부딪혔다. "왓츠앱 비즈니스 API는 Meta에 직접 앱 등록하면 무료 아닌가?"라고
막연히 생각했는데, 파고들수록 무료가 아니었고 선택지도 하나가 아니었다.

정리해야 할 질문이 이만큼이었다.

- Meta Cloud API 직접 연동은 정말 무료인가?
- Twilio 같은 BSP(Business Solution Provider)를 끼면 뭐가 더 붙나?
- 어느 쪽이든 왓츠앱을 쓰려면 뭘 먼저 준비해야 하나?
- 발송 실패 시 SMS 폴백은 누가 처리하나?

## 원인 (무료의 실체)

"Meta 직접이면 무료"는 반은 맞고 반은 틀리다.

- **인프라(Cloud API 접근·호스팅)는 무료** — 맞다. Meta가 직접 호스팅하고
  접근 비용이 없다.
- 하지만 **메시지 자체는 유료** — 2025년 7월 1일부터 대화(conversation)
  단위가 아니라 **건당 과금**으로 바뀌었다. 요율은 템플릿 카테고리와 수신자
  국가번호에 따라 다르다.

우리가 보낼 배송 알림은 **Utility(유틸리티) 카테고리**로 가장 싼 등급이고,
고객이 먼저 메시지를 보낸 뒤 24시간(서비스 윈도우) 안에 보내는 Utility
메시지는 무료다. 반면 마케팅 메시지는 훨씬 비싸다.

여기에 더해, 어느 쪽을 고르든 **공통으로 필요한 것**이 있다.

- **Meta 비즈니스 인증** (사업자등록 기반)
- **WABA**(WhatsApp Business Account)와 발신 번호 등록
- **템플릿 사전 승인** — 기업이 먼저 보내는 모든 메시지는 승인된 템플릿이어야
  한다. 상태가 10단계면 템플릿도 그만큼 승인받아야 한다(심사 대기열이 생긴다).

## 해결 과정 (의사결정)

### 1. 비용 구조를 실제로 비교

메시지 1건의 비용을 뜯어보면 이렇게 쌓인다.

![메시지 1건 비용 구조 - Meta 직접 vs Twilio passthrough + 마크업](/assets/img/posts/whatsapp-notification-meta-vs-twilio-cost.png)

- **Meta 직접**: Meta 템플릿 요금만.
- **Twilio 경유**: 같은 Meta 요금이 그대로 전가(passthrough)되고, 그 위에
  Twilio 수수료 **건당 $0.005**(수신·발신 모두)가 붙는다.

### 2. 진짜 변수는 가격이 아니었다

여기서 함정 — 규모를 넣어보면 가격은 의사결정 변수가 아니다. 소규모 알림
(예: 월 100건 안팎)이면 Twilio 수수료를 다 더해도 커피 한 잔이 안 된다.
진짜 갈림길은 두 가지였다.

- **SMS 폴백을 누가 쏘나** — 왓츠앱이 실패했을 때 SMS로 대체 발송하는 경로.
- **벤더를 몇 개 두나** — Meta 직접이면 왓츠앱과 SMS가 별도 벤더라 2개,
  Twilio면 왓츠앱+SMS를 **한 API**로 처리한다.

### 3. 선택: Twilio 단일 스택

Twilio는 왓츠앱과 SMS를 한 API로 제공하고, **SMS 폴백이 내장**돼 있으며,
WhatsApp Self Sign-up으로 승인 대기를 우회해 카드 등록만으로 바로 시작할 수
있다. 국내 문자 사업자(예: NHN Cloud) 승인을 기다리던 상황에서, Twilio 하나로
발송·폴백·번호 관리를 묶으면 일정 리스크가 줄었다.

> 단, Twilio를 써도 **Meta 비즈니스 인증·WABA·템플릿 승인은 똑같이 필요**하다.
> Twilio가 그 과정을 콘솔에서 대행할 뿐, 건너뛰는 게 아니다.

## 사용한 기술

- **WhatsApp Business Platform (Cloud API)** — Meta 직접 연동. 인프라 무료,
  메시지 건당 과금(2025-07 개편), 템플릿 사전 승인 필수
- **Twilio** — BSP(Business Solution Provider). 왓츠앱+SMS 단일 API, SMS 폴백
  내장, Self Sign-up, 건당 $0.005 수수료
- **Utility 템플릿 / 24시간 서비스 윈도우** — 배송 알림의 과금 등급과 무료 구간

> **🧭 기획자·사업자라면**
> 1. "무료 API"라는 말은 대개 **인프라가 무료**라는 뜻이지 메시지가 무료라는 뜻이 아니다. 채널 비용은 건당 요율 × 발송량으로 잡아야 하고, PoC 규모에선 대체로 무시 가능하지만 대량 발송으로 가면 카테고리(Utility vs 마케팅)가 비용을 가른다.
> 2. 벤더를 하나로 묶을지(Twilio) 직접 여러 개를 붙일지(Meta+문자사)는 비용이 아니라 **운영 복잡도와 일정 리스크**의 문제다. 승인 대기가 크리티컬 패스라면, 수수료를 조금 더 내더라도 대기를 우회하는 쪽이 프로젝트를 살린다.
{: .prompt-tip }

## 정리

1. Meta Cloud API는 인프라만 무료다. 메시지는 2025년 7월부터 건당 과금이며, 배송 알림은 가장 싼 Utility 등급이다.
2. Twilio를 끼우면 Meta 요금 passthrough + 건당 $0.005가 붙지만, 소규모에선 비용 차이가 무의미하다.
3. 진짜 결정 변수는 가격이 아니라 SMS 폴백 처리와 벤더 수 — 승인 대기를 우회하려면 왓츠앱+SMS를 한 API로 묶는 Twilio가 유리했다. 단 Meta 비즈니스 인증·템플릿 승인은 어느 쪽이든 필요하다.
