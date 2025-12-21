import json
import cv2
import random
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np

from make_qrcode import generate_qr_code_image

from imgbb import upload_image_to_imgbb

def count_files(directory):
    """
    디렉토리 내 파일 개수를 반환합니다.
    """
    if not os.path.exists(directory):
        return 0
    files = os.listdir(directory)
    file_count = len(files)
    return file_count


def resize_image(background, max_width, max_height):
    original_height, original_width = background.shape[:2]
    scaling_factor = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * scaling_factor)
    new_height = int(original_height * scaling_factor)
    resized_background = cv2.resize(background, (new_width, new_height))
    return resized_background


def crop_image(image, top, bottom, left, right):
    height, width = image.shape[:2]
    top = min(top, height)
    bottom = min(bottom, height)
    left = min(left, width)
    right = min(right, width)
    return image[top:height-bottom, left:width-right]

def add_qr_code_to_image(background, qr_code_img):
    # 이미지가 단일 채널(그레이스케일)인 경우 3채널로 변환
    if len(qr_code_img.shape) == 2:  # 그레이스케일인 경우
        qr_code_img = cv2.cvtColor(qr_code_img, cv2.COLOR_GRAY2BGR)
    # QR 코드 이미지가 4채널(RGBA)인 경우 3채널로 변환
    elif qr_code_img.shape[2] == 4:
        qr_code_img = cv2.cvtColor(qr_code_img, cv2.COLOR_BGRA2BGR)

    # QR 코드 이미지 크기 조정 (여기서는 100x100 픽셀로 조정)
    qr_code_img_resized = resize_image(qr_code_img, 450, 450)

    qr_code_img_cropped = crop_image(qr_code_img_resized, top=27, bottom=27, left=27, right=27)

    # QR 코드의 높이와 너비
    qr_height, qr_width = qr_code_img_cropped.shape[:2]

    # 배경 이미지의 채널을 3채널로 변환 (필요시)
    if background.shape[2] == 4:
        background = cv2.cvtColor(background, cv2.COLOR_BGRA2BGR)

    # 배경 이미지의 너비 구하기
    background_height, background_width = background.shape[:2]

    # QR 코드가 배경 이미지의 오른쪽 상단에 위치하도록 X, Y 오프셋 계산
    x_offset = background_width - qr_width - 30  # 오른쪽 여백 45픽셀
    y_offset = 30  # 위쪽 여백 45픽셀

    # QR 코드가 3채널(RGB)이므로 그냥 덮어씌우기
    background[y_offset:y_offset+qr_height, x_offset:x_offset+qr_width] = qr_code_img_cropped

    return background

def save_qr_code_only(qr_url, format='jpg', save_dir='save_qrcode_gif'):
    """
    URL을 받아 QR 코드를 생성하고 지정된 폴더에 저장한 뒤, 파일명과 QR 이미지 배열을 반환
    """
    os.makedirs(save_dir, exist_ok=True) # 지정된 저장 폴더가 없으면 생성

    qr_code_img = generate_qr_code_image(qr_url, format=format)
    
    # 랜덤 파일명 생성
    num_files = count_files(save_dir) # 지정된 폴더 기준으로 파일 개수 카운트
    random_hex = ''.join(random.choice('0123456789ABCDEF') for _ in range(5))
    qr_filename = f"qr_{random_hex}_{num_files}.png"
    
    cv2.imwrite(f"./{save_dir}/{qr_filename}", qr_code_img)
    
    return qr_filename, qr_code_img

def compose_final_image(static_image_bytes, qr_code_img):
    """
    이미지 바이트와 QR 코드 이미지(numpy array)를 받아 합성 후 저장
    """
    # Bytes -> OpenCV Image 변환
    nparr = np.frombuffer(static_image_bytes, np.uint8)
    background_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # QR 코드 합성
    final_img = add_qr_code_to_image(background_img, qr_code_img)

    # 파일 저장
    num_files = count_files('./save')
    random_hex = ''.join(random.choice('0123456789ABCDEF') for _ in range(5))
    save_path_name = f'{num_files + 1}-{random_hex}'
    
    cv2.imwrite(f'./save/{save_path_name}.png', final_img)
    
    return save_path_name