---
title: "클로드 코드 작업을 블로그로 자동 발행하기 — 티스토리 API 종료 후 GitHub Pages로"
date: 2026-06-11 13:40:00 +0900
categories: [개발, 자동화]
tags: [claude-code, github-pages, jekyll, chirpy, adsense, blog-automation]
description: 클로드 코드로 작업한 내용을 블로그에 자동 발행하려다 티스토리 API 종료를 만났다. GitHub Pages + Jekyll Chirpy + 스킬 조합으로 비용 0원에 해결한 과정.
---

## 문제

클로드 코드(Claude Code)로 작업한 내용을 매번 수동으로 블로그에 옮기는 게 번거로웠다.
원하는 것은 세 가지였다.

- 작업이 끝나면 "문제 → 원인 → 해결 → 사용 기술" 구조의 글로 자동 정리
- 명령 한 번으로 블로그에 발행
- 별도 API 비용 없이 (Claude API 미사용, 구독만으로) + 장기적으로 애드센스 수익화

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

**4) 배포 확인**

```bash
curl -sL https://아이디.github.io | grep -oE "<title>[^<]*</title>"
curl -s -o /dev/null -w "%{http_code}" https://아이디.github.io/sitemap.xml   # 200
```

**5) 발행 자동화 — 클로드 코드 스킬**

`~/.claude/skills/blog-post/SKILL.md`에 절차를 정의했다: 세션에서 문제·원인·해결·기술 추출 →
초안을 채팅으로 보여주고 → 민감정보·사실관계 검수 후 승인 받으면 → `_posts/`에 마크다운 작성 →
git push → 빌드·URL 200 확인. 이 글이 그 스킬로 발행된 첫 글이다.

실패한 경로도 기록해 둔다. 처음엔 WebFetch류 도구로 애드센스 부착 여부를 확인하려 했는데,
HTML→마크다운 변환 과정에서 스크립트 태그가 제거되어 "광고 없음"이라는 오답이 나왔다.
원본 HTML을 받아 grep하는 것이 정확하다.

```bash
curl -sL "https://대상사이트" | grep -oE "(adsbygoogle|googlesyndication|ca-pub-[0-9]+)"
```

## 사용한 기술

- **GitHub Pages + GitHub Actions** — 무료 정적 호스팅과 자동 빌드·배포
- **Jekyll Chirpy 테마** — sitemap, RSS, SEO 메타태그, 검색, 다크모드 내장
- **gh CLI** — 저장소 생성, Pages 설정, 빌드 모니터링까지 터미널에서 처리
- **Public Suffix List** — 서브도메인이 독립 사이트로 취급되는 근거
- **클로드 코드 스킬** — 반복 워크플로(요약→검수→발행)를 마크다운 파일 하나로 정의

## 정리

- 티스토리는 API 종료로 자동화가 막혔고, Vercel 무료 플랜은 약관이 광고를 금지한다.
- `github.io`는 PSL 등재 덕분에 서브도메인 그대로 애드센스 승인이 가능하다 — 비용 0원 경로.
- 발행 파이프라인이 "마크다운 작성 + git push"로 단순해지면, LLM 도구의 스킬 하나로 블로그 자동화가 끝난다.
