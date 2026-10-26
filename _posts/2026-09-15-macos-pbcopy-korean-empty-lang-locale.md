---
title: "macOS pbcopy·pbpaste 사용법 — 한글이 0바이트로 복사될 때 원인은 비어 있는 $LANG"
headline: "pbcopy 한글 0바이트"
highlight: "0바이트"
date: 2026-09-15 14:05:00 +0900
categories: [개발, 트러블슈팅]
tags: [macos, pbcopy, pbpaste, locale, shell, utf-8]
description: "pbcopy·pbpaste로 터미널에서 클립보드를 쓰는 기본 사용법과, 한글이 든 텍스트가 에러 없이 0바이트로 복사되는 문제. 원인은 비어 있는 $LANG — 로케일 값별로 직접 측정한 결과와 pbpaste까지 깨지는 이유를 정리했다."
image:
  path: /assets/img/posts/macos-pbcopy-korean-empty-lang-locale-hero.png
  alt: 같은 pbcopy 명령이 영문은 복사되고 한글은 0바이트가 되는 비교 화면
---

## pbcopy·pbpaste 기본 사용법

`pbcopy`는 표준 입력을 클립보드에 넣고, `pbpaste`는 클립보드 내용을 표준 출력으로 꺼낸다. macOS에 기본으로 들어 있다.

```bash
pbcopy < notes.txt          # 파일 내용을 클립보드로
git log -1 --format=%H | pbcopy   # 명령 출력을 클립보드로
pbpaste > saved.txt         # 클립보드를 파일로
pbpaste | wc -c             # 클립보드에 몇 바이트가 들어 있나
```

자주 걸리는 게 **끝의 개행**이다. `echo`는 출력 끝에 개행을 붙이고, 그게 그대로 복사된다.

```text
$ echo "hello" | pbcopy && pbpaste | xxd
00000000: 6865 6c6c 6f0a                           hello.     ← 0a(개행)가 붙었다

$ printf '%s' "hello" | pbcopy && pbpaste | xxd
00000000: 6865 6c6c 6f                             hello
```

토큰이나 ID처럼 한 줄 값을 복사해 어딘가에 붙여 넣을 거라면 `printf '%s'`를 쓰거나 `tr -d '\n'`으로 개행을 뺀다.

```bash
date +%F | tr -d '\n' | pbcopy
```

`pbcopy`는 클립보드가 하나뿐인 게 아니다. `-pboard` 옵션으로 `general`(기본값)·`ruler`·`find`·`font` 중 하나를 고를 수 있다. 이 글의 실측은 전부 **`-pboard find`** 에서 했다. 일반 클립보드에 들어 있던 내용을 테스트로 덮어쓰지 않기 위해서다.

## 문제 — 한글이 0바이트로 복사됐다

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

## 원인 — 로케일이 비어 있으면 UTF-8이 아닌 인코딩으로 읽는다

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

`man pbcopy`의 Encoding 항목에 답이 있다. `pbcopy`와 `pbpaste`는 **로케일 환경변수로 입출력 인코딩을 정하고, 로케일로 정할 수 없으면 표준 C 인코딩을 쓴다**고 적혀 있다. 그리고 UTF-8 사용을 권장한다.

그 "표준 C 인코딩"이 이 맥(시스템 언어 한국어)에서는 **EUC-KR 계열**이었다. 아래 실측에서 바이트로 확인된다. UTF-8 한글 바이트열은 그 인코딩에서 유효하지 않으니 **입력을 통째로 버린다.** 그러고도 종료 코드는 0이다.

터미널 앱을 직접 쓸 때는 이 문제를 안 겪는다. man 페이지에도 적혀 있듯 **터미널 앱은 기본으로 UTF-8을 쓰고 로케일 변수를 알아서 잡아준다.** 이 버그는 **터미널 앱을 거치지 않는 환경**에서 나온다 — CI 러너, launchd/cron으로 뜬 프로세스, 에이전트 도구가 띄운 셸 등. 이 문제를 처음 만난 것도 AI 에이전트가 띄운 셸이었다.

### 실측 — 어떤 로케일 값이면 되나

환경변수를 전부 비운 상태(`env -i`)에서 하나씩 넣어 가며 `한글테스트abc`(18바이트)를 복사했다. 붙여넣기는 매번 UTF-8 로케일로 읽었다. macOS 26.2(Apple Silicon)에서 측정했다.

| 설정 | 종료 코드 | 붙여넣은 바이트 |
|---|---|---|
| (로케일 없음) | 0 | **0** |
| `LANG=C` | 0 | **0** |
| `LANG=ko_KR` (`.UTF-8` 없음) | 0 | **0** |
| `LANG=ko_KR.UTF-8` | 0 | 18 |
| `LANG=en_US.UTF-8` | 0 | 18 |
| `LANG=C.UTF-8` | 0 | 18 |
| `LC_CTYPE=UTF-8` | 0 | 18 |
| `LC_ALL=ko_KR.UTF-8` | 0 | 18 |

세 가지가 보인다.

1. **실패해도 종료 코드는 전부 0이다.** 종료 코드로는 절대 못 잡는다.
2. **언어는 상관없고 `.UTF-8`만 중요하다.** `en_US.UTF-8`도, `C.UTF-8`도 된다.
3. **`LANG=ko_KR`은 답이 아니다.** 이건 의외였다. macOS의 로케일 정의를 보면 `ko_KR`의 문자 처리(`/usr/share/locale/ko_KR/LC_CTYPE`)는 `C.UTF-8`을 가리킨다. 그런데도 0바이트가 나왔다. 반대로 `LC_CTYPE=UTF-8`처럼 언어 없이 인코딩만 적은 값은 통했다. `pbcopy`가 로케일 정의가 아니라 **값에 적힌 인코딩 표기(`.UTF-8`)를 보고 판단하는 것으로 보인다** — 확인한 건 결과뿐이고 내부 동작은 추정이다. 어느 쪽이든 결론은 같다. **`.UTF-8`을 반드시 적는다.**

영문만 든 입력(`abc123`, 6바이트)은 로케일이 없어도 6바이트가 그대로 복사됐다. ASCII는 어느 인코딩에서도 같은 바이트라서다. **영문으로 테스트하면 이 버그는 영영 안 보인다.**

### pbpaste도 같은 이유로 깨진다

반대 방향도 확인했다. 이번엔 UTF-8 로케일로 **제대로 복사한 뒤**, 로케일 없이 `pbpaste`로 꺼냈다.

```text
$ env -i pbpaste -pboard find | xxd
00000000: c7d1 b1db c5d7 bdba c6ae 6162 63         ..........abc

$ LANG=ko_KR.UTF-8 pbpaste -pboard find | xxd
00000000: ed95 9cea b880 ed85 8cec 8aa4 ed8a b861  ...............a
00000010: 6263                                     bc
```

18바이트가 13바이트가 됐다. 앞의 10바이트(`c7d1 b1db …`)는 "한글테스트"를 EUC-KR로 인코딩한 값과 정확히 같다.

```text
$ printf '한글테스트' | iconv -f UTF-8 -t EUC-KR | xxd
00000000: c7d1 b1db c5d7 bdba c6ae                 ..........
```

즉 `pbpaste`는 클립보드의 한글을 **EUC-KR 바이트로 바꿔서** 내보낸다. UTF-8을 기대하는 쪽에서 받으면 글자가 깨진다. **복사하는 쪽과 꺼내는 쪽 모두 UTF-8 로케일이어야 한다.**

## 해결

로케일을 명시한다.

```bash
LANG=ko_KR.UTF-8 LC_ALL=ko_KR.UTF-8 pbcopy < prompt.txt
```

`en_US.UTF-8`이어도 된다. 중요한 건 언어가 아니라 **`.UTF-8`** 부분이다. 꺼낼 때도 마찬가지다.

```bash
LANG=ko_KR.UTF-8 pbpaste > out.txt
```

그리고 복사한 다음엔 **반드시 검증한다.** 이 버그의 본질은 "조용히 실패한다"는 것이라, 확인하지 않으면 다음 단계까지 빈 클립보드를 들고 간다.

![locale이 비어 있음을 확인하고, LANG을 지정해 복사한 뒤 바이트 수를 비교해 OK를 받는 터미널 화면](/assets/img/posts/macos-pbcopy-korean-empty-lang-locale-terminal.png)
_진단 → 수정 → 검증. 마지막 줄의 바이트 수 비교가 핵심이다._

```bash
LANG=ko_KR.UTF-8 pbcopy < prompt.txt
[ "$(LANG=ko_KR.UTF-8 pbpaste | wc -c)" = "$(wc -c < prompt.txt)" ] && echo OK || echo MISMATCH
```

launchd처럼 셸 설정이 없는 환경이면 아예 환경변수로 박아두는 게 낫다.

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
> - **한글 환경은 기본값이 아니다.** 해외 도구·CI·SaaS는 ASCII를 기본 가정으로 만들어진다. 영문으로만 테스트하면 이 버그는 아예 안 보인다. 한국어 서비스라면 **테스트 데이터에 한글을 반드시 넣는 것**이 가장 싼 방어선이다. 같은 사고는 클립보드뿐 아니라 파일명·CSV·PDF 생성에서도 같은 형태로 반복된다.
{: .prompt-tip }

## 사용한 기술

- **`pbcopy` / `pbpaste`** — macOS 클립보드 CLI. 입출력 인코딩을 로케일에서 읽는다. `-pboard`로 클립보드 종류(`general`·`find` 등)를 고를 수 있다.
- **`LANG` / `LC_ALL` / `LC_CTYPE`** — 로케일 환경변수. `LC_ALL`이 나머지를 전부 덮어쓴다. 값의 핵심은 `.UTF-8`이다.
- **`env -i`** — 환경변수를 전부 비운 상태로 명령을 실행한다. 로그인 셸이 아닌 환경을 재현할 때 쓴다.
- **`xxd` / `iconv`** — 실제 바이트를 보고, 어떤 인코딩의 값인지 대조한다.

## 정리

1. `pbcopy`가 빈 클립보드를 만들면 **권한이 아니라 로케일**을 먼저 의심한다. 한글로 테스트하면 1초에 갈린다. 영문으로는 절대 안 갈린다.
2. 값은 `LANG=ko_KR.UTF-8`처럼 **`.UTF-8`까지** 붙인다. `ko_KR`만 쓰면 똑같이 0바이트다. 꺼내는 `pbpaste`에도 같은 로케일이 필요하다.
3. 조용히 실패하는 명령은 **성공을 확인하는 습관**으로만 막을 수 있다. 종료 코드 0은 "했다"지 "됐다"가 아니다.

---

이 문제를 만난 원래 작업은 여기 → [맥미니를 24시간 봇 러너로 만들기 — launchd + caffeinate 상주 프로세스의 함정 두 개](/posts/mac-mini-launchd-caffeinate-resident-runner/)
