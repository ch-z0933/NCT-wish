import requests
import time

# 目標 URL
url = "https://www.fanmeofficial.com/api/merchants/676a73a4b4857d0045b9424a/products/698074227f039c011c134d72/check_stock"
params = {
    "variation_id": "6980742204b90f0014c8666a"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fanmeofficial.com/products/photoevent-kncwi926020001-sion"
}

def check_stock():
    try:
        response = requests.get(https://www.fanmeofficial.com/api/merchants/676a73a4b4857d0045b9424a/products/698074227f039c011c134d72/check_stock?variation_id=6980742204b90f0014c8666a, params=params, headers=headers)
        data = response.json()
        
        # 提取庫存數量
        stock = data.get('quantity')
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 目前剩餘庫存: {stock}")
        
    except Exception as e:
        print(f"發生錯誤: {e}")

# 每 60 秒檢查一次
while True:
    check_stock()
    time.sleep(60)
