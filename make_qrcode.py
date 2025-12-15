import subprocess
import time
import re
import os
import requests
import numpy as np
import cv2

import qrcode

def generate_qr_code_image(url):
    # 정규식 패턴을 사용하여 VHcQhFN 및 7bfd23e1883f 추출
    match = re.search(r'https://i\.ibb\.co/([^/]+)/([^/]+)\.jpg', url)

    if match:
        data1 = match.group(1)
        data2 = match.group(2)
        target_url = f'https://4cut.vercel.app/ImageDownloadPage?data1={data1}&data2={data2}'
    else:
        print("URL 형식이 맞지 않습니다.")
        target_url = url # fallback

    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    # PIL 이미지를 생성
    pil_img = qr.make_image(fill='black', back_color='white').convert('RGB')
    
    # PIL 이미지를 numpy 배열(OpenCV 포맷)로 변환
    open_cv_image = np.array(pil_img)
    # RGB를 BGR로 변환 (OpenCV는 BGR 사용)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    
    return open_cv_image

