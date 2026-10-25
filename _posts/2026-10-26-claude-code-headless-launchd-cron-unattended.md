---
title: "Claude Code headless(claude -p)를 launchd·cron으로 매일 무인 실행하기 — 석 달 돌리며 정한 규칙"
headline: "Claude Code 무인 실행"
highlight: "무인 실행"
date: 2026-10-26 08:10:00 +0900
categories: [개발, 자동화]
tags: [claude-code, launchd, cron, automation, macos, headless]
description: "Claude Code를 claude -p로 매일 아침 무인 실행한 지 석 달. 터미널에선 멀쩡하던 게 스케줄에 걸면 에러 없이 조용히 끝났다. plist·래퍼 템플릿, cron 대신 launchd를 쓰는 이유, 도움말에 없는 --max-turns 실측, 성공·실패·건너뜀 3상태 보고까지 정리했다."
image:
  path: /assets/img/posts/claude-code-headless-launchd-hero.webp
  alt: launchd가 래퍼 스크립트를 깨우고 claude -p 실행 후 산출물로 성공을 판정해 결과를 세 가지로 보고하는 흐름도
---

## 문제 — 터미널에선 되는데, 스케줄에 걸면 조용히 끝난다

2026년 7월 20일부터 매일 아침 8시에 Claude Code를 무인으로 돌리고 있다. 전날 기록을 읽어 글로 정리하고, 블로그에 **임시저장까지만** 해두는 작업이다. 그 사이 기계를 두 번 옮겼다(맥 → 윈도우 → 맥미니). 오늘 아침까지 봇이 남긴 초안 커밋이 92개다.

터미널에서 `claude`를 직접 실행할 때는 한 번도 안 깨지던 게, 스케줄에 걸자 **깨지는 방식이 달라졌다.** 에러가 나서 멈추는 게 아니라, **아무 일도 없었던 것처럼 끝났다.** 사람이 블로그를 열어보기 전까지는 아무도 몰랐다.

이 글은 그 과정에서 정한 규칙을 **바로 가져다 쓸 수 있는 템플릿**으로 정리한 것이다. 실패의 자세한 경위는 [네이버 블로그 발행 자동화](/posts/naver-blog-publish-automation/) 글에 따로 적었다.

## 최소 구성 — plist 하나, 래퍼 하나

![launchd가 08:00에 래퍼를 깨우고, 래퍼가 PATH를 잡은 뒤 claude -p를 실행하고, 산출물로 성공을 판정해 성공·실패·건너뜀 셋 중 하나로 보고하는 흐름](/assets/img/posts/claude-code-headless-launchd-flow.webp)

구조는 단순하다. **launchd는 시간만 맞춰 래퍼를 깨우고, 판단은 전부 래퍼가 한다.** plist에 로직을 넣지 않는 게 핵심이다.

`~/Library/LaunchAgents/com.example.claude-daily.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.claude-daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/me/project/scripts/daily_run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/me/project/run_logs/launchd.out</string>
    <key>StandardErrorPath</key>
    <string>/Users/me/project/run_logs/launchd.err</string>
</dict>
</plist>
```

경로는 전부 **절대경로**여야 한다. `~`도 `$HOME`도 안 풀린다 → [plist는 절대경로만 받는다](/posts/mac-mini-launchd-caffeinate-resident-runner/)

등록하고 바로 한 번 돌려본다. `load`/`unload`는 man 페이지에서 레거시로 분류돼 있고, 지금 권장되는 건 `bootstrap`·`kickstart`다.

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.claude-daily.plist
launchctl kickstart gui/$(id -u)/com.example.claude-daily     # 예약 시각을 기다리지 않고 지금 실행
launchctl print gui/$(id -u)/com.example.claude-daily | grep -E "runs|last exit code"
#   runs = 6
#   last exit code = 0
```

래퍼 `scripts/daily_run.sh`의 뼈대:

```bash
#!/bin/bash
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

# launchd는 최소 PATH(/usr/bin:/bin:/usr/sbin:/sbin)로 실행된다 — brew 경로를 직접 얹는다
for d in /opt/homebrew/bin "$HOME/bin"; do [ -d "$d" ] && PATH="$d:$PATH"; done
export PATH
CLAUDE="$(command -v claude || echo /opt/homebrew/bin/claude)"   # 반드시 PATH 설정 뒤에

mkdir -p run_logs
exec >>"run_logs/run-$(date +%F-%H%M%S).log" 2>&1   # 실행마다 로그 파일 하나

DATE="$(date -v-1d +%F)"   # 어제 (macOS date 문법)

for attempt in 1 2 3; do
  "$CLAUDE" -p "/daily-compile $DATE" \
    --dangerously-skip-permissions --max-turns 60 || true
  [ -f "posts/$DATE.md" ] && break          # 성공 판정 = 산출물이 생겼는가
  sleep $((attempt * 120))                  # 2분, 4분 백오프
done
```

`claude -p "/스킬이름 인자"`처럼 **슬래시 커맨드를 그대로 프롬프트로 넘길 수 있다.** 무인 작업의 절차를 스킬 파일에 적어 두면, 래퍼는 "언제, 무엇을 넘길지"만 책임지면 된다.

아래는 이 뼈대의 각 줄이 왜 그렇게 생겼는지다.

## cron 말고 launchd를 쓰는 이유 — 자는 동안 놓친 실행

맥에서도 `crontab`은 동작한다. 그런데 노트북이나 절전하는 맥이라면 결정적인 차이가 있다.

![cron은 08:00에 맥이 자고 있으면 그날 실행을 건너뛰고, launchd는 깨어나는 즉시 한 번 실행한다. 예약 시각을 두 번 자면서 지나쳤으면 launchd도 두 번이 아니라 한 번으로 합친다](/assets/img/posts/claude-code-headless-launchd-sleep.webp)

`man launchd.plist`의 `StartCalendarInterval` 설명에 따르면, cron은 **컴퓨터가 자는 동안의 실행을 건너뛰고**, launchd는 **다음에 깨어날 때 실행한다.** 그리고 잠든 사이 예약 시각이 여러 번 지나갔으면 **한 번으로 합쳐서** 실행한다.

여기서 두 가지가 따라 나온다.

1. **08:00에 맥이 덮여 있어도 그날 작업이 사라지지 않는다.** 뚜껑을 여는 순간 돈다. cron이었으면 그날은 0회다.
2. **대신 "어제 하루"만 처리하면 날짜가 빈다.** 목요일 밤에 덮고 토요일 오전 10시에 열면, 금·토 08:00 두 번이 한 번으로 합쳐진다. 그 한 번이 "어제(금요일)"만 처리하면 목요일 기록은 영영 빠진다.

그래서 실제 래퍼는 위 뼈대처럼 `DATE`를 하나만 잡지 않는다. **최근 5일 중 "기록은 있는데 아직 처리 안 된 날"을 찾아 전부 처리한다.** 오늘 할 일을 찾는 게 아니라 **아직 안 된 일을 찾는** 방식이다. 이 누락일 스캔의 구현은 [앞 글](/posts/naver-blog-publish-automation/)에 있다.

> 깨어난 직후에 실행된다는 건, **네트워크가 아직 안 붙었을 수도 있다**는 뜻이기도 하다. 실제로 `API Error: Unable to connect to API (ENOTFOUND)`로 죽은 날이 있었다. 그게 웨이크 직후 타이밍 탓인지는 확정하지 못했다. 다만 재시도와 누락일 스캔이 있으면 원인과 무관하게 다음 실행이 만회한다.
{: .prompt-info }

## 플래그 — 무엇을 넘기고, 무엇을 직접 확인했나

무인 실행에 쓰는 플래그를 Claude Code 2.1.241 기준으로 전부 직접 확인했다.

| 플래그 | 역할 | 확인한 방법 |
|---|---|---|
| `-p`, `--print` | 비대화형 실행. 응답을 출력하고 종료 | `claude --help` |
| `--dangerously-skip-permissions` | 모든 권한 확인 생략 ("Bypass all permission checks") | `claude --help` |
| `--max-turns N` | 에이전트 턴 수 상한 | **도움말에 없음.** 직접 실행해 동작 확인 |
| `--allowedTools` | 허용할 도구를 지정 | `claude --help` |
| `--max-budget-usd` | API 비용 상한 (`--print`에서만) | `claude --help` |
| `--output-format json` | 결과를 JSON으로 (`subtype` 등) | 직접 실행 |

### `--max-turns`는 도움말에 없지만 동작한다

래퍼에 석 달째 `--max-turns 60`을 넘기고 있는데, 이번에 `claude --help`를 다시 보니 **이 플래그가 목록에 없었다.** 조용히 무시되고 있는 건지 확인해야 했다.

먼저 **모르는 플래그를 주면 어떻게 되는지** 봤다.

```text
$ claude -p "reply with the single word ok" --this-flag-does-not-exist
error: unknown option '--this-flag-does-not-exist'
```

모르는 플래그는 에러로 거절한다. 그러니 `--max-turns`가 받아들여진다는 건 **CLI가 아는 플래그**라는 뜻이다. 실제로 제한이 걸리는지는 도구를 두 번 써야 끝나는 작업에 상한 1을 줘서 확인했다.

```text
$ claude -p "Run 'ls /tmp | head -3', then run 'date', then tell me both outputs." \
    --max-turns 1 --allowedTools "Bash(ls:*)" "Bash(date)"
Error: Reached max turns (1)
$ echo $?
1
```

`--output-format json`으로 보면 `"subtype": "error_max_turns"`, `"is_error": true`가 찍힌다. **도움말에 없을 뿐 동작하고, 상한에 걸리면 종료코드 1을 낸다.**

> 도움말만 보고 "없어진 플래그네" 하고 지우면, 에이전트가 같은 일을 계속 반복할 때 막아줄 장치가 사라진다. **무인 실행의 플래그는 문서가 아니라 실행 결과로 확인한다.**
{: .prompt-warning }

## 성공 판정은 종료코드가 아니라 산출물로

턴 상한 초과가 종료코드 1로 잡힌다면, 종료코드로 성공을 판정해도 될까. 그렇지 않았다.

7월 26일 실행 로그에는 이 한 줄이 남았다.

```text
API Error: Connection closed mid-response. The response above may be incomplete.
```

글을 쓰던 도중 연결이 끊겼고, 그날 글은 만들어지지 않았다. 이때 종료코드가 무엇이었는지는 로그에 안 남았고, 일부러 연결을 끊어 재현하는 것도 못 했다. **확인하지 못한 실패 경로가 있다는 것 자체가** 종료코드를 믿으면 안 되는 이유다.

그래서 래퍼는 `|| true`로 종료코드를 흘려보내고, **"결과 파일이 생겼는가"**만 본다. 다음 날 실행 로그가 이 방식이 동작하는 걸 보여준다.

```text
    에세이 생성 시도 1/3
    [!] posts/2026-07-26.md 미생성 — 120s 후 재시도
    에세이 생성 시도 2/3
    [+] 임시저장 완료 2026-07-26
```

1회차가 실패했고, 2분 뒤 2회차가 성공했다. 사람은 아무것도 하지 않았다.

## 조용한 성공, 시끄러운 실패 — 결과는 세 가지로 보고한다

무인 실행 결과는 매번 텔레그램으로 받는다. 처음엔 **성공 아니면 실패**, 두 가지였다. 이게 양쪽으로 다 틀렸다.

![결과를 성공·실패 두 가지로만 보고하면 기록 없는 날이 실패 알림으로 나가고 날짜 계산이 깨진 날은 할 일 없음으로 침묵한다. 성공·실패·건너뜀 세 가지로 나누고 날짜를 검증하면 둘 다 바로잡힌다](/assets/img/posts/claude-code-headless-launchd-states.webp)

### 시끄러운 실패 — 기록이 없는 날을 실패라고 알렸다

9월 23일 08:00. 전날 기록 파일은 **있었지만 항목이 0건**이었다. 파일 존재 검사는 통과했고, Claude는 세 번 모두 "기록이 없다"고 **정확하게** 답했다. 그런데 래퍼는 결과 파일이 안 생겼으니 재시도를 돌렸고, 6분을 쓴 뒤 `❌ 실패` 알림을 보냈다.

사람이 "에러 난 건가?" 하고 들여다보게 만들었다. **틀린 알림 한 번이 알림 전체의 신뢰를 깎는다.** 다음부터 진짜 실패 알림이 와도 "또 그거겠지" 하게 된다.

고친 방법은 **"건너뜀"을 별도 상태로 두는 것**이다. 처리할 기록이 없는 날은 재시도 없이 건너뛰고, 알림에도 실패와 다른 줄로 적는다.

```bash
if [ "$(grep -c '^## ' "logs/$DATE.md")" -eq 0 ]; then
  echo "    로그에 항목이 0건 — 스킵"
  SKIPPED+=("$DATE")       # FAILED가 아니라 SKIPPED
  return
fi
```

### 조용한 성공 — "할 일 없음"이 고장을 숨긴다

반대 방향의 함정은 윈도우로 옮길 때 발견했다. 윈도우 기본 PATH에는 `python3`라는 **Microsoft Store 앱 실행 별칭**이 있다. `command -v python3`로는 존재한다고 나오는데, 실행하면 exit 49로 죽는다(윈도우에서 실측).

래퍼는 파이썬으로 날짜를 계산한다. 이 스텁을 파이썬으로 잡았다면 이렇게 흘러간다.

1. 날짜 계산 결과가 빈 문자열
2. 처리할 날짜가 0개
3. "누락일 없음 — 처리할 것 없음"으로 **exit 0**
4. 텔레그램 알림도 같은 파이썬으로 보내니 **알림조차 안 감**

매일 성공한 척하며 아무것도 안 하는 상태다. 이건 실제로 터지기 전에 막았다. **`command -v`로 고르지 않고, 후보를 실제로 실행해 보고 고르는** 루프를 넣었다.

```bash
PY=""
for _c in python3 python py; do
  _p="$(command -v "$_c" 2>/dev/null)" || continue
  "$_p" -c "import sys" >/dev/null 2>&1 && { PY="$_p"; break; }   # 돌아가는 것만 채택
done
```

그리고 "할 일 없음"으로 끝나기 전에 **그 판단의 전제가 멀쩡한지** 먼저 검사한다. 날짜 형식이 깨졌으면 조용히 끝내지 않고 크게 실패시킨다.

```bash
if ! kst_date 0 | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
  tg "🚨 파이프라인 중단 — 날짜 계산 실패 (PY=$PY)"
  exit 1
fi
```

정리하면 규칙은 둘이다.

- 결과는 **성공 / 실패 / 건너뜀** 세 가지로 보고한다. "할 일 없음"도 알린다 — 알림이 안 오면 그게 이상 신호가 된다.
- "할 일 없음"으로 끝나는 경로는 **그 판단의 전제(날짜·입력)를 먼저 검증**한다.

## 이미 다른 글에서 다룬 함정

무인 실행에서 걸린 나머지는 각각 따로 정리해 뒀다.

- **launchd는 로그인 셸의 PATH를 물려받지 않는다** — 그래서 `ffmpeg`를 못 찾고 죽은 날이 있다. 대화형 셸에선 재현이 안 된다. → [맥미니 상주 러너의 함정](/posts/mac-mini-launchd-caffeinate-resident-runner/)
- **봇이 커밋하는 저장소에서 `git add -A`를 쓰면** 개발 중인 코드가 봇의 `draft:` 커밋에 섞여 들어간다. 7월 28일에 두 번 겪었다. → [봇이 커밋하는 파이프라인의 git 규율](/posts/live-pipeline-git-discipline/)
- **같은 대상에 쓰는 파이프라인이 둘이면 시각을 띄운다.** 같은 블로그에 임시저장하는 두 작업을 08:00과 11:00으로 세 시간 떨어뜨렸다. 앞 작업이 재시도(2분·4분)를 여러 날짜에 걸쳐 돌면 한 시간 간격으로는 겹칠 수 있었다.

> **🧭 기획자·사업자라면**
> **`--dangerously-skip-permissions`는 이름 그대로 모든 확인을 건너뛴다.** 무인 실행엔 확인 버튼을 누를 사람이 없으니 사실상 필수다. 대신 **봇이 할 수 있는 일의 끝을 설계로 정해야 한다.** 이 파이프라인은 초안(임시저장)까지만 만들고, 공개 발행 버튼은 사람이 누른다. 봇이 이상한 글을 써도 공개 전에 걸린다. 권한을 줄이는 대신 **되돌릴 수 없는 마지막 단계만 사람에게 남기는** 방식이다.
> **비용 상한도 같은 이야기다.** 재시도가 있으면 실패한 날은 호출이 몇 배로 늘어난다. `--max-turns`와 `--max-budget-usd`로 상한을 걸어 두면 "밤새 돌다 청구서"가 구조적으로 막힌다. 그리고 무인 자동화의 운영 비용은 결국 **알림을 믿을 수 있느냐**다. 오탐 한 번이 알림 체계 전체를 무력화한다.
{: .prompt-tip }

## 사용한 기술

- **Claude Code `-p`(headless)** — 비대화형 실행. 슬래시 커맨드를 프롬프트로 넘겨 스킬을 호출할 수 있다.
- **launchd `StartCalendarInterval`** — 맥의 스케줄러. cron과 달리 자는 동안 놓친 실행을 깨어날 때 한 번으로 합쳐 실행한다.
- **`launchctl bootstrap` / `kickstart` / `print`** — 등록, 즉시 실행, 상태 확인(`runs`, `last exit code`). `load`/`unload`는 레거시.
- **`--max-turns`** — 도움말에 없지만 동작하는 턴 상한. 초과 시 `Error: Reached max turns`, exit 1.
- **산출물 기반 성공 판정** — 종료코드 대신 결과 파일 존재로 판정하고, 백오프 재시도.
- **3상태 보고** — 성공·실패·건너뜀을 분리해 텔레그램으로 통지.

## 정리

- launchd는 **시간만 맞추고 판단은 래퍼가** 한다. 잠든 사이 놓친 실행은 한 번으로 합쳐지니, **"어제"가 아니라 "아직 안 된 날"을 찾게** 짠다.
- 플래그와 실패 경로는 **문서가 아니라 실행으로** 확인한다. `--max-turns`는 도움말에 없지만 동작했고, 연결 끊김은 재현하지 못했다 — 그래서 성공은 **산출물로** 판정한다.
- 결과는 **성공·실패·건너뜀** 셋으로 알린다. 시끄러운 오탐도, 조용한 "할 일 없음"도 무인 시스템을 망가뜨린다.
