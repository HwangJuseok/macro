<div align="center">

# 🎯 수강신청 빈자리 감지기 (Pixel Watch)
### Image-based Seat Availability Detector for Course Registration

**"새로고침 대신, 픽셀이 대신 지켜봅니다."**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6F00?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Template%20Matching-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Array%20Ops-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-Image%20Processing-3776AB?style=for-the-badge)
![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-Screen%20Control-000000?style=for-the-badge)
![keyboard](https://img.shields.io/badge/keyboard-Hotkey%20Hook-4B0082?style=for-the-badge)
![PyInstaller](https://img.shields.io/badge/PyInstaller-EXE%20Build-2C3E50?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-Personal%20Use-lightgrey?style=for-the-badge)

</div>

---

## 📖 목차

1. [프로젝트 심층 소개 (Overview)](#-프로젝트-심층-소개-overview)
2. [사용 기술 및 라이브러리 (Tech Stack)](#-사용-기술-및-라이브러리-tech-stack--dependencies)
3. [핵심 기능 및 상세 로직 (Key Features & Logic)](#-핵심-기능-및-상세-로직-key-features--logic)
4. [프로젝트 구조 (Directory Structure)](#-프로젝트-구조-및-파일-설명-directory-structure)
5. [Getting Started](#-getting-started-설치-및-실행-가이드)
6. [Troubleshooting & Dev Log](#-troubleshooting--dev-log-트러블슈팅-및-개발-일지)
7. [주의 사항 (Disclaimer)](#️-주의-사항-disclaimer)

---

## 🔍 프로젝트 심층 소개 (Overview)

### 어떤 문제를 해결하는가?

대학교 **수강신청**은 인기 과목의 경우 정원이 순식간에 마감되고, 이후 수강 정정 기간(강의 취소/변경)에 **빈자리(TO)** 가 나오는 순간을 사람이 직접 화면을 응시하며 F5(새로고침)를 반복 클릭해서 잡아야 합니다.

- 사람이 계속 화면을 지켜보는 것은 **집중력 소모와 피로**를 유발합니다.
- 여러 과목(강의 리스트)의 "정원/신청" 텍스트를 눈으로 비교하는 것은 **반응 속도가 느리고 실수하기 쉽습니다.**
- 새로고침만으로는 **어느 줄(과목)에 자리가 났는지 즉시 파악하기 어렵습니다.**

`pixel_watch.py`는 이 문제를 **OCR이나 서버 API 호출이 아닌, 화면 픽셀 자체를 비교하는 방식**으로 해결합니다. 특정 화면 영역(수강신청 리스트의 "정원" 텍스트가 표시되는 좌표)을 캡처해두고, 이후 동일 좌표를 주기적으로 재캡처하여 **이미지가 조금이라도 달라지면(= 숫자가 바뀌면) 즉시 감지**하는 방식입니다.

### 전체 작동 흐름 (Architecture Flow) — 시나리오

이 프로그램은 크게 **3단계 파이프라인**으로 설계되어 있으며, 각 단계는 `threading.Thread`로 분리되어 Tkinter GUI가 멈추지 않도록(Non-blocking) 처리됩니다.

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  1. 영역 설정      │ →  │  2. 학습(캡처)      │ →  │  3. 감시(모니터링)   │ →  │  4. 알림/발견       │
│  (Set Region)     │    │  (Learning)        │    │  (Monitoring)      │    │  (Alert)           │
└──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
```

**Step 1 — 영역 설정 (`logic_set_region`)**
> 사용자가 [1. 영역 설정] 버튼을 누르면, 프로그램은 별도 스레드에서 `keyboard.wait('f2')`로 대기 상태에 들어갑니다.
> 1. 사용자가 마우스를 **감시할 리스트의 좌상단**에 놓고 `F2`를 누르면 `pyautogui.position()`으로 좌표 `(x1, y1)`를 획득합니다.
> 2. 이어서 마우스를 **우하단**으로 옮기고 다시 `F2`를 누르면 `(x2, y2)`를 획득합니다.
> 3. 두 좌표의 차이를 이용해 `self.region = (x1, y1, x2-x1, y2-y1)` 형태의 캡처 영역(사각형)을 확정합니다.
> → 이 영역이 이후 모든 스크린샷의 기준(ROI, Region of Interest)이 됩니다.

**Step 2 — 학습 모드 (`logic_learning`)**
> 수강신청 리스트는 보통 5개 과목(줄)이 화면에 동시에 노출됩니다(`self.subject_count = 5`).
> 1. 사용자가 스크롤/화살표 키로 **1번째 과목 줄**에 커서(포커스)를 맞추고 `F2`를 누릅니다.
> 2. `capture_screen()`이 해당 영역을 `pyautogui.screenshot()`으로 캡처 → `numpy` 배열로 변환 → `cv2.cvtColor(..., COLOR_RGB2GRAY)`로 **그레이스케일 변환** 후 `self.ref_imgs` 리스트에 저장합니다.
> 3. 이 과정을 `subject_count`(5회)만큼 반복하여, **"정상 상태(빈자리 없음)"의 기준 이미지 5장**을 확보합니다.
> 4. 학습이 끝나면 `popup_learning_result()`가 호출되어, 저장된 5장의 기준 이미지를 **Tkinter Toplevel 팝업 창**으로 2배 확대하여 보여줌으로써 사용자가 영역이 올바르게 잡혔는지 즉시 육안 검증할 수 있습니다.

**Step 3 — 감시 모드 (`logic_monitoring`)**
> [3. 감시 시작] 버튼을 누르면 3초 카운트다운 후 무한 루프(`while self.is_running`)가 시작됩니다.
> 1. 현재 커서가 위치한 줄(`curr_idx`)의 화면을 캡처합니다.
> 2. `cv2.matchTemplate(ref_img, curr_img, cv2.TM_CCOEFF_NORMED)`로 **기준 이미지와 현재 이미지의 유사도(정규화된 상관계수, 0~1)** 를 계산합니다.
> 3. `max_val < 0.99` (유사도 99% 미만) 이면 **"정원 숫자가 바뀌었다" = 빈자리 발생**으로 판단하고 즉시 루프를 탈출, `found_empty_seat()`를 호출합니다.
> 4. 변화가 없다면 `pyautogui.press('down'/'up')`으로 **커서를 한 줄씩 이동**하며 다음 과목을 검사합니다. 이때 `direction` 플래그를 이용해 5개 줄을 **핑퐁(왕복)** 형태로 순회하여, 리스트 끝에서 스크롤이 밀리지 않도록 설계되어 있습니다.
> 5. 각 검사 사이에는 `self.move_delay`(0.2초)만큼 대기하여 서버/화면 렌더링 부하를 줄입니다.
> 6. 루프 중 `keyboard.is_pressed('esc')`를 매 사이클마다 체크하여 **언제든 즉시 중단**할 수 있게 했습니다.

**Step 4 — 발견 및 알림 (`found_empty_seat` / `play_alarm_sound`)**
> 1. 변화가 감지되면 즉시 감시를 멈추고(`stop_monitoring`), 모든 조작 버튼을 비활성화하여 **오작동으로 인한 재클릭을 원천 차단**합니다.
> 2. `self.root.attributes('-topmost', True)`로 창을 **강제로 최상단에 띄우고** `focus_force()`로 포커스를 가져옵니다.
> 3. 별도 스레드에서 `winsound.Beep(2500, 300)`을 **0.1초 간격으로 10회 반복**하여 강력한 경고음을 재생합니다(메인 스레드 블로킹 방지).
> 4. `popup_comparison()`으로 **"저장된 기준 이미지" vs "변화가 감지된 현재 이미지"** 를 나란히 띄워, 사용자가 오탐(false positive)인지 실제 빈자리인지 눈으로 즉시 대조·확인할 수 있게 합니다.
> 5. 마지막으로 `messagebox.showwarning`으로 몇 번째 줄인지 명시적으로 알려주고, 사용자가 직접 신청을 마친 뒤 [초기화] 버튼으로 처음부터 재시작하도록 유도합니다.

---

## 🧰 사용 기술 및 라이브러리 (Tech Stack & Dependencies)

`pixel_watch.py`의 `import` 구문을 기준으로 분석한 스택입니다. (별도 `requirements.txt`는 저장소에 없어 소스 코드 기반으로 정리했습니다.)

| 구분 | 라이브러리 | 배지 | 역할 |
|---|---|---|---|
| 언어 | Python 3.x | ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) | 전체 스크립트 런타임 |
| GUI | `tkinter` (`scrolledtext`, `messagebox`) | ![Tkinter](https://img.shields.io/badge/-Tkinter-FF6F00?style=flat-square) | 메인 윈도우, 로그창, 팝업, 경고창 구성 |
| 이미지 처리 | `Pillow` (`PIL.Image`, `PIL.ImageTk`) | ![Pillow](https://img.shields.io/badge/-Pillow-3776AB?style=flat-square) | 캡처된 numpy/cv2 이미지를 Tkinter에서 렌더링 가능한 포맷으로 변환·확대 |
| 컴퓨터 비전 | `opencv-python` (`cv2`) | ![OpenCV](https://img.shields.io/badge/-OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white) | 그레이스케일 변환, `matchTemplate` 기반 이미지 유사도(변화) 검출 |
| 수치 연산 | `numpy` | ![NumPy](https://img.shields.io/badge/-NumPy-013243?style=flat-square&logo=numpy&logoColor=white) | 스크린샷 → 배열 변환, cv2 연산의 기반 자료구조 |
| 화면 제어 | `pyautogui` | ![PyAutoGUI](https://img.shields.io/badge/-PyAutoGUI-000000?style=flat-square) | 특정 좌표 스크린샷 캡처, 마우스 위치 획득, 키 입력(`↑`/`↓`) 시뮬레이션 |
| 전역 단축키 | `keyboard` | ![keyboard](https://img.shields.io/badge/-keyboard-4B0082?style=flat-square) | `F2` 핫키 대기(`wait`), `ESC` 눌림 여부 실시간 감지(`is_pressed`) |
| 사운드 | `winsound` (표준 라이브러리, Windows 전용) | ![Windows](https://img.shields.io/badge/-winsound-0078D6?style=flat-square&logo=windows&logoColor=white) | 비프음 기반 경고 알람 재생 |
| 동시성 | `threading` | ![Threading](https://img.shields.io/badge/-threading-lightgrey?style=flat-square) | GUI 프리징 방지를 위한 백그라운드 작업 분리 |
| 시간 | `time`, `datetime` | ![Time](https://img.shields.io/badge/-time%2Fdatetime-lightgrey?style=flat-square) | 딜레이 제어, 경과 시간 타이머, 로그 타임스탬프 |
| 빌드/배포 | `PyInstaller` | ![PyInstaller](https://img.shields.io/badge/-PyInstaller-2C3E50?style=flat-square) | `.py`를 단일 실행 파일(`.exe`)로 패키징 |

> ⚠️ `winsound`는 **Windows 전용 표준 라이브러리**이며, `keyboard`/`pyautogui`의 전역 후킹 특성상 이 프로그램은 **Windows 환경**에서만 정상 동작합니다.

---

## ⚙️ 핵심 기능 및 상세 로직 (Key Features & Logic)

### 1. 좌표 기반 ROI(관심영역) 캡처
- `capture_screen()` 함수가 핵심 유틸리티로, `self.region`(x, y, width, height)을 인자로 `pyautogui.screenshot(region=...)`을 호출합니다.
- 반환된 PIL 이미지를 `np.array()`로 변환 후 `cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)`로 흑백 변환합니다. 색상 정보를 버리는 이유는 (1) 연산량 감소, (2) 색상 안티앨리어싱/렌더링 미세 차이에 따른 **오탐(false positive) 감소** 효과 때문입니다.

### 2. 템플릿 매칭 기반 변화 감지 (핵심 알고리즘)
- OCR로 숫자를 읽어 "0 → 1"을 비교하는 대신, `cv2.matchTemplate(ref, curr, cv2.TM_CCOEFF_NORMED)`을 사용해 **두 이미지가 픽셀 단위로 얼마나 유사한지(0.0~1.0)** 를 계산합니다.
- `cv2.minMaxLoc(score)`로 최댓값(`max_val`)을 추출하고, **임계값 0.99**를 기준으로 판단합니다.
  - `max_val >= 0.99` → 동일한 화면(변화 없음) → 다음 줄로 이동
  - `max_val < 0.99` → 픽셀이 달라짐(숫자/텍스트 변경 추정) → **즉시 정지 및 알림**
- 이 방식은 폰트, 언어, UI 테마에 관계없이 "달라졌다/안달라졌다"만 판단하면 되므로 **OCR보다 훨씬 빠르고 오류에 강합니다.**

### 3. 핑퐁(왕복) 스캔 방식의 다중 과목 순회
- `direction` 변수(`1` 또는 `-1`)를 이용해 `curr_idx`가 0 → `subject_count-1` → 0 순으로 왕복하도록 구현되어 있습니다.
- 매 사이클마다 `pyautogui.press('down' 또는 'up')`으로 실제 방향키를 눌러 리스트 화면의 포커스를 이동시키므로, **웹페이지의 실제 스크롤/포커스 상태와 캡처 대상이 항상 일치**하도록 설계되어 있습니다.

### 4. 논블로킹 GUI를 위한 스레드 분리 설계
- `F2`/`ESC` 대기(`keyboard.wait`, `keyboard.is_pressed`)는 **블로킹 호출**이기 때문에 메인 스레드(Tkinter 이벤트 루프)에서 실행하면 창이 멈춥니다(Not Responding).
- 이를 방지하기 위해 영역 설정(`logic_set_region`), 학습(`logic_learning`), 감시(`logic_monitoring`), 알람 사운드(`play_alarm_sound`)를 모두 `threading.Thread(..., daemon=True)`로 실행하여 **UI 반응성을 유지**합니다.
- 단, Tkinter 위젯 갱신(팝업 띄우기 등)은 스레드-세이프하지 않으므로 `self.root.after(0, self.popup_learning_result)`처럼 **메인 스레드에 작업을 위임(schedule)** 하는 패턴을 사용했습니다.

### 5. 실시간 타이머 & 로그 시스템
- `update_timer()`는 `root.after(100, ...)`로 자기 자신을 100ms마다 재호출하는 **재귀 스케줄링 패턴**으로 감시 경과 시간을 `HH:MM:SS` 형태로 갱신합니다.
- `log()` 함수는 `datetime.now().strftime("[%H:%M:%S] ")`로 타임스탬프를 찍어 `ScrolledText`에 누적 출력하며, 매번 `state='disabled'`로 되돌려 **사용자의 직접 편집을 막는 읽기 전용 로그 콘솔**을 구현했습니다.

### 6. 안전장치: 초기화(Reset) 흐름 강제
- 빈자리가 감지되면 [초기화] 버튼을 제외한 모든 조작 버튼이 `disabled` 처리됩니다. 사용자가 실제로 수강신청을 완료했는지 확인하지 않은 채 **감시를 재개해 버리는 실수를 방지**하기 위한 UX 안전장치입니다.

---

## 📂 프로젝트 구조 및 파일 설명 (Directory Structure)

```bash
sugangsinchung/
├── .git/                     # Git 버전 관리 메타데이터 (커밋 히스토리, 브랜치 정보)
├── build/                    # PyInstaller 빌드 시 생성되는 임시 중간 산출물 폴더 (배포용 아님)
├── dist/                     # PyInstaller 최종 빌드 결과(.exe)가 생성되는 폴더 (배포용 실행 파일 위치)
├── pixel_watch.py            # ⭐ 핵심 소스코드: GUI 구성 + 영역설정/학습/감시 로직 전체
├── pixel_watch.spec          # PyInstaller 빌드 설정 파일 (콘솔 모드 O, name='pixel_watch')
├── sugangsinchung.spec       # PyInstaller 빌드 설정 파일 (콘솔 모드 X = 창 숨김, name='sugangsinchung')
└── README.md                 # 프로젝트 설명 문서 (본 파일)
```

> 💡 두 개의 `.spec` 파일은 **동일한 `pixel_watch.py`를 빌드 대상**으로 하되, `console` 옵션만 다릅니다.
> - `pixel_watch.spec` → `console=True` (디버깅용, 콘솔 창과 함께 실행되어 에러 로그 확인 가능)
> - `sugangsinchung.spec` → `console=False` (배포/실사용용, 검은 콘솔 창 없이 GUI만 실행)

---

## 🚀 Getting Started (설치 및 실행 가이드)

### 1️⃣ 사전 요구사항
- OS: **Windows 10 / 11** (`winsound`, `keyboard` 전역 후킹 특성상 Windows 전용)
- Python **3.9 이상** 권장

### 2️⃣ 저장소 클론

```bash
git clone <이 저장소의 URL>
cd sugangsinchung
```

### 3️⃣ 가상환경 생성 (권장)

```bash
python -m venv venv
venv\Scripts\activate
```

### 4️⃣ 의존 라이브러리 설치

저장소에 `requirements.txt`가 없으므로, 아래 명령어로 직접 설치합니다.

```bash
pip install pyautogui opencv-python numpy keyboard pillow
```

> `tkinter`, `winsound`, `threading`, `time`, `datetime`은 Python 표준 라이브러리로 별도 설치가 필요 없습니다.

### 5️⃣ 실행 (개발 모드)

> ⚠️ `keyboard` 라이브러리는 전역 키보드 후킹을 위해 **관리자 권한(Run as Administrator)** 이 필요할 수 있습니다.

```bash
python pixel_watch.py
```

### 6️⃣ 사용 방법 (앱 조작 순서)

1. **[1. 영역 설정]** 클릭 → 수강신청 리스트의 **좌상단**에 마우스를 놓고 `F2` → **우하단**에 놓고 `F2`
2. **[2. 학습 시작]** 클릭 → 5개 과목 줄에 순서대로 커서를 맞추고 각각 `F2` 5회 입력 → 학습 이미지 팝업으로 검증
3. **[3. 감시 시작]** 클릭 → 3초 카운트다운 후 자동 감시 시작 (필요 시 `ESC`로 즉시 중단)
4. 빈자리 감지 시 **경고음 + 비교 이미지 팝업 + 알림창**이 뜨며, 신청 완료 후 **[↻ 초기화]** 버튼으로 재시작

### 7️⃣ 실행 파일(.exe) 빌드

```bash
# 콘솔 창 없이(배포용, 권장)
pyinstaller sugangsinchung.spec

# 콘솔 창 포함(디버깅용)
pyinstaller pixel_watch.spec
```

빌드가 완료되면 `dist/` 폴더 안에 실행 파일이 생성됩니다.

---

## 🛠️ Troubleshooting & Dev Log (트러블슈팅 및 개발 일지)

프로젝트를 진행하며 실제로 마주쳤을 법한 기술적 이슈들과 코드에 반영된 해결 방식을 정리했습니다.

### 🧩 이슈 1. "F2를 기다리는 동안 프로그램이 멈춰요 (Not Responding)"
- **원인**: `keyboard.wait('f2')`는 키가 눌릴 때까지 **스레드를 블로킹**하는 동기 함수입니다. 이를 메인 스레드(Tkinter 이벤트 루프)에서 바로 호출하면 GUI 전체가 응답 없음 상태에 빠집니다.
- **해결**: `start_set_region_thread()`, `start_learning_thread()`처럼 **버튼 클릭 → 별도 데몬 스레드 생성 → 그 안에서 블로킹 대기**하는 구조로 전면 분리했습니다. 덕분에 F2를 기다리는 동안에도 메인 창은 계속 응답 가능한 상태를 유지합니다.

### 🧩 이슈 2. "스레드에서 팝업을 띄우면 창이 깨지거나 튕겨요"
- **원인**: Tkinter는 **스레드 세이프하지 않습니다.** 백그라운드 스레드에서 직접 `Toplevel()`이나 위젯을 생성/수정하면 예측 불가능한 크래시나 렌더링 오류가 발생할 수 있습니다.
- **해결**: 학습 완료 시 `self.root.after(0, self.popup_learning_result)`, 빈자리 발견 시 `self.root.after(0, lambda: self.popup_comparison(...))` 형태로 **실제 UI 갱신은 항상 `after()`를 통해 메인 스레드 이벤트 루프에 위임**하도록 통일했습니다.

### 🧩 이슈 3. "정원 숫자가 바뀐 게 아닌데도 자꾸 오탐(false alarm)이 떠요"
- **원인**: 초기에는 픽셀을 완전히 동일한지(`==`) 비교하는 방식을 고려했으나, 화면 렌더링 시 안티앨리어싱, 커서 깜빡임, 미세한 압축/색상 차이 등으로 **완전 동일 비교는 비현실적**이었습니다.
- **해결**: `cv2.matchTemplate` + `TM_CCOEFF_NORMED`(정규화 상관계수) 방식으로 전환하고, 임계값을 `0.99`로 설정했습니다. 완전히 같은 화면은 보통 0.999~1.0에 수렴하고, 텍스트가 바뀌면 값이 뚜렷하게 하락하는 것을 실험적으로 확인하여 **오탐과 미탐 사이의 균형점**으로 0.99를 채택했습니다.

### 🧩 이슈 4. "5개 과목을 어떻게 순서대로, 계속 도는 방식으로 검사할까?"
- **원인**: 단순히 `curr_idx`를 계속 증가시키면 리스트 끝에서 범위를 벗어나거나, 매번 맨 위로 스크롤을 되돌려야 해서 비효율적이었습니다.
- **해결**: `direction` 플래그(`1`/`-1`)를 두어 **핑퐁(왕복) 방식**으로 방향키를 눌러가며 순회하도록 구현, 리스트 최상단/최하단에서 자연스럽게 방향을 전환하도록 처리했습니다.

### 🧩 이슈 5. "빈자리를 놓치지 않았는지, 오작동은 아닌지 신뢰할 수가 없어요"
- **원인**: 자동화 매크로 특성상 "정말 감지가 맞게 됐는지" 사용자가 눈으로 확인할 방법이 없으면 신뢰하고 쓰기 어렵습니다.
- **해결**: `popup_learning_result()`(학습 검증용)와 `popup_comparison()`(발견 시 Before/After 비교용) 두 개의 시각화 팝업을 추가했습니다. `PIL.Image.resize(..., Image.Resampling.NEAREST)`로 저해상도 캡처 이미지를 **2배 확대**하여 육안 대조가 쉽도록 처리한 것이 포인트입니다.

### 🧩 이슈 6. "감지 후에도 알람이 계속 울려서 시끄럽거나, 반대로 못 듣고 지나쳐요"
- **원인**: `winsound.Beep`을 1회만 재생하면 자리를 비운 사이 놓칠 수 있고, 무한 반복하면 알아챈 뒤에도 계속 시끄럽습니다.
- **해결**: `play_alarm_sound()`에서 **0.1초 간격, 10회 반복**으로 횟수를 제한한 비프음을 재생하도록 절충했고, 동시에 `root.attributes('-topmost', True)` + `focus_force()`로 **창을 강제 전면 배치**하여 소리를 놓치더라도 시각적으로 즉시 인지 가능하도록 이중 안전장치를 마련했습니다.

### 🧩 이슈 7. "배포용 exe에서는 콘솔 창이 거슬려요"
- **원인**: 개발 중에는 에러 로그 확인을 위해 콘솔이 필요하지만, 실사용 배포판에서는 검은 콘솔 창이 함께 뜨는 것이 지저분하고 사용자 경험을 해칩니다.
- **해결**: `.spec` 파일을 **용도별로 분리**했습니다. 디버깅용 `pixel_watch.spec`은 `console=True`, 배포용 `sugangsinchung.spec`은 `console=False`로 설정하여 하나의 소스코드에서 두 가지 빌드 산출물을 관리합니다.

---

## ⚠️ 주의 사항 (Disclaimer)

- 본 프로그램은 **개인 학습 및 편의 목적**으로 제작되었습니다.
- 실제 대학/기관의 수강신청 시스템 이용 약관에 따라 **자동화 매크로 사용이 제한되거나 제재 대상이 될 수 있습니다.** 사용 전 소속 기관의 정책을 반드시 확인하시고, 사용에 따른 책임은 사용자 본인에게 있습니다.
- `pyautogui.press`, `keyboard` 등을 통한 실제 키 입력을 수행하므로, 감시 중에는 **다른 작업 창을 조작하지 않는 것**을 권장합니다.
