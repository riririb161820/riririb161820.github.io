---
title: "GitHub Actions cron이 예약대로 안 도는 이유와 상주 러너 이중화"
headline: "cron이 안 돌았다"
date: 2026-07-10 15:20:00 +0900
categories: [개발, 트러블슈팅]
tags: [github-actions, cron, 스케줄러, 자동매매, 인프라]
description: "GitHub Actions 스케줄이 하루 11회 예정 중 1회만 실행됐다. cron이 best-effort라 지연·스킵된다는 함정과, 상주 러너 + Actions 폴백 이중화로 해결한 방법."
image:
  path: /assets/img/posts/github-actions-cron-skip-resident-runner-hero.png
  alt: GitHub Actions cron이 예약대로 실행되지 않는 문제와 이중화 해결
---

## 문제

자동매매 봇을 GitHub Actions cron으로 5~30분마다 돌게 해뒀는데, 실행 이력을 보니 **하루 11회 예정 중 실제로는 1회만** 돌았다. 그마저 예정 시각보다 27분 늦었다.

```
gh run list --workflow "Intraday Trading"
2026-07-07T04:34:37Z schedule completed   ← 오늘 유일
(나머지 스케줄 트리거는 실행 기록 자체가 없음)
```

"실시간 단타"를 표방하는 봇인데, 스케줄이 이렇게 스킵되면 매매 기회를 놓치고 보유 포지션의 손절 감시도 늦어진다. 근간이 흔들리는 문제였다.

## 원인

GitHub의 공식 문서에 답이 있었다. **`schedule` 이벤트는 best-effort**다:

> "The schedule event can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour. If there is a sufficient delay, the run may be skipped entirely."

즉 cron은 "예약"이 아니라 **"희망사항"**이다. 부하가 높으면 지연되고, 충분히 밀리면 **아예 건너뛴다.** 특히 매시 정각은 전 세계 워크플로가 몰려 최악이다. 일반적인 배치 작업이면 몇 번 스킵돼도 무해하지만, **정시성이 생명인 트레이딩 봇에는 치명적**이다.

## 해결 과정

"클라우드 하나에 의존하지 말고 이중화"로 방향을 잡았다.

**1. 상주 러너를 주 러너로.** 사용자의 윈도우 노트북(상시 전원)에서 봇을 5분 주기로 돌리고, 매 사이클 상태를 레포에 커밋(push)하게 했다. 배치 스크립트가 크래시 시 자동 재시작하고, 6시간마다 스스로 재시작하며 `git pull`로 코드를 무인 갱신한다.

**2. GitHub Actions는 폴백으로 강등.** 다만 둘이 동시에 돌면 장부가 충돌한다. 그래서 **스테일 가드(stale guard)**를 넣었다:

```python
def other_runner_active(window_min=25):
    last_cycle = read_last_signal_timestamp()
    age = now() - last_cycle
    return age < window_min * 60   # 25분 내 활동 흔적 있으면 True
```

- 상주 러너가 살아있으면(최근 25분 내 사이클) → Actions는 실행돼도 **스스로 양보**하고 종료
- 상주 러너가 죽으면(25분 무신호) → Actions가 **자동 인계**

**3. 실전 검증.** 만든 날 밤, 윈도우 노트북이 절전으로 꺼졌다. 확인해보니 Actions 폴백이 밤새 자동으로 이어받아 시스템이 살아남아 있었다. 어느 러너가 커밋했는지는 **커밋 타임존이 지문**이 됐다 — 상주 러너는 `+0900`(KST), Actions는 `+0000`(UTC)로 찍힌다.

```
15:52 커밋 +0900  → 윈도우 러너
01:35 커밋 +0000  → Actions 폴백 (윈도우 다운 후 인계)
```

## 사용한 기술

- **GitHub Actions `schedule`의 한계**: best-effort, 고부하 시 지연·스킵. 정시성 요구 워크로드엔 부적합.
- **상주 러너 + 폴백 이중화**: 주 러너(로컬)가 정시성을 담당, 클라우드는 생존 폴백.
- **스테일 가드**: 마지막 활동 타임스탬프로 "다른 러너가 살아있나"를 판정해 단일 기록자를 보장.
- **커밋 타임존 지문**: `+0900` vs `+0000`으로 어느 머신이 커밋했는지 사후 추적.

## 정리

1. **GitHub Actions cron은 예약이 아니라 희망사항이다** — 공식 문서도 best-effort라 명시한다. 정시성이 필요하면 쓰지 마라.
2. **정시성이 생명인 워크로드는 상주 러너를 주로, 클라우드를 폴백으로** 두는 이중화가 답이다.
3. **폴백은 성능이 아니라 생존을 산다** — 주 러너가 죽는 건 '만약'이 아니라 '언제'의 문제다.

---

> 이 글은 [AI 자동매매 봇 3주 검증 회고](/posts/ai-trading-bot-3week-validation/)의 트러블슈팅 서브클러스터 중 하나입니다.
{: .prompt-info }
