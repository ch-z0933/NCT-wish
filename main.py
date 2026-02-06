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
    # 請確保你的試算表名稱已改為 "NCTWISH_Sales_Data" 或你喜歡的名字
    return client.open("NCTWISH_Sales_Data").sheet1

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"雲端連線失敗: {e}")
    sheet = None

# --- 2. 原始設定區 ---
st.set_page_config(page_title="NCT WISH 戰情室", layout="wide")
st.title("🌟 NCT WISH [COLORFUL] 合照活動 - 庫存監控")

# 基礎 API URL (不帶 variation_id)
BASE_API_URL = "https://www.fanmeofficial.com/api/merchants/676a73a4b4857d0045b9424a/products/698074227f039c011c134d72/check_stock"

# 【關鍵】請在這裡填入你觀察到的成員名稱與 ID
MEMBERS_CONFIG = {
    "SION": "6980742204b90f0014c8666a",
    # "RIKU": "填入你看到的 ID",
    # "YUSHI": "填入你看到的 ID",
    # ...以此類推
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.fanmeofficial.com/products/photoevent-kncwi926020001-sion"
}

# --- 3. 初始化資料 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['時間', '事件', '詳情'])
if 'member_logs' not in st.session_state:
    st.session_state.member_logs = {}
if 'member_last_stock' not in st.session_state:
    st.session_state.member_last_stock = {}

def get_member_stock(m_name, v_id):
    try:
        res = requests.get(f"{BASE_API_URL}?variation_id={v_id}&t={int(time.time())}", headers=HEADERS, timeout=10)
        data = res.json()
        return data.get('quantity', 0)
    except:
        return None

# --- 4. 主程式執行 ---
status_placeholder = st.empty()

while True:
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz).strftime("%H:%M:%S")
    
    current_status = []
    
    for name, v_id in MEMBERS_CONFIG.items():
        stock = get_member_stock(name, v_id)
        
        if stock is not None:
            # 如果是第一次執行，記錄初始庫存
            if name not in st.session_state.member_last_stock:
                st.session_state.member_last_stock[name] = stock
                st.session_state.member_logs[name] = pd.DataFrame([
                    {'時間': now, '狀態': '開始監控', '變動': 0, '剩餘庫存': stock}
                ])
            
            last_stock = st.session_state.member_last_stock[name]
            
            # 庫存有變動 (剩餘庫存減少 = 賣出)
            if stock != last_stock:
                diff = last_stock - stock  # 正數代表賣出
                status = "🛒 售出" if diff > 0 else "🔄 庫存回補"
                
                # 寫入 Google Sheets
                if sheet:
                    try:
                        m_sheet = sheet.spreadsheet.worksheet(name)
                        m_sheet.append_row([now, status, diff, stock])
                    except:
                        pass # 找不到分頁就跳過

                # 更新 Session State
                new_entry = pd.DataFrame([{'時間': now, '狀態': status, '變動': diff, '剩餘庫存': stock}])
                st.session_state.member_logs[name] = pd.concat([new_entry, st.session_state.member_logs[name]], ignore_index=True)
                
                # 記錄到全體異動日誌
                log_entry = pd.DataFrame([{'時間': now, '事件': f"{name} {status}", '詳情': f"變動 {diff}, 剩餘 {stock}"}])
                st.session_state.history = pd.concat([log_entry, st.session_state.history], ignore_index=True)
                
                st.session_state.member_last_stock[name] = stock
            
            current_status.append({"成員": name, "目前剩餘庫存": stock})

    # --- 畫面渲染 ---
    with status_placeholder.container():
        st.write("### 👥 各成員庫存現況")
        st.table(pd.DataFrame(current_status))

        st.write("### 📄 個別監控紀錄")
        if current_status:
            tabs = st.tabs([m['成員'] for m in current_status])
            for i, tab in enumerate(tabs):
                m_name = current_status[i]['成員']
                with tab:
                    st.dataframe(st.session_state.member_logs[m_name], use_container_width=True)

        st.write("### 📜 全體異動日誌 (庫存異動時才會顯示)")
        st.dataframe(st.session_state.history, use_container_width=True)

    time.sleep(20) # Fanme 建議不要刷太快，20-30秒一次較安全
    st.rerun()
