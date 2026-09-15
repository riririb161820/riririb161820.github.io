---
title: "맥미니를 24시간 봇 러너로 만들기 — launchd + caffeinate 상주 프로세스의 함정 두 개"
headline: "launchd 함정 두 개"
date: 2026-09-15 14:00:00 +0900
categories: [개발, 자동화]
tags: [launchd, macos, caffeinate, mac-mini, automation, github-actions]
description: "5분마다 돌아야 할 봇이 3.3시간마다 돌고 있었다. 맥미니를 상주 러너로 세우면서 걸린 두 가지 — launchd가 PATH를 안 물려받는 것과 plist가 절대경로만 받는 것. 그리고 맥이 자면 봇도 잔다는 문제."
image:
  path: /assets/img/posts/mac-mini-launchd-caffeinate-resident-runner-hero.png
  alt: GitHub Actions cron의 실측 실행률 22.9%와 맥미니 상주 루프 5분 주기를 비교한 구조도
---

## 문제

주식·코인 자동매매 봇을 하나 굴리고 있다. 전 구간 모의투자·페이퍼 체결이라 실제 돈은 나가지 않는다. 이 봇은 **5분마다** 한 사이클을 돈다. 시세를 받아 진입 신호를 보고, 보유 종목의 손절·익절 조건을 확인한다. 5분은 취향이 아니라 요구사항이다. 타이트한 손절(ATR×1 또는 −3%)을 걸어두고 3시간마다 확인한다면, 손절선은 장식이다.

두 달 전에 이 봇의 스케줄이 안 지켜지는 문제를 한 번 정리했다 — [GitHub Actions cron이 예약대로 안 도는 이유와 상주 러너 이중화](/posts/github-actions-cron-skip-resident-runner/). 그때 내린 처방은 **주 러너는 내 기계, Actions는 폴백**이었고, 주 러너는 윈도우 노트북이었다.

그런데 그 노트북을 다른 용도로 쓰게 되면서 **폴백만 남은 상태로 두 달이 흘렀다.** 이번 글은 그 뒷이야기 — 주 러너를 **맥미니**로 다시 세우면서 걸린 것들이다.

## 왜 기계를 옮겨야 했나

### 재측정: 두 달 전보다 나빠졌다

폴백만으로 버틸 수 있는지부터 확인했다. 실행 기록 100건을 긁어 간격을 재봤다.

```bash
gh run list --workflow=intraday-trading.yml -L 100 \
  --json startedAt,conclusion,event
```

![GitHub Actions 실행 간격 분포 — 예정 구간인 30분 이하가 0회, 2~4시간이 65회로 가장 많다](/assets/img/posts/mac-mini-launchd-caffeinate-resident-runner-gap-chart.png)
_실행 99구간의 간격 분포. 예정대로였다면 전부 맨 위 칸에 있어야 한다._

16일 6시간 동안 **예정 437회 중 실제 100회, 실행률 22.9%.** 최소 간격이 **122분**이라 "30분마다"는 관측 기간 내내 단 한 번도 지켜지지 않았다. 최대 공백은 **766분(12.8시간)**이었다.

두 달 전 관찰은 "하루 11회 중 1회"였는데, 표본을 키워 재보니 같은 결론이 더 선명해졌다. **폴백은 폴백일 뿐이다.**

### 반증: 내 설정 문제는 아닌가

기계를 옮기기 전에, 내 워크플로 탓일 가능성부터 지웠다.

**① 실행이 실패했나?** → `{"success": 100}` — 100건 전부 성공이다. 취소도 타임아웃도 없다.

**② `concurrency` 때문에 큐에서 취소됐나?** → 아니다. 이 설정은 앞 실행이 진행 중일 때 뒤에 온 실행을 대기시키고, 그 사이 새 실행이 또 오면 대기 중이던 것을 취소한다. 충분히 의심할 만했다. 그런데 실행 시간을 재보니 최장 **225초**. 공백은 최소 122분이라 겹칠 수가 없다.

**③ 워크플로가 비활성화됐나?** → `active` 상태였다.

셋 다 아니면 결론은 하나다. **실행이 실패한 게 아니라 애초에 생성되지 않았다.** 안 뜬 337회는 어디에도 기록되지 않는다. 그래서 알림도 없었다. 원인 자체에 대한 자세한 설명은 [앞 글](/posts/github-actions-cron-skip-resident-runner/)에 정리해뒀다.

### 그 사이 데이터는 못 쓰게 됐다

스케줄이 깨진 20거래일 성적은 일평균 **-1,032원**, 목표 달성 2/20일, 누적 -20,637원, MDD -4.64%였다. 목표가 하루 +1,000원이었으니 정반대다.

그런데 진짜 손해는 액수가 아니다. **이 숫자로는 전략을 평가할 수 없다.** 5분마다 손절을 확인하도록 설계한 전략을 3시간마다 확인한 결과이니, 전략이 나쁜 건지 실행이 나쁜 건지 분리가 안 된다. 20일치를 통째로 버려야 한다. 전략을 손대기 전에 **실행 환경부터 고쳐야** 하는 이유다.

## 해결 과정 — 맥미니 상주 러너

### 러너 스크립트

기존 윈도우 배치 파일과 같은 동작을 하는 셸 스크립트를 만들었다.

```bash
#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${BOT_PYTHON:-python3}"
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q

# 맥은 유휴 시 잠들면 러너가 멈춘다 → caffeinate로 슬립 억제(있을 때만)
CAFFEINATE=()
command -v caffeinate >/dev/null 2>&1 && CAFFEINATE=(caffeinate -dimsu)

while true; do
  echo "[$(date '+%F %T')] git pull"
  git pull --rebase --autostash origin main
  pip install -r requirements.txt -q
  "${CAFFEINATE[@]}" python -m app.intraday_bot --loop 300 --push
  echo "[$(date '+%F %T')] bot exited — 60s later restart"
  sleep 60
done
```

**`caffeinate -dimsu`가 핵심이다.** 맥의 기본 동작은 "유휴하면 잔다"이고, 자면 5분 루프도 같이 잔다. 윈도우 노트북 때는 없던 변수다. `-d`(디스플레이) `-i`(유휴) `-m`(디스크) `-s`(AC 전원 시) `-u`(사용자 활동 시뮬레이션)로 **봇이 도는 동안만** 슬립을 막는다.

시스템 설정에서 "자동 잠자기 끄기"를 영구히 켜는 것보다 이쪽이 낫다 — **봇이 죽으면 맥도 정상적으로 다시 잠든다.** 슬립 억제가 프로세스 수명에 묶이는 것이다.

나머지 두 가지는 기존 구조 그대로다. 바깥 `while` 루프가 크래시를 60초 뒤에 되살리고, 봇은 6시간마다 스스로 정상 종료해서 루프가 `git pull`부터 다시 시작하게 한다(= 무인 코드 갱신).

```python
if time.time() - t0 > 6 * 3600:
    print("정기 재시작 — 러너 스크립트가 최신 코드 pull 후 재기동")
    if push:
        _push_state()
    return
```

### 함정 1 — launchd는 로그인 셸의 PATH를 물려받지 않는다

맥에서 상시 가동은 launchd다. 터미널에서 잘 되던 스크립트가 launchd로 띄우면 `git: command not found`로 죽는다. `.zshrc`가 실행되지 않기 때문이다.

plist에 PATH를 명시해야 한다.

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>PATH</key>
  <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
</dict>
```

같은 이유로 로케일도 안 물려받는다. 한글을 다루는 스크립트라면 `LANG`도 같이 박아두는 게 안전하다 — 이것 때문에 이날 따로 한 번 더 막혔다([pbcopy가 한글을 조용히 버린 건](/posts/macos-pbcopy-korean-empty-lang-locale/) 같은 뿌리의 문제다).

### 함정 2 — plist는 절대경로만 받는다

plist에는 `~`도, 상대경로도 못 쓴다. 저장소 위치가 기계마다 다르면 매번 손으로 고쳐야 한다는 뜻이고, 실제로 "그 기계에 저장소가 어디 있더라?"에서 한 번 멈췄다.

설치 시점에 치환하는 걸로 해결했다. **저장소 루트에서** 실행하면 경로를 손댈 일이 없다.

```bash
mkdir -p ~/Library/LaunchAgents logs
sed "s|/PLACEHOLDER/REPO/PATH|$PWD|g" scripts/com.example.bot.plist \
  > ~/Library/LaunchAgents/com.example.bot.plist

grep -n "$PWD" ~/Library/LaunchAgents/com.example.bot.plist   # 치환 확인
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.bot.plist
launchctl print gui/$(id -u)/com.example.bot | head -20        # 상태 확인
```

`RunAtLoad`로 로그인 시 자동 시작, `KeepAlive`로 죽으면 재기동, `ThrottleInterval 60`으로 재기동 폭주를 막는다. 중지는 `launchctl bootout gui/$(id -u)/com.example.bot`.

> 경로에 **공백이 있으면 launchd가 인자를 쪼갠다.** 공백 없는 경로에 두는 게 안전하다.
{: .prompt-warning }

### 헤드리스 맥미니라면 하나 더

LaunchAgent는 **로그인 세션에서** 뜬다. 모니터 없이 두는 맥미니를 재부팅해도 봇이 살아나게 하려면 두 가지가 더 필요하다.

- 시스템 설정 > 사용자 및 그룹 > **자동 로그인** 켜기
- `sudo pmset autorestart 1` — 전원이 끊겼다 들어오면 자동으로 켜지게

### 러너는 한 대만

이중화 구조(상주 주 러너 + Actions 폴백)는 앞 글에서 만든 그대로 쓴다. 장부의 마지막 사이클 시각을 보고 상주 러너가 살아 있으면 Actions가 스스로 양보하는 스테일가드다.

```python
def _other_runner_active(cfg, window_min: int = 25) -> bool:
    """최근 25분 내 다른 러너의 사이클 흔적이 있으면 True."""
```

여기서 이번에 새로 배운 제약이 하나 있다. **상주 러너를 두 대 켜면 안 된다.** 스테일가드는 Actions만 양보시키지, 상주끼리는 서로 모른다. 옛 윈도우 노트북과 맥미니를 동시에 켜면 같은 장부에 둘이 쓴다. 기계를 옮기는 작업에서 가장 쉬운 사고라, 저장소의 작업 규칙 문서 맨 위에 박아뒀다.

> **🔐 기계 사이로 키 파일 옮길 때**
>
> 이 봇은 증권사 API 키가 든 `.env`가 필요하다. 기계를 옮기면서 한 가지는 확실히 했다 — **AI 세션 입력창에 키를 붙여넣지 않는다.** 붙여넣는 순간 대화 기록에 영구 저장되고, 그 기록은 내가 지울 수 없는 곳까지 간다. 파일로 직접 옮기거나, 정 안 되면 터미널에만 붙여넣는다. 옮긴 뒤 클립보드와 임시 사본을 지우는 것까지가 한 세트다.
{: .prompt-danger }

> **🧭 기획자·사업자라면**
>
> - **"0원"의 진짜 가격은 SLA 없음이다.** 무료 CI의 cron에는 실행 보장이 없다. 비용 0원을 얻는 대신 "정해진 시각에 돈다"는 계약을 포기한 것이다.
> - **가장 비싼 장애는 에러가 아니라 침묵이다.** 실패는 알림이 오지만 실행이 안 뜬 건 아무도 알려주지 않는다. 모니터링을 "에러 발생 시 알림"으로만 짜면 이런 장애는 영원히 안 보인다. **"N분간 실행 기록이 없으면 알림"**(하트비트)이 필요한 이유다.
> - **인프라는 한 번 정하고 끝이 아니다.** 두 달 전 "윈도우 노트북 = 주 러너"로 정리했는데, 그 기계의 용도가 바뀌자 시스템이 조용히 폴백으로 내려앉았다. **어떤 기계가 무슨 역할인지**를 문서에 적고, 역할이 바뀌면 같이 갱신해야 한다.
{: .prompt-tip }

## 사용한 기술

- **launchd (`launchctl bootstrap` / `bootout` / `print`)** — macOS의 상주 프로세스 관리자. `RunAtLoad`·`KeepAlive`·`ThrottleInterval`.
- **`caffeinate`** — macOS 슬립 억제. 프로세스를 감싸면 그 프로세스가 사는 동안만 적용된다.
- **`pmset autorestart`** — 정전 복구 시 자동 부팅.
- **`gh run list --json`** — 실행 기록을 JSON으로 받아 집계. 체감이 아니라 숫자로 말하려면 여기서 시작한다.
- **스테일가드 패턴** — 공유 상태의 마지막 갱신 시각으로 "다른 러너가 살아있나"를 판정해 단일 기록자를 보장. 분산 락 없이 파일 하나로 되는 값싼 방법.

## 정리

1. **맥을 상주 러너로 쓸 땐 `caffeinate`로 프로세스를 감싼다.** 시스템 설정을 영구히 바꾸는 것보다 낫다 — 봇이 죽으면 맥도 정상적으로 잔다.
2. **launchd는 로그인 셸 환경을 물려받지 않는다.** PATH와 로케일은 plist에 직접 박는다. plist의 절대경로는 설치 시 `sed`로 치환하면 기계가 바뀌어도 손댈 게 없다.
3. **상주 러너는 한 대만.** 폴백을 양보시키는 스테일가드가 있어도 상주끼리는 서로를 모른다. 기계를 옮길 땐 옛 러너를 끄는 것이 첫 단계다.

> 이 봇은 모의투자·페이퍼 체결 단계이며, 이 글은 투자 권유가 아니다. 손익 숫자를 그대로 적은 건 자랑이 아니라 **스케줄이 깨지면 전략 평가 자체가 불가능해진다**는 걸 보여주기 위해서다.
{: .prompt-warning }
