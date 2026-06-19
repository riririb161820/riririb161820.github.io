---
title: "Claude Code 스킬을 여러 PC에서 공유하기 — Mac·Windows 자동 동기화 파이프라인"
headline: "스킬 PC 동기화"
date: 2026-06-16 09:40:00 +0900
categories: [개발, 자동화]
tags: [claude-code, skills, git, github, launchd, automation]
description: Claude Code 스킬을 한 PC에서 만들면 다른 PC에선 쓸 수 없다. GitHub 저장소 + launchd/작업 스케줄러로 "저장하면 자동으로 양쪽에 반영되는" 동기화 파이프라인을 만든 과정. 개인 스킬과 플러그인 스킬의 차이, OS 종속 요소 제거까지.
image:
  path: /assets/img/posts/claude-skills-cross-machine-sync.png
  alt: 스킬을 한 번 저장하면 macOS와 Windows 두 PC가 GitHub를 통해 자동 동기화되는 구조도
---

## 문제

Claude Code에 스킬(Skill)을 여러 개 만들어 쓰다 보면 자연스럽게 부딪히는 벽이 있다.
**"이 스킬, 다른 PC에서도 그대로 쓰고 싶은데?"**

나는 Mac과 Windows를 오가며 작업한다. 그런데 스킬은 `~/.claude/skills/` 폴더에 쌓여 있고,
이건 그 PC 안에만 있다. Windows에서 같은 스킬을 쓰려면 폴더를 수동으로 복사해야 하는데 —
한쪽에서 스킬을 고치는 순간 두 PC가 어긋난다. "방금 고친 게 어느 쪽이었지?"가 반복된다.

목표는 하나였다: **한쪽에서 스킬을 저장하면, 다른 쪽에도 알아서 반영되게 만들자.**

![변경 전(수동 복사·누락)과 변경 후(GitHub 자동 동기화) 비교 카드](/assets/img/posts/claude-skills-sync-asis-tobe.svg)

## 원인 — 왜 단순 복사로는 안 되나

폴더를 한 번 복사하는 것으로 끝나지 않는 이유가 두 가지 있었다.

![개인 스킬과 플러그인 스킬의 차이](/assets/img/posts/claude-skills-two-types.svg)

**1) 스킬은 두 종류다.** 내가 만든 **개인 스킬**(`blog-post`, `image-video-gen` 등)은
`~/.claude/skills/<이름>/SKILL.md` 구조로 그 폴더 안에 그대로 있다. git으로 묶으면 끝이다.
하지만 **플러그인 스킬**(`anthropic-skills:work-log`처럼 `:`로 네임스페이스가 붙은 것)은
이 폴더에 없다. 플러그인 캐시(세션 경로)에 따로 있어서 git에 안 잡힌다. 그래서 `work-log`,
`session-handoff` 같은 걸 같이 공유하려면 **개인 스킬로 복제**해 넣어야 했다.

**2) 스킬 안에 OS 종속 요소가 박혀 있다.** 복제한 `work-log` 스킬에는
`/Users/<사용자>/...` 같은 macOS 절대경로가 하드코딩돼 있었다. 이대로 Windows로
넘기면 그 경로가 없어서 동작하지 않는다. 시간대(KST 보정)나 코워크 전용 호출도 마찬가지다.

## 해결 과정

### 1) GitHub 저장소로 묶기

먼저 스킬 폴더를 git 저장소로 만들어 GitHub에 올렸다. 민감 파일이 섞여 들어가지 않도록
`.gitignore`부터 깔았다.

```bash
cd ~/.claude/skills
git init
# .gitignore: *.env, *.pem, *token*, *secret*, .DS_Store ...
git add -A
git commit -m "Add Claude Code skills for cross-machine sharing"
git branch -M main
git remote add origin https://github.com/<id>/claude-skills.git
git push -u origin main
```

인증은 `gh` CLI가 이미 https로 로그인돼 있어 그대로 통과했다. `.gitignore`에 `*token*` 같은
패턴을 넣을 땐 **정상 스킬 파일이 실수로 제외되지 않는지** 한 번 확인하는 게 안전하다.

```bash
git ls-files --others --ignored --exclude-standard
```

### 2) 플러그인 스킬 복제 + OS 호환화

플러그인 스킬의 원본을 찾아 개인 스킬 폴더로 복사했다. 그리고 하드코딩된 절대경로를
홈 기준(`~`)으로 바꿔 양쪽 OS에서 풀리게 했다.

```diff
- /Users/<사용자>/업무일지/일지_YYYY-MM-DD.md
+ ~/업무일지/일지_YYYY-MM-DD.md
```

> `~`는 macOS에선 `/Users/<사용자>`, Windows에선 `C:\Users\<사용자>`로 풀린다.

날짜를 가져오는 단계도 환경별로 분기했다 — Claude Code(로컬)는 Bash, Windows는 PowerShell
`Get-Date`, 코워크(UTC 셸)는 `TZ='Asia/Seoul'` 보정.

### 3) "저장하면 자동 push" 파이프라인

핵심이다. 두 PC에 같은 sync 스크립트를 두고, 각 OS의 스케줄러가 주기적으로 실행하게 했다.
스크립트가 하는 일은 **로컬 변경 커밋 → 원격 변경 흡수(rebase) → push** 세 단계. 이 순서라서
두 PC가 서로의 변경을 받아 **양방향으로 수렴**한다.

![자동 동기화 파이프라인 흐름도](/assets/img/posts/claude-skills-sync-pipeline.svg)

스크립트 핵심(macOS/Linux):

```bash
cd ~/.claude/skills || exit 0
# 1) 로컬 변경 먼저 커밋 (rebase는 깨끗한 트리를 요구)
[ -n "$(git status --porcelain)" ] && git add -A && git commit -m "Auto-sync ..."
# 2) 원격 변경 통합
git fetch -q origin main
git rebase -q origin/main || { git rebase --abort; exit 1; }  # 충돌 시 중단
# 3) 올리기
git push -q origin main
```

**Mac은 launchd**로 3분 간격 + 로그인 시 실행하게 등록했다.

```bash
launchctl load -w ~/Library/LaunchAgents/com.<id>.claude-skills-sync.plist
```

**Windows는 작업 스케줄러**에 같은 일을 하는 `sync-skills.ps1`을 3분 간격으로 등록한다.

```powershell
$action  = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$env:USERPROFILE\.claude\skills\sync-skills.ps1`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 3)
Register-ScheduledTask -TaskName 'ClaudeSkillsSync' -Action $action -Trigger $trigger
```

검증은 끝단까지 했다. 데몬이 실제 변경을 만들고 → 자동 커밋 → GitHub 원격까지 push되는지
원격 커밋 해시가 바뀌는 걸로 확인했다(`git ls-remote` 전후 비교). 무변경일 땐 불필요한 커밋을
만들지 않는 것도 확인했다.

### 4) 앞으로 만드는 스킬은 자동으로 양 OS 호환되게

마지막으로, 매번 OS 호환을 손으로 챙기지 않으려고 **메타 스킬**을 하나 더 만들었다.
"스킬 만들어줘 / 수정해줘" 요청이 들어오면 트리거되어, 저장 전에 체크리스트(절대경로 금지,
셸 분기, OS 전용 도구 회피, 시간대, 파일명 규칙 등)를 강제한다. 이 스킬 자체도 자동 동기화로
양쪽 PC에 퍼진다.

## 사용한 기술

- **Claude Code Skills** — `~/.claude/skills/<이름>/SKILL.md` 구조. 개인 스킬 vs 플러그인 스킬(`:` 네임스페이스) 구분이 핵심.
- **git + GitHub** — 중앙 저장소. `rebase`로 선형 히스토리 유지, 충돌 시 자동 중단.
- **gh CLI** — https 인증 + `gh auth setup-git`으로 비대화형 push.
- **launchd** (macOS) — `StartInterval`로 주기 실행, `RunAtLoad`로 로그인 시 실행.
- **작업 스케줄러 / PowerShell** (Windows) — `Register-ScheduledTask`로 동일 주기 실행.

## 정리

- 스킬 공유는 "폴더 복사"가 아니라 **중앙 저장소 + 양방향 자동 동기화**로 풀어야 어긋나지 않는다.
- **개인 스킬과 플러그인 스킬은 다르다.** 플러그인 스킬은 git에 안 잡히므로 필요한 것만 복제해야 한다.
- 여러 OS를 오간다면 **절대경로·셸·시간대 같은 OS 종속 요소**를 처음부터 제거해 두는 게 핵심이다.
