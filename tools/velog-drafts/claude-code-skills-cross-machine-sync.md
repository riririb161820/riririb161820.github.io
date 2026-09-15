Claude Code 스킬을 여러 개 만들어 쓰다 보면 부딪히는 벽이 있다. **"이 스킬, 다른 PC에서도 그대로 쓰고 싶은데?"**

스킬은 `~/.claude/skills/`에 쌓이고, 이건 그 PC 안에만 있다. 폴더를 복사하면 될 것 같지만 그렇지 않다. 한쪽에서 고치는 순간 두 PC가 어긋나고, "방금 고친 게 어느 쪽이었지?"가 반복된다.

단순 복사가 왜 안 되는지부터 짚고 가야 제대로 된 동기화를 만들 수 있다.

## 원인 — 왜 단순 복사로는 안 되나

폴더를 한 번 복사하는 것으로 끝나지 않는 이유가 두 가지 있었다.

![개인 스킬과 플러그인 스킬의 차이](https://riririb.com/assets/img/posts/claude-skills-two-types.svg)

**1) 스킬은 두 종류다.** 내가 만든 **개인 스킬**(`blog-post`, `image-video-gen` 등)은
`~/.claude/skills/<이름>/SKILL.md` 구조로 그 폴더 안에 그대로 있다. git으로 묶으면 끝이다.
하지만 **플러그인 스킬**(`anthropic-skills:work-log`처럼 `:`로 네임스페이스가 붙은 것)은
이 폴더에 없다. 플러그인 캐시(세션 경로)에 따로 있어서 git에 안 잡힌다. 그래서 `work-log`,
`session-handoff` 같은 걸 같이 공유하려면 **개인 스킬로 복제**해 넣어야 했다.

**2) 스킬 안에 OS 종속 요소가 박혀 있다.** 복제한 `work-log` 스킬에는
`/Users/<사용자>/...` 같은 macOS 절대경로가 하드코딩돼 있었다. 이대로 Windows로
넘기면 그 경로가 없어서 동작하지 않는다. 시간대(KST 보정)나 코워크 전용 호출도 마찬가지다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[Claude Code 스킬을 여러 PC에서 공유하기 — Mac·Windows 자동 동기화 파이프라인](https://riririb.com/posts/claude-code-skills-cross-machine-sync/)**
