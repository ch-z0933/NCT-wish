import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

# --- 1. Google Sheets 核心連線 ---
def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # 請確認你的試算表名稱改為 "NCTWISH_Sales_Data"
    return client.open("NCTWISH_Sales_Data").sheet1

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"雲端連線失敗: {e}")
    sheet = None

# --- 2. 原始設定區 ---
st.set_page_config(page_title="NCT WISH 戰情室", layout="wide")
st.title("🌟 NCT WISH [COLORFUL] 合照活動 - 即時銷售監控")

# 你的基準起點庫存
BASE_STOCK = 14995 

# 基礎 API 網址
BASE_API_URL = "https://www.fanmeofficial.com/api/merchants/676a73a4b4857d0045b9424a/products/698074227f039c011c134d72/check_stock"

# 成員 ID 配置 (請根據你觀察到的 ID 補完)
MEMBERS_CONFIG = {
    "SION": "6980742204b90f0014c8666a",
    # "RIKU": "請填入 RIKU 的 ID",
    # "YUSHI": "請填入 YUSHI 的 ID",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# --- 3. 初始化資料庫 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['時間', '事件', '變動'])
if 'member_logs' not in st.session_state:
    st.session_state.member_logs = {}
if 'member_last_sales' not in st.session_state:
    st.session_state.member_last_sales = {}

def get_stock(v_id):
    try:
        res = requests.get(f"{BASE_API_URL}?variation_id={v_id}&t={int(time.time())}", headers=HEADERS, timeout=10)
        return res.json().get('quantity', 0)
    except:
        return None

# --- 4. 主程式執行 ---
status_placeholder = st.empty()

while True:
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz).strftime("%H:%M:%S")
    
    current_summary = []
    
    for name, v_id in MEMBERS_CONFIG.items():
        stock = get_stock(v_id)
        
        if stock is not None:
            # 計算銷量 = 基準 14995 - 目前剩餘
            total_sales = BASE_STOCK - stock
            
            # 初始化該成員紀錄
            if name not in st.session_state.member_last_sales:
                st.session_state.member_last_sales[name] = total_sales
                st.session_state.member_logs[name] = pd.DataFrame([
                    {'時間': now, '狀態': '開始監控', '購買張數': 0, '累積總銷量': total_sales}
                ])
            
            last_sales = st.session_state.member_last_sales[name]
            
            # 若總
