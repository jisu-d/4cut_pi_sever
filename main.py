import os
import uuid
import asyncio
import aiofiles
from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from service import upload_gif_and_create_qr, background_full_process, GIF_QR_SAVE_DIR, TEMP_STATIC_UPLOAD_DIR

# Ensure save directories exist
os.makedirs("save", exist_ok=True)
os.makedirs("save_qrcode", exist_ok=True) # 기존 save_qrcode는 일단 유지 (레거시 코드 때문일수도)
os.makedirs("save_print_img", exist_ok=True)
os.makedirs(GIF_QR_SAVE_DIR, exist_ok=True)
os.makedirs("save_qrcode_static", exist_ok=True)
os.makedirs(TEMP_STATIC_UPLOAD_DIR, exist_ok=True) # 임시 파일 저장 디렉토리 생성

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
    temp_static_filepath = None
    try:
        # 1. GIF 파일은 먼저 읽고 처리 (응답 속도 최우선)
        gif_bytes = await gif_file.read()
        qr_filename, gif_url = await upload_gif_and_create_qr(gif_bytes)

        # 2. Static 파일은 임시 디스크에 비동기적으로 저장 (메모리 절약 및 핸들러 블로킹 최소화)
        # Unique한 임시 파일명 생성
        file_extension = static_file.filename.split(".")[-1] if static_file.filename else "jpg"
        temp_static_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_static_filepath = os.path.join(TEMP_STATIC_UPLOAD_DIR, temp_static_filename)

        print(f"Main: Saving static file to temporary path: {temp_static_filepath}")
        async with aiofiles.open(temp_static_filepath, 'wb') as out_file:
            while content := await static_file.read(1024 * 1024):  # 1MB 씩 청크로 읽고 쓰기
                await out_file.write(content)
        print(f"Main: Static file saved to temporary path: {temp_static_filepath}")

        # 3. Static 파일 관련 무거운 작업들은 백그라운드로 위임
        try:
            p_num = int(print_count)
        except ValueError:
            p_num = 1
            
        background_tasks.add_task(background_full_process, p_num, temp_static_filepath)

        # 4. 즉시 응답 반환 (GIF QR URL)
        qr_image_url = f"{request.base_url}qrcodes/{qr_filename}"
        
        return {
            'msg': 'success',
            'image_url': qr_image_url,
            'gif_url': gif_url 
        }

    except Exception as e:
        print(f"Main Process Error: {e}")
        # 에러 발생 시 임시 파일 정리
        if temp_static_filepath and os.path.exists(temp_static_filepath):
            try:
                os.remove(temp_static_filepath)
                print(f"Main Error Cleanup: Deleted temp file {temp_static_filepath}.")
            except Exception as cleanup_e:
                print(f"Main Error Cleanup: Failed to delete temp file: {cleanup_e}")
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
