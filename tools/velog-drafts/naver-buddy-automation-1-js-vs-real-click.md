네이버 블로그 서로이웃을 자동으로 늘리려고 공식 API부터 확인했다. 오픈API 카탈로그 전체를 훑은 결과, **블로그 관련은 검색 API 하나뿐**이다. 서이추·공감·댓글 API는 존재하지 않는다.

브라우저 자동화 외에 길이 없는데, 여기서 문제는 "브라우저 자동화"가 한 덩어리가 아니라는 점이다. JS로 `click()`을 부르면 되는 동작과, 실제 클릭이 필요한 동작이 갈린다.

## 원인

### 폐기된 엔드포인트부터 밟았다

가장 먼저 시도한 게 이거였다.

```
https://blog.naver.com/BuddyAddForm.naver?blogId=example_blog
```

결과는 **404**.

![폐기된 BuddyAddForm 주소에 접속하면 나오는 네이버 404 화면 — "페이지 주소를 확인해주세요"](https://riririb.com/assets/img/posts/naver-buddy-automation-1-js-vs-real-click-404.png)
_검색으로 나오는 옛 자료에 이 주소가 남아 있는데, 지금은 죽은 주소다._

살아있는 주소를 찾으려고 블로그 페이지의 `이웃추가` 버튼을 **실제로 클릭해서** 열리는 팝업 URL을 회수했다.

```
https://blog.naver.com/BuddyAdd.naver?blogId=example_blog&trackingCode=post_end
```

그런데 이 PC판 주소는 **직접 이동하면 `ERR_ABORTED`** 가 난다. referer가 필요하다. 자동화에서 매번 블로그 페이지를 열고 버튼을 눌러야 한다는 뜻이라 비효율적이었다.

모바일을 확인하니 답이 나왔다.

![세 번의 시도: BuddyAddForm은 404, BuddyAdd는 ERR_ABORTED, 모바일 BuddyAddForm은 직접 진입 성공](https://riririb.com/assets/img/posts/naver-buddy-automation-1-js-vs-real-click-endpoint-path.png)
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

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[네이버 블로그 서이추 자동화하기 (1) — JS click이 안 먹히는 버튼 구분하기](https://riririb.com/posts/naver-buddy-automation-1-js-vs-real-click/)**
