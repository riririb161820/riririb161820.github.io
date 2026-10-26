인스타그램 댓글에 반응해 DM을 보내는 봇을 Meta 플랫폼에 올리다 네 군데에서 막혔다. 모아놓고 보니 공통점이 있었다. **네 번 모두 에러 메시지가 엉뚱한 곳을 가리켰다.**

그중 두 가지를 옮긴다. 비밀번호를 바꾼 적도 없는데 뜨는 `OAuthException 190`, 그리고 Test 버튼은 되는데 실제 댓글 webhook은 0건인 상황이다.

## ① "비밀번호를 바꾼 적 없는데" — OAuthException 190

![OAuthException 190의 증상·원인·해결 다이어그램](https://riririb.com/assets/img/posts/body-ts-oauth-190.png)

조금 전까지 잘 되던 토큰이 갑자기 막힌다.

```json
{
  "error": {
    "message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.",
    "type": "OAuthException",
    "code": 190
  }
}
```

비밀번호를 바꾼 적이 없는데 "세션이 무효화됐다"고 나온다.

**원인은 토큰 재생성이다.** 같은 계정의 토큰을 새로 만들면 **이전 세션·토큰이 무효화**된다. 개발 중에 대시보드에서 토큰을 몇 번 다시 뽑거나, 같은 계정을 자체 앱과 다른 도구(예: Composio)에 번갈아 연결하면, 한쪽을 새로 만드는 순간 다른 쪽이 죽어 190이 뜬다.

메시지에 적힌 "changed their password"는 190이 뜨는 여러 경우 중 하나일 뿐인데, Meta가 **코드 하나에 안내 문구 하나를 붙여둔 탓**에 늘 비밀번호 이야기가 나온다.

해결은 단순하다.

- 토큰은 **한 번만 발급하고 재생성하지 않는다.** 발급 즉시 시크릿·`.env`에 넣고 그대로 쓴다.
- 이미 죽었으면 **재발급(또는 OAuth 재연결) 후 설정을 한 번에 끝내고**, 이후 손대지 않는다.
- 유효성은 한 줄로 확인한다.

```bash
curl -s "https://graph.instagram.com/v21.0/me?fields=username&access_token=$TOKEN"
# username이 나오면 유효, 190이면 무효
```

## ③ Test 버튼은 되는데 실제 댓글 webhook은 안 온다

![댓글 webhook 미수신의 점검 순서 다이어그램](https://riririb.com/assets/img/posts/body-ts-comment-webhook.png)

게시물에 실제로 댓글을 달았는데 **서버에 들어온 이벤트가 0건**이다. 반면 Meta 대시보드의 **"Test" 버튼으로 보낸 샘플 webhook은 정상 도착**한다.

이 조합이 중요한 단서다. **전달 경로(콜백 URL·서명 검증)는 멀쩡하고, 실제 댓글 이벤트만 생성되지 않는 상황**이라는 뜻이다. 콜백 쪽을 아무리 뒤져도 답이 없다.

점검 순서는 이렇다.

1. **개발 모드 제약** — 개발 모드에서는 **앱에 역할이 있는 계정**(테스터·개발자·관리자)의 이벤트만 webhook이 발생한다. 역할 없는 계정이 단 댓글은 오지 않는다. ②에서 테스터 수락을 끝내야 하는 이유가 여기 있다.
2. **`comments` 필드 미구독** — 계정-앱 구독(`subscribed_apps`)에 `messages`만 있고 `comments`가 빠진 경우.
3. **권한 미추가** — 토큰에 `instagram_business_manage_comments`가 없으면 댓글 이벤트에 접근할 수 없다. 권한을 추가한 뒤에는 **토큰을 다시 발급**해야 반영된다.

해결은 셋을 차례로 맞추는 것이다.

```bash
# 구독 설정 (comments 포함)
curl -s -X POST "https://graph.instagram.com/v21.0/me/subscribed_apps?subscribed_fields=comments,messages&access_token=$TOKEN"

# 확인 — ['comments','messages']가 나와야 정상
curl -s "https://graph.instagram.com/v21.0/me/subscribed_apps?access_token=$TOKEN"
```

권한은 `instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_manage_messages` 3종을 추가하고 토큰을 재발급한다. 테스트는 **테스터로 등록·수락이 끝난 계정**으로 댓글을 달아야 한다.

> **여기서 ①과 충돌한다.** ③은 권한 추가 후 "토큰 재발급"을 요구하고, ①은 "토큰을 재생성하지 말라"고 한다. 그래서 **권한을 먼저 다 맞춘 뒤 토큰을 마지막에 한 번 발급**하는 순서가 된다. 반대로 하면 190을 다시 만든다.

**일반 공개 팔로워의 댓글까지 받으려면** 앱을 Live로 전환하고 App Review(Advanced Access)를 통과해야 한다. 그리고 이건 사업자 인증이 전제다 — 개발 모드로는 영원히 테스터 계정만 다룰 수 있다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[인스타 자동화 봇이 막히는 네 지점 — OAuth 190·테스터 Pending·댓글 webhook·wrangler login](https://riririb.com/posts/instagram-bot-meta-platform-four-blockers/)**
