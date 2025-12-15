import cv2
import numpy as np
import subprocess

def mm_to_pixels(mm, dpi=300):
    return int(mm * dpi / 25.4)

def add_margin(image, top_mm, bottom_mm, left_mm, right_mm, dpi=300, color=(255, 255, 255)):
    # 밀리미터를 픽셀로 변환
    top = mm_to_pixels(top_mm, dpi)
    bottom = mm_to_pixels(bottom_mm, dpi)
    left = mm_to_pixels(left_mm, dpi)
    right = mm_to_pixels(right_mm, dpi)
    
    # 여백 추가
    return cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

def printImgs(printoutNum, path):
    image_path = f'./save/{path}.png'
    output_path = f'./save_print_img/{path}_with_margin.png'
    
    # 이미지 로드
    img = cv2.imread(image_path)
    
    # 밀리미터 단위로 여백 설정
    top_mm, bottom_mm, left_mm, right_mm = 16, 18.5, 8.5, 12
    
    # 여백 추가
    img_with_margin = add_margin(img, top_mm, bottom_mm, left_mm, right_mm)
    
    # 이미지 저장
    cv2.imwrite(output_path, img_with_margin)
    
    # 이미지 인쇄
    # for _ in range(printoutNum):
    #     subprocess.run(['lp', '-d', 'Canon_SELPHY_CP1300_', output_path], check=True)
