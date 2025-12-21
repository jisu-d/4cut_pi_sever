import asyncio
import numpy as np
import os
import aiofiles
import cv2
from imgbb import upload_image_to_imgbb
from overlay_qr_img import save_qr_code_only, compose_final_image
from print_img import printImgs

GIF_QR_SAVE_DIR = "save_qrcode_gif"
STATIC_QR_SAVE_DIR = "save_qrcode_static"
TEMP_STATIC_UPLOAD_DIR = "temp_static_uploads" # 새로운 임시 파일 저장 디렉토리

async def upload_gif_and_create_qr(gif_bytes: bytes):
    """
    GIF 파일만 먼저 업로드하고 프론트엔드용 QR을 생성하여 반환 (빠른 응답용)
    """
    os.makedirs(GIF_QR_SAVE_DIR, exist_ok=True)

    # GIF 업로드 (네트워크 I/O이므로 별도 스레드에서 실행)
    gif_url = await asyncio.to_thread(upload_image_to_imgbb, gif_bytes)
    
    if not gif_url:
        raise Exception("GIF image upload failed")

    # GIF용 QR 생성 및 저장 (프론트엔드 반환용, format='gif')
    qr_gif_filename, _ = await asyncio.to_thread(
        save_qr_code_only, 
        gif_url, 
        format='gif', 
        save_dir=GIF_QR_SAVE_DIR
    )
    
    return qr_gif_filename, gif_url

def background_full_process(print_count: int, static_file_path: str):
    """
    백그라운드 작업:
    1. 임시 파일 경로에서 이미지 데이터 읽기
    2. Static 이미지 압축 및 업로드 (최적화)
    3. Static QR 생성
    4. 이미지 합성 (원본 사용)
    5. 인쇄
    6. 임시 파일 삭제
    """
    try:
        os.makedirs(STATIC_QR_SAVE_DIR, exist_ok=True)
        
        # 임시 파일에서 static_bytes 읽기
        print(f"Background: Reading static image from temporary file: {static_file_path}...")
        with open(static_file_path, "rb") as f:
            static_bytes = f.read()

        # [최적화] 업로드 속도 향상을 위해 이미지 압축 (Quality 90)
        try:
            nparr = np.frombuffer(static_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # JPG 압축 인코딩
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, encoded_img = cv2.imencode('.jpg', img_cv, encode_param)
            upload_bytes = encoded_img.tobytes()
            
            print(f"Background: Optimized image size for upload: {len(static_bytes)/1024:.1f}KB -> {len(upload_bytes)/1024:.1f}KB")
        except Exception as e:
            print(f"Background Warning: Compression failed, using original. {e}")
            upload_bytes = static_bytes

        # 1. Static 이미지 업로드
        print("Background: Starting static image upload...")
        static_url = upload_image_to_imgbb(upload_bytes)
        
        if not static_url:
            print("Background Error: Static image upload failed.")
            return

        # 2. 인쇄용 Static QR 생성 (메모리 및 파일 저장)
        _, qr_static_img_array = save_qr_code_only(static_url, format='jpg', save_dir=STATIC_QR_SAVE_DIR)
        
        # 3. 이미지 합성 (중요: 인쇄 품질을 위해 '원본 static_bytes' 사용)
        saved_path = compose_final_image(static_bytes, qr_static_img_array)
        
        # 4. 인쇄 수행
        printImgs(print_count, saved_path)
        print(f"Background: Print job completed successfully for {saved_path}")
        
    except Exception as e:
        print(f"Background Process Critical Error: {e}")
    finally:
        # 작업 완료 후 임시 파일 삭제 (리소스 정리)
        if os.path.exists(static_file_path):
            try:
                os.remove(static_file_path)
                print(f"Background: Temporary file {static_file_path} deleted.")
            except Exception as e:
                print(f"Background Warning: Failed to delete temp file: {e}")
