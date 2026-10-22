---
title: "muse.ai는 VPN 없이 쓸 수 있다 — 지역 차단이 걸리는 진짜 시점"
headline: "VPN은 가입 때만"
highlight: "가입 때만"
date: 2026-10-22 07:00:00 +0900
categories: [개발, 운영]
tags: [meta-muse, vpn, geo-blocking, whatsapp, app-store]
description: "미국 IP로 Muse 가입을 끝내고 나서 VPN을 내려봤다. 웹앱이 한국 IP로 그대로 열렸다. 지역 게이트가 계정 프로비저닝 단계에만 걸린다는 뜻이다. 폰에서는 앱스토어 국가 제한이라는 다른 벽이 있었고, 그건 WhatsApp 채널로 넘었다."
image:
  path: /assets/img/posts/muse-ai-no-vpn-after-signup-hero.webp
  alt: 신규 가입에만 VPN이 필요하고 가입 완료 후에는 웹앱과 WhatsApp 채널이 VPN 없이 동작하는 구조도
---

> **이 시리즈**
> - 1편 — [한국에서 muse.ai 가입하기 — 브라우저 위장은 전부 헛수고였다](/posts/muse-ai-korea-signup-geoblock/)
> - **2편 — muse.ai는 VPN 없이 쓸 수 있다 (현재 글)**
{: .prompt-info }

## 문제

[1편](/posts/muse-ai-korea-signup-geoblock/)에서 미국 IP를 고정해 Muse 가입을 끝냈다. 그러고 나니 당연한 질문이 남았다.

**쓸 때마다 VPN을 켜야 하나?**

이게 사소한 문제가 아닌 이유가 있다. 터널이 전체 트래픽을 미국으로 보내기 때문에 켜두는 동안 국내 서비스가 느려지고, Tailscale 같은 다른 VPN과는 아예 공존이 안 된다. 게다가 Proton 무료 플랜은 **동시 1기기**라 맥과 폰 중 하나만 쓸 수 있다.

그리고 폰에는 벽이 하나 더 있었다. **한국 앱스토어에 Muse 앱이 없다.**

## 원인

### 지역 게이트는 "계속" 걸리는 게 아니었다

VPN을 내리고 출구 IP가 한국으로 돌아온 상태에서 그냥 들어가 봤다.

```bash
$ curl -s https://ipinfo.io/json
{
  "city": "Seoul",
  "country": "KR",
  "org": "AS4766 Korea Telecom"
}
```

이 상태로 `muse.ai`를 열었더니 **대기자 명단이 아니라 앱이 그대로 떴다.** 혹시 캐시인가 싶어 캐시를 무시하고 다시 로드했고, 1편에서 차단당했던 `muse.ai/access`를 **주소창에 직접 입력**해봤다. 결과는 앱으로 리디렉트였다.

| 시점 | 출구 IP | `muse.ai/access` 결과 |
|---|---|---|
| 가입 시도 (1편) | 서울 · KT | ❌ Join the waitlist |
| 가입 직후 | 시애틀 · US | ✅ 온보딩 진입 |
| **가입 완료 후** | **서울 · KT** | **✅ 앱으로 리디렉트** |

같은 IP, 같은 URL인데 결과가 뒤집혔다. 바뀐 변수는 **계정이 프로비저닝됐다는 것** 하나다.

즉 Meta는 요청마다 국가를 검사하는 게 아니라, **계정을 발급할 때 한 번** 검사한다. 한번 발급된 계정은 어디서 접속하든 열린다.

> **🧭 기획자·사업자라면**
> 지역 제한을 **프로비저닝 시점에만** 거는 설계는 서버 부담이 적고 정상 사용자(여행·출장 중 접속)를 막지 않는다는 장점이 있다. 대신 **"한 번만 통과하면 영구히 열린다"**는 뜻이기도 하다. 차단의 목적이 *법적 준수*인지 *수요 조절*인지에 따라 이 설계의 적정성이 갈린다. 전자라면 지속 검증이 필요하고, 후자라면 지금 설계로 충분하다.
{: .prompt-tip }

### 폰은 별개의 벽이다 — 앱스토어 국가

웹은 해결됐는데 폰은 다른 문제였다. 한국 앱스토어에서 Muse를 검색하면 나오지 않는다.

스토어 등록 여부는 **iTunes Search API**로 국가별 비교가 가능하다. 앱을 설치하거나 계정을 바꾸지 않고도 확인할 수 있어서 이럴 때 유용하다.

```bash
curl -s "https://itunes.apple.com/search?term=muse%20meta&entity=software&country=us&limit=8"
curl -s "https://itunes.apple.com/search?term=muse%20meta&entity=software&country=kr&limit=8"
```

결과가 갈렸다.

| 스토어 | `Muse from Meta` (`com.facebook.hatch`) |
|---|---|
| 미국 | ✅ 등록됨 |
| 한국 | ❌ 없음 |

**지역 차단과 앱스토어 국가 제한은 완전히 별개의 축이다.** VPN으로 IP를 바꿔도 Apple ID의 국가는 그대로라 설치가 안 된다. 미국 Apple ID를 따로 만드는 수밖에 없는데, 그러면 기존 계정으로 산 앱의 업데이트가 꼬인다.

![서비스 지역 차단은 출발 IP를, 앱스토어 제한은 Apple ID 국가를 본다는 두 벽의 비교도](/assets/img/posts/muse-ai-no-vpn-after-signup-two-walls.webp)
_판정 축이 다르면 우회 수단도 달라진다_

## 해결 과정

### 1. WhatsApp 채널 — 앱스토어를 통째로 건너뛴다

Muse 설정을 뒤지다 **Messaging channels** 항목을 발견했다.

> Chat with your agent in other messaging apps.
> **Available — WhatsApp**

WhatsApp은 한국 앱스토어에 정상 등록돼 있다. 즉 **Muse 앱을 설치할 수 없어도 WhatsApp으로 에이전트와 대화할 수 있다.** 연결은 QR 스캔 한 번이다.

설정 → Messaging channels → WhatsApp 을 열면 QR이 나오고, 폰의 WhatsApp으로 스캔하면 끝난다. 상태 표시가 `Available`에서 `Connected`로 바뀐다.

그리고 **연결 후 폰에서 VPN 없이 Muse에게 메시지를 보내 답장을 받았다.** 당연한 결과다 — WhatsApp 트래픽은 `muse.ai`가 아니라 WhatsApp 서버로 가고, 애초에 계정 게이트는 이미 통과한 상태다.

> **⚠️ 이 QR은 비밀번호와 같다**
> Muse가 QR 아래에 직접 경고를 붙여둔다.
> *"This code gives full control of your agent. Keep it safe and don't share it with others."*
> 스크린샷으로 남기거나 공유하면 에이전트 제어권이 통째로 넘어간다. 이 글에 QR 화면 캡처를 싣지 않은 이유이기도 하다.
{: .prompt-warning }

### 2. 대안으로 준비했다가 필요 없어진 것 — WireGuard 앱 + Safari

WhatsApp을 찾기 전에는 "폰에도 VPN을 깔고 Safari로 웹앱을 쓰자"는 쪽으로 준비했었다. 실제로 설정까지 다 만들어뒀다.

한국 앱스토어 등록 여부부터 확인했고, 둘 다 있었다.

| 앱 | 번들 ID | 한국 스토어 |
|---|---|---|
| WireGuard | `com.wireguard.ios` | ✅ |
| Proton VPN | `ch.protonmail.vpn` | ✅ |

Proton 앱은 무료 플랜에서 국가를 못 고르니([1편 참고](/posts/muse-ai-korea-signup-geoblock/)), 폰에서도 **WireGuard 설정 파일로 미국 서버를 고정**하는 편이 확실하다. Proton 계정의 WireGuard 페이지에서 플랫폼을 iOS로 고르고 미국 서버를 선택해 `.conf`를 받은 뒤, 맥에서 폰으로 AirDrop하면 WireGuard 앱이 받아 가져온다.

```bash
$ grep Endpoint iphone-muse-us-US-FREE-32.conf
Endpoint = 203.0.113.59:51820

$ curl -s https://ipinfo.io/203.0.113.59/json | grep -E '"city"|"country"'
  "city": "Seattle",
  "country": "US",
```

> 여기 적힌 IP는 `203.0.113.x`(RFC 5737 문서용 예약 대역)로 바꿔 쓴 값이다. 실제 서버 주소가 아니니 **본인 계정에서 받은 설정 파일의 엔드포인트를 그대로 쓰면 된다.**
{: .prompt-info }

**그런데 결국 쓰지 않았다.** 앞에서 확인했듯 가입이 끝난 계정은 VPN이 아예 필요 없기 때문이다. 게다가 Proton 무료는 동시 1기기라 폰을 붙이면 맥을 내려야 한다. 만들어놓고 버린 경로지만, "VPN이 필요 없다"를 확인하기 전까지는 합리적인 준비였다.

### 3. 정리된 운용 모델

| 상황 | VPN |
|---|---|
| **신규 가입** | **필요** — 미국 IP로 계정을 발급받는 단계 |
| 맥에서 웹앱 사용 | 불필요 |
| 폰에서 WhatsApp으로 사용 | 불필요 |
| 폰에 Muse 앱 설치 | VPN으로 해결 안 됨 (미국 Apple ID 필요) |

터널을 내리고 Tailscale을 다시 켰다. 평소 환경 그대로 Muse를 쓴다.

```bash
sudo PATH=/opt/homebrew/bin:$PATH wg-quick down /opt/homebrew/etc/wireguard/pvpnus.conf
```

## 사용한 기술

- **iTunes Search API** — `https://itunes.apple.com/search?term=...&entity=software&country=<국가코드>`. 앱 설치나 계정 전환 없이 **스토어 국가별 등록 여부**를 비교할 수 있다. "이 앱이 한국에 있나?"를 확인하는 가장 빠른 방법이다.
- **Muse Messaging channels** — 에이전트를 외부 메신저에 연결하는 기능. 현재 WhatsApp을 지원한다.
- **WireGuard iOS** — 설정 파일을 AirDrop으로 넘기면 바로 가져온다. 결국 쓰지 않았지만 폰에서 국가를 고정해야 할 때의 경로.
- **`wg-quick down`** — 터널 해제. Tailscale과 공존이 안 되므로 작업이 끝나면 내리는 편이 낫다.

## 정리

- Muse의 지역 차단은 **계정 프로비저닝 때 한 번만** 걸린다. 가입만 미국 IP로 끝내면 그 뒤로는 한국 IP에서 웹앱까지 전부 열린다.
- **앱스토어 국가 제한은 VPN으로 해결되지 않는다.** IP가 아니라 Apple ID 국가를 보기 때문이다. 스토어 등록 여부는 iTunes Search API로 미리 확인할 수 있다.
- 폰에서는 **WhatsApp 채널**이 가장 깔끔하다. 앱 설치도, VPN도 필요 없다. 단 연결 QR은 에이전트 제어권 자체이므로 비밀번호처럼 다뤄야 한다.
