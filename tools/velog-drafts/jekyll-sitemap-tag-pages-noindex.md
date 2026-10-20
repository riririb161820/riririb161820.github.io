Jekyll 플러그인으로 태그 페이지에 `noindex` 메타를 넣었다. 빌드가 성공했고 에러도 없었다.

그런데 배포된 페이지를 열어보니 **메타 태그가 없었다.**

코드는 이랬다.

```ruby
page.output = page.output.sub("</head>", "#{NOINDEX_META}</head>")
```

가장 흔한 방식이다. 문제는 이 문자열이 최종 출력에 **존재하지 않는다**는 것이었다.

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

![처음 쓴 코드는 </head>를 찾지만 압축으로 사라져 실패하고, 여는 head 뒤에 넣는 방식으로 고친 비교](https://riririb.com/assets/img/posts/jekyll-sitemap-tag-pages-noindex-trap.webp)

그래서 **여는 `<head>` 뒤**에 넣는 방식으로 바꿨다.

```ruby
page.output = page.output.sub("<head>", "<head>#{NOINDEX_META}")
```

여는 태그는 압축해도 사라지지 않는다.

> **빌드 성공은 적용 성공이 아니다.** `sub`·`gsub`처럼 "없으면 조용히 넘어가는" 치환은 실패해도 로그에 아무것도 안 남는다. 배포된 HTML을 직접 받아 확인해야 한다.

확인은 `curl`로 한다.

```bash
curl -s https://riririb.com/tags/seo/ | grep -o '<meta name="robots"[^>]*>'
# <meta name="robots" content="noindex, follow">
```

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[사이트맵의 68%가 태그 페이지였다 — Jekyll 저가치 URL 걷어내기](https://riririb.com/posts/jekyll-sitemap-tag-pages-noindex/)**
