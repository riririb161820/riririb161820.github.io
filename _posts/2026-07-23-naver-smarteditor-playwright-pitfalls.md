---
title: "네이버 스마트에디터 Playwright 자동화 — 캡션·폰트·콜라주가 조용히 틀어지는 함정 5가지"
headline: "조용한 실패"
date: 2026-07-23 18:20:00 +0900
categories: [개발, 자동화]
tags: [playwright, naver-blog, smarteditor, automation, dom]
description: "Playwright로 네이버 스마트에디터에 글을 자동 입력하면 로그는 전부 성공인데 결과물이 미묘하게 틀어진다. 캡션이 본문으로 새고, 소제목 폰트가 안 먹고, 콜라주가 맨 아래로 밀리는 다섯 가지 함정을 DOM 근거와 함께 실측으로 정리했다."
image:
  path: /assets/img/posts/naver-smarteditor-pitfalls-hero.png
  alt: 로그는 전부 성공인데 실제 결과물은 캡션·콜라주가 틀어진 대비
---

Playwright로 네이버 블로그 글을 자동으로 쓰는 스크립트를 짰다. 제목 넣고, 본문 넣고, 사진 올리고, 소제목 키우고, 콜라주 묶고 — 로그를 보면 `[+] 캡션`, `[+] 콜라주 3장`, `[+] 발행 완료`가 줄줄이 찍힌다. 다 성공이다.

그런데 실제로 저장된 글을 열어보면 캡션이 본문에 섞여 다음 문장과 붙어 있고, 키운 줄 알았던 소제목은 본문이랑 크기가 똑같고, 세 장짜리 콜라주는 글 맨 아래에 혼자 떨어져 있다.

이 글의 교훈은 딱 하나다.

> **로그의 `[+] 성공`은 "명령이 나갔다"는 뜻이지 "동작했다"는 뜻이 아니다.**

브라우저 자동화, 특히 리치 에디터를 상대할 때 이 둘의 간극이 어디서 벌어지는지, 그리고 그걸 어떻게 눈으로 잡았는지 — 실제로 밟은 다섯 개의 함정을 순서대로 풀어쓴다. 셀렉터와 코드는 실측한 그대로다.

## 함정 1 — 캡션이 캡션칸이 아니라 본문으로 샌다

### 증상

사진을 넣고 캡션(사진 설명)을 달려고 사진 삽입 직후에 이렇게 했다.

```python
page.keyboard.type(caption)
```

로그는 성공. 그런데 저장된 글을 보면 캡션칸은 여전히 "사진 설명을 입력하세요." 플레이스홀더 그대로고, 내가 넣으려던 캡션은 **본문 문단**에 들어가 바로 다음 문장과 붙어버렸다. 예를 들어 캡션 "식전빵"과 다음 문단 "첫 접시는 전복."이 이렇게 나온다.

```
식전빵첫 접시는 전복.
```

![캡션이 본문으로 새는 증상과 수정 후 캡션칸에 분리된 결과](/assets/img/posts/naver-smarteditor-pitfalls-caption.png)

### 왜 그런가 (DOM 근거)

스마트에디터의 캡션칸(`.se-caption`)은 비어 있을 때 `se-is-empty` 클래스로 **숨어 있다.** 사진을 막 삽입한 시점의 포커스는 캡션칸이 아니라 본문 컨텐츠 영역에 있다. 그 상태로 `keyboard.type`을 하면 글자가 전부 본문으로 흘러들어간다. 캡션칸은 **컴포넌트를 클릭해서 열어줘야** 입력을 받는다.

### 실패한 접근

- 사진 삽입 후 그냥 타이핑 → 본문으로 샘.
- `Tab`으로 캡션칸에 가려는 시도 → 포커스가 엉뚱한 곳으로 튐.
- 무엇보다, **타이핑이 성공했는지 코드가 확인하질 않으니** 로그는 매번 성공이었다.

### 해결

컴포넌트를 클릭해 캡션칸을 열고 → 캡션칸을 클릭해 → 입력하고 → `innerText`로 **진짜 들어갔는지 확인**해서 참/거짓을 돌려준다.

```python
def insert_caption(page, text: str) -> bool:
    comp = page.locator(".se-component:has([class*=caption])").last
    comp.click(timeout=6000)          # 컴포넌트를 선택해야 캡션칸이 열린다
    cap = comp.locator("[class*='se-caption']").first
    cap.click(timeout=4000)
    page.keyboard.type(text, delay=15)
    got = comp.evaluate(
        "e => { const c = e.querySelector('[class*=caption]');"
        " return c ? (c.innerText || '') : ''; }")
    return text[:6] in got            # 플레이스홀더면 실패
```

`text[:6] in got`가 핵심이다. 캡션칸이 안 열려서 플레이스홀더 그대로면 이 비교가 거짓이 되고, 그때는 캡션을 본문 문단으로 떨어뜨리되 앞뒤로 줄을 띄워 최소한 다음 문장과는 안 붙게 폴백한다.

그리고 하나 더 — 캡션을 넣은 뒤 **본문으로 빠져나오는 처리**가 없으면, 다음 문단 첫 줄이 방금 그 캡션칸(또는 다음 사진의 캡션칸)으로 빨려 들어간다. `Escape`+`End`+`Enter`만으로는 포커스가 캡션에 남는 경우가 있어서, `ArrowDown` 2회로 확실히 아래 문단으로 내려간다.

```python
def leave_caption(page):
    page.keyboard.press("Escape")
    page.locator(".se-component:has([class*=caption])").last.click(timeout=3000)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("End")
    page.keyboard.press("Enter")
```

인용구 컴포넌트를 빠져나올 때도 `ArrowDown` 2회만 통했다. `Escape`+`ArrowDown`+`End`나 `Ctrl+Enter`는 커서가 컴포넌트 안에 남아 이후 본문이 통째로 그 안에 들어간다. 스마트에디터에서 "컴포넌트 밖으로 나가기"는 `ArrowDown`이 정답이라고 외워두면 편하다.

## 함정 2 — 소제목 폰트 크기가 아무 에러 없이 안 먹는다

### 증상

소제목을 본문(16px)보다 크게(19px) 만들려고 폰트 크기 드롭다운을 열어 19를 골랐다. 로그에 에러 없음. 그런데 저장된 글의 소제목은 본문과 크기가 똑같다. **소제목 세 개가 한 번도 19px이 안 먹은 채로** 발행 직전까지 갔다.

### 왜 그런가 (DOM 근거)

폰트 드롭다운 항목의 `innerText`를 찍어봤더니 이렇게 나왔다.

```
"19\n19"
```

숫자가 두 줄로 온다(선택된 항목은 `"16\n16\n선택됨"`처럼 세 줄). 그런데 예전 코드는 항목을 이렇게 찾고 있었다.

```python
# 예전 — 정확일치라 한 번도 안 맞음
has_text=re.compile(r"^19$")
```

`^19$` 정확일치는 `"19\n19"`에 **절대 안 맞는다.** 그래서 항목을 못 찾고 그냥 지나갔는데, 못 찾은 게 예외를 던지지도 않으니 로그엔 아무 흔적이 없었다. 전형적인 "조용한 실패"다.

### 실패한 접근

- `^19$` 정규식 정확일치 → 개행 때문에 영구 미스.
- 그냥 클릭만 하고 적용 여부를 확인 안 함 → 클릭이 빗나가도 통과.

### 해결

`innerText`를 개행으로 잘라 **첫 줄만** 비교하고, 성공 여부를 반환한다.

```python
def set_font_size(page, size: str) -> bool:
    page.locator("button.se-font-size-code-toolbar-button").click(timeout=4000)
    ok = page.evaluate("""(size) => {
        const box = [...document.querySelectorAll('.se-toolbar-option-font-size-code')]
                    .find(e => e.getClientRects().length);
        if (!box) return 'no-dropdown';
        const b = [...box.querySelectorAll('button')].find(
            x => ((x.innerText || '').trim().split('\\n')[0] === String(size)));
        if (!b) return 'no-option';
        b.click();
        return 'ok';
    }""", size)
    if ok != "ok":
        print(f"    [!] 폰트 크기 {size} 적용 실패 ({ok})")
    return ok == "ok"
```

`split('\n')[0]`로 첫 줄만 떼어 `"19"`와 비교한다. 그리고 `no-dropdown`/`no-option`/`ok`를 구분해 반환하니, 실패하면 로그에 왜 실패했는지가 남는다. "성공한 척"이 사라진 게 실제 수정의 절반이다.

> **🧭 기획자·사업자라면**
> 무인 자동화의 진짜 위험은 "터지는 실패"가 아니라 "조용한 실패"다. 크래시는 알림이 오지만, 폰트가 안 먹은 글은 며칠씩 그대로 발행되며 아무도 모른다. 그래서 **성공 로그를 신뢰하는 비용**과 **결과물을 검증하는 비용**은 다른 항목이다. 자동화를 도입할 때 "돌아가는 것"과 "맞게 돌아가는 것"을 확인하는 단계를 처음부터 공수에 넣어야, 몇 주 뒤 "그동안 나간 결과물이 다 틀어져 있었다"를 안 밟는다.
{: .prompt-tip }

## 함정 3 — 콜라주가 글 맨 아래로 밀린다

### 증상

사진 여러 장을 콜라주로 묶어 본문 중간에 넣었는데, 저장된 글에서 콜라주가 **글 맨 아래**에 혼자 떨어져 있다. 다른 날은 멀쩡하고, 사진 용량이 크거나 네트워크가 느린 날만 그런다 — 재현이 간헐적이라 더 골치였다.

![고정 sleep과 상태 폴링의 타임라인 비교](/assets/img/posts/naver-smarteditor-pitfalls-timeline.png)

### 왜 그런가

사진 업로드 뒤에 이렇게 고정 대기를 걸고 있었다.

```python
time.sleep(5)   # 업로드 끝나겠지
```

업로드가 5초 안에 끝나면 문제없다. 그런데 콜라주나 큰 사진이 5초를 넘기면, 봇은 이미 `sleep`을 끝내고 **다음 문단을 타이핑하는 중**이다. 그러다 뒤늦게 업로드가 완료되면 사진은 "지금 커서가 있는 위치"에 떨어지는데, 그 커서는 이미 글 아래쪽으로 내려가 있다. 그래서 사진이 글 맨 아래로 밀린다.

### 해결

시간을 믿지 말고 **DOM 상태를 믿는다.** `.se-component` 개수가 실제로 늘어날 때까지 폴링한다. 단, 반드시 상한(타임아웃)을 둬서 업로드가 끝내 안 되는 날 무한대기에 빠지지 않게 한다.

```python
before = page.locator(".se-component").count()
with page.expect_file_chooser(timeout=10000) as fc:
    page.locator("button.se-image-toolbar-button").click()
fc.value.set_files(files)
# ... (여러 장이면 '콜라주' 옵션 클릭) ...

landed = False
for _ in range(80):          # 최대 40초까지 기다린다
    if page.locator(".se-component").count() > before:
        landed = True
        break
    time.sleep(0.5)
if not landed:
    print(f"    [!] 사진 업로드 확인 실패 — 순서가 밀릴 수 있습니다")
```

`sleep(5)` → "컴포넌트 수가 늘 때까지, 단 최대 40초". 고정 대기를 상태 기반 대기로 바꾸는 건 브라우저 자동화의 기본기인데, 리치 에디터에서는 특히 이 한 줄이 순서를 지킨다.

## 함정 4 — 대표(썸네일) 이미지가 엉뚱한 걸로 나간다

### 증상

블로그 목록과 검색 결과에 뜨는 썸네일이, 정작 보여주고 싶은 사진이 아니라 글 맨 앞에 깔아둔 **배너/안내 이미지**로 나갔다.

![목록 썸네일이 배너에서 첫 실제 사진으로 바뀐 before/after](/assets/img/posts/naver-smarteditor-pitfalls-thumbnail.png)

### 왜 그런가

대표 이미지를 지정하는 코드가 아예 없었다. 그러면 네이버 기본 동작(**첫 번째 이미지 = 대표**)에 맡겨진다. 그런데 글 맨 앞에 배너 같은 걸 깔아두는 구조라면, 그 배너가 곧 목록·검색 썸네일이 되어버린다. 대표 이미지는 발행 다이얼로그가 아니라 **사진 컴포넌트 위에 붙은 버튼**(`button.se-set-rep-image-button`)으로 지정한다는 것도 처음엔 몰랐다.

### 해결

두 조각으로 나눴다. ① 어떤 사진을 대표로 삼을지 순번을 계산하고(`cover_index`), ② 그 순번의 컴포넌트에서 대표 버튼을 눌러 **정말 선택됐는지 확인**한다(`set_rep_image`).

```python
def cover_index(blocks) -> int:
    """대표로 삼을 사진이 몇 번째 이미지 컴포넌트인지 계산.
    파일명이 cover. 로 시작하는 걸 우선, 없으면 배너를 건너뛴 첫 실제 사진."""
    n, fallback = 0, None
    for b in blocks:
        if b[0] not in ("image", "images"):
            continue
        first = b[1][0] if isinstance(b[1], list) else b[1]
        name = Path(first).name.lower()
        if name.startswith("cover."):
            return n
        if fallback is None and "/assets/disclosure/" not in first.replace("\\", "/"):
            fallback = n
        n += 1
    return fallback if fallback is not None else 0
```

```python
def set_rep_image(page, index: int = 0) -> bool:
    comps = page.locator(".se-component:has(button.se-set-rep-image-button)")
    comp = comps.nth(index)
    btn = comp.locator("button.se-set-rep-image-button").first
    comp.click(timeout=6000)          # 버튼은 컴포넌트를 선택해야 눌린다
    btn.click(timeout=4000)
    ok = "se-is-selected" in (btn.get_attribute("class") or "")
    print(f"    [{'+' if ok else '!'}] 대표 이미지 지정 {'완료' if ok else '실패'}")
    return ok
```

`se-is-selected` 클래스로 지정 성공을 확인하는 게 포인트다. 이건 네이버 UI 버튼을 누르는 거라 네이버가 UI를 바꾸면 깨질 수 있다 — 그러니 **실패해도 예외를 삼키지 말고 반드시 로그로 남긴다.** 대표 이미지처럼 "발행 뒤에야 티 나는" 항목은 조용히 실패하면 제일 늦게 발견된다.

## 함정 5 — `--preview`: 저장하지 않고 결과를 눈으로 검증하는 하네스

여기까지 온 다섯 번째가 사실 **나머지 넷을 잡게 해준 도구**다. 함정 1~4는 공통점이 있다 — 캡션칸·폰트·콜라주 위치·대표 이미지 전부 **실제 에디터 화면을 봐야만** 맞는지 알 수 있다. 코드로 `activeElement`나 `innerText`를 찍어도 중첩 iframe과 지연 렌더 때문에 100% 확신이 안 선다.

그래서 저장/발행을 하지 않고 **에디터 화면만 스크롤하며 캡처**하는 모드를 만들었다. 저장 목록 UI를 거치지 않고 실제 렌더 결과를 그대로 눈으로 본다.

![body는 안 움직이고 .se-content 컨테이너가 스크롤되는 구조](/assets/img/posts/naver-smarteditor-pitfalls-scroll.png)

여기서도 함정이 둘 있었다.

### 함정 5-1 — 스크롤 대상이 `body`가 아니다

`window.scrollTo`로 화면을 내리며 캡처했더니 **딱 2장**만 찍히고 나머지는 같은 화면이었다. 원인은 `document.body.scrollHeight`가 **1000으로 고정**되어 있었던 것. 스마트에디터는 `body`가 아니라 내부 컨테이너(`.se-content`)가 스크롤된다. `body`를 아무리 내려도 안 움직인다.

셀렉터를 하드코딩하는 대신, **실제로 스크롤 가능한 요소를 찾아서** 그걸 움직인다.

```python
info = page.evaluate('''() => {
    let best = null;
    document.querySelectorAll('*').forEach(e => {
        const over = e.scrollHeight - e.clientHeight;
        if (over > 400 && e.clientHeight > 300 && (!best || over > best.over))
            best = {over, h: e.scrollHeight,
                    sel: e.className ? '.' + e.className.toString()
                         .trim().split(/\\s+/)[0] : e.tagName};
    });
    return best || {over: 0, h: document.body.scrollHeight, sel: 'window'};
}''')
```

`scrollHeight - clientHeight`(넘치는 양)가 가장 큰 요소를 스크롤 대상으로 고른다. 그러면 네이버가 컨테이너 클래스명을 바꿔도 알아서 따라간다.

### 함정 5-2 — 캡처 장수를 상한으로 자르면 글 끝이 말없이 안 찍힌다

처음엔 "최대 16장까지 캡처"처럼 **장수**로 상한을 뒀다. 그랬더니 긴 글의 뒤쪽(마무리·해시태그 줄)이 아무 경고 없이 안 찍혔다. 상한을 넘긴 부분이 조용히 사라진 것 — 검수용 도구가 정작 검수 대상을 빠뜨리는 아이러니다.

상한을 **장수가 아니라 간격(px)으로 흡수**하도록 바꿨다. 글이 길면 캡처 간격을 넓혀서라도 끝까지 담고, 넘칠 때만 경고를 띄운다.

```python
step, MAX_SHOTS = 800, 40
h = int(info["h"])
n = h // step + 1
if n > MAX_SHOTS:
    n, step = MAX_SHOTS, h // MAX_SHOTS + 1
    print(f"    [!] 글이 길어 캡처 간격을 {step}px 로 넓힙니다")
```

검수 도구의 제1원칙은 "빠뜨릴 때 조용하지 말 것"이다. 빠뜨리더라도 반드시 시끄럽게 빠뜨려야 검수의 의미가 산다.

## 사용한 기술

- **Playwright (sync API, `launch_persistent_context`)** — 로그인 세션을 프로필 디렉터리에 유지해 캡차/재로그인 자동화를 피한다.
- **`page.locator(...)` + `:has()` CSS 관계 셀렉터** — `.se-component:has([class*=caption])`처럼 "캡션칸을 가진 컴포넌트"를 한 번에 잡는다.
- **`page.evaluate`로 브라우저 컨텍스트 안에서 판정** — `innerText.split('\n')[0]`, `scrollHeight - clientHeight` 계산처럼 DOM 상태를 파이썬으로 끌어와 검증한다.
- **상태 기반 대기(polling) vs 고정 `sleep`** — `.se-component` 개수 증가를 기다리되 항상 상한을 둔다.
- **스크린샷 기반 시각 검수** — 코드 판정이 불확실한 리치 에디터에서는 결국 렌더된 화면이 최종 진실이다.

## 정리

다섯 개 버그가 전부 같은 뿌리였다. **로그의 성공은 "명령을 보냈다"는 기록일 뿐, "브라우저가 의도대로 반영했다"는 증거가 아니다.** 리치 에디터는 숨은 캡션칸, 개행이 낀 드롭다운 텍스트, 지연 업로드, 중첩 iframe으로 이 간극을 넓힌다.

교훈을 한 줄로 압축하면:

1. **캡션·폰트·대표 이미지처럼 "넣었다"고 끝나는 동작은 반드시 넣은 결과를 다시 읽어 확인한다.** (`innerText`로 되읽기)
2. **시간(`sleep`)이 아니라 상태(`.se-component` 개수)를 기다린다.** 단 상한을 둔다.
3. **코드 판정이 불확실하면 화면을 캡처해 눈으로 본다.** 그리고 그 검수 도구는 빠뜨릴 때 조용하지 않게 만든다.

다음 편에서는 이 스크립트를 **매일 무인으로 도는 라이브 파이프라인**에 코드로 이식하면서 겪은 것 — 봇이 몇 분 간격으로 커밋을 쏘는 저장소에 손대는 git 규율과, 경로에 `#`가 있어 스크립트가 잘리던 함정 — 을 정리한다.
