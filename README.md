# Galaxy Battery Check

**v1.4.3 · Windows · Python · ADB · 비공식 프로그램**

Galaxy Battery Check는 삼성 갤럭시 스마트폰이 ADB(Android Debug Bridge)를 통해 제공하는 배터리 정보를 확인하는 Windows용 프로그램입니다. BSOH, ASOC, 충전 사이클, 배터리 온도 등을 조회하고 결과를 JSON 파일로 저장할 수 있습니다. 루트 권한은 필요하지 않습니다.

> **비공식 프로그램 안내**  
> 개인 개발자가 제작한 도구이며, 삼성전자와 제휴하거나 삼성전자로부터 승인·인증·후원을 받은 프로그램이 아닙니다. 배터리 정보를 조회하는 용도로만 사용하며 공식 배터리 진단을 대신하지 않습니다.

## 실행 화면

![Galaxy Battery Check v1.4.3 실행 화면](screenshots/galaxy-battery-check.png)

위 화면은 Windows에서 실제로 실행한 예시입니다. 표시되는 수치는 연결 기기와 운영체제 버전에 따라 다릅니다.

## 주요 기능

- **BSOH / ASOC 조회:** 기기가 공개한 값만 표시합니다. 지원하지 않거나 읽을 수 없는 항목은 `확인 불가`로 표시합니다.
- **배터리 상세 정보:** 충전량, 온도, 기록된 최고 온도, 최초 사용 기록일 및 충전 사이클 등 확인 가능한 항목을 표시합니다.
- **용량 참고값:** 정격 용량(mAh)을 입력하면 남은 전하량 등을 바탕으로 간이 추정치를 계산합니다. 실측 용량이 아닙니다.
- **ADB 기기 선택:** 연결된 기기를 검색하고 ADB 실행 파일 경로를 지정할 수 있습니다.
- **JSON 저장:** 조회한 정보를 파일로 보관할 수 있습니다.
- **다국어 GUI:** Windows 표시 언어를 감지해 한국어·영어·일본어 중 하나를 선택합니다. 해당하지 않는 언어에서는 영어를 사용하며, 프로그램에서도 직접 변경할 수 있습니다.

## 실행 환경

- Windows 10 또는 Windows 11
- Python 3.10 이상
- [Android SDK Platform-Tools (ADB)](https://developer.android.com/tools/releases/platform-tools)
- USB 디버깅을 허용한 삼성 갤럭시 스마트폰 및 USB 데이터 케이블

Python 소스 코드 배포본입니다. **독립 실행형 EXE와 ADB 실행 파일은 포함되어 있지 않습니다.** 별도 Python 패키지 설치 없이 표준 라이브러리로 실행됩니다.

## 실행 방법

1. Windows에 Python 3.10 이상을 설치합니다.
2. 위 링크에서 Android SDK Platform-Tools를 내려받아 압축을 풉니다.
3. 휴대전화에서 *개발자 옵션 → USB 디버깅*을 켜고 PC에 연결합니다.
4. 휴대전화에 나타나는 USB 디버깅 허용 창에서 해당 PC를 승인합니다.
5. `galaxy battery check.pyw`를 실행합니다.
6. GUI에서 `adb.exe` 경로를 지정하고 **기기 검색 → 연결 기기 선택 → 배터리 조회** 순서로 진행합니다.

예를 들어 Platform-Tools를 `C:\platform-tools`에 풀었다면 ADB 실행 파일은 `C:\platform-tools\adb.exe`입니다. ADB가 이미 환경 변수 `PATH`에 등록되어 있다면 경로를 직접 선택하지 않아도 됩니다.

명령 프롬프트나 PowerShell에서 GUI를 시작하려면 다음 명령어를 사용할 수 있습니다.

```powershell
pythonw "galaxy battery check.pyw"
```

바탕화면 바로가기는 `create desktop shortcut.cmd`로 생성할 수 있습니다. 바로가기 역시 설치된 Python으로 소스 코드를 실행합니다.

### 명령줄 실행

```powershell
python "galaxy battery check.py" --version
python "galaxy battery check.py" --json
python "galaxy battery check.py" --save "battery report.json"
```

여러 기기가 연결되어 있으면 `--serial` 옵션으로 대상 기기를 지정해야 합니다. ADB 경로는 `--adb` 옵션으로도 설정할 수 있습니다.

## BSOH·ASOC 값이 나오지 않을 때

프로그램은 주로 `adb shell dumpsys battery` 출력에서 BSOH(`mSavedBatteryBsoh`)와 ASOC(`mSavedBatteryAsoc`)를 읽습니다. ASOC는 기기에서 접근 가능한 경우 일부 sysfs 항목도 확인합니다.

One UI 7을 포함해 Android·One UI 버전과 기기 모델에 따라 제공되는 정보가 다릅니다. BSOH 값이 없다면 임의의 수치를 만들어 표시하지 않으며 `확인 불가`로 처리합니다. ASOC가 표시되어도 BSOH와 동일한 의미로 해석해서는 안 됩니다.

ADB 연결 상태를 확인하려면 다음 명령어를 실행합니다.

```powershell
adb devices
```

`unauthorized`가 표시되면 휴대전화 화면에서 USB 디버깅 권한을 승인해야 합니다. 연결 기기가 보이지 않으면 USB 케이블, 드라이버 및 ADB 경로를 확인하세요.

## 지원 언어 및 후원

| GUI 언어 | 후원 페이지 |
| --- | --- |
| 한국어 | [투네이션](https://toon.at/donate/637833976686140024) |
| English | [Ko-fi](https://ko-fi.com/sakai38666) |
| 日本語 | [Ko-fi](https://ko-fi.com/sakai38666) |

후원은 선택 사항입니다. 프로그램 하단의 제작자 이름을 클릭하면 [개발자 블로그](https://wezard4u.tistory.com/)로 이동합니다.

## 진단 결과에 대한 주의사항

배터리 수치와 추정값은 참고용입니다. 정확한 상태 확인이나 수리가 필요하다면 삼성전자 공식 서비스센터 또는 해당 지역의 공식 지원·수리 창구를 이용하세요. 프로그램에서 조회한 JSON에는 기기 식별 정보가 포함될 수 있으므로 외부에 공개하기 전에 내용을 확인하는 것이 좋습니다.

**English:** This is an independent, unofficial battery information utility. It is not affiliated with, endorsed, certified, or sponsored by Samsung Electronics. Results are for reference only. For an accurate assessment, contact Samsung Support or a Samsung-authorized repair provider.

**日本語:** 本ソフトウェアは個人開発の非公式ツールであり、Samsung Electronicsとの提携・承認・認定・後援関係はありません。診断結果は参考情報です。正確な状態の確認はSamsungサポート、またはご利用の通信事業者の修理窓口にご相談ください。

Samsung 및 Galaxy는 삼성전자의 상표입니다. 제품명은 지원 대상 기기를 설명하기 위해 사용했습니다.

## 배포 파일 및 체크섬

배포 ZIP 파일 정보입니다. 아래 체크섬은 실제 제공된 파일에서 검증했습니다.

| 항목 | 값 |
| --- | --- |
| 파일명 | `GalaxyBatteryCheck v1.4.3 Unofficial.zip` |
| 파일 크기 | 160,110 bytes (약 156.4 KiB) |
| MD5 | `913215e82baae2d2c1e5e69067fccf27` |
| SHA-1 | `bae73577aef5d6ef0277ce5e9dcea5e0fdc9edd8` |
| SHA-256 | `fe049082707e95be2a265458847000bf14c2323ef2720745bfd04464fad0b0e9` |

**해시 검증:** 제공된 배포 ZIP 원본으로 MD5, SHA-1, SHA-256 일치를 확인했습니다. GitHub의 `Source code (zip)` 자동 생성 파일이나 이 저장소의 소스 업로드용 ZIP과는 별개의 파일입니다.

### VirusTotal 분석 결과

[Galaxy Battery Check v1.4.3 — VirusTotal 파일 분석](https://www.virustotal.com/gui/file/fe049082707e95be2a265458847000bf14c2323ef2720745bfd04464fad0b0e9/details)

분석 결과는 참고 자료이며 파일의 안전성을 보증하지 않습니다.

Windows PowerShell에서 내려받은 ZIP의 SHA-256 해시는 다음 명령어로 확인할 수 있습니다.

```powershell
Get-FileHash -Algorithm SHA256 ".\GalaxyBatteryCheck v1.4.3 Unofficial.zip"
```

## 제작자 및 저작권

- 개발자: **Sakai**
- 블로그: <https://wezard4u.tistory.com/>
- 저작권: **© 2026 꿈을꾸는 파랑새. All rights reserved.**

별도의 오픈소스 라이선스는 부여하지 않았습니다. 소스 코드를 열람할 수 있다는 사실만으로 수정·재배포·상업적 사용 권한이 허용되는 것은 아닙니다. 자세한 사항은 [`NOTICE.txt`](NOTICE.txt)를 참고하세요.
