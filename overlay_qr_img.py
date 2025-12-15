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


def base64_to_mat(base64_data):
    # base64 데이터가 4의 배수가 아니면 패딩 추가
    padding = len(base64_data) % 4
    if padding != 0:
        base64_data += '=' * (4 - padding)

    # base64 데이터를 바이트로 디코딩
    img_data = base64.b64decode(base64_data)

    # 바이트 데이터를 numpy 배열로 변환
    img_array = np.frombuffer(img_data, dtype=np.uint8)

    # numpy 배열을 OpenCV 이미지로 디코딩
    mat_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    return mat_image

def overlay_qr_on_image(data):
    # Base64 헤더 제거 (data:image/png;base64, 등)
    if ',' in data:
        data = data.split(',')[1]

    # Base64 디코딩 (이미지 데이터 획득)
    img_data = base64.b64decode(data)
    
    # ImgBB 업로드 (메모리 상의 데이터 바로 전송)
    img_url = upload_image_to_imgbb(img_data)

    # OpenCV 이미지 변환
    nparr = np.frombuffer(img_data, np.uint8)
    img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # QR코드 생성 (메모리 상에서 이미지 객체 획득)
    qr_code_img = generate_qr_code_image(img_url)

    # QR 코드 합성 (메모리 상의 QR 이미지 사용)
    background_with_overlays_with_QR = add_qr_code_to_image(img_array, qr_code_img)

    # 파일 저장 준비
    num_files = count_files('./save')
    random_hex = ''.join(random.choice('0123456789ABCDEF') for _ in range(5))
    random_path = f'{num_files + 1}-{random_hex}'
    
    # 최종 결과 저장
    cv2.imwrite(f'./save/{random_path}.png', background_with_overlays_with_QR)
    
    # Main.py 요구사항(QR URL 반환)을 위해 QR 코드 별도 저장
    qr_filename = f"{random_path}_qrcode.png"
    cv2.imwrite(f"./save_qrcode/{qr_filename}", qr_code_img)

    # base64로 인코딩된 이미지 데이터 반환
    return random_path, qr_filename