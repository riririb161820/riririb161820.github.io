---
title: "사이트맵의 68%가 태그 페이지였다 — Jekyll 저가치 URL 걷어내기 (사이트맵 2편)"
headline: "사이트맵 135→38"
highlight: "135→38"
date: 2026-10-19 09:12:00 +0900
categories: [개발, 운영]
tags: [jekyll, chirpy, sitemap, seo, github-pages]
description: "jekyll-archives는 태그마다 페이지를 하나씩 만든다. 사이트맵 135개 URL 중 92개가 태그 목록이었고 그중 68개는 글이 1편뿐이었다. 플러그인으로 걷어내 38개로 줄인 과정과, 압축 때문에 noindex 주입이 조용히 실패했던 함정."
image:
  path: /assets/img/posts/jekyll-sitemap-tag-pages-noindex-hero.webp
  alt: 사이트맵 135개 중 92개가 태그 페이지였고 적용 후 38개로 줄어든 구성 변화 그래프
---

> **사이트맵 시리즈**
> 1편 — [GitHub Pages 사이트맵이 3개월간 '가져올 수 없음'이던 진짜 이유](/posts/github-pages-sitemap-couldnt-fetch-custom-domain/)
> **2편 — 사이트맵의 68%가 태그 페이지였다 ← 지금 보는 글**
{: .prompt-info }

## 문제

[1편](/posts/github-pages-sitemap-couldnt-fetch-custom-domain/)에서 구글이 사이트맵을 3개월간 "가져올 수 없음"으로 뒀던 원인을 찾았다. 크롤 예산이 배정되지 않은 것이었고, 커스텀 도메인으로 해결했다.

그 과정에서 사이트맵을 뜯어보다 따로 발견한 게 있다. **URL 135개 중 실제 글은 38개뿐이었다.**

나머지 97개는 뭐였을까.

```text
/tags/seo/
/tags/jekyll/
/tags/github-pages/
/tags/chirpy/
...
```

**태그 목록 페이지가 92개**였다. 전체의 68%다. 더 나쁜 건 그중 **68개가 글이 딱 1편만 걸린 페이지**였다는 것이다.

글 한 편에 태그를 5개 달면 태그 페이지가 5개 생긴다. 그 글이 유일한 글인 태그라면, **본문이 하나도 없고 글 제목 하나만 있는 페이지**가 사이트맵에 올라간다.

## 원인 — jekyll-archives는 원래 그렇게 동작한다

Chirpy 테마는 `jekyll-archives` 플러그인을 쓴다. `_config.yml`에 이렇게 설정돼 있다.

```yaml
jekyll-archives:
  enabled: [categories, tags]
  permalinks:
    tag: /tags/:name/
    category: /categories/:name/
```

이게 **태그마다 페이지를 하나씩 생성**한다. 사용자가 태그를 눌러 탐색하려면 필요한 페이지라 기능 자체는 정상이다.

문제는 `jekyll-sitemap`이 **생성된 페이지를 전부 사이트맵에 넣는다**는 것이다. 둘 다 각자 맞게 동작하는데, 합쳐지면 사이트맵이 저가치 URL로 가득 찬다.

### 왜 신경 써야 하나

크롤 예산이 넉넉한 사이트라면 무시해도 된다. 구글이 알아서 걸러낸다.

**신생 사이트는 다르다.** 1편에서 확인한 크롤링 통계가 이랬다.

| 항목 | 값 |
|---|---|
| 총 크롤링 요청(90일) | 48건 |
| 목적: 검색(신규 발견) | 2% |

90일에 48건이면 하루 0.5건이다. 이 희소한 예산을 **글 1편짜리 태그 페이지가 먼저 가져가면** 정작 글이 뒤로 밀린다. 사이트맵은 "여기부터 봐 달라"는 우선순위 신호인데, 그 신호의 68%가 노이즈였던 셈이다.

## 해결 — 플러그인 하나로 걷어내기

테마가 **gem 기반**이라 레이아웃 파일이 저장소에 없다. `_layouts/`를 오버라이드하면 테마 업데이트 때마다 깨진다. 그래서 **Jekyll Hooks로 출력만 손대는** 방식을 썼다.

![jekyll-archives가 만든 태그 페이지를 pre_render에서 sitemap:false, post_render에서 noindex,follow로 처리하는 흐름](/assets/img/posts/jekyll-sitemap-tag-pages-noindex-flow.webp)

`_plugins/filter-archive-pages.rb`:

```ruby
NOINDEX_META = '<meta name="robots" content="noindex, follow">'

def archive_listing?(page)
  url = page.url.to_s
  return false if url == "/tags/" || url == "/categories/"

  url.start_with?("/tags/", "/categories/")
end

# 생성기(jekyll-archives)가 돈 뒤, 렌더 전에 사이트맵 제외 표시를 붙인다.
Jekyll::Hooks.register :site, :pre_render do |site|
  site.pages.each do |page|
    page.data["sitemap"] = false if archive_listing?(page)
  end
end

# 렌더된 HTML의 <head> 바로 뒤에 noindex 메타를 삽입한다.
Jekyll::Hooks.register :site, :post_render do |site|
  site.pages.each do |page|
    next unless archive_listing?(page)
    next if page.output.nil? || page.output.include?(NOINDEX_META)

    page.output = page.output.sub("<head>", "<head>#{NOINDEX_META}")
  end
end
```

세 가지를 의도적으로 갈랐다.

**① `sitemap: false`와 `noindex`를 둘 다 건다.** 사이트맵에서 빼는 것만으로는 색인을 막지 못한다. 사이트맵은 "봐 달라"는 요청이지 "보지 마라"가 아니다. 내부 링크를 타고 들어오면 그대로 색인된다.

**② `noindex`가 아니라 `noindex, follow`다.** 색인은 막되 **크롤러가 링크는 계속 따라가게** 한다. 태그 페이지는 글로 가는 통로라서, `nofollow`까지 걸면 글 발견 경로를 스스로 끊는 꼴이 된다.

**③ 탭 페이지 `/tags/`·`/categories/`는 남긴다.** 전체 태그를 모아 보여주는 이 두 페이지는 허브 역할이라 색인 가치가 있다. 개별 태그 페이지만 제외한다.

사용자가 보는 동작은 **아무것도 바뀌지 않는다.** 태그를 눌러 탐색하는 흐름은 그대로다.

## 함정 — 압축 때문에 조용히 실패했다

처음 쓴 코드는 이랬다.

```ruby
page.output = page.output.sub("</head>", "#{NOINDEX_META}</head>")
```

`</head>` 앞에 끼워 넣는, 가장 흔한 방식이다. **빌드는 성공했고 에러도 없었다.** 그런데 배포된 페이지를 열어보니 메타 태그가 없었다.

원인은 Chirpy의 HTML 압축 설정이었다.

```yaml
compress_html:
  clippings: all
  endings: all
```

`endings: all`이 **생략 가능한 종료 태그를 제거**한다. `</head>`는 HTML 명세상 생략 가능해서 최종 출력에서 사라진다. 찾을 문자열이 없으니 `sub`는 **아무것도 바꾸지 않고 조용히 통과**한다. 예외도 안 난다.

![처음 쓴 코드는 </head>를 찾지만 압축으로 사라져 실패하고, 여는 head 뒤에 넣는 방식으로 고친 비교](/assets/img/posts/jekyll-sitemap-tag-pages-noindex-trap.webp)

그래서 **여는 `<head>` 뒤**에 넣는 방식으로 바꿨다.

```ruby
page.output = page.output.sub("<head>", "<head>#{NOINDEX_META}")
```

여는 태그는 압축해도 사라지지 않는다.

> **빌드 성공은 적용 성공이 아니다.** `sub`·`gsub`처럼 "없으면 조용히 넘어가는" 치환은 실패해도 로그에 아무것도 안 남는다. 배포된 HTML을 직접 받아 확인해야 한다.
{: .prompt-warning }

확인은 `curl`로 한다.

```bash
curl -s https://riririb.com/tags/seo/ | grep -o '<meta name="robots"[^>]*>'
# <meta name="robots" content="noindex, follow">
```

## 결과

| | 적용 전 | 적용 후 |
|---|---|---|
| 사이트맵 URL | 135개 | **38개** |
| 그중 태그 목록 | 92개 (68%) | **0개** |
| `/tags/` 탭 페이지 | 포함 | 포함 (의도) |

오늘 다시 재보니 글이 늘어 사이트맵은 50개가 됐다. 구성은 **글 38개 + 그 외 12개**(홈·탭·피드 등)로, 태그 페이지는 `/tags/` 탭 하나만 남아 있다.

```bash
curl -s https://riririb.com/sitemap.xml | grep -o '<loc>[^<]*tags[^<]*</loc>'
# <loc>https://riririb.com/tags/</loc>
```

**다만 이 작업만으로 색인이 풀리지는 않았다.** 1편에서 적었듯 사이트맵은 여전히 "가져올 수 없음"이었고, 진짜 해법은 커스텀 도메인이었다. 이 글의 작업은 **사이트맵 품질 개선**이지 색인 문제의 해결책이 아니다. 순서를 섞어 읽으면 헛수고한다.

> **🧭 기획자·사업자라면**
> **도구를 합칠 때 생기는 문제는 각 도구의 버그가 아니다.** jekyll-archives도 jekyll-sitemap도 각자 정상 동작했다. 합쳐졌을 때의 결과를 아무도 책임지지 않았을 뿐이다. 통합 지점을 보는 사람이 따로 있어야 한다.
> **그리고 "에러 없음"을 성공 신호로 쓰면 안 된다.** 이번 함정은 빌드 로그가 깨끗했다. 성공 판정 기준을 *실행됐는가*가 아니라 *결과물이 바뀌었는가*로 두면 이런 게 걸러진다. 배포 파이프라인에 산출물 검증 한 줄을 넣는 비용이 훨씬 싸다.
{: .prompt-tip }

## 사용한 기술

- **jekyll-archives** — 태그·카테고리별 목록 페이지 생성. `_config.yml`의 `jekyll-archives.enabled`로 제어한다.
- **Jekyll Hooks** — 빌드 단계에 끼어드는 훅. `:site, :pre_render`는 렌더 전(front matter 조작), `:site, :post_render`는 렌더 후(HTML 문자열 조작)에 돈다. **gem 테마를 오버라이드하지 않고 손대는 표준 경로다.**
- **`sitemap: false`** — jekyll-sitemap이 읽는 front matter 플래그. 페이지 단위 제외.
- **`noindex, follow`** — 색인은 막고 링크 추적은 허용. 통로 역할 페이지에 쓴다.
- **`compress_html`의 `endings: all`** — 생략 가능한 종료 태그 제거. 편의 기능이지만 문자열 치환을 조용히 깨뜨린다.

## 정리

- 사이트맵에 **글보다 목록 페이지가 많다면** 신생 사이트에선 크롤 예산을 깎아먹는다. 한 번 세어볼 가치가 있다.
- 사이트맵 제외와 `noindex`는 **다른 일**이다. 둘 다 걸어야 하고, 통로 페이지는 `follow`를 남긴다.
- HTML 압축이 켜져 있으면 **`</head>` 같은 종료 태그가 사라진다.** 문자열 치환은 여는 태그를 기준으로 하고, 배포본을 `curl`로 확인한다.
