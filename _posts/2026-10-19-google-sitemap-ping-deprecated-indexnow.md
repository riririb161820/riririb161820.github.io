---
title: "google.com/ping은 2023년에 죽었다 — 새 글을 검색엔진에 알리는 현재의 방법"
headline: "ping 폐지, 그럼 뭘 쓰나"
highlight: "ping 폐지"
date: 2026-10-19 13:20:00 +0900
categories: [개발, 운영]
tags: [seo, indexnow, sitemap, jekyll, github-pages]
description: "글을 올리면 구글에 ping을 쏘라는 조언이 아직도 돌아다닌다. 직접 호출해 보면 404다. 구글은 2023년 6월에 폐지했고 빙은 410으로 응답한다. 폐지 이유와 현재의 대체 수단(구글은 lastmod, 나머지는 IndexNow)을 실측으로 정리했다."
image:
  path: /assets/img/posts/google-sitemap-ping-deprecated-indexnow-hero.webp
  alt: 구글 ping 404와 빙 ping 410, IndexNow 200 응답을 비교한 그래픽
---

> **이 글만 읽어도 됩니다.** `google.com/ping`이 왜 404인지와 지금 쓸 수 있는 대체 수단을 다룹니다.
> 이걸 조사하게 된 배경이 궁금하면 → [신생 블로그가 3개월간 구글에 안 잡힌 이유](/posts/github-pages-sitemap-couldnt-fetch-custom-domain/)
{: .prompt-info }

## 문제

블로그 색인이 안 되는 원인을 찾던 중, 검색하면 가장 많이 나오는 조언이 이것이었다.

```text
새 글을 올리면 구글에 ping을 쏘세요
https://www.google.com/ping?sitemap=https://example.com/sitemap.xml
```

블로그 글, 플러그인 문서, AI 답변까지 전부 이걸 권했다. 그래서 직접 호출해 봤다.

## 원인 — 두 엔드포인트 다 죽어 있다

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://www.google.com/ping?sitemap=https://riririb.com/sitemap.xml"
# 404
```

본문은 이렇게 돌아온다.

```html
<TITLE>Sitemaps ping is deprecated. See https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping.</TITLE>
<H1>Sitemaps ping is deprecated. ...</H1>
<H2>Error 404</H2>
```

구글이 404와 함께 **폐지 공지 링크를 본문에 적어 돌려준다.** 친절하지만, 바꿔 말하면 아직도 이 주소를 때리는 코드가 그만큼 많다는 뜻이다.

내친김에 빙도 재봤다.

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://www.bing.com/ping?sitemap=https://riririb.com/sitemap.xml"
# 410
```

**410 Gone.** 구글만의 일이 아니다. 두 엔진 다 이 방식을 버렸다.

### 구글이 밝힌 폐지 이유

공지 원문([Search Central Blog, 2023-06-26](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping))을 열어보면 이유가 적혀 있다.

> "Our internal studies—and also other search engines such as Bing—tell us that at this point these unauthenticated sitemap submissions are not very useful. **In fact, in the case of Google Search, the vast majority of the submissions lead to spam.**"

인증 없이 아무나 때릴 수 있는 엔드포인트라 **제출 대부분이 스팸**이었다는 것이다. 빙도 같은 판단이었다고 명시한다. 410이 그 결과다.

공지는 기존 코드에 대해서도 못 박는다.

> "Any existing code or plugins which use this endpoint will not cause problems for Google Search; you don't need to make any changes (but using the endpoint will also not do anything useful)."

**에러는 안 나지만 아무 효과도 없다.** 그래서 ping을 넣어둔 파이프라인은 조용히 돌면서 아무 일도 안 한다. 가장 알아차리기 어려운 종류의 고장이다.

## 해결 — 두 갈래로 갈린다

ping 하나로 모든 엔진에 알리던 시대가 끝나면서, **구글과 나머지의 방법이 달라졌다.**

![구글은 robots.txt·Search Console·lastmod로, 빙·네이버·Yandex는 IndexNow로 갈리는 구조 비교](/assets/img/posts/google-sitemap-ping-deprecated-indexnow-flow.webp)

### 구글 — 자동 통보 수단이 없다

공지가 권한 대체 수단은 셋이다.

> "You can still submit your sitemaps through robots.txt and Search Console"

여기에 **lastmod**가 더해진다.

> "nowadays lastmod is indeed useful in many cases and we're **using it as a signal for scheduling crawls** to URLs that we previously discovered"

즉 "새 글이 있다"를 능동적으로 쏘는 대신, **사이트맵에 정확한 수정 시각을 적어두면 구글이 크롤 일정에 반영**한다.

```bash
curl -s https://riririb.com/robots.txt
# Sitemap: https://riririb.com/sitemap.xml
```

`lastmod`는 Chirpy의 훅이 **git 이력에서 가져온다.** `_plugins/posts-lastmod-hook.rb`:

```ruby
Jekyll::Hooks.register :posts, :post_init do |post|
  commit_num = `git rev-list --count HEAD "#{ post.path }"`

  if commit_num.to_i > 1
    lastmod_date = `git log -1 --pretty="%ad" --date=iso "#{ post.path }"`
    post.data['last_modified_at'] = lastmod_date
  end
end
```

커밋이 2개 이상인 글, 즉 **발행 후 실제로 고친 글에만** 수정 시각을 붙인다. 이게 중요하다. 공지가 경고하는 지점이 바로 여기다.

> "it needs to **consistently match reality**: if your page changed 7 years ago, but you're telling us in the lastmod element that it changed yesterday, eventually we're not going to believe you anymore"

모든 글의 `lastmod`를 빌드할 때마다 갱신하면 "매일 전부 수정됨"이 되고, 그 신호는 곧 무시당한다. **안 고친 글에는 안 붙이는 게 맞다.**

> **구글에는 "새 글 알림" API가 없다.** Search Console의 URL 검사 → 색인 생성 요청은 **UI 클릭만 가능**하고 하루 10여 건 한도다. Indexing API가 있긴 하지만 채용공고·라이브 스트리밍 전용이라 일반 글에는 쓸 수 없다.
{: .prompt-warning }

### 빙·네이버·Yandex — IndexNow

나머지 엔진은 **IndexNow**라는 공통 프로토콜로 모였다. [indexnow.org](https://www.indexnow.org/) 문서에 참여 엔진으로 Bing·Naver·Yandex·Seznam이 적혀 있다. **구글은 없다.**

준비는 두 가지다.

**① 키 파일을 사이트 루트에 둔다.** 파일명이 키이고, 내용도 같은 키다.

```bash
curl -s https://riririb.com/5768935f2adfde244257b38d96dddc03.txt
# 5768935f2adfde244257b38d96dddc03
```

이게 소유권 증명이다. 아무나 남의 사이트 URL을 제출하지 못하게 막는 장치이고, ping이 스팸으로 무너진 자리를 메우는 부분이다.

**② 변경된 URL을 JSON으로 POST한다.**

```python
ENDPOINT = "https://api.indexnow.org/indexnow"

payload = {
    "host": HOST,
    "key": KEY,
    "keyLocation": KEY_LOCATION,
    "urlList": urls,
}
req = urllib.request.Request(
    ENDPOINT,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8"},
    method="POST",
)
```

표준 라이브러리만 쓴다. 발행 직후 실행하면 이렇게 돌아온다.

```text
[+] IndexNow 200 — 1개 URL 통보 완료
```

`200`과 `202` 둘 다 접수 성공이다. 실패 코드는 의미가 명확하다 — **`403`은 키 불일치**(키 파일이 없거나 내용이 다름), **`422`는 URL 불일치**(제출한 URL의 호스트가 `host` 필드와 다름).

## 함정 — 사이트맵을 XML로 파싱하려다 막혔다

인자 없이 실행하면 사이트맵 전체를 통보하도록 만들었다. 처음엔 당연히 `xml.etree`를 썼다.

그런데 이 맥에서 깨졌다. 더 고약한 건 **`import`는 통과한다**는 것이다.

```python
import xml.etree.ElementTree as ET   # 여기선 아무 일도 안 일어난다
ET.fromstring("<a><b>x</b></a>")     # 여기서 죽는다
```

```text
ImportError: dlopen(.../pyexpat.cpython-314-darwin.so):
  Symbol not found: _XML_SetAllocTrackerActivationThreshold
  Expected in: /usr/lib/libexpat.1.dylib
→ No module named expat; use SimpleXMLTreeBuilder instead
```

Homebrew로 설치한 Python 3.14의 `pyexpat`이 **새 libexpat에 맞춰 빌드됐는데, 실행 시엔 macOS 시스템의 구버전 `/usr/lib/libexpat.1.dylib`을 잡는다.** 심볼이 없어 로드에 실패한다. `xml.etree`는 파서를 **지연 로딩**해서, import 줄에서는 멀쩡해 보이다가 실제 파싱에서 터진다.

사이트맵은 형식이 고정돼 있어 `<loc>`만 뽑으면 되므로 정규식으로 갈았다.

```python
# 정규식으로 <loc>만 뽑는다 — 일부 환경의 파이썬은 pyexpat이 깨져 있어
# xml.etree로 파싱하면 죽는다. 사이트맵은 형식이 고정이라 안전하다.
urls = [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", raw, re.S)]
```

**일반적으로 XML을 정규식으로 파싱하는 건 나쁜 습관이다.** 다만 여기선 입력이 우리가 생성한 사이트맵 하나로 고정돼 있고, 뽑는 것도 단일 태그라 범위가 좁다. 그 조건을 주석에 남겨뒀다.

> **🧭 기획자·사업자라면**
> **이 글의 기법들은 색인 문제의 해법이 아니다.** 나는 사이트맵을 정리하고, ping을 조사하고, IndexNow를 붙였다. 전부 제대로 했고 전부 효과가 없었다. 3개월간 구글 색인은 홈 1페이지 그대로였다. **효과가 있었던 건 연 14,000원짜리 도메인 하나**였고, 연결 즉시 46페이지가 잡혔다([전말](/posts/github-pages-sitemap-couldnt-fetch-custom-domain/)).
> **순서를 틀리면 정교한 삽질이 된다.** 통보 수단은 *크롤 예산을 받는 사이트*에서만 의미가 있다. 받지 못하는 사이트에선 아무리 알려도 안 온다. 게다가 IndexNow에 **구글은 참여하지 않는다** — 유입의 대부분을 쥔 엔진에는 애초에 효과가 0인 작업이었다.
> **돈으로 끝나는 문제를 시간으로 풀지 마라.** 14,000원과 3개월을 맞바꿨다. 기술로 해결할 수 있을 것 같아 보이는 문제일수록, 먼저 **"이거 돈으로 끝나나?"** 를 한 번 물어볼 값어치가 있다.
{: .prompt-tip }

## 사용한 기술

- **IndexNow** — 변경된 URL을 검색엔진에 알리는 공통 프로토콜. 키 파일로 소유권을 증명한다. 참여: 빙·네이버·Yandex·Seznam. **구글 미참여.**
- **sitemap `lastmod`** — 구글이 크롤 일정 신호로 쓴다고 공식 확인한 요소. **실제와 일치해야** 신뢰를 유지한다.
- **Jekyll Hooks (`:posts, :post_init`)** — 글 단위 초기화 훅. git 이력을 읽어 `last_modified_at`을 채운다.
- **Search Console URL 검사** — 구글에 개별 URL 색인을 요청하는 유일한 경로. UI 전용, 하루 10여 건.
- **`pyexpat`** — CPython의 XML 파서 바인딩. 시스템 libexpat과 버전이 어긋나면 **파싱 시점에** 로드 실패한다.

## 정리

- `google.com/ping`은 **2023년 6월에 폐지**됐고 지금은 404다. 빙은 410이다. 이걸 권하는 글은 오래된 정보다.
- 구글에는 **새 글을 알리는 자동 수단이 없다.** robots.txt·Search Console·`lastmod`로 간접적으로 전할 뿐이고, `lastmod`는 거짓이면 신뢰를 잃는다.
- 빙·네이버·Yandex는 **IndexNow**로 통보한다. 키 파일 하나와 JSON POST면 끝이고, `200`/`202`가 접수 성공이다.
