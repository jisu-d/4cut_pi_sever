import asyncio
import numpy as np
import os
from imgbb import upload_image_to_imgbb
from overlay_qr_img import save_qr_code_only, compose_final_image
from print_img import printImgs

GIF_QR_SAVE_DIR = "save_qrcode_gif"
STATIC_QR_SAVE_DIR = "save_qrcode_static"

async def upload_gif_and_create_qr(gif_bytes: bytes):
    """
    GIF 파일만 먼저 업로드하고 프론트엔드용 QR을 생성하여 반환 (빠른 응답용)
    """
    os.makedirs(GIF_QR_SAVE_DIR, exist_ok=True)

    # GIF 업로드 (비동기 처리)
    gif_url = await asyncio.to_thread(upload_image_to_imgbb, gif_bytes)
    
    if not gif_url:
        raise Exception("GIF upload failed")

    # GIF QR 생성 및 저장
    qr_gif_filename, _ = await asyncio.to_thread(save_qr_code_only, gif_url, format='gif', save_dir=GIF_QR_SAVE_DIR)
    
    return qr_gif_filename, gif_url

def background_full_process(print_count: int, static_bytes: bytes):
    """
    백그라운드 작업:
    1. Static 이미지 업로드 (오래 걸림)
    2. Static QR 생성
    3. 이미지 합성
    4. 인쇄
    """
    try:
        os.makedirs(STATIC_QR_SAVE_DIR, exist_ok=True)
        
        # 1. Static 이미지 업로드
        # 동기 함수지만 FastAPI BackgroundTasks에서 실행되므로 메인 스레드 차단 안 함
        print("Background: Starting static image upload...")
        static_url = upload_image_to_imgbb(static_bytes)
        
        if not static_url:
            print("Background Error: Static image upload failed.")
            return

        # 2. 인쇄용 Static QR 생성 (메모리 및 파일 저장)
        _, qr_static_img_array = save_qr_code_only(static_url, format='jpg', save_dir=STATIC_QR_SAVE_DIR)
        
        # 3. 이미지 합성
        saved_path = compose_final_image(static_bytes, qr_static_img_array)
        
        # 4. 인쇄 수행
        printImgs(print_count, saved_path)
        print(f"Background: Print job completed successfully for {saved_path}")
        
    except Exception as e:
        print(f"Background Process Critical Error: {e}")