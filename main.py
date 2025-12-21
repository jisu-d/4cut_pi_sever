import os
from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from service import upload_gif_and_create_qr, background_full_process, GIF_QR_SAVE_DIR

# Ensure save directories exist
os.makedirs("save", exist_ok=True)
os.makedirs("save_print_img", exist_ok=True)
os.makedirs(GIF_QR_SAVE_DIR, exist_ok=True)
os.makedirs("save_qrcode_static", exist_ok=True)

app = FastAPI()

# Mount directories
app.mount("/images", StaticFiles(directory="save"), name="images")
app.mount("/qrcodes", StaticFiles(directory=GIF_QR_SAVE_DIR), name="qrcodes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/shutdown")
def shutdown_raspberry_pi():
    os.system("sudo shutdown -h now")
    return {"message": "라즈베리파이가 종료됩니다..."}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/printImgs")
async def read_root(
    request: Request,
    background_tasks: BackgroundTasks,
    print_count: str = Form(...),
    static_file: UploadFile = File(...),
    gif_file: UploadFile = File(...)
):
    try:
        # 파일 읽기
        static_bytes = await static_file.read()
        gif_bytes = await gif_file.read()

        # 1. [Fast] GIF만 먼저 업로드 및 QR 생성
        qr_filename, gif_url = await upload_gif_and_create_qr(gif_bytes)

        # 2. [Slow] Static 이미지 업로드 및 인쇄 작업은 백그라운드로 위임
        try:
            p_num = int(print_count)
        except ValueError:
            p_num = 1
            
        background_tasks.add_task(background_full_process, p_num, static_bytes)

        # 3. 즉시 응답 반환
        qr_image_url = f"{request.base_url}qrcodes/{qr_filename}"
        
        return {
            'msg': 'success',
            'image_url': qr_image_url,
            'gif_url': gif_url 
        }

    except Exception as e:
        return {"msg": "fail", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  
        host="0.0.0.0", 
        port=8000, 
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem", 
        log_level="info",
        reload=True             
    )