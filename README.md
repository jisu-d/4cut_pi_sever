# 4Cut Pi Server

라즈베리파이 기반의 **독립형 네컷 사진 인쇄 서버**입니다.
촬영된 사진을 클라우드에 업로드하여 QR 코드를 생성하고, 사진 합성 후 프린터로 출력하는 기능을 수행합니다.

## 핵심 특징

1.  **Print Server:** USB 연결된 프린터(Canon SELPHY CP1300) 제어 및 인쇄 명령 (CUPS 기반)
2.  **Hotspot AP:** 촬영 기기를 위한 독립적인 Wi-Fi 네트워크 환경 지원
3.  **UX 최적화:** GIF 업로드 및 QR 생성 선처리로 대기 시간 최소화 (Non-blocking)

## 동작 시나리오 (Workflow)

1.  **준비:** 라즈베리파이(Print Server)가 **Wi-Fi 핫스팟**을 생성하고 대기합니다.
2.  **연결:** 촬영 기기(iPad, PC 등)에서 라즈베리파이 Wi-Fi에 접속합니다.
3.  **요청:** 촬영 기기에서 사진을 찍고 `/printImgs` API로 전송합니다. 화면에 표시할 QR 코드 이미지를 반환합니다.
4.  **출력:** 라즈베리파이가 사진을 처리(QR 생성, 합성)하고 USB 연결된 프린터로 인쇄합니다.

## 기술 스택

*   **Core:** Python 3.11+, FastAPI, Uvicorn
*   **Image:** OpenCV, NumPy, Pillow, qrcode
*   **System:** CUPS (`lp` command), ImgBB API

## 디렉토리 구조

```bash
4cut_pi_sever/
├── main.py              # API 진입점 및 라우터 설정
├── service.py           # 비즈니스 로직 및 백그라운드 작업 처리
├── imgbb.py             # ImgBB API 업로드 모듈
├── make_qrcode.py       # URL -> QR 코드 이미지 변환
├── overlay_qr_img.py    # 이미지 합성 로직
├── print_img.py         # 프린터 제어 (여백 조정 및 인쇄 명령)
├── save/                # 최종 합성된 인쇄용 이미지 저장소
├── save_qrcode_gif/     # GIF 다운로드용 QR 코드 저장소
├── save_qrcode_static/  # 인쇄 이미지에 합성할 QR 코드 저장소
└── save_print_img/      # 인쇄 여백이 적용된 파일 저장소
```

## 설치 및 실행

### 1. 환경 설정
*   **OS:** Raspberry Pi OS (Linux)
*   **패키지 설치:** `sudo apt install cups libopencv-dev`
*   **프린터 설정:** CUPS 드라이버 설치 및 `print_img.py` 내 프린터 이름 수정
*   **네트워크 구성 (중요):** 라즈베리파이는 **Wi-Fi 핫스팟(AP)** 역할을 수행하지만, ImgBB 업로드를 위해서는 **유선 LAN(Ethernet)** 등을 통해 외부 인터넷에 연결되어 있어야 합니다.

## 서버 실행

```bash
# 개발 모드 (Auto Reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 프로덕션 모드 (배포용)
python main.py
```

## API 명세

### `POST /printImgs`
사진 처리 및 인쇄 요청

*   **Request:** `print_count` (int), `static_file` (img), `gif_file` (gif)
*   **Response:**
    ```json
    {
        "msg": "success",
        "image_url": "http://<IP>:8000/qrcodes/...",
        "gif_url": "https://ibb.co/..."
    }
    ```

### `POST /shutdown`
시스템 종료 (`sudo shutdown -h now`)
