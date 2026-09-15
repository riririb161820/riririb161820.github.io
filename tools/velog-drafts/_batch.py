#!/usr/bin/env python3
"""velog 발췌본 35개 일괄 생성.

각 항목: slug -> (velog 제목, 발췌할 섹션 번호, 새로 쓴 도입부)
도입부는 원문 복사가 아니라 velog 독자(한국 개발자)를 향해 새로 쓴 글이다.
문체는 원문과 같은 평어체로 통일한다(발췌 본문이 평어체라 섞이면 티가 난다).
"""
import os
import subprocess
import sys

REPO = "/Users/riririb/#ridev/riririb161820.github.io"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "velog")

POSTS = {
"claude-code-blog-automation-github-pages": ("클로드 코드 작업을 블로그로 자동 발행하기 — 티스토리 API가 막힌 뒤의 선택지", [2], """\
클로드 코드로 작업한 내용을 블로그에 옮기는 걸 자동화하려다 알게 된 제약들을 정리한다.

처음 계획은 단순했다. 티스토리나 워드프레스에 API로 글을 쏘면 되겠거니 했다. 그런데 파고들수록 선택지가 하나씩 지워졌다. 티스토리는 API를 닫았고, Vercel은 약관이 걸렸고, Jekyll은 날짜 하나 잘못 적으면 글이 404가 됐다.

**결론부터 말하면 GitHub Pages + Jekyll Chirpy로 갔다.** 왜 그렇게 됐는지, 조사 단계에서 부딪힌 제약들을 아래에 적는다.
"""),

"website-analytics-goatcounter-ga4-search-console": ("GA4 하나면 되는 거 아닌가? — 통계 도구 3종의 역할이 안 겹치는 이유", [2], """\
블로그를 만들고 첫 글을 올리면 바로 궁금해진다. "여기 들어오는 사람이 있긴 한가?"

막상 붙이려고 보면 헷갈린다. GA4 하나면 되나? 세 개를 다 깔면 중복 아닌가?

**답은 "안 겹친다"** 다. GoatCounter, GA4, Search Console은 각각 다른 질문에 답한다. 셋을 같이 써야 그림이 완성되는데, 그 역할 구분을 아래에 정리했다.
"""),

"claude-code-skills-cross-machine-sync": ("Claude Code 스킬을 Mac·Windows에서 같이 쓰기 — 단순 복사로는 안 되는 이유", [2], """\
Claude Code 스킬을 여러 개 만들어 쓰다 보면 부딪히는 벽이 있다. **"이 스킬, 다른 PC에서도 그대로 쓰고 싶은데?"**

스킬은 `~/.claude/skills/`에 쌓이고, 이건 그 PC 안에만 있다. 폴더를 복사하면 될 것 같지만 그렇지 않다. 한쪽에서 고치는 순간 두 PC가 어긋나고, "방금 고친 게 어느 쪽이었지?"가 반복된다.

단순 복사가 왜 안 되는지부터 짚고 가야 제대로 된 동기화를 만들 수 있다.
"""),

"blog-to-instagram-automation-1-design": ("블로그 글 → 인스타 카드뉴스 자동화를 막는 세 개의 벽", [2], """\
블로그에 글을 하나 올리면 인스타에는 같은 내용을 카드뉴스로 다시 만들어야 했다. 요약하고, 디자인하고, 6~10장 편집하고, 발행하고, 캡션 쓰고. 글 한 편당 30분~1시간이 또 붙었다.

"블로그 글 하나 = 인스타 게시물 하나"를 손 안 대고 만들고 싶었는데, 설계를 시작하니 벽이 세 개 있었다.
"""),

"blog-to-instagram-automation-2-card-generation": ("AI로 카드뉴스 만들면 한글이 깨지는 이유 (해결: HTML + Chrome 캡처)", [2], """\
인스타 카드에는 한글 텍스트가 들어가야 한다. "어차피 이미지니까 AI로 통째로 생성하면 되겠지" 했는데 — **글자가 깨졌다.** 제목도 본문도 알아볼 수 없는 형태로 뭉개졌다.

이미지 생성 모델을 써본 사람은 한 번쯤 겪는 문제인데, 왜 그런지 알면 해결책도 자명해진다.
"""),

"blog-to-instagram-automation-3-design": ("벤치마킹과 카피의 경계 — 잘되는 카드를 참고하되 짝퉁은 안 되게", [2], """\
잘되는 인스타 카드 계정을 보면 "이렇게 만들고 싶다" 싶다. 그런데 그대로 따라 만들면 짝퉁이고, 남의 사진·밈을 가져다 쓰면 저작권 문제다.

참고는 하고 싶은데 어디까지가 허용이고 어디부터가 베끼기일까. 이 선을 말로 정의해두지 않으면 매번 감으로 판단하게 된다.
"""),

"blog-to-instagram-automation-4-publish": ("Instagram API 심사 없이 캐러셀 자동 발행하기 (Composio)", [3], """\
만든 카드를 인스타에 자동으로 올리려면 Instagram Graph API가 필요하다. 그런데 직접 앱을 만들어 App Review를 받는 건 시간·서류 부담이 크다. 자동 발행 하나 하려고 며칠~몇 주를 기다릴 순 없었다.

**우회로는 "승인된 중개자"를 쓰는 것이다.** 이미 심사를 통과한 서비스의 권한에 올라타는 방식인데, 실제로 돌려보니 삽질 포인트가 여럿 있었다.
"""),

"blog-to-instagram-automation-5-dm-wall": ("사업자등록이 없으면 인스타 DM 자동화는 못 합니다 (Meta Advanced Access)", [2], """\
댓글에 키워드를 달면 자동으로 DM을 보내고, 팔로우 여부를 확인해 링크를 주는 follow-gate 봇을 만들었다. 코드는 완성됐고 동작도 했다.

그런데 공개할 수가 없었다. **Meta의 Advanced Access 심사를 통과해야 하는데, 여기서 사업자등록이 걸린다.**

개인 개발자가 인스타 DM 자동화를 기획한다면 코드를 짜기 전에 이걸 먼저 알아야 한다.
"""),

"ig-cloudflare-wrangler-login-failed": ("wrangler login 실패 (Timed out / consent verifier already used / ERR_CONNECTION_REFUSED)", [2], """\
Cloudflare Workers를 배포하려는데 `wrangler login`이 브라우저 인증까지는 가고 그 뒤로 안 넘어간다. 재시도하면 에러 메시지만 바뀐다.

```text
✘ [ERROR] Timed out waiting for authorization code, please try again.
▲ [WARNING] Received query string parameter doesn't match the one sent!
The consent verifier has already been used
ERR_CONNECTION_REFUSED (localhost:8976)
```

셋 다 같은 뿌리에서 나온다. **결론부터 말하면 OAuth를 포기하고 API 토큰으로 가는 게 답이다.**
"""),

"instagram-api-oauthexception-190-session-invalidated": ("Instagram API OAuthException 190 'session has been invalidated' — 비밀번호 안 바꿨는데도 나는 이유", [2], """\
조금 전까지 잘 되던 Instagram Graph API 토큰이 갑자기 막힌다.

```json
{"error": {"message": "Error validating access token: The session has been invalidated because the user changed their password or Facebook has changed the session for security reasons.", "type": "OAuthException", "code": 190}}
```

비밀번호를 바꾼 적도 없는데 "세션이 무효화됐다"고 나온다. 원인은 다른 데 있었다 — 토큰을 다루는 습관 하나가 문제였다.
"""),

"instagram-comment-webhook-not-working-dev-mode": ("Instagram 댓글 webhook이 안 올 때 점검 순서 (Test 버튼은 되는데 실제 댓글만 안 오는 경우)", [2], """\
게시물에 실제로 댓글을 달았는데 webhook 엔드포인트에 이벤트가 0건 들어온다. 그런데 Meta 대시보드의 **Test 버튼으로 보낸 샘플은 정상 도착**한다.

이 조합이 진단의 핵심이다. 전달 경로는 멀쩡한데 실제 이벤트만 안 생긴다는 뜻이라, 볼 곳이 좁혀진다. 점검 순서대로 정리했다.
"""),

"instagram-tester-invite-accept-error": ("Instagram 테스터 초대가 Pending에서 안 풀릴 때 ('문제가 발생했습니다')", [2], """\
Meta 앱에서 Instagram 테스터를 추가했는데 상태가 **Pending**에서 안 풀린다. 수락하려고 instagram.com → 설정 → **앱 및 웹사이트(manage_access)** 에 들어가면 페이지가 아예 안 열린다.

```text
문제가 발생했습니다
문제가 발생하여 페이지를 읽어들이지 못했습니다.
```

시크릿 모드로도, 다른 브라우저로도 같은 에러가 난다. 브라우저 문제가 아니라는 뜻이다.
"""),

"wso2-devportal-api-no-login": ("WSO2 Devportal, 회원가입 없이 API 스펙 전부 받아내기", [2], """\
연동해야 할 API의 개발자 포털에 들어갔더니 로그인 폼뿐이었다. 회원가입은 막혀 있고, 계정이 언제 나올지도 모르는데 연동 일정은 이미 잡혀 있다.

스펙 없이는 요청·응답 타입 설계도 시작할 수 없다. 그런데 이 포털이 **WSO2 API Manager 기반**이라는 게 실마리였다 — 구조를 알면 로그인 없이 열리는 문이 보인다.
"""),

"b2b-api-http-400-good-signal": ("B2B API 연동에서 HTTP 400이 반가운 신호인 이유 (401 vs 400 vs 200)", [2], """\
파트너 API에 첫 호출을 던졌더니 `400 Bad Request`가 돌아왔다. 처음엔 인증이 틀린 줄 알고 토큰부터 다시 봤다.

그런데 **400은 오히려 좋은 신호였다.** 인증을 통과해서 백엔드까지 도달했다는 뜻이기 때문이다. 연동 검증 단계에서 상태코드를 어떻게 읽어야 하는지 정리한다.
"""),

"whatsapp-notification-meta-vs-twilio": ("왓츠앱 비즈니스 API는 무료가 아니다 — Meta 직접 vs Twilio 의사결정 기준", [2], """\
글로벌 고객에게 왓츠앱으로 주문·배송 알림을 보내는 기능을 설계하다 벽에 부딪혔다. "Meta에 직접 앱 등록하면 무료 아닌가?"라고 막연히 생각했는데, 파고들수록 무료가 아니었다.

과금 구조부터 템플릿 사전승인, 비즈니스 인증, SMS 폴백까지 — 도입 전에 알아야 할 것들을 정리했다.
"""),

"ai-trading-bot-3week-validation": ("자동매매 봇 3주 — 검증이 수익을 지운 기록", [3], """\
"하루 천원 버는 자동매매 봇"을 만들어달라는 한 문장으로 시작했다. 3주 뒤 목표는 바뀐다. **"하루 1,000원이 안 돼도 되니 꾸준한 플러스를 내라."**

왜 목표가 바뀌었냐면, 검증을 제대로 해보니 수익이 사라졌기 때문이다. 성공담이 아니라 기각의 기록이다.

이 프로젝트에서 가장 중요했던 건 코드가 아니라 **무엇을 검증했어야 했나**였다.
"""),

"financial-filter-bank-debt-ratio-false-positive": ("부채비율 필터가 우량 은행을 걸러낼 때 — 은행은 예수금이 부채다", [2], """\
"부채비율 500% 초과 배제"라는 흔한 재무 필터를 만들었더니 배제 목록에 카카오뱅크가 떴다. 부채비율 1072%로.

영업이익 1,576억 흑자의 우량 은행인데 필터가 걸러내고 있었다. 원인은 필터 로직이 아니라 **회계 구조**에 있었다.
"""),

"github-actions-cron-skip-resident-runner": ("GitHub Actions cron이 예약대로 안 도는 이유 (하루 11회 중 1회 실행)", [2], """\
스케줄을 5~30분마다 돌게 해뒀는데 실행 이력을 보니 **하루 11회 예정 중 실제로는 1회**만 돌았다. 그마저 예정 시각보다 27분 늦었다.

버그를 의심했지만 아니었다. **GitHub Actions의 cron은 원래 best-effort다.** 문서에 적혀 있는 동작인데, 이걸 모르고 시간에 민감한 작업을 얹으면 조용히 망가진다.
"""),

"multiasset-backtest-index-alignment-bug": ("백테스트가 수익률을 뻥튀기할 때 — 바 인덱스 정렬 함정", [2], """\
코인 5종과 주식 24종을 합쳐 백테스트를 돌렸더니 합산 수익률이 +13.84%가 나왔다. 코인 단독 +2.81%, 주식 단독 +1.78%인데 합치니 두 자릿수가 됐다.

분산 효과라기엔 과했다. **너무 좋은 숫자는 축하가 아니라 조사 대상**이라 루프를 뜯어봤고, 실제 값은 +7.71%였다.
"""),

"yahoo-quotesummary-401-dart-api": ("좀비 피처 — 코드는 있는데 전 종목이 결측이던 재무 필터", [2], """\
"적자 기업은 신규 매수에서 배제"하는 필터를 넣었다. 코드도 있고 배포도 됐다. 그런데 라이브에서 확인하니 **24개 전 종목이 재무 데이터 없음**이었다.

필터는 결측 시 중립 통과하도록 설계돼 있어서, 아무도 걸러지지 않는 장식이 돼 있었다. 기능은 있는데 효과는 없는 상태 — **좀비 피처**다.

에러 로그는 하나도 없었다. 그게 이 버그의 성질이다.
"""),

"live-pipeline-git-discipline": ("봇이 몇 분마다 커밋하는 저장소에 코드 고쳐 넣기 — git 규율 네 가지", [2], """\
매일 무인으로 도는 파이프라인 저장소는 봇이 몇 분 간격으로 커밋을 쏜다. `git status`를 찍으면 내가 건드리지도 않은 파일이 이미 수정돼 있고, push하려면 원격이 이미 앞서 있다.

여기서 평소 습관대로 `git add -A`를 하면 봇 산출물과 `.env`까지 딸려 들어간다. 라이브 저장소에는 별도의 규율이 필요하다.
"""),

"naver-blog-publish-automation": ("텔레그램 기록 → AI 글 → Playwright 임시저장, 매일 무인으로", [1], """\
매일 블로그 한 편을 손으로 쓰지 않고 남기는 파이프라인을 만들었다. 다만 두 가지를 처음부터 못 박았다.

**발행은 사람이 누른다** — 자동화는 임시저장까지만. 검수 없이 공개되면 위치 노출·사실 오류가 그대로 나간다. **수치는 창작 금지** — 기록에 있는 값만 쓰고 없으면 비운다.

이 두 제약에서 구조가 자연스럽게 나왔다.
"""),

"ffmpeg-amix-volume-ramp": ("ffmpeg amix로 합쳤더니 뒤로 갈수록 소리가 커진다 (normalize 기본값 함정)", [2], """\
문장별로 합성한 나레이션 21개를 `adelay`로 배치하고 `amix`로 합쳤다. 들어보니 앞부분은 잘 안 들리는데 뒷부분은 귀가 아팠다.

느낌이 아니라 값으로 재봤더니 앞뒤 평균 **22dB 차이**였다. 원인은 내 배치가 아니라 `amix`의 기본 동작에 있었다.
"""),

"ffmpeg-typing-subtitle": ("자막이 한 글자씩 찍히게 만들기 — 글자가 좌우로 흔들리지 않으려면", [2], """\
숏폼 자막이 한 번에 툭 나타나는 것과 타이핑되듯 찍히는 것은 체감이 꽤 다르다. 후자가 시선을 붙잡는다.

원리는 단순해 보였다. 문장 앞부분만 잘라낸 조각을 여러 개 만들고 시간대별로 하나씩 보여주면 된다. 그렇게 만들었더니 **문장이 좌우로 출렁였다.**
"""),

"reference-voice-f0-matching": ("레퍼런스 목소리를 감이 아니라 숫자로 찾기 (F0 155.2Hz vs 161.2Hz)", [2], """\
레퍼런스 영상의 나레이션과 같은 결의 목소리를 골라야 했다. 여기서 실수를 했다. **"앱 내장 AI 보이스일 겁니다"** 라고 단정해버린 것이다.

그럴듯했지만 확인한 게 아니었고, 틀렸다. 게다가 그 사이 엉뚱한 음성으로 나레이션을 다 만들어둔 상태였다.

그래서 감을 버리고 숫자로 갔다 — 오디오를 받아 기본 주파수(F0)를 재는 방법이다.
"""),

"shortform-auto-render-cutsheet": ("릴스·쇼츠·네이버 클립은 결국 같은 세로 영상 — 편집기 없이 찍어내기", [2], """\
영상은 여전히 처음부터 끝까지 손으로 만들고 있었다. 1080×1920으로 맞추고, 자막을 넣고, 그 자막이 앱 UI에 가리는지 확인하고, 컷 순서를 바꾸고 다시 렌더한다. **컷 하나를 고치면 그 뒤가 전부 밀린다.**

더 큰 문제는 "이 자막이 이 그림과 맞나"를 확인할 방법이 없다는 거였다. 22컷을 처음부터 재생하며 눈으로 대조해야 했다.
"""),

"shortform-narration-cut-length": ("숏폼 나레이션이 배속처럼 들릴 때 — 컷 길이를 말에 맞추기", [2], """\
나레이션은 컷 하나에 문장 하나씩 배치된다. 문장이 컷보다 길면 말속도를 올려서 맞췄는데, 상한으로 걸어둔 **+55%에 붙은 문장이 다섯 개**였다.

1.55배는 사람 말이 아니라 배속 재생이다. 컷 길이를 눈대중으로 정한 게 화근이었다.
"""),

"ai-business-team-1-subagent-cannot-reply": ("AI 에이전트로 사업팀 만들기 — 구조의 한계인 줄 알았던 것이 이름 문제였다", [6, 7], """\
AI 에이전트들로 사업팀을 꾸리는 걸 시도한 첫날 기록이다. 에이전트끼리 직접 묻고 답하는 구조를 만들었는데, 돌려보니 **질문은 가는데 답이 안 돌아왔다.**

나는 이걸 구조적 한계로 진단하고 조직도를 갈아엎었다. 그런데 재시험에서 그 진단이 반증됐다. 원인은 훨씬 사소했다.

오진과 반증 과정을 그대로 남긴다 — 같은 착각을 할 사람이 있을 것 같아서다.
"""),

"subagent-no-agent-reachable-reply-failure": ("No agent named 'general-purpose' is reachable — 이름을 붙이면 회신이 돌아온다", [1, 3], """\
Claude Code에서 서브에이전트 A가 B에게 던진 질문은 잘 도달한다. 그런데 B가 답을 보내려는 순간 이 에러로 끊긴다.

가는 길은 있고 돌아오는 길이 없는 상태다. 게다가 **질문한 쪽에는 아무 에러도 안 뜬다.** 그냥 조용히 타임아웃될 뿐이라 진단이 어렵다.
"""),

"naver-buddy-automation-1-js-vs-real-click": ("JS click이 안 먹히는 버튼 구분하기 — 네이버 자동화 실측", [2], """\
네이버 블로그 서로이웃을 자동으로 늘리려고 공식 API부터 확인했다. 오픈API 카탈로그 전체를 훑은 결과, **블로그 관련은 검색 API 하나뿐**이다. 서이추·공감·댓글 API는 존재하지 않는다.

브라우저 자동화 외에 길이 없는데, 여기서 문제는 "브라우저 자동화"가 한 덩어리가 아니라는 점이다. JS로 `click()`을 부르면 되는 동작과, 실제 클릭이 필요한 동작이 갈린다.
"""),

"naver-buddy-automation-2-cafe-api-callback-url": ("네이버 카페 글쓰기 API가 막혀 있던 진짜 이유 — Callback URL", [2], """\
카페 글쓰기를 스마트에디터에 실제 키보드로 타이핑해서 해결해뒀다. 동작은 했지만 취약했다. 에디터 DOM이 조금만 바뀌어도 깨진다.

그런데 공식 API 카탈로그를 다시 보니 **카페 게시글 등록 API가 존재했다.** 처음엔 "쓸 수 없다"고 결론 냈었는데, 그 판단이 틀렸다. 막혀 있던 건 API가 아니라 앱 설정 한 줄이었다.
"""),

"naver-buddy-automation-3-no-webhook-polling": ("네이버 블로그엔 웹훅이 없다 — 폴링 소스 3개 실측 비교", [2], """\
서로이웃 관계에서 가장 중요한 규범은 답방이다. 이걸 자동화하려면 "이웃이 새 글을 올렸다"는 사건을 알아야 한다.

가장 깔끔한 건 웹훅인데, 공식 API 카탈로그 전체를 확인한 결과 **웹훅은 존재하지 않는다.** 그래서 폴링으로 갔고, 쓸 수 있는 소스 3개를 실제로 재서 비교했다.
"""),

"naver-buddy-automation-4-browser-token-diet": ("브라우저 자동화 토큰 99% 줄이기 — 범인은 본문이 아니었다", [2], """\
LLM이 브라우저를 조종하는 자동화를 돌리면 토큰이 순식간에 녹는다. 24명에게 공감·댓글을 돌리는 작업 한 번에 수십만 토큰이 나갔다.

처음엔 원인을 **본문 텍스트**로 의심했다. 남의 글을 읽어서 댓글을 써야 하니까. 그런데 실제로 재보니 범인은 완전히 다른 데 있었다.
"""),

"naver-buddy-automation-5-automation-tell": ("자동화 티는 어디서 나는가 — 분당 5~6건이 자백한 것", [2], """\
댓글에 자동으로 답글을 다는 작업을 돌렸다. 내용은 나쁘지 않았다. 댓글을 실제로 읽고, 질문에 답하고, 상대 경험을 받아줬다.

그런데 타임스탬프를 보니 **분당 5~6건, 약 11초에 하나씩**이었다. 사람이 댓글을 읽고 2~3문장을 쓰는 속도가 아니다. 게다가 새벽 1시에 11개가 연달아 달렸다.

원인은 프롬프트에 적은 한 단어였다.
"""),

"github-pages-sitemap-couldnt-fetch-custom-domain": ("Search Console 사이트맵 '가져올 수 없음' — 크롤링 통계를 먼저 보세요", [3], """\
github.io 블로그의 사이트맵이 3개월간 "가져올 수 없음"이었다. 사이트맵 XML은 유효했고, robots.txt도 정상이었고, Lighthouse SEO 점수는 100점이었다. 빙에서는 같은 사이트가 20페이지 넘게 색인되고 있었다.

그런데 구글 색인은 홈페이지 하나뿐이었다.

원인은 사이트맵에 없었다. **Search Console의 "크롤링 통계" 보고서** — 3개월 동안 한 번도 안 열어본 그 페이지에 답이 있었다.
"""),
}


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    warned, failed = [], []
    for slug, (title, sections, intro) in POSTS.items():
        intro_path = os.path.join(OUT_DIR, f"{slug}.intro.md")
        with open(intro_path, "w", encoding="utf-8") as f:
            f.write(intro)
        r = subprocess.run(
            [sys.executable, "tools/velog_crosspost.py", "--slug", slug,
             "--sections", ",".join(str(s) for s in sections),
             "--intro", intro_path, "--title", title,
             "--out", os.path.join(OUT_DIR, f"{slug}.md")],
            cwd=REPO, capture_output=True, text=True)
        if r.returncode != 0:
            failed.append((slug, r.stderr.strip() or r.stdout.strip()))
            continue
        ratio = [l for l in r.stdout.splitlines() if "재사용 비율" in l]
        pct = ratio[0].split(":")[-1].strip() if ratio else "?"
        flag = "  ⚠ 중복경고" if "경고" in r.stdout else ""
        if flag:
            warned.append(slug)
        print(f"  {pct:>5}  {slug}{flag}")

    print(f"\n생성 {len(POSTS) - len(failed)}개 / 실패 {len(failed)}개 / 중복경고 {len(warned)}개")
    for slug, err in failed:
        print(f"  [실패] {slug}: {err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
