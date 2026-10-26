Claude Code를 `claude -p`로 매일 아침 무인 실행한 지 석 달이 됐다. 터미널에서 직접 돌릴 때는 한 번도 안 깨지던 게, 스케줄에 걸자 에러 없이 조용히 끝나는 날이 생겼다.

그 과정에서 확인한 것 중 두 가지를 옮긴다. 맥에서 cron 대신 launchd를 써야 하는 이유, 그리고 **도움말에는 없는데 실제로는 동작하는 `--max-turns`** 이야기다. plist·래퍼 템플릿과 3상태 보고는 원문에 있다.

## cron 말고 launchd를 쓰는 이유 — 자는 동안 놓친 실행

맥에서도 `crontab`은 동작한다. 그런데 노트북이나 절전하는 맥이라면 결정적인 차이가 있다.

![cron은 08:00에 맥이 자고 있으면 그날 실행을 건너뛰고, launchd는 깨어나는 즉시 한 번 실행한다. 예약 시각을 두 번 자면서 지나쳤으면 launchd도 두 번이 아니라 한 번으로 합친다](https://riririb.com/assets/img/posts/claude-code-headless-launchd-sleep.webp)

`man launchd.plist`의 `StartCalendarInterval` 설명에 따르면, cron은 **컴퓨터가 자는 동안의 실행을 건너뛰고**, launchd는 **다음에 깨어날 때 실행한다.** 그리고 잠든 사이 예약 시각이 여러 번 지나갔으면 **한 번으로 합쳐서** 실행한다.

여기서 두 가지가 따라 나온다.

1. **08:00에 맥이 덮여 있어도 그날 작업이 사라지지 않는다.** 뚜껑을 여는 순간 돈다. cron이었으면 그날은 0회다.
2. **대신 "어제 하루"만 처리하면 날짜가 빈다.** 목요일 밤에 덮고 토요일 오전 10시에 열면, 금·토 08:00 두 번이 한 번으로 합쳐진다. 그 한 번이 "어제(금요일)"만 처리하면 목요일 기록은 영영 빠진다.

그래서 실제 래퍼는 위 뼈대처럼 `DATE`를 하나만 잡지 않는다. **최근 5일 중 "기록은 있는데 아직 처리 안 된 날"을 찾아 전부 처리한다.** 오늘 할 일을 찾는 게 아니라 **아직 안 된 일을 찾는** 방식이다. 이 누락일 스캔의 구현은 [앞 글](https://riririb.com/posts/naver-blog-publish-automation/)에 있다.

> 깨어난 직후에 실행된다는 건, **네트워크가 아직 안 붙었을 수도 있다**는 뜻이기도 하다. 실제로 `API Error: Unable to connect to API (ENOTFOUND)`로 죽은 날이 있었다. 그게 웨이크 직후 타이밍 탓인지는 확정하지 못했다. 다만 재시도와 누락일 스캔이 있으면 원인과 무관하게 다음 실행이 만회한다.

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

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[Claude Code headless(claude -p)를 launchd·cron으로 매일 무인 실행하기 — 석 달 돌리며 정한 규칙](https://riririb.com/posts/claude-code-headless-launchd-cron-unattended/)**
