import base64
import requests
 
from dotenv import load_dotenv
import os

# .env 파일 활성화
load_dotenv()

SERVICE_KEY = os.getenv('IMGBB_API_KEY')


def upload_image_to_imgbb(image_data):
    # image_data가 bytes 타입이면 base64 문자열로 인코딩
    if isinstance(image_data, bytes):
        base64_image = base64.b64encode(image_data).decode('utf-8')
    else:
        # 이미 문자열(Base64)이라면 그대로 사용
        base64_image = image_data

    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": SERVICE_KEY,
        "image": base64_image,
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data['data']['url']
    else:
        return None
