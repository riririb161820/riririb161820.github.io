---
# the default layout is 'page'
icon: fas fa-info-circle
order: 4
---

## riririb.log

개발하면서 만난 문제를 **문제 → 원인 → 해결 → 사용 기술** 순서로 기록하는 블로그입니다.

같은 에러를 만난 사람이 검색으로 들어와서 원인과 해결책을 바로 가져갈 수 있는 글을 목표로 합니다. 그래서 결과만 적지 않고, 먼저 해 본 시도가 왜 실패했는지도 같이 남깁니다. 검색해서 들어온 사람은 대개 그 실패한 시도 중 하나를 하고 있는 중이기 때문입니다.

### 누가 쓰나

개발자가 아니라 **기획자**가 씁니다. Claude Code 같은 AI 코딩 도구로 업무와 개인 작업을 직접 자동화하면서, 막힌 지점과 풀어낸 방법을 기록합니다.

기획자가 쓰다 보니 글마다 "이 기술적 선택이 비용·리스크·일정에는 무엇을 뜻하는가"를 따로 적습니다. 본문 중간의 **🧭 기획자·사업자라면** 상자가 그 부분입니다. 개발자는 해결 방법을, 기획자나 사업자는 판단 기준을 가져가면 됩니다.

### 글을 쓰는 원칙

- **직접 해 본 것만 씁니다.** 명령어·설정·수치는 실제로 실행해서 나온 결과입니다. 확인하지 못한 부분은 "확인하지 못했다"고 적습니다.
- **틀린 내용은 고칩니다.** 발행 뒤에 틀린 부분을 찾으면 본문을 고치고, 겹치는 글은 하나로 합칩니다. 옛 주소는 합친 글로 연결됩니다.
- **화면 캡처는 가려서 올립니다.** 토큰·계정 정보·개인정보가 찍힌 부분은 가린 뒤 올립니다.

### 주로 다루는 주제

- **AI 코딩 도구로 자동화하기** — Claude Code를 사람 없이 매일 돌리기([launchd·cron 무인 실행]({% post_url 2026-10-26-claude-code-headless-launchd-cron-unattended %})), 두 기계의 Claude 세션이 git으로 일을 주고받기([작업 요청 채널]({% post_url 2026-10-27-claude-code-two-machines-git-ops-channel %}))
- **네이버 블로그 자동화** — [스마트에디터 Playwright 함정]({% post_url 2026-07-23-naver-smarteditor-playwright-pitfalls %}), [발행 자동화]({% post_url 2026-07-28-naver-blog-publish-automation %}), 서로이웃 자동화 시리즈
- **블로그 운영과 검색 노출** — [GitHub Pages 사이트맵 '가져올 수 없음' 해결]({% post_url 2026-09-15-github-pages-sitemap-couldnt-fetch-custom-domain %}), IndexNow, 이미지 최적화
- **숏폼 영상 자동 제작** — ffmpeg 자막·음량, 나레이션과 컷 길이 맞추기
- **API 연동 트러블슈팅** — Instagram Graph API, B2B API 검증, macOS 명령줄 도구

글 전체는 [카테고리](/categories/)와 [아카이브](/archives/)에서 볼 수 있습니다.

### 연결

- Instagram: [@riririb.dev](https://www.instagram.com/riririb.dev/) — 블로그 글을 카드뉴스로 요약해 올립니다
- 문의: `ssadaegi282@gmail.com` — 글의 오류 제보도 환영합니다
