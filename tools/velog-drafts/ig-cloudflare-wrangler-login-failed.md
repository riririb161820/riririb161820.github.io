Cloudflare Workers를 배포하려는데 `wrangler login`이 브라우저 인증까지는 가고 그 뒤로 안 넘어간다. 재시도하면 에러 메시지만 바뀐다.

```text
✘ [ERROR] Timed out waiting for authorization code, please try again.
▲ [WARNING] Received query string parameter doesn't match the one sent!
The consent verifier has already been used
ERR_CONNECTION_REFUSED (localhost:8976)
```

셋 다 같은 뿌리에서 나온다. **결론부터 말하면 OAuth를 포기하고 API 토큰으로 가는 게 답이다.**

## 원인

- 로그인 OAuth는 **로컬 콜백 서버(localhost:8976)** 가 떠 있는 동안 승인을 받아야 한다.
- 백그라운드/반복 실행으로 **state가 어긋나거나**, 승인 시점에 **콜백 서버가 이미 종료**돼 있으면 위 에러가 난다(consent 재사용·연결 거부).

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[Cloudflare wrangler login 실패 해결 (Timed out / consent already used / localhost 연결 거부)](https://riririb.com/posts/ig-cloudflare-wrangler-login-failed/)**
