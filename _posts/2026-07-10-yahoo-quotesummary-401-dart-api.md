---
title: "Yahoo quoteSummary 401로 재무 데이터가 죽었을 때 — DART API로 교체"
headline: "재무가 죽어 있었다"
date: 2026-07-10 15:30:00 +0900
categories: [개발, 트러블슈팅]
tags: [yahoo-finance, dart, 재무데이터, api, 좀비피처]
description: "재무 필터 코드는 있는데 전 종목이 결측이었다. Yahoo quoteSummary가 crumb 요구로 401을 뱉으며 조용히 폴백되던 좀비 피처의 정체와, DART 공시 API 연동으로 되살린 과정."
image:
  path: /assets/img/posts/yahoo-quotesummary-401-dart-api-hero.png
  alt: Yahoo 재무 API가 401로 죽어 재무 필터가 무력화된 문제
---

## 문제

봇에 "적자 기업은 신규 매수에서 배제"하는 재무 필터를 넣었다. 코드도 있고, 배포도 됐다. 그런데 라이브에서 확인해보니 **24개 전 종목이 재무 '데이터 없음'**으로 나왔다. 필터는 결측 시 중립 통과하도록 설계돼서, 사실상 **아무도 걸러지지 않는 장식**이 돼 있었다.

기능은 있는데 효과는 없는 상태 — 이른바 **좀비 피처(zombie feature)**다.

## 원인

재무 데이터를 Yahoo Finance의 `quoteSummary` 엔드포인트에서 받고 있었는데, 실측해보니 **401 Unauthorized**를 뱉었다.

```
GET https://query1.finance.yahoo.com/v10/finance/quoteSummary/005930.KS
→ 401 (Invalid Crumb)
```

Yahoo가 어느 시점부터 이 엔드포인트에 **crumb(세션 토큰) 요구**를 걸었다. 봇은 crumb 없이 요청했고, 401이 떨어지자 `try/except`가 조용히 잡아 None을 반환했다. 필터는 None을 "결측→중립 통과"로 처리하니 **에러 하나 없이, 알람 하나 없이** 재무 필터가 통째로 무력화돼 있었다.

이게 좀비 피처의 무서운 점이다. **데이터 소스의 사망은 예외를 던지지 않는다** — 폴백이 조용히 상시화되면서 "있는데 효과 없는" 상태로 굳는다.

## 해결 과정

애초에 Yahoo는 국내 종목에 공신력도 없었다. 용도별로 공식 소스를 갈랐다:

| 데이터 | 폐기 | 교체 |
|--------|------|------|
| 재무제표 | Yahoo quoteSummary | **DART(금융감독원 전자공시)** |
| 변동성(VIX) | Yahoo ^VIX | CBOE 공식 CSV |
| 환율 | Yahoo | 한국은행 ECOS |

재무는 **DART Open API**(무료 키)로 교체했다:

1. `corpCode.xml`(전체 기업 고유번호 zip)에서 유니버스 종목의 `corp_code`를 매핑해 캐시.
2. `fnlttSinglAcnt.json`으로 최신 분기 보고서의 영업이익·자본총계·부채총계를 조회.
3. 적자·자본잠식·과다부채면 신규 매수 배제.

교체 후 실측하니 **24/24 전 종목 실데이터**가 들어왔다. 배터리 3사(LG화학·삼성SDI·LG엔솔)가 1분기 영업적자로 실제 배제됐고, 이는 공시 사실과 정합했다.

## 사용한 기술

- **Yahoo quoteSummary crumb 401**: 비공식 엔드포인트라 예고 없이 인증이 걸린다. 무료·비공식 API는 언제든 죽을 수 있다.
- **좀비 피처 탐지**: "코드가 있다"가 "동작한다"가 아니다. 라이브에서 실제 값이 오는지 주기적으로 실측하라. 조용한 폴백은 알람이 안 울린다.
- **DART Open API**: 국내 상장사 재무의 공식 원본. `corpCode.xml`(고유번호) → `fnlttSinglAcnt.json`(재무제표) 2단계.
- **산출 주체 원칙**: 지표는 만든 곳에서 받아라. VIX는 CBOE, 재무는 DART, 환율은 한국은행.

## 정리

1. **데이터 소스의 사망은 알람 없이 온다** — try/except가 잡아 조용히 폴백되면 "있는데 효과 없는" 좀비 피처가 된다.
2. **코드 존재 ≠ 기능 작동** — 라이브에서 실제 값이 오는지 실측으로 확인하라.
3. **지표는 산출 주체에서 받아라** — 국내 재무는 Yahoo가 아니라 DART 공시가 원본이다.

---

> 이 글은 [AI 자동매매 봇 3주 검증 회고](/posts/ai-trading-bot-3week-validation/)의 트러블슈팅 서브클러스터 중 하나입니다.
{: .prompt-info }
