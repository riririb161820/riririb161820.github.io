---
title: "클로드 코드 작업을 블로그로 자동 발행하기 — 조사부터 구축, 운영까지 한 세션의 기록"
date: 2026-06-11 13:10:00 +0900
categories: [개발, 자동화]
tags: [claude-code, github-pages, jekyll, chirpy, adsense, blog-automation, flux]
description: 클로드 코드 작업을 블로그로 자동 발행하는 파이프라인을 한 세션 만에 구축했다. 티스토리 API 종료, Vercel 약관, Jekyll 미래 날짜 404, 로컬 FLUX 썸네일 생성까지 — 조사부터 운영 루틴 완성까지의 전 과정.
image:
  path: /assets/img/posts/claude-code-blog-automation-pipeline.png
  alt: 터미널의 코드가 git을 거쳐 블로그 글로 발행되는 자동화 파이프라인
---

## 문제

클로드 코드(Claude Code)로 작업한 내용을 매번 수동으로 블로그에 옮기는 게 번거로웠다.
원하는 것은 네 가지였다.

- 작업이 끝나면 "문제 → 원인 → 해결 → 사용 기술" 구조의 글로 자동 정리
- 명령 한 번으로 블로그에 발행
- 별도 API 비용 없이 (Claude API 미사용, 구독만으로)
- 장기적으로 구글 애드센스 수익화

처음 계획은 티스토리나 워드프레스에 API로 글을 올리는 것이었다.

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

## 해결 과정

결론: **GitHub Pages(무료) + Jekyll Chirpy 테마 + 클로드 코드 스킬**. 발행은 git push가 전부라 API 키도 필요 없다.

**1) 저장소 생성 — Chirpy 스타터 템플릿 사용**

```bash
gh repo create 아이디.github.io --template cotes2020/chirpy-starter --public --clone
```

**2) Pages 빌드 방식을 workflow로 변경**

저장소를 만들면 Pages가 legacy(브랜치 빌드)로 켜지는데, Chirpy는 GitHub Actions 빌드가 필요하다.

```bash
gh api -X PUT repos/아이디/아이디.github.io/pages -f build_type=workflow
```

**3) `_config.yml` 설정** — `lang: ko-KR`, `timezone: Asia/Seoul`, 블로그 제목·URL·GitHub 계정 입력 후 push.

**4) 발행 자동화 — 클로드 코드 스킬 작성**

`~/.claude/skills/blog-post/SKILL.md`에 절차를 정의했다: 세션에서 문제·원인·해결·기술 추출 →
초안을 채팅으로 보여주고 → 민감정보·사실관계 검수 후 승인 받으면 → `_posts/`에 마크다운 작성 →
git push → 빌드·URL 200 확인. 클로드 코드 스킬은 마크다운 파일 하나라서, 운영하며 얻는
교훈을 그 자리에서 규칙으로 추가할 수 있다 — 아래 트러블슈팅들이 실제로 그렇게 반영됐다.

**5) 트러블슈팅: 빌드는 성공인데 글만 404**

첫 글을 push하자 GitHub Actions는 success인데 글 URL이 404였다. 원인은 front matter의
`date`를 실제 시각보다 미래로 적은 것. Jekyll은 빌드 시점 기준 미래 날짜 글을 **경고 없이 조용히
제외**한다. 글 날짜(13:40)가 빌드 시각(13:29)보다 10분 미래였을 뿐인데 글이 통째로 빠졌다.

```bash
# 발행 전 현재 시각 확인 — date는 반드시 이보다 과거로
date "+%Y-%m-%d %H:%M:%S %z"
```

날짜를 과거로 고쳐 다시 push하니 200. "빌드 성공 + 글 404" 조합이면 가장 먼저 날짜를 의심하자.
(Jekyll에는 미래 글을 노출하는 `future` 옵션도 있지만, 발행 시각을 과거로 적는 쪽이 부작용이 없다.)

**6) 대표 이미지 — 로컬 FLUX로 생성**

썸네일·소셜 미리보기(og:image)용 이미지는 로컬 GPU에서 FLUX.1 schnell로 생성했다 (비용 0원).
소셜 미리보기 표준 비율 1.91:1에 맞춰 1216x640 (64의 배수)로 만들고, Chirpy front matter의
`image:` 항목에 연결하면 글 상단과 공유 미리보기에 모두 쓰인다.

**7) 이미지 정책 — 실제 캡처 우선, 생성은 폴백**

운영하다 보면 작업 중 화면 캡처(특히 수정 전/후 비교)가 생성 이미지보다 글의 증거력이 훨씬 높다.
그래서 정책을 뒤집었다: 작업 세션 중 시각적 before/after가 생기면 공개 저장소 **밖의** 스테이징
폴더에 모아두고, 발행 시 민감정보 검수를 통과한 것만 블로그 저장소로 복사한다. 캡처가 없는
터미널 작업(이 글처럼)일 때만 FLUX로 생성한다. 캡처를 바로 공개 저장소에 넣지 않는 이유는
터미널·화면 캡처에 토큰이나 내부 데이터가 찍히기 쉽기 때문이다.

## 사용한 기술

- **GitHub Pages + GitHub Actions** — 무료 정적 호스팅과 자동 빌드·배포
- **Jekyll Chirpy 테마** — sitemap, RSS, SEO 메타태그, 검색, 다크모드 내장
- **gh CLI** — 저장소 생성, Pages 설정, 빌드 모니터링까지 터미널에서 처리
- **Public Suffix List** — 서브도메인이 독립 사이트로 취급되는 근거
- **클로드 코드 스킬** — 반복 워크플로(요약→검수→발행)를 마크다운 파일 하나로 정의, 운영 교훈을 누적
- **FLUX.1 schnell (로컬 ComfyUI)** — 무료 썸네일 생성

## 정리

- 티스토리는 API 종료, Vercel 무료 플랜은 약관이 광고를 금지 — 무료 + 애드센스 + 자동화 조합은 GitHub Pages가 정답이었다.
- `github.io`는 PSL 등재 덕분에 서브도메인 그대로 애드센스 승인이 가능하다 — 비용 0원 경로.
- 빌드 성공인데 글이 404면 front matter의 미래 날짜를 의심하자. Jekyll은 미래 글을 조용히 제외한다.
- 파이프라인이 "마크다운 + git push"로 단순해지면, 스킬 하나로 블로그 자동화가 끝난다 — 그리고 운영하며 배운 것을 스킬에 계속 적어 넣는 것이 자동화의 본체다.
