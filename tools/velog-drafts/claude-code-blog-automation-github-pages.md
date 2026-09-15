클로드 코드로 작업한 내용을 블로그에 옮기는 걸 자동화하려다 알게 된 제약들을 정리한다.

처음 계획은 단순했다. 티스토리나 워드프레스에 API로 글을 쏘면 되겠거니 했다. 그런데 파고들수록 선택지가 하나씩 지워졌다. 티스토리는 API를 닫았고, Vercel은 약관이 걸렸고, Jekyll은 날짜 하나 잘못 적으면 글이 404가 됐다.

**결론부터 말하면 GitHub Pages + Jekyll Chirpy로 갔다.** 왜 그렇게 됐는지, 조사 단계에서 부딪힌 제약들을 아래에 적는다.

## 원인 (조사하며 알게 된 제약들)

자동 발행 경로를 조사하면서 플랫폼별 제약이 하나씩 드러났다.

- **티스토리**: Open API가 2024년 2월에 완전 종료되어 글쓰기 API 자체가 없다. 자동화하려면 브라우저 조작뿐인데, UI 변경에 취약하고 약관 리스크가 있다.
- **wordpress.com 무료 플랜**: 애드센스를 달 수 없다.
- **설치형 워드프레스**: REST API + Application Password로 자동화는 깔끔하지만, 호스팅 비용이 연 6~12만 원 발생한다.
- **Vercel 무료(Hobby) 플랜**: Fair Use 정책이 "Google AdSense를 포함한 광고 게재"를 상업적 사용으로 명시해 금지한다. 광고를 달려면 Pro(월 $20)가 필요하다.

반전은 GitHub Pages였다. `아이디.github.io`는 "정식 도메인"이 아닌데도 애드센스가 붙은 실사례가 있다.
이유는 `github.io`가 **Public Suffix List(PSL)** 에 등재되어 있기 때문이다. PSL에 오른 주소의 바로 아래
서브도메인은 `.com` 아래 도메인과 동급의 독립 사이트로 취급되고, 구글도 이 목록을 따른다.
그래서 사이트 단위로 승인하는 애드센스에 개별 등록이 가능하다. `xxx.tistory.com` 블로그들이
애드센스를 다는 것과 같은 원리다.

```bash
# github.io가 PSL에 있는지 직접 확인
curl -s https://publicsuffix.org/list/public_suffix_list.dat | grep -n "^github.io$"
# → 13767:github.io
```

GitHub Pages 약관이 금지하는 것은 전자상거래·상용 SaaS 운영이고, 콘텐츠 블로그의 광고는 금지 목록에 없다.

조사 단계에서 도구의 함정도 하나 만났다. 다른 블로그에 애드센스가 실제로 붙어 있는지
LLM의 웹 페이지 요약 도구로 확인하려 했는데 "광고 없음"이라는 오답이 나왔다.
HTML→마크다운 변환 과정에서 스크립트 태그가 제거되기 때문이다. 원본 HTML을 받아 grep해야 정확하다.

```bash
curl -sL "https://대상사이트" | grep -oE "(adsbygoogle|googlesyndication|ca-pub-[0-9]+)"
```

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[클로드 코드 작업을 블로그로 자동 발행하기 — 조사부터 구축, 운영까지 한 세션의 기록](https://riririb.com/posts/claude-code-blog-automation-github-pages/)**
