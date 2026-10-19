---
title: "커버 이미지 4.57MB를 90KB로 — 같은 그림, 변환만 했다"
headline: "커버 4.57MB→90KB"
highlight: "4.57MB→90KB"
date: 2026-10-19 14:30:00 +0900
categories: [개발, 운영]
tags: [webp, performance, jekyll, chirpy, lighthouse]
description: "블로그 홈 첫 화면이 커버 이미지만으로 4.5MB를 받고 있었다. 1080² PNG를 640² WebP로 바꿔 90KB로 줄인 과정 — 원본을 지우지 않는 이유, eager/lazy 분기, width·height를 적어야 하는 이유까지."
image:
  path: /assets/img/posts/blog-cover-image-webp-optimization-hero.webp
  alt: 홈 첫 화면 커버 10장이 PNG 4.57MB에서 WebP 90KB로 줄어든 비교 그래프
---

## 문제

블로그 메인에 카드뉴스형 커버를 깔았다. 글마다 1080×1080 PNG를 한 장씩 만들어 붙이는 구조였다.

보기엔 좋았는데, PageSpeed Insights 모바일 점수가 이랬다.

| 항목 | 점수 |
|---|---|
| SEO | 100 |
| 권장사항 | 100 |
| 접근성 | 95 |
| **성능** | **63** |

성능만 혼자 떨어져 있었다. 세부 지표를 보니 원인이 명확했다.

- **LCP 12.3초** (가장 큰 콘텐츠가 그려지기까지)
- FCP 3.8초
- 이미지 절감 여지 **2.9MB** / 전체 페이지 **4.2MB**

페이지 무게의 대부분이 이미지였고, 그 이미지가 전부 커버였다.

## 원인 — 1080² PNG를 640 자리에 넣고 있었다

두 가지가 겹쳤다.

**① 포맷.** PNG는 사진·일러스트에 비효율적이다. 커버는 FLUX로 만든 일러스트 위에 텍스트를 얹은 그림이라 색 영역이 넓은데, PNG는 무손실이라 그대로 다 저장한다.

**② 크기.** 원본은 1080×1080인데, 홈 카드가 실제로 쓰는 표시 크기는 그 절반 정도다. **화면에 안 쓰이는 픽셀을 그대로 내려받고 있었다.**

지금 수치로 재보면 이렇다.

```bash
# 커버 40장 PNG 합계
17.76 MB   (평균 455 KB)
```

홈 첫 화면에 뜨는 10장만 따져도 **4.57MB**다. 모바일에서 이걸 받고 나서야 첫 화면이 완성되니 LCP가 12초를 넘을 수밖에 없다.

## 해결 — 640² WebP로 변환하고, 원본은 남긴다

![gen_cover.py가 PNG와 WebP를 함께 만들고, 웹은 WebP를 인스타는 PNG를 쓰는 구조](/assets/img/posts/blog-cover-image-webp-optimization-flow.webp)

커버 생성기(`tools/gen_cover.py`)가 PNG를 만든 직후 WebP를 함께 뽑도록 했다.

```python
def to_webp(png_path: str) -> str | None:
    """블로그가 실제로 서빙하는 640² WebP를 함께 만든다."""
    webp = os.path.splitext(png_path)[0] + ".webp"
    try:
        subprocess.run(["cwebp", "-quiet", "-q", "80", "-resize", "640", "640",
                        png_path, "-o", webp], check=True)
    except FileNotFoundError:
        print("  [!] cwebp 없음 — WebP 미생성. `brew install webp` 후 다시 실행하세요.")
        return None
    print("  ✓", os.path.basename(webp))
    return webp
```

`cwebp` 한 줄이다. `-q 80`(품질)과 `-resize 640 640`(크기)을 같이 건다. **포맷만 바꾸는 게 아니라 크기도 함께 줄이는 게 핵심**이다 — 둘 중 하나만 하면 절반의 효과만 난다.

결과는 이렇다.

| | PNG 1080² | WebP 640² | |
|---|---|---|---|
| 커버 1장 평균 | 455 KB | **9.5 KB** | |
| 홈 첫 화면 10장 | 4.57 MB | **90 KB** | **52배** |
| 커버 40장 전체 | 17.76 MB | **382 KB** | 97.9% 절감 |

눈으로 봐도 차이가 없다. 아래가 현재 홈이다.

![WebP 커버로 렌더된 현재 블로그 홈 화면](/assets/img/posts/blog-cover-image-webp-optimization-home.webp)

### ① PNG 원본은 지우지 않는다

변환했다고 원본을 지우면 안 된다. **인스타그램 카드 파이프라인이 `covers/<slug>.png`를 그대로 쓴다.** 1:1 1080² 규격이 인스타 피드 규격과 같아서 그대로 재사용하는 구조다.

웹에서는 **참조만 안 할 뿐**이고 저장소에는 둘 다 남는다. `_layouts/home.html`이 `.webp`를 가리키도록 바꾸는 것으로 끝난다.

```liquid
{% assign cover = '/assets/img/covers/' | append: post.slug | append: '.webp' %}
```

### ② 첫 2장만 eager, 나머지는 lazy

전부 `lazy`로 걸면 **첫 화면에 보이는 카드까지 늦게 뜬다.** LCP를 잡으려던 작업이 LCP를 망치는 셈이다.

반대로 전부 `eager`면 스크롤해야 보이는 카드까지 한꺼번에 받는다.

```liquid
<img src="{{ cover | relative_url }}" alt="{{ post.title | xml_escape }}"
     width="640" height="640"
     {% if forloop.index <= 2 %}loading="eager" fetchpriority="high"
     {% else %}loading="lazy" decoding="async"{% endif %}>
```

화면에 바로 보이는 **첫 2장만** `eager` + `fetchpriority="high"`로 올리고, 나머지는 `lazy` + `decoding="async"`로 내렸다.

### ③ width·height를 반드시 적는다

이게 빠지면 **레이아웃이 튄다.** 이미지가 로드되기 전에는 높이가 0이라 아래 내용이 위로 올라와 있다가, 로드되는 순간 밀려 내려간다. 사용자가 읽던 줄이 움직이고, Lighthouse는 이걸 CLS(누적 레이아웃 이동)로 잡는다.

`lazy`를 걸면 로드가 늦어지므로 **이 문제가 더 심해진다.** `width="640" height="640"`을 적어 브라우저가 미리 자리를 잡게 해야 한다.

> **포맷 변경만 하고 `width`·`height`를 안 적으면, 무게는 줄었는데 체감은 더 나빠질 수 있다.** 용량과 레이아웃 안정성은 별개 지표다.
{: .prompt-warning }

## 함정 — `_src` 폴더는 배포에서 빠진다

커버의 배경 일러스트 원본은 `assets/img/covers/_src/`에 보관한다. 그런데 **Jekyll은 언더스코어로 시작하는 폴더를 빌드에서 제외한다.** `_posts`·`_layouts`처럼 Jekyll의 예약 영역으로 취급하기 때문이다.

의도한 동작이었다 — 배경 원본은 웹에 서빙할 필요가 없으니까. 다만 **모르고 쓰면 "파일을 올렸는데 404"로 한참 헤맨다.** 저장소에는 있고 사이트에는 없다.

배포에 포함돼야 하는 자산이라면 언더스코어로 시작하는 폴더에 두면 안 된다.

> **🧭 기획자·사업자라면**
> **"보기 좋게"와 "빨리 뜨게"는 종종 반대 방향이다.** 커버 이미지를 넣은 건 메인을 보기 좋게 만들려던 결정이었고, 그게 성능 63점과 LCP 12초를 만들었다. 디자인 결정을 할 때 **"이게 몇 KB짜리 결정인가"**를 같이 물어야 한다.
> **그리고 이번 작업은 콘텐츠를 하나도 안 줄였다.** 그림도 자리도 그대로고 변환만 했는데 52배가 줄었다. 성능 개선을 "뭘 뺄까"로 접근하기 전에, **같은 것을 더 싸게 전달하는 방법**이 남아 있는지 먼저 본다. 뺄 것을 고르는 회의보다 이쪽이 훨씬 싸게 끝난다.
{: .prompt-tip }

## 사용한 기술

- **WebP** — 구글이 만든 이미지 포맷. 같은 품질에서 PNG·JPEG보다 작다. 주요 브라우저 전부 지원한다.
- **`cwebp`** — WebP 변환 CLI(`brew install webp`). `-q`로 품질, `-resize`로 크기를 같이 지정한다.
- **`loading="lazy"` / `fetchpriority="high"`** — 브라우저 기본 기능. 화면 밖 이미지는 미루고, LCP 후보는 우선 받게 한다.
- **`width`·`height` 속성** — 로드 전에 자리를 잡아 CLS를 막는다. lazy를 쓸수록 더 중요하다.
- **Jekyll의 언더스코어 규칙** — `_`로 시작하는 폴더는 빌드 산출물에서 제외된다. 보관용 원본을 두기엔 좋고, 서빙할 자산을 두기엔 나쁘다.

## 정리

- 이미지 성능은 **포맷과 크기를 같이** 손봐야 한다. 한쪽만 하면 절반만 줄어든다.
- 원본을 지울 필요는 없다. **웹에서 참조하지 않는 것만으로 충분**하고, 다른 파이프라인이 원본을 계속 쓸 수 있다.
- `lazy`를 걸 때는 **첫 화면 이미지를 제외**하고, `width`·`height`를 반드시 함께 적는다.
