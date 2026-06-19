---
title: "블로그 글을 인스타그램에 자동 발행하기 (2) — 카드뉴스 자동 생성 (AI로 글자 넣으면 깨진다)"
date: 2026-06-19 10:08:00 +0900
categories: [개발, 자동화]
tags: [instagram, automation, html, chrome-headless, blog-to-insta]
image:
  path: /assets/img/posts/blog-to-insta-2-card.png
  alt: 블로그→인스타 자동화 시리즈 진행도 — 2편 카드 자동 생성 단계 강조
description: 블로그 글을 인스타 카드뉴스로 자동 변환하기. AI 이미지 생성으로 글자를 넣으면 깨지는 문제를 HTML 템플릿+Chrome 헤드리스 캡처로 해결한 방법과 함정(폰트 로딩·글자수). (시리즈 2편)
---

> **🗺 시리즈: 블로그 → 인스타 자동화** — 지금은 **② 카드 자동 생성**
>
> ← 이전 편: [(1) 전체 설계와 도구 선택](/posts/blog-to-instagram-automation-1-design/)
>
> ① 전체 설계 · **②** 카드 자동 생성 *(현재 글)* · ③ 디자인 · ④ 발행 · ⑤ DM의 벽
{: .prompt-info }

## 문제

블로그 글을 인스타 카드로 바꾸려면 카드에 **한글 텍스트**를 넣어야 한다. 처음엔 "어차피 이미지니까 AI로 카드를 통째로 생성하면 되겠지" 했는데 — **글자가 깨졌다.** 제목도 본문도, 알아볼 수 없는 형태로 뭉개졌다.

![AI 생성은 글자가 깨지고, HTML 렌더는 선명하다](/assets/img/posts/body-blog-to-insta-2-card.png)

## 원인 — 왜 AI 생성 카드는 글자가 깨지나

이미지 생성 모델(FLUX 등)은 픽셀을 "그리는" 방식이라 **정확한 글자 형태를 만들지 못한다.** 영문도 자주 깨지고 **한글은 더 심하다**(받침·복잡한 자소가 뭉개진다). 카드뉴스의 핵심은 "읽히는 텍스트"인데, 그게 깨지면 카드 자체가 무용지물이다.

## 해결 과정 — 텍스트는 HTML로 그리고 Chrome으로 캡처

핵심 전환은 이거였다. 카드를 *이미지 생성*이 아니라 **웹페이지 렌더링**으로 만든다.

1. HTML/CSS로 카드 한 장을 **1080×1350**으로 디자인 — 텍스트는 웹폰트라 100% 선명
2. 슬라이드 내용(JSON)을 템플릿에 주입
3. **Chrome 헤드리스로 스크린샷** → PNG
4. 한글은 **Pretendard** 웹폰트로 일관성 확보
5. 배경 일러스트가 필요할 때만 로컬 FLUX로 생성(글자 없는 이미지로)

```bash
chrome --headless --window-size=1080,1350 \
  --virtual-time-budget=3000 \
  --screenshot=slide.png "file://card.html"
```

### 빠뜨리기 쉬운 함정 두 가지

- **폰트 로딩 대기**: `--virtual-time-budget` 을 안 주면 **웹폰트가 적용되기 전에 캡처**된다. HTML로 그렸는데도 글자가 기본 폰트로 나오거나 깨져 보이는 건 십중팔구 이것 때문이다.
- **글자수와 박스 넘침**: 카드 폭은 고정(1080px)이라 제목이 길면 박스를 넘는다. 요약으로 욱여넣지 말고 **다음 슬라이드로 분리**하는 규칙을 두면 레이아웃이 안 깨진다.

결과적으로 블로그 글 한 편이 **글자 하나 안 깨진 카드 6장 PNG**로 자동 생성된다.

## 사용한 기술

- **Chrome 헤드리스 `--screenshot`** — 별도 설치 없이 OS에 이미 있는 무료 렌더 엔진
- **HTML/CSS 템플릿**(데이터 주입식) · **Pretendard**(한글) · **Node.js**(반복 렌더) · 로컬 FLUX(배경만)

> **🧭 기획자·사업자라면**
> - "AI가 다 해준다"는 환상에 주의 — **AI가 잘하는 일(배경 이미지)과 못하는 일(정확한 텍스트)을 구분**해 배치하는 게 품질을 가른다.
> - 카드 디자인을 외주/툴 구독 대신 **템플릿 1개 + 자동 렌더**로 바꾸면, 글이 늘어도 한계비용이 0에 수렴한다.
{: .prompt-tip }

## 정리

- 카드의 글자를 AI 이미지 생성으로 넣지 마라 — 깨진다.
- 텍스트는 HTML로 그리고 Chrome 헤드리스로 캡처 = 무료·선명·자동.
- 폰트 로딩 대기(`--virtual-time-budget`)와 글자수 분리만 챙기면 레이아웃이 안 깨진다.

### 시리즈 목차

1. [전체 설계와 도구 선택](/posts/blog-to-instagram-automation-1-design/)
2. **카드뉴스 자동 생성** (현재 글)
3. [벤치마킹 vs 카피, 나만의 디자인](/posts/blog-to-instagram-automation-3-design/)
4. [Composio로 자동 발행](/posts/blog-to-instagram-automation-4-publish/)
5. [DM 자동화의 벽](/posts/blog-to-instagram-automation-5-dm-wall/)
