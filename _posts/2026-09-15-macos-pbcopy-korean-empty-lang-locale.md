---
title: "macOS pbcopy가 한글을 조용히 버릴 때 — 원인은 비어 있는 $LANG"
headline: "pbcopy 한글 0바이트"
date: 2026-09-15 14:05:00 +0900
categories: [개발, 트러블슈팅]
tags: [macos, pbcopy, locale, shell, utf-8]
description: "pbcopy로 한글이 든 파일을 복사했는데 클립보드가 비어 있다. 에러도 없고 종료 코드는 0. 영문은 정상. 원인은 $LANG이 비어 있어 pbcopy가 비ASCII 입력을 통째로 버리는 것이었다."
image:
  path: /assets/img/posts/macos-pbcopy-korean-empty-lang-locale-hero.png
  alt: 같은 pbcopy 명령이 영문은 복사되고 한글은 0바이트가 되는 비교 화면
---

## 문제

한글이 든 텍스트 파일을 클립보드에 넣으려 했다.

```bash
pbcopy < prompt.txt
```

종료 코드 0. 에러 없음. 그런데 붙여넣으면 **아무것도 안 나온다.**

```bash
pbpaste | wc -c
#        0
```

파일은 멀쩡했다.

```bash
wc -c prompt.txt
#     3872 prompt.txt
```

## 원인

처음엔 샌드박스나 권한 문제로 의심했다. 클립보드 접근이 막혔나 싶어 샌드박스를 끄고 다시 해봤다. 똑같이 0바이트. 파일 경로를 의심해 `cat file | pbcopy`로도 해봤다. 역시 0바이트.

그런데 이걸 해보니 갈렸다.

```bash
echo "test123" | pbcopy && pbpaste
# test123        ← 된다

echo "한글테스트" | pbcopy && pbpaste
#                 ← 빈 줄
```

**영문은 되고 한글은 안 된다.** 권한 문제가 아니라 인코딩 문제다.

```bash
echo "locale: [$LANG]"
# locale: []
```

`$LANG`이 비어 있었다.

`pbcopy`는 입력 인코딩을 `LANG`/`LC_CTYPE`에서 읽는다. 로케일이 비어 있으면 기본 인코딩(Mac OS Roman 계열)으로 해석하는데, UTF-8 한글 바이트열은 여기서 유효하지 않다. 그래서 **입력을 통째로 버린다.** 그러고도 종료 코드는 0이다.

터미널을 직접 쓸 때는 `.zshrc`가 로케일을 잡아주니 이 문제를 안 겪는다. 이 버그는 **로그인 셸을 거치지 않는 환경**에서 나온다 — CI 러너, launchd/cron으로 뜬 프로세스, 에이전트 도구가 띄운 셸 등.

## 해결

로케일을 명시한다.

```bash
LANG=ko_KR.UTF-8 LC_ALL=ko_KR.UTF-8 pbcopy < prompt.txt
```

`en_US.UTF-8`이어도 된다. 중요한 건 언어가 아니라 **`.UTF-8`** 부분이다.

그리고 복사한 다음엔 **반드시 검증한다.** 이 버그의 본질은 "조용히 실패한다"는 것이라, 확인하지 않으면 다음 단계까지 빈 클립보드를 들고 간다.

![locale이 비어 있음을 확인하고, LANG을 지정해 복사한 뒤 바이트 수를 비교해 OK를 받는 터미널 화면](/assets/img/posts/macos-pbcopy-korean-empty-lang-locale-terminal.png)
_진단 → 수정 → 검증. 마지막 줄의 바이트 수 비교가 핵심이다._

```bash
LANG=ko_KR.UTF-8 pbcopy < prompt.txt
[ "$(pbpaste | wc -c)" = "$(wc -c < prompt.txt)" ] && echo OK || echo MISMATCH
```

launchd나 CI처럼 셸 설정이 없는 환경이면 아예 환경변수로 박아두는 게 낫다.

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>LANG</key>
  <string>ko_KR.UTF-8</string>
</dict>
```

> **🧭 기획자·사업자라면**
>
> - **"에러가 없다"와 "성공했다"는 다른 말이다.** 이 버그는 종료 코드 0으로 실패한다. 자동화 파이프라인을 점검할 때 "실패 알림이 안 왔으니 잘 돌고 있다"는 가장 위험한 가정이다.
> - **한글 환경은 기본값이 아니다.** 해외 도구·CI·SaaS는 ASCII를 기본 가정으로 만들어진다. 비ASCII가 조용히 잘리는 사고는 클립보드뿐 아니라 파일명·CSV·PDF 생성에서도 같은 형태로 반복된다.
{: .prompt-tip }

## 사용한 기술

- **`pbcopy` / `pbpaste`** — macOS 클립보드 CLI. 입력 인코딩을 로케일에서 읽는다.
- **`LANG` / `LC_ALL` / `LC_CTYPE`** — 로케일 환경변수. `LC_ALL`이 나머지를 전부 덮어쓴다.
- **로그인 셸 vs 비로그인 프로세스** — `.zshrc`/`.bash_profile`을 읽지 않는 실행 경로에서는 PATH·로케일 같은 기본값이 없다고 가정해야 한다.

## 정리

1. `pbcopy`가 빈 클립보드를 만들면 **권한이 아니라 로케일**을 먼저 의심한다. 영문만 되는지 테스트하면 1초에 갈린다.
2. `LANG=ko_KR.UTF-8`을 붙이고, **복사 후 바이트 수를 비교해 검증**한다.
3. 조용히 실패하는 명령은 **성공을 확인하는 습관**으로만 막을 수 있다. 종료 코드 0은 "했다"지 "됐다"가 아니다.

---

이 문제를 만난 원래 작업은 여기 → [맥미니를 24시간 봇 러너로 만들기 — launchd + caffeinate 상주 프로세스의 함정 두 개](/posts/mac-mini-launchd-caffeinate-resident-runner/)
