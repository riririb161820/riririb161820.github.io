`pbcopy < file.txt`를 실행했는데 붙여넣기가 비어 있다. 에러도 없고 종료 코드는 0이다. 영문은 멀쩡히 복사되고 한글만 사라진다.

원인은 비어 있는 `$LANG`이다. 로케일이 없으면 pbcopy는 UTF-8이 아닌 인코딩으로 입력을 읽는데, 시스템 언어가 한국어인 맥에서 그 인코딩은 EUC-KR 계열이었다. UTF-8 한글은 거기서 유효하지 않으니 통째로 버려진다. 터미널 앱은 로케일을 알아서 잡아줘서 안 겪고, launchd·CI·에이전트 도구가 띄운 셸에서 나온다.

로케일 값을 하나씩 바꿔 가며 재 보니 의외인 것도 있었다. `LANG=ko_KR`처럼 `.UTF-8`을 빼면 여전히 0바이트다.

## 문제 — 한글이 0바이트로 복사됐다

한글이 든 텍스트 파일을 클립보드에 넣으려 했다.

```bash
pbcopy < prompt.txt
```

종료 코드 0. 에러 없음. 그런데 붙여넣으면 **아무것도 안 나온다.**

```bash
pbpaste | wc -c
#        0
```

파일은 멀쩡했다.

```bash
wc -c prompt.txt
#     3872 prompt.txt
```

## 해결

로케일을 명시한다.

```bash
LANG=ko_KR.UTF-8 LC_ALL=ko_KR.UTF-8 pbcopy < prompt.txt
```

`en_US.UTF-8`이어도 된다. 중요한 건 언어가 아니라 **`.UTF-8`** 부분이다. 꺼낼 때도 마찬가지다.

```bash
LANG=ko_KR.UTF-8 pbpaste > out.txt
```

그리고 복사한 다음엔 **반드시 검증한다.** 이 버그의 본질은 "조용히 실패한다"는 것이라, 확인하지 않으면 다음 단계까지 빈 클립보드를 들고 간다.

![locale이 비어 있음을 확인하고, LANG을 지정해 복사한 뒤 바이트 수를 비교해 OK를 받는 터미널 화면](https://riririb.com/assets/img/posts/macos-pbcopy-korean-empty-lang-locale-terminal.png)
_진단 → 수정 → 검증. 마지막 줄의 바이트 수 비교가 핵심이다._

```bash
LANG=ko_KR.UTF-8 pbcopy < prompt.txt
[ "$(LANG=ko_KR.UTF-8 pbpaste | wc -c)" = "$(wc -c < prompt.txt)" ] && echo OK || echo MISMATCH
```

launchd처럼 셸 설정이 없는 환경이면 아예 환경변수로 박아두는 게 낫다.

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>LANG</key>
  <string>ko_KR.UTF-8</string>
</dict>
```

> **🧭 기획자·사업자라면**
>
> - **"에러가 없다"와 "성공했다"는 다른 말이다.** 이 버그는 종료 코드 0으로 실패한다. 자동화 파이프라인을 점검할 때 "실패 알림이 안 왔으니 잘 돌고 있다"는 가장 위험한 가정이다.
> - **한글 환경은 기본값이 아니다.** 해외 도구·CI·SaaS는 ASCII를 기본 가정으로 만들어진다. 영문으로만 테스트하면 이 버그는 아예 안 보인다. 한국어 서비스라면 **테스트 데이터에 한글을 반드시 넣는 것**이 가장 싼 방어선이다. 같은 사고는 클립보드뿐 아니라 파일명·CSV·PDF 생성에서도 같은 형태로 반복된다.

---

### 전체 내용은 원문에

이 글은 발췌본입니다. 실패한 시도와 검증 과정까지 포함한 전문은 원문에 있습니다.

👉 **[macOS pbcopy·pbpaste 사용법 — 한글이 0바이트로 복사될 때 원인은 비어 있는 $LANG](https://riririb.com/posts/macos-pbcopy-korean-empty-lang-locale/)**
