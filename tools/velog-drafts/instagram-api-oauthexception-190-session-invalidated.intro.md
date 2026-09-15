조금 전까지 잘 되던 Instagram Graph API 토큰이 갑자기 막힌다.

```json
{"error": {"message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.", "type": "OAuthException", "code": 190}}
```

비밀번호를 바꾼 적도 없는데 "세션이 무효화됐다"고 나온다. 원인은 다른 데 있었다 — 토큰을 다루는 습관 하나가 문제였다.
