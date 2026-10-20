블로그 색인이 안 되는 원인을 찾다가, 검색하면 가장 많이 나오는 조언을 만났다.

```text
새 글을 올리면 구글에 ping을 쏘세요
https://www.google.com/ping?sitemap=https://example.com/sitemap.xml
```

블로그 글, 플러그인 문서, AI 답변까지 전부 이걸 권했다. 그래서 직접 호출해 봤다.

결론부터 말하면 **두 엔진 다 이 방식을 버렸다.**

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

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[google.com/ping은 2023년에 죽었다 — 새 글을 검색엔진에 알리는 현재의 방법](https://riririb.com/posts/google-sitemap-ping-deprecated-indexnow/)**
