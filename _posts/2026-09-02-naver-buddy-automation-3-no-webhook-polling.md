---
title: "네이버 블로그엔 웹훅이 없다 (3) — 이웃새글을 폴링으로 받는 법"
headline: "웹훅 없이 새글 감지"
date: 2026-09-02 22:30:00 +0900
categories: [개발, 자동화]
tags: [naver-buddy-automation, 네이버블로그, 웹훅, 폴링, rss]
description: "이웃 새 글이 올라오면 웹훅으로 받고 싶었다. 네이버 공식 API 카탈로그 전체를 확인한 결과 웹훅은 존재하지 않았다. 대신 쓸 수 있는 폴링 소스 3개를 실측 비교하고, RSS가 왜 가장 비싼 선택인지 정리했다."
image:
  path: /assets/img/posts/naver-buddy-automation-3-no-webhook-polling-hero.png
  alt: 네이버에는 웹훅이 없어 폴링으로 대체하는 구조와 세 가지 폴링 소스의 크기 비교
---

> **시리즈 「네이버 서이추 자동화」**
> [1편](/posts/naver-buddy-automation-1-js-vs-real-click/) · [2편](/posts/naver-buddy-automation-2-cafe-api-callback-url/) · **3편 (현재 글)** · [4편 토큰 99% 줄이기](/posts/naver-buddy-automation-4-browser-token-diet/) · [5편 자동화 티는 어디서 나는가](/posts/naver-buddy-automation-5-automation-tell/)
{: .prompt-info }

## 문제

서로이웃 관계에서 가장 중요한 규범은 **답방**이다. 이웃이 새 글을 올리면 찾아가서 공감하고 댓글을 남기는 것. 이걸 자동화하려면 **"이웃이 새 글을 올렸다"는 사건을 알아야** 한다.

가장 깔끔한 건 웹훅이다. 새 글이 등록되면 내 엔드포인트로 POST가 오는 구조. 그래서 찾아봤다.

## 원인

### 웹훅은 존재하지 않는다

[네이버 오픈API 카탈로그](https://developers.naver.com/docs/common/openapiguide/apilist.md) 문서 전체를 확인했다. 제공되는 API는 이것이 전부다.

| 구분 | API |
|---|---|
| 로그인 방식 | 네이버 로그인 · 카페(가입·글쓰기) · 캘린더 |
| 비로그인 방식 | 데이터랩 · 검색 · 이미지/음성 캡차 · 공유하기 · 오픈메인 |

**문서 전문에서 `웹훅` / `webhook` / `푸시` / `구독` / `콜백` 이 한 번도 나오지 않는다.**

블로그 관련은 검색 API(`/v1/search/blog`) 하나뿐이고, **이웃새글 API 자체가 없다.** 애초에 이벤트 푸시라는 구조가 존재하지 않는다. 전부 요청-응답 방식이다.

> 없는 걸 찾느라 시간을 쓰지 않으려면, 추측하지 말고 **공식 카탈로그를 처음에 통째로 읽는 게** 빠르다.
{: .prompt-tip }

## 해결 과정

웹훅이 없으면 **폴링으로 웹훅을 만들면 된다.** 문제는 "무엇을 폴링할 것인가"였다. 후보 3개를 전부 실측했다.

### 후보 1 — 이웃새글 피드 API (정답)

이웃새글 페이지의 네트워크를 뜯어서 내부 API를 찾았다.

```
GET https://section.blog.naver.com/ajax/BuddyPostList.naver?page=1&groupId=0
```

- 로그인 필요 (`credentials: 'include'`)
- referer를 `https://section.blog.naver.com/BlogHome.naver` 로 줄 것

응답 구조는 이렇다.

```
{ buddyPostList: [...], buddyPostTotalCount, hasBuddy, hasBuddyPost }
```

각 항목에 들어 있는 필드:

```
blogId · logNo · nickName · blogName · postUrl · title · briefContents
addDate(ms 타임스탬프) · sympathyCnt · commentCnt · thumbnails · profileUrl
```

**`addDate`가 밀리초 타임스탬프로 온다.** 이게 결정적이다. 마지막으로 처리한 시각만 저장해 두면 신규 항목을 정확히 골라낼 수 있다.

그리고 무엇보다 **내 이웃 전체를 한 번의 호출로** 가져온다. 이웃이 몇 명이든 요청 1회다.

### 후보 2 — 개별 블로그 RSS

```
https://rss.blog.naver.com/{blogId}.xml
```

로그인 없이 동작한다. 표준 RSS 2.0이다. 여기까진 좋았는데 크기를 재보고 접었다.

### 후보 3 — 개별 블로그 최근글 JSON

```
https://blog.naver.com/PostTitleListAsync.naver?blogId={id}&countPerPage=5
```

로그인 불필요. 제목·작성일·댓글수만 주는 가장 가벼운 조회다.

### 실측 — RSS는 가장 비싼 선택이었다

같은 블로그, 같은 글 기준으로 응답 크기를 쟀다.

| 소스 | 크기 |
|---|---:|
| RSS 전문 `rss.blog.naver.com/{id}.xml` | **104,691 bytes** |
| PostView 원본 HTML (1건) | 207,693 bytes |
| 최근글 목록 JSON (5건, 메타만) | **4,485 bytes** |
| 브라우저 `.se-main-container` innerText (1건) | **400~3,300자** |

RSS는 **최근 글 여러 편의 본문 전문**을 CDATA로 통째로 실어 보낸다. 그래서 104KB다.

우리 루틴은 항상 **"최신 1편"** 만 본다. 그런데 RSS를 쓰면 20편치를 받는 셈이다. **본문을 직접 읽는 것보다 30~200배 비싸다.**

RSS가 유리한 경우는 딱 하나다 — "한 블로그의 여러 글을 한꺼번에" 필요할 때. 우리 경우가 아니었다.

![RSS 104KB, PostView HTML 207KB, 목록 JSON 4.4KB, 본문 innerText 3KB를 나란히 비교한 막대](/assets/img/posts/naver-buddy-automation-3-no-webhook-polling-size.png)
_최신 1편만 필요한데 RSS는 20편치를 실어 보낸다_

### 셀프 웹훅 구조

```
N분마다 BuddyPostList 폴링
  → 저장해둔 lastSeenAddDate 보다 큰 항목만 = 신규 이웃새글
  → 원하는 곳으로 전달 (알림 / 답방 루틴 트리거)
  → lastSeenAddDate 갱신
```

폴링 주기는 **5~15분**으로 잡았다. 이웃새글은 초 단위 실시간성이 필요 없고, 과도한 폴링은 어뷰징으로 보일 수 있다.

## 사용한 기술

- **`BuddyPostList.naver`** — 이웃새글 피드 내부 API. 이웃 전체를 1회 호출로
- **타임스탬프 기반 델타 감지** — `addDate`(ms)를 커서로 써서 신규만 추출
- **DevTools 네트워크 패널** — 공개 문서에 없는 내부 엔드포인트를 찾는 실질적 방법
- **응답 크기 실측** — "RSS가 편하다"는 통념을 숫자로 뒤집음

> **🧭 기획자·사업자라면**
> - **"웹훅 지원"은 연동 견적을 가르는 항목이다.** 웹훅이 있으면 이벤트 기반으로 싸게 끝나지만, 없으면 폴링 인프라(스케줄러·상태 저장·중복 방지)를 직접 만들어야 한다. 외부 서비스 연동을 검토할 때 **가장 먼저 확인할 스펙**이다.
> - **표준 규격이 항상 저렴한 건 아니다.** RSS는 표준이라 붙이기 쉽지만 이 경우 30~200배 비쌌다. **"우리가 실제로 필요한 데이터 단위"** 로 비용을 재봐야 한다.
> - **폴링 주기는 비용이자 리스크다.** 짧으면 서버 부담과 어뷰징 판정, 길면 반응이 느려진다. 실시간성이 정말 필요한 업무인지부터 되물어야 한다.
{: .prompt-tip }

## 정리

- 네이버는 블로그 웹훅을 제공하지 않는다. 공식 카탈로그 전문에 웹훅·푸시·구독 개념이 아예 없다.
- 대안은 **`BuddyPostList.naver` 폴링**이다. 이웃 전체를 1회 호출로 가져오고, `addDate`(ms)로 신규만 정확히 걸러낸다.
- **RSS는 쓰지 말 것.** 104KB 대 3KB — 최신 1편만 필요한 루틴에서는 30~200배 손해다.
