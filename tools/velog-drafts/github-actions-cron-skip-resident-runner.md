스케줄을 5~30분마다 돌게 해뒀는데 실행 이력을 보니 **하루 11회 예정 중 실제로는 1회**만 돌았다. 그마저 예정 시각보다 27분 늦었다.

버그를 의심했지만 아니었다. **GitHub Actions의 cron은 원래 best-effort다.** 문서에 적혀 있는 동작인데, 이걸 모르고 시간에 민감한 작업을 얹으면 조용히 망가진다.

## 원인

GitHub의 공식 문서에 답이 있었다. **`schedule` 이벤트는 best-effort**다:

> "The schedule event can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour. If there is a sufficient delay, the run may be skipped entirely."

즉 cron은 "예약"이 아니라 **"희망사항"**이다. 부하가 높으면 지연되고, 충분히 밀리면 **아예 건너뛴다.** 특히 매시 정각은 전 세계 워크플로가 몰려 최악이다. 일반적인 배치 작업이면 몇 번 스킵돼도 무해하지만, **정시성이 생명인 트레이딩 봇에는 치명적**이다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[GitHub Actions cron이 예약대로 안 도는 이유와 상주 러너 이중화](https://riririb.com/posts/github-actions-cron-skip-resident-runner/)**
