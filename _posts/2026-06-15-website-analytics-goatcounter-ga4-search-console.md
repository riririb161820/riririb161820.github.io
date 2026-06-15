---
title: "블로그 방문 통계 보는 법 — GoatCounter·GA4·Search Console 3종 셋업 가이드"
date: 2026-06-15 08:45:00 +0900
categories: [개발, 운영]
tags: [analytics, goatcounter, ga4, search-console, seo, jekyll, chirpy]
description: 사이트나 블로그를 만들면 방문자 통계가 궁금해진다. GoatCounter, Google Analytics 4, Search Console — 역할이 겹치지 않는 무료 도구 3종을 함께 쓰면 무엇을 알 수 있는지, Jekyll Chirpy 기준 셋업 방법까지 정리한다.
image:
  path: /assets/img/posts/website-analytics-three-tools.png
  alt: GoatCounter, GA4, Search Console 세 가지 통계 도구가 하나의 대시보드로 모이는 일러스트
---

## 문제

블로그를 만들고 첫 글을 올리면 바로 궁금해진다. **"여기 들어오는 사람이 있긴 한가?"**

그런데 막상 통계를 붙이려고 보면 선택지가 헷갈린다. GA4를 써야 하나? 그거 하나면 되나?
세 개를 다 깔면 중복 아닌가? 결론부터 말하면 — **GoatCounter, GA4, Search Console는 역할이 서로 다르고,
셋을 함께 써야 그림이 완성된다.** 이 글은 그 세 도구가 각각 무엇을 답해주는지와 셋업 방법을 정리한다.

## 원인 — 왜 한 개로 안 되나 (세 도구의 역할 구분)

핵심은 이 한 줄이다: **Search Console는 "방문자가 도착하기 전", GoatCounter·GA4는 "도착한 후"를 본다.**

| 도구 | 답해주는 질문 | 성격 |
|---|---|---|
| **Search Console** | 구글 검색에서 내 글이 어떤 검색어에 노출되고 몇 번 클릭됐나? 색인은 됐나? | 유입(검색) 분석 |
| **GoatCounter** | 어떤 글이 며칠에 몇 번 읽혔나? (글별 조회수) | 가벼운 방문 통계 |
| **GA4** | 방문자가 어디서 왔고, 얼마나 머물고, 어떤 행동을 했나? | 상세 행동 분석 |

- **Search Console**는 통계 도구가 아니라 **검색 노출 도구**다. "사람이 들어오게 만드는" 쪽이라, 수익화가 목표면 사실상 1순위다. 색인·사이트맵·검색어 데이터를 여기서 본다.
- **GoatCounter**는 쿠키를 쓰지 않아 **동의 배너가 필요 없고**, 설정이 가장 간단하다. Jekyll Chirpy 테마에선 이걸 연결하면 **글 하단에 조회수가 표시**되는 기능까지 딸려 온다.
- **GA4**는 가장 자세하지만 대시보드가 복잡하고, 쿠키를 쓰기 때문에 방문자 지역에 따라 **동의 배너가 필요할 수 있다.** 대신 **애드센스와 연동**이 매끄러워, 나중에 "어떤 글이 돈이 되는지" 볼 때 강하다.

세 도구 모두 **무료**이고, 셋을 함께 쓰면 "검색 노출(Search Console) → 유입 → 글별 조회수(GoatCounter) → 행동·수익(GA4)"의 전 구간이 보인다.

## 해결 과정 — Jekyll Chirpy 기준 셋업

Chirpy 테마는 세 가지를 모두 내장 지원해서, `_config.yml`에 발급받은 코드만 채우면 된다. 별도 코드 작성이 없다.

**1) GoatCounter** — [goatcounter.com](https://www.goatcounter.com)에서 가입하며 `code`(예: `yoursite`)를 정한다. 가입 시 "Fill in N here"라는 봇 방지 칸이 나오는데, 말 그대로 그 숫자 N을 입력하면 된다.

```yaml
analytics:
  goatcounter:
    id: yoursite          # yoursite.goatcounter.com 의 yoursite 부분
pageviews:
  provider: goatcounter   # 글 하단 조회수 표시 (Chirpy는 goatcounter만 지원)
```

**2) GA4** — [analytics.google.com](https://analytics.google.com)에서 속성 생성 → 웹 데이터 스트림에 사이트 URL 등록 → 측정 ID `G-XXXXXXXXXX`를 받는다.

```yaml
analytics:
  google:
    id: G-XXXXXXXXXX
```

**3) Search Console** — [search.google.com/search-console](https://search.google.com/search-console)에서 URL 접두어로 사이트 등록 → 소유권 확인 방법 중 **"HTML 태그"** 선택 → `<meta name="google-site-verification" content="...">`의 content 값을 복사한다.

```yaml
webmaster_verifications:
  google: 여기에_인증코드
```

⚠️ 순서 주의: **인증 코드를 config에 넣고 배포(push)한 뒤** Search Console에서 "확인" 버튼을 눌러야 통과한다. 메타태그가 사이트에 떠 있어야 구글이 읽을 수 있기 때문이다. 배포 후 실제로 태그가 들어갔는지는 이렇게 확인한다.

```bash
curl -sL "https://내사이트/" | grep "google-site-verification"
```

확인이 끝나면 같은 화면에서 **사이트맵**(`sitemap.xml`)을 제출한다. Chirpy는 사이트맵을 자동 생성한다.

**막혔던 지점: "사이트맵을 가져올 수 없음"**

사이트맵을 제출하자마자 "가져올 수 없음(Couldn't fetch)"이 떴다. 사이트맵 자체는 정상이었다(HTTP 200, 유효한 XML, robots.txt 허용). 원인은 **만든 지 얼마 안 된 새 사이트**라 구글봇이 아직 한 번도 크롤링하지 않았기 때문이다. 새 사이트에서 흔한 정상 상태로, 보통 며칠 안에 자동으로 "성공"으로 바뀐다. 삭제·재제출을 반복할 필요는 없고, 굳이 재촉하려면 URL 검사 → 색인 생성 요청으로 구글봇을 한 번 부르면 된다.

## 사용한 기술

- **GoatCounter** — 쿠키 없는 경량 방문 통계, 동의 배너 불필요, 글별 조회수
- **Google Analytics 4 (GA4)** — 상세 행동 분석, 애드센스 연동
- **Google Search Console** — 검색 노출·색인·사이트맵, 검색어 데이터
- **Jekyll Chirpy** — 세 도구를 `_config.yml` 설정만으로 연결 (코드 작성 불필요)

## 정리

- 세 도구는 중복이 아니다. **Search Console는 도착 전(검색 노출), GoatCounter·GA4는 도착 후(방문·행동)** 를 본다.
- 가장 간단·프라이버시 친화적인 건 GoatCounter, 가장 상세한 건 GA4, 검색 유입의 핵심은 Search Console — 셋 다 무료다.
- 새 사이트의 "사이트맵 가져올 수 없음"은 대개 크롤링 대기 상태일 뿐, 며칠 기다리면 풀린다.
