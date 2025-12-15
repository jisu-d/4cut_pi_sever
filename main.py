import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from overlay_qr_img import overlay_qr_on_image
from print_img import printImgs

# Ensure save directory exists
os.makedirs("save", exist_ok=True)

app = FastAPI()

# Mount the static directory to serve images
app.mount("/images", StaticFiles(directory="save"), name="images")
app.mount("/qrcodes", StaticFiles(directory="save_qrcode"), name="qrcodes")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PRINTOUT_INFO(BaseModel):
    printoutNum: int
    base64_data: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/printImgs")
def read_root(data: PRINTOUT_INFO, request: Request):
    combined_img_path, qr_img_path = overlay_qr_on_image(data.base64_data)
    printImgs(data.printoutNum, combined_img_path)

    # Construct the full URL for the QR code image
    # request.base_url returns the full scheme://host:port/
    image_url = f"{request.base_url}qrcodes/{qr_img_path}"

    return {
        'msg': 'success',
        'image_url': image_url
    }