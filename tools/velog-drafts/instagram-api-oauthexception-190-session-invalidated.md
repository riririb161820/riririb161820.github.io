조금 전까지 잘 되던 Instagram Graph API 토큰이 갑자기 막힌다.

```json
{"error": {"message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.", "type": "OAuthException", "code": 190}}
```

비밀번호를 바꾼 적도 없는데 "세션이 무효화됐다"고 나온다. 원인은 다른 데 있었다 — 토큰을 다루는 습관 하나가 문제였다.

## 원인

- **토큰을 새로 생성하면 같은 계정의 이전 세션/토큰이 무효화**된다.
- 개발 중 대시보드에서 토큰을 **여러 번 재생성**하거나, 같은 계정으로 다른 도구(예: Composio)와 자체 앱을 번갈아 연결하면, 한쪽을 새로 만들 때 다른 쪽 세션이 죽어 190이 뜬다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[Instagram API OAuthException 190 'session has been invalidated' 해결](https://riririb.com/posts/instagram-api-oauthexception-190-session-invalidated/)**
