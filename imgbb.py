import base64
import requests
 
from dotenv import load_dotenv
import os

# .env 파일 활성화
load_dotenv()

SERVICE_KEY = os.getenv('IMGBB_API_KEY')


def upload_image_to_imgbb(image_data, filename="image.jpg"):
    url = "https://api.imgbb.com/1/upload"
    
    # 기본 파라미터 (API 키)
    payload = {
        "key": SERVICE_KEY,
    }

    try:
        if isinstance(image_data, bytes):
            # 바이너리 데이터인 경우: multipart/form-data로 직접 전송
            # 호출부에서 넘겨준 filename 사용 (예: "image.gif")
            files = {
                "image": (filename, image_data)
            }
            response = requests.post(url, data=payload, files=files)
        else:
            # 문자열(Base64 또는 URL)인 경우: 기존 방식 호환
            payload["image"] = image_data
            response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data['data']['url']
        else:
            print(f"ImgBB Upload Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"ImgBB Exception: {e}")
        return None
