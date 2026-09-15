댓글에 키워드를 달면 자동으로 DM을 보내고, 팔로우 여부를 확인해 링크를 주는 follow-gate 봇을 만들었다. 코드는 완성됐고 동작도 했다.

그런데 공개할 수가 없었다. **Meta의 Advanced Access 심사를 통과해야 하는데, 여기서 사업자등록이 걸린다.**

개인 개발자가 인스타 DM 자동화를 기획한다면 코드를 짜기 전에 이걸 먼저 알아야 한다.

## 원인 — 타인 데이터 = Advanced Access = 사업자등록

공개 팔로워의 댓글·DM은 **타인의 데이터**다. 이걸 처리하려면 Instagram 권한을 **Advanced Access**로 받아야 하고, 그러려면 **App Review + business verification**이 필요하다.

문제는 business verification이 **등록된 사업체(법인/개인사업자)** 를 전제로 한다는 것. **개인 신분증·개인 명의 서류로는 인증이 안 된다**(인정 서류가 전부 사업체 명의). 게다가 개발 모드에서는 **테스터로 등록된 계정의 이벤트만** webhook이 오므로, 일반 팔로워의 실제 댓글로는 봇이 반응하지 않는다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[블로그 글을 인스타그램에 자동 발행하기 (5) — 사업자 없으면 인스타 DM 자동화 못 합니다 (Meta App Review 벽)](https://riririb.com/posts/blog-to-instagram-automation-5-dm-wall/)**
