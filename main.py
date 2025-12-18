import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import uvicorn

from overlay_qr_img import overlay_qr_on_image
from print_img import printImgs

# Ensure save directory exists
os.makedirs("save", exist_ok=True)

app = FastAPI()

# Mount the static directory to serve images
app.mount("/images", StaticFiles(directory="save"), name="images")
app.mount("/qrcodes", StaticFiles(directory="save_qrcode"), name="qrcodes")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PRINTOUT_INFO(BaseModel):
    printoutNum: int
    base64_data: str

@app.post("/shutdown") # 라즈베리파이 종료 api
def shutdown_raspberry_pi():
    os.system("sudo shutdown -h now")
    return {"message": "라즈베리파이가 종료됩니다..."}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/printImgs")
def read_root(data: PRINTOUT_INFO, request: Request):
    combined_img_path, qr_img_path = overlay_qr_on_image(data.base64_data)
    printImgs(data.printoutNum, combined_img_path)

    image_url = f"{request.base_url}qrcodes/{qr_img_path}"

    return {
        'msg': 'success',
        'image_url': image_url
    }

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