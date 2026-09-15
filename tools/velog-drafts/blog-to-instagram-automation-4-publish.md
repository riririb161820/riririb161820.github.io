만든 카드를 인스타에 자동으로 올리려면 Instagram Graph API가 필요하다. 그런데 직접 앱을 만들어 App Review를 받는 건 시간·서류 부담이 크다. 자동 발행 하나 하려고 며칠~몇 주를 기다릴 순 없었다.

**우회로는 "승인된 중개자"를 쓰는 것이다.** 이미 심사를 통과한 서비스의 권한에 올라타는 방식인데, 실제로 돌려보니 삽질 포인트가 여럿 있었다.

## 해결 과정 — 승인된 중개자(Composio)로 우회

이미 Meta 승인을 받은 중개 서비스 **Composio**를 쓰면, 내 계정만 OAuth로 연결해 **심사 없이** 캐러셀을 발행할 수 있다. 단계별로 함정이 있었다.

### 1) 인스타를 비즈니스/크리에이터로 전환
개인 계정으론 API 발행이 안 된다. 프로페셔널 전환(무료)이 전제.

### 2) Composio 연결 (OAuth)
브라우저로 한 번 인증하면 연결된다. 단, **토큰을 대시보드에서 자꾸 새로 만들면 세션이 무효화**된다(OAuthException 190). [→ 트러블슈팅: OAuth 190](https://riririb.com/posts/instagram-api-oauthexception-190-session-invalidated/)

### 3) 카드 PNG → JPEG 변환
인스타 API는 **JPEG + 공개 HTTPS URL만** 받는다. PNG는 거부된다. macOS `sips`로 변환했다.

```bash
sips -s format jpeg -s formatOptions 92 slide.png --out slide.jpg
```

### 4) 공개 URL 호스팅
API가 이미지를 가져갈 **공개 URL**이 필요하다. 이미 쓰던 GitHub Pages 저장소에 올려 URL을 확보했다(추가 비용 0).

### 5) 캐러셀 컨테이너 생성 → 발행
이미지 URL들로 캐러셀 컨테이너를 만들고 발행. 참고로 **게시물 삭제는 API가 지원하지 않아**(앱에서 수동), 계정 **핸들 표기**(예: 점/밑줄)도 발행 전에 카드와 일치시켜야 한다.

결과: 블로그 글 → 카드 6장 캐러셀이 **심사 없이 자동 발행**됐다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[블로그 글을 인스타그램에 자동 발행하기 (4) — Instagram API 심사 없이 자동 발행 (Composio)](https://riririb.com/posts/blog-to-instagram-automation-4-publish/)**
