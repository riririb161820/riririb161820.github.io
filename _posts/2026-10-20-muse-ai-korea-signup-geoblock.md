---
title: "한국에서 muse.ai 가입하기 — 브라우저 위장은 전부 헛수고였다"
headline: "muse.ai 한국 가입"
highlight: "한국 가입"
date: 2026-10-20 13:35:00 +0900
categories: [개발, 운영]
tags: [meta-muse, vpn, wireguard, proton-vpn, geo-blocking]
description: "Meta의 개인 AI 에이전트 Muse는 미국·캐나다 전용이다. 언어·타임존·UA·위치 API를 전부 미국으로 바꿔도 대기자 명단으로 떨어진다. 지역 차단이 실제로 무엇을 보는지 실측으로 확인하고, 무료 VPN으로 미국 IP를 고정해 가입까지 끝낸 과정."
image:
  path: /assets/img/posts/muse-ai-korea-signup-geoblock-hero.webp
  alt: 브라우저 레벨 위장은 차단되고 출발 IP만 바꾸면 통과하는 구조를 비교한 그래픽
---

> **이 시리즈**
> - **1편 — 한국에서 muse.ai 가입하기 (현재 글)**
> - 2편 — VPN 없이 muse.ai 사용하기 *(곧 발행)*
{: .prompt-info }

## 문제

Meta가 내놓은 개인 AI 에이전트 **Muse**(muse.ai)는 미국과 캐나다에서만 쓸 수 있다. 한국에서 가입을 시도하면 이상하게도 **중간까지는 다 된다.**

이메일을 넣으면 인증 코드가 오고, 코드를 넣으면 통과하고, 이름과 생년월일을 넣고 Confirm까지 눌러 **Meta 계정이 실제로 생성된다.** 그런데 바로 그 다음 화면에서 끝난다.

```text
Join the waitlist for Muse
Muse isn't available in your country or region yet.
We'll let you know when it's available to you.
```

![왼쪽은 브라우저를 조종한 작업 로그, 오른쪽은 muse.ai/access가 대기자 명단 화면을 띄운 모습](/assets/img/posts/muse-ai-korea-signup-geoblock-waitlist.webp)
_가입 폼을 전부 통과한 뒤 `muse.ai/access`에서 떨어진다_

가입 폼 어디에도 국가를 묻는 입력란이 없었다. 그런데 마지막에 국가를 이유로 막는다. **어디서 국가를 판정하는가?** 이게 이 글의 출발점이다.

## 원인

### 처음 의심한 것: 브라우저가 한국을 흘리고 있다

가장 먼저 떠오른 건 브라우저가 내보내는 신호였다. 한국어 브라우저, `Asia/Seoul` 타임존, 한국 좌표. Chrome DevTools로 전부 미국으로 덮었다.

| 항목 | 원래 | 위장 후 |
|---|---|---|
| `Accept-Language` | `ko-KR` | `en-US,en;q=0.9` |
| `navigator.language` | `ko-KR` | `en-US` |
| `Intl...timeZone` | `Asia/Seoul` | `America/Los_Angeles` |
| `getTimezoneOffset()` | `-540` | `420` |
| User-Agent | 한국 환경 | macOS Chrome 141 |
| 위치 API | 서울 | 샌프란시스코 |

타임존은 에뮬레이션 옵션에 없어서 페이지 로드 전 주입 스크립트로 덮었다.

```js
const ro = Intl.DateTimeFormat.prototype.resolvedOptions;
Intl.DateTimeFormat.prototype.resolvedOptions = function () {
  const o = ro.call(this);
  o.timeZone = 'America/Los_Angeles';
  return o;
};
Date.prototype.getTimezoneOffset = function () { return 420; };
```

페이지는 실제로 영어로 바뀌었다. 위장 자체는 먹혔다. **그래도 대기자 명단이었다.**

### 밝혀진 것: 게이트는 출발 IP만 본다

답은 나중에 역방향으로 나왔다. 미국 IP를 붙인 뒤, **위장을 하나도 걸지 않은 한국어 브라우저**로 접속했더니 그대로 통과했다.

즉 Meta는 브라우저가 뭐라고 말하는지에 관심이 없다. **패킷이 어디서 출발했는지만 본다.** 가입 폼에 국가 입력란이 없었던 것도 같은 이유다 — IP로 판정하는데 굳이 물어볼 이유가 없다.

여기서 분명히 해둘 것이 있다. **브라우저로 바꿀 수 있는 것은 언어·UA·타임존·위치 API까지다. 출발 IP는 브라우저가 건드릴 수 없다.** 자동화 도구로 브라우저를 아무리 정교하게 조종해도 이 선은 못 넘는다.

> **🧭 기획자·사업자라면**
> 지역 제한을 설계할 때 판정축이 무엇인지가 사용자 경험을 가른다. Muse는 **계정 생성을 다 받아놓고 마지막에 차단**한다. 사용자 입장에선 이메일 인증까지 끝낸 뒤 거절당하는 셈이라 체감 불만이 크다. 국가 판정을 진입 시점으로 당기거나, 최소한 가입 전 안내를 두는 편이 이탈 비용이 낮다.
{: .prompt-tip }

## 해결 과정

### 1. 무료 VPN에는 함정이 있다 — 국가를 고를 수 없다

미국 IP가 필요하다는 건 알았다. Proton VPN 무료 플랜을 봤더니 조건이 나쁘지 않았다. 데이터 무제한, 카드 등록 불필요, 그리고 **10개국에 미국과 캐나다가 모두 포함**되어 있다. Muse가 지원하는 두 나라가 다 들어 있는 것이다.

문제는 공식 문서의 이 문장이었다.

> Free: Servers in 10 countries, **randomly selected**, so you can't choose a specific country.

앱으로 연결하면 10개국 중 아무 데나 붙는다. 미국이 걸릴 때까지 재접속을 반복해야 하고, 서버 변경에는 쿨다운까지 있다.

### 2. WireGuard 설정 파일은 서버를 직접 고르게 해준다

여기가 이 글의 핵심이다. **앱에서는 국가를 못 고르지만, WireGuard 설정 파일 생성 페이지에서는 서버를 직접 지정할 수 있다.**

`account.proton.me` → VPN → WireGuard 로 들어가면 플랫폼을 고르고 서버를 선택해 `.conf`를 내려받는 화면이 있다. 무료 계정인데도 **미국 섹션에 `US-FREE#12`부터 수십 대가 부하율과 함께 전부 나열된다.** 각 행의 생성 버튼을 누르면 그 서버로 고정된 설정 파일이 만들어진다.

![Proton 계정의 WireGuard 설정 페이지에서 US-FREE 서버들이 부하율과 함께 나열된 목록](/assets/img/posts/muse-ai-korea-signup-geoblock-proton-wireguard.webp)
_무료 플랜인데도 미국 서버를 하나씩 지정해 설정 파일을 만들 수 있다_

무작위 배정 제약이 여기서 무력화된다.

내려받은 파일이 정말 미국인지는 엔드포인트 주소로 확인했다.

```bash
$ grep Endpoint pvpnus.conf
Endpoint = 149.40.62.56:51820

$ curl -s https://ipinfo.io/149.40.62.56/json
{
  "city": "Seattle",
  "region": "Washington",
  "country": "US",
  "org": "AS212238 Datacamp Limited"
}
```

### 3. `wg-quick`이 설정 파일을 거부한다

터널을 올리려다 바로 막혔다.

```text
wg-quick: The config file must be a valid interface name, followed by .conf
```

Proton이 내려준 파일명은 `mac-muse-us-US-FREE-26.conf`였다. 앞부분이 **22자**다. 네트워크 인터페이스 이름은 15자를 넘을 수 없어서 파일명 자체가 거부당한 것이다. 설정 내용과는 무관하다.

짧은 이름으로 복사하면 끝난다.

```bash
mkdir -p /opt/homebrew/etc/wireguard
cp ~/Downloads/mac-muse-us-US-FREE-26.conf /opt/homebrew/etc/wireguard/pvpnus.conf
chmod 600 /opt/homebrew/etc/wireguard/pvpnus.conf   # 개인키가 들어 있다

sudo PATH=/opt/homebrew/bin:$PATH wg-quick up /opt/homebrew/etc/wireguard/pvpnus.conf
```

`PATH`를 명시한 이유는 `wg-quick`이 내부적으로 `wg`와 `wireguard-go`를 호출하는데, `sudo` 환경에는 Homebrew 경로가 없어서다.

### 4. 터널은 붙었는데 모든 사이트가 안 열린다

터널이 올라왔고 출구 IP도 시애틀로 바뀌었다. 그런데 브라우저가 **모든 주소에서 `ERR_NAME_NOT_RESOLVED`**를 뱉었다. `curl`은 exit code 6(호스트 해석 실패)이었다.

이상한 건, **IP를 직접 때리면 정상 응답**이 온다는 점이었다. 연결은 멀쩡하고 이름 해석만 죽은 것이다.

```bash
$ scutil --dns | grep -m8 "nameserver\["
  nameserver[0] : 100.100.100.100
  nameserver[1] : fd7a:115c:a1e0::53
  nameserver[0] : 10.2.0.1
```

`100.100.100.100`은 **Tailscale의 MagicDNS**다. Tailscale이 시스템 DNS 1순위를 쥐고 있었는데, 전체 터널이 올라가면서 Tailscale로 가는 경로가 끊겼다. 그러니 1순위 resolver가 응답 불능이 된 것이다. Proton이 넣어준 `10.2.0.1`은 멀쩡했다 — 직접 질의하면 정상 응답한다.

```bash
$ dig +short @10.2.0.1 ipinfo.io
34.117.59.81
```

Tailscale을 내리면 해결된다. 둘은 동시에 못 쓴다.

```bash
osascript -e 'quit app "Tailscale"'
```

### 5. 연령 확인 — 카드, 인스타그램, 페이스북

미국 IP로 다시 들어가니 대기자 명단이 사라지고 온보딩으로 넘어갔다. 그런데 마지막 관문이 하나 더 있었다.

```text
Confirm your age
Use credit card info to help us confirm your age.
Your card will be charged $1.00, which will be refunded in 5-7 business days.
...
You can also continue with your Instagram or Facebook account to confirm your age.
```

세 갈래인데 결과가 갈렸다.

**카드** — 국가 드롭다운에 South Korea가 있지만, 한국 카드에 한국 청구 국가를 넣는 순간 "미국에서 접속한 사용자"라는 전제와 정면으로 충돌한다. 실제로 카드가 계속 거부됐다는 보고가 많다.

**인스타그램** — 시도했지만 **"로봇이 아닙니다" 화면이 뜬 뒤 로그인 폼으로 되돌아오는 루프**에 갇혔다. 세션이 아예 생성되지 않았다. VPN 대역이 데이터센터 IP로 분류돼 의심 로그인 방어가 발동한 것으로 보인다. 평소 한국에서 쓰던 계정에 갑자기 시애틀 IP로 접근했으니 당연한 반응이다.

**페이스북** — 한 번에 통과했다. 같은 Meta 서비스인데 인스타그램보다 VPN IP에 관대했다.

연령 확인이 뜨면 페이스북 연동이 가장 빠르다. 이 패턴은 커뮤니티 후기에서도 반복적으로 보고된다.

> **⚠️ 주의**
> 연령 확인에 소셜 계정을 연동하면 **그 계정의 실제 신원이 Muse 계정에 결합된다.** IP는 미국으로 바꿨어도 연결된 계정의 가입 국가와 활동 이력은 한국이다. 지역 우회는 Meta 약관 위반 소지가 있고, 불일치가 누적되면 나중에 계정이 제한될 수 있다.
{: .prompt-warning }

## 사용한 기술

- **Chrome DevTools MCP** — 브라우저를 외부에서 조종해 스냅샷·입력·헤더 에뮬레이션 수행. `Accept-Language` 주입과 위치 오버라이드가 여기서 나온다.
- **Proton VPN Free** — 데이터 무제한, 10개국(US·CA 포함), 동시 1기기. 앱은 국가 선택 불가지만 WireGuard 설정 생성은 서버 지정이 된다.
- **WireGuard / `wg-quick`** — `brew install wireguard-tools`. 인터페이스 이름 15자 제한에 주의.
- **`scutil --dns`** — macOS의 실제 resolver 우선순위 확인. DNS 문제는 여기서 시작하면 빠르다.
- **`ipinfo.io`** — 출구 IP와 임의 IP의 지리 정보 조회. 터널이 진짜 미국으로 나가는지 검증하는 데 사용.

## 정리

- Muse의 지역 차단은 **출발 IP만 본다.** 언어·타임존·UA·위치 API를 아무리 미국으로 맞춰도 소용없고, 반대로 미국 IP만 있으면 한국어 브라우저로도 통과한다.
- 무료 VPN은 "국가 선택 불가"가 기본이지만, **WireGuard 설정 파일을 직접 생성하면 서버를 고정**할 수 있다. 이게 무료 플랜의 실질적인 제약 해제 지점이다.
- 가입 과정에서 막히는 두 지점은 **DNS 충돌**(Tailscale 등 다른 VPN과 공존 불가)과 **연령 확인**(페이스북 연동이 가장 안정적)이다.

그런데 가입을 마치고 나서 예상 밖의 사실을 하나 더 확인했다. **VPN을 내려도 Muse가 그대로 열린다.** 다음 편에서 다룬다.
