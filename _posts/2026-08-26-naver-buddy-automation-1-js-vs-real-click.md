---
title: "네이버 블로그 서이추 자동화하기 (1) — JS click이 안 먹히는 버튼 구분하기"
headline: "네이버 서이추 자동화"
date: 2026-08-26 15:40:00 +0900
categories: [개발, 자동화]
tags: [naver-buddy-automation, 네이버블로그, 브라우저자동화, chrome-devtools, mcp]
description: "네이버는 서로이웃 신청·공감·댓글 API를 제공하지 않는다. 브라우저 자동화로 뚫으면서 JS click으로 되는 동작과, 실제 클릭·실제 키보드가 필요한 동작을 실측으로 갈랐다. 폐기된 엔드포인트를 세 번 만에 찾은 과정까지."
image:
  path: /assets/img/posts/naver-buddy-automation-1-js-vs-real-click-hero.png
  alt: 네이버 서이추 자동화에서 JS만으로 되는 동작, 실제 클릭이 필요한 동작, 실제 키보드가 필요한 동작을 3개 층으로 나눈 그림
---

## 문제

네이버 블로그 **서로이웃(서이추)** 을 자동으로 늘리고 싶었다. 카페 서이추 게시판에서 대상을 찾아 → 그 사람 최신 글에 공감·댓글을 남기고 → 서이추를 신청하는 흐름이다.

먼저 공식 API부터 확인했다. [네이버 오픈API 카탈로그](https://developers.naver.com/docs/common/openapiguide/apilist.md) 전체를 훑은 결과는 이렇다.

- **로그인 방식**: 네이버 로그인 · 카페(가입·글쓰기) · 캘린더
- **비로그인 방식**: 데이터랩 · 검색 · 캡차 · 공유하기 · 오픈메인

**블로그 관련은 검색 API(`/v1/search/blog`) 하나뿐이다.** 서이추·공감·댓글 API는 존재하지 않는다. 브라우저 자동화 외에 길이 없다.

문제는 "브라우저 자동화"가 한 덩어리가 아니라는 점이었다. 어떤 버튼은 JavaScript로 `.click()`만 해도 눌리고, 어떤 버튼은 **아무리 클릭해도 반응이 없었다.**

## 원인

### 폐기된 엔드포인트부터 밟았다

가장 먼저 시도한 게 이거였다.

```
https://blog.naver.com/BuddyAddForm.naver?blogId=example_blog
```

결과는 **404**.

![폐기된 BuddyAddForm 주소에 접속하면 나오는 네이버 404 화면 — "페이지 주소를 확인해주세요"](/assets/img/posts/naver-buddy-automation-1-js-vs-real-click-404.png)
_검색으로 나오는 옛 자료에 이 주소가 남아 있는데, 지금은 죽은 주소다._

살아있는 주소를 찾으려고 블로그 페이지의 `이웃추가` 버튼을 **실제로 클릭해서** 열리는 팝업 URL을 회수했다.

```
https://blog.naver.com/BuddyAdd.naver?blogId=example_blog&trackingCode=post_end
```

그런데 이 PC판 주소는 **직접 이동하면 `ERR_ABORTED`** 가 난다. referer가 필요하다. 자동화에서 매번 블로그 페이지를 열고 버튼을 눌러야 한다는 뜻이라 비효율적이었다.

모바일을 확인하니 답이 나왔다.

![세 번의 시도: BuddyAddForm은 404, BuddyAdd는 ERR_ABORTED, 모바일 BuddyAddForm은 직접 진입 성공](/assets/img/posts/naver-buddy-automation-1-js-vs-real-click-endpoint-path.png)
_세 번 만에 자동화에 쓸 수 있는 주소를 찾았다._

```
https://m.blog.naver.com/BuddyAddForm.naver?blogId={id}&trackingCode=post_end&loadOnModalView=true&template=modal&isShowingGnb=false
```

**모바일 폼은 직접 진입이 된다.** 자동화용 정답은 이쪽이었다.

### 진짜 문제 — `.click()`이 무시되는 버튼

게시글 **공감(좋아요)** 버튼에서 막혔다.

```js
document.querySelector('a.u_likeit_button._face').click();
// → 클래스가 계속 "u_likeit_button _face off" (off 그대로)
```

합성 이벤트를 풀 시퀀스로 쏴봐도 마찬가지였다.

```js
const opts = {bubbles:true, cancelable:true, view:window, clientX:x, clientY:y, button:0};
a.dispatchEvent(new PointerEvent('pointerdown', opts));
a.dispatchEvent(new MouseEvent('mousedown', opts));
a.dispatchEvent(new PointerEvent('pointerup', opts));
a.dispatchEvent(new MouseEvent('mouseup', opts));
a.dispatchEvent(new MouseEvent('click', opts));
// → 여전히 off
```

**`event.isTrusted`를 검사하기 때문이다.** 스크립트가 만든 이벤트는 `isTrusted: false`라 걸러진다. CDP(Chrome DevTools Protocol)로 **브라우저 레벨의 진짜 입력**을 넣어야만 통과한다.

카페 글쓰기의 **스마트에디터**는 한 단계 더 심했다.

```js
document.execCommand('insertText', false, '텍스트');   // → false 반환, 아무 일도 안 일어남
paragraph.querySelector('span').textContent = '텍스트'; // → 에디터가 무시, 저장 시 반영 안 됨
```

에디터 영역에는 `contenteditable` 속성조차 없었다. 실제 편집은 **숨겨진 입력 프록시 div**에서 일어나고 화면은 별도로 렌더된다. `document.designMode`도 `off`였다. 즉 **DOM을 직접 건드리는 모든 방법이 통하지 않는다.**

## 해결 과정

### 3개 층으로 갈렸다

전부 실측해서 정리하면 이렇다.

| 동작 | JS만으로 | 실제 클릭 | 실제 키보드 |
|---|:---:|:---:|:---:|
| 서이추 신청 (모바일 폼) | ✅ | | |
| 댓글 등록 | ✅ * | | |
| 답글 등록 | ✅ | | |
| 댓글 공감 | ✅ | | |
| **게시글 공감** | ❌ | **✅ 필요** | |
| **카페 스마트에디터 본문** | ❌ | ❌ | **✅ 필요** |

\* 댓글은 **댓글창을 여는 버튼만** 실클릭이 필요하고, 창이 열린 뒤 입력·전송은 JS로 된다.

**서이추 신청은 JS만으로 완결된다.** 이게 가장 큰 수확이었다.

```js
document.getElementById('bothBuddyRadio').click();   // 서로이웃 선택
await wait(400);
const ta = document.querySelector('textarea');
ta.value = '(신청 메시지)';
ta.dispatchEvent(new Event('input', {bubbles:true}));
document.querySelector('a.btn_ok').click();
// → title이 "서로이웃 신청 완료"로 바뀌면 성공
```

여기서 반드시 짚어야 할 게 하나 있다. 이 폼에는 **기본 메시지가 미리 채워져 있다.**

![네이버 모바일 서이추 신청 폼의 메시지 입력칸에 "우리 서로이웃해요~"가 기본값으로 채워져 있는 화면](/assets/img/posts/naver-buddy-automation-1-js-vs-real-click-prefill.png)
_서로이웃을 선택하면 이 문구가 그대로 들어가 있다._

서이추 관련 실무 글을 여럿 찾아봤는데, **거절 사유 1순위로 만장일치였던 게 정확히 이 기본 멘트**였다. 자동화든 수동이든 **반드시 덮어써야 한다.**

### 실클릭이 필요한 곳은 접근성 트리로

CDP 기반 도구(chrome-devtools MCP)에서는 요소를 좌표가 아니라 **접근성 트리의 uid**로 지정해 클릭한다.

```
take_snapshot → uid 확보 → click(uid)
```

성공하면 클래스가 `_face off` → `_face on` 으로 바뀐다. **클릭했다고 끝내지 말고 상태 변화를 반드시 확인해야 한다.** 눌린 줄 알았는데 안 눌린 경우가 실제로 있었다.

### 스마트에디터는 실키보드로

```
1. 입력할 문단을 click 으로 포커스
2. press_key("End")     ← 캐럿을 줄 끝으로
3. type_text("내용")     ← 실제 키 입력
```

줄바꿈은 `type_text`의 `submitKey: "Enter"` 로 처리했다. 다만 **이모지는 본문 타이핑에서 빼는 게 안전**했다. 제목 입력은 일반 `input`이라 그냥 채워 넣으면 된다.

### 덤으로 확보한 조회용 API

자동화의 절반은 "누구에게 신청할지 고르는 일"인데, 이건 다행히 HTTP만으로 된다.

```
# 카페 게시판 목록 (로그인 필요)
apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid=&search.menuid=&search.page=

# 카페 글 본문 (로그인 필요)
apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/{cafeId}/articles/{articleId}

# 블로그 최근 글 — 로그인 불필요
blog.naver.com/PostTitleListAsync.naver?blogId={id}&countPerPage=5
```

특히 마지막 것은 **로그인 없이** 제목·작성일·댓글수를 JSON으로 준다. "이 사람이 최근에 글을 쓰고 있나"를 확인하는 활동성 필터를 여기서 공짜로 만들 수 있었다.

> 응답에 `\'` 가 섞여 있어 그냥 `JSON.parse` 하면 깨진다. `text.replace(/\\'/g, "'")` 후 파싱해야 한다.
{: .prompt-warning }

## 사용한 기술

- **chrome-devtools MCP** — CDP로 브라우저를 제어한다. `isTrusted` 이벤트를 만들 수 있는 게 핵심
- **접근성 트리(a11y tree) 스냅샷** — 좌표 대신 uid로 요소를 지정한다. 레이아웃이 바뀌어도 안 깨진다
- **로그인 세션 재사용** — 이미 로그인된 브라우저를 붙여 쓴다. 비밀번호를 코드나 자동화에 넣지 않는다
- **`event.isTrusted`** — 브라우저가 실제 사용자 입력에만 `true`를 주는 플래그. 자동화 차단의 실질적 방어선

> **🧭 기획자·사업자라면**
> - **"API가 없다 = 자동화 불가"가 아니다.** 다만 견적을 내기 전에 **"어디까지 JS로 되는가"를 먼저 실측**해야 한다. 순수 HTTP 스크립트로 될 거라 가정하고 착수하면, 에디터 하나 때문에 전면 재설계가 난다.
> - **세션 의존은 그대로 운영 비용이다.** 이 방식은 로그인된 브라우저가 항상 떠 있어야 한다. 서버·클라우드로 옮길 수 없고, 로그인이 끊기면 전부 멈춘다. "어디서 돌 것인가"를 기술 선택보다 먼저 정해야 한다.
> - **차단은 악의가 아니라 기본값이다.** `isTrusted` 검사는 특정 서비스가 우리를 막으려고 넣은 게 아니라 웹 표준의 보안 장치다. 우회가 아니라 **정상 입력 경로를 쓰는 것**이 맞는 접근이고, 그래서 비용(속도)이 든다.
{: .prompt-tip }

## 정리

- 네이버는 서이추·공감·댓글 API를 제공하지 않는다. 블로그 관련 공식 API는 검색뿐이다.
- 동작은 **JS로 되는 것 / 실클릭이 필요한 것 / 실키보드가 필요한 것** 3개 층으로 갈린다. 게시글 공감은 실클릭, 스마트에디터는 실키보드가 필요하다.
- `BuddyAddForm.naver`(PC)는 폐기됐다. 자동화에는 **직접 진입이 되는 모바일 폼**을 쓴다. 그리고 기본 멘트 `"우리 서로이웃해요~"` 는 반드시 덮어쓴다.
