게시물에 실제로 댓글을 달았는데 webhook 엔드포인트에 이벤트가 0건 들어온다. 그런데 Meta 대시보드의 **Test 버튼으로 보낸 샘플은 정상 도착**한다.

이 조합이 진단의 핵심이다. 전달 경로는 멀쩡한데 실제 이벤트만 안 생긴다는 뜻이라, 볼 곳이 좁혀진다. 점검 순서대로 정리했다.

## 원인 (점검 순서대로)

1. **개발 모드 제약** — 개발 모드에서는 **앱에 역할이 있는 계정(테스터/개발자/관리자)** 의 이벤트만 webhook이 발생한다. 비(非)테스터의 댓글은 오지 않는다.
2. **comments 필드 미구독** — 계정-앱 구독(`subscribed_apps`)에 `messages`만 있고 `comments`가 빠진 경우.
3. **권한 미추가** — `instagram_business_manage_comments` 권한이 토큰에 없으면 댓글 이벤트 접근 불가(권한 추가 후 **토큰 재발급** 필요).

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[Instagram 댓글 webhook이 안 올 때 (개발 모드·comments 구독·권한 체크)](https://riririb.com/posts/instagram-comment-webhook-not-working-dev-mode/)**
