import os
import uuid
import asyncio
from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from service import upload_gif_and_create_qr, background_full_process, GIF_QR_SAVE_DIR

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
        # 1. GIF 파일은 먼저 읽고 처리 (응답 속도 최우선)
        gif_bytes = await gif_file.read()
        qr_filename, gif_url = await upload_gif_and_create_qr(gif_bytes)

        # 2. Static 파일 메모리에 로드
        static_bytes = await static_file.read()

        # 3. Static 파일 관련 무거운 작업들은 백그라운드로 위임
        try:
            p_num = int(print_count)
        except ValueError:
            p_num = 1
            
        # 데이터를 직접 전달 (I/O 병목 제거)
        background_tasks.add_task(background_full_process, p_num, static_bytes)

        # 4. 즉시 응답 반환 (GIF QR URL)
        qr_image_url = f"{request.base_url}qrcodes/{qr_filename}"
        
        return {
            'msg': 'success',
            'image_url': qr_image_url,
            'gif_url': gif_url 
        }

    except Exception as e:
        print(f"Main Process Error: {e}")
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
