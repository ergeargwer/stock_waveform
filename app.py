import streamlit as st
import os
from dotenv import load_dotenv

from data_loader import (
    get_stock_data,
    compute_daily_change,
    period_return_pct,
    max_drawdown_pct,
)
from waveform import build_stock_figure

load_dotenv()

st.set_page_config(page_title="Stock Waveform", layout="wide")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;600&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', 'Noto Sans TC', sans-serif;
        color: #e0e6f0;
    }
    .stApp {
        background-color: #0e1117;
    }
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
    }
    .stButton > button {
        width: 100%;
        background-color: #4e9af1;
        color: white;
        border-radius: 6px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #3b82f6;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        color: #4e9af1;
    }
    div[data-testid="metric-container"] {
        background-color: #1e2433;
        border: 1px solid #2d3548;
        border-radius: 8px;
        padding: 15px;
    }
</style>
""",
    unsafe_allow_html=True,
)

api_key = os.getenv("FINMIND_API_KEY")
if not api_key or api_key == "your_api_key_here":
    st.error("⚠️ 尚未設定 FINMIND_API_KEY，請複製 `.env.example` 為 `.env` 並填入金鑰。")

st.sidebar.markdown(
    "<h2 style='text-align: center; color: #e0e6f0; margin-bottom: 0;'>Stock Waveform</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='text-align: center; color: #8892a4; font-size: 0.9rem; margin-top: 5px;'>波形視覺化分析</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("<hr style='border-color: #2d3548;'>", unsafe_allow_html=True)

ticker = st.sidebar.text_input("股票代碼", placeholder="例如 2330", value="2330")
n_days = st.sidebar.slider("觀察交易日數", min_value=10, max_value=120, value=30, step=5)
submit_btn = st.sidebar.button("產生波形圖")

# 首次進入自動載入預設標的；之後改參數需按按鈕
if "has_loaded" not in st.session_state:
    st.session_state.has_loaded = False

should_load = submit_btn or not st.session_state.has_loaded


@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_data(ticker_code: str, days: int):
    """快取 API 結果一小時，避免重複請求。"""
    return get_stock_data(ticker_code, days)


if should_load:
    ticker = ticker.strip()
    if not ticker:
        st.warning("請輸入股票代碼。")
        st.stop()

    with st.spinner(f"正在取得 {ticker} 資料..."):
        try:
            df = load_stock_data(ticker, n_days)
        except ValueError as e:
            st.warning(str(e))
            st.stop()

    st.session_state.has_loaded = True

    if len(df) < 10:
        st.warning("資料筆數不足 10 筆，請嘗試縮短天數或確認代碼。")
        st.stop()

    df = compute_daily_change(df)

    latest_close = float(df["close"].iloc[-1])
    latest_change = float(df["change_pct"].iloc[-1])
    period_ret = period_return_pct(df["close"])
    drawdown = max_drawdown_pct(df["close"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新收盤價", f"{latest_close:.2f}")
    col2.metric(
        "最新日漲跌",
        f"{latest_change:.2f}%",
        delta=f"{latest_change:.2f}%",
        delta_color="normal",
    )
    col3.metric(
        "區間報酬",
        f"{period_ret:.2f}%",
        delta=f"{period_ret:.2f}%",
        delta_color="normal",
        help="觀察期第一個交易日收盤 → 最後一個交易日收盤的報酬率",
    )
    col4.metric(
        "最大回撤",
        f"{drawdown:.2f}%",
        delta=f"{drawdown:.2f}%",
        delta_color="inverse",
        help="依時間順序，相對歷史最高收盤的最大跌幅（peak-to-trough）",
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    fig = build_stock_figure(df, ticker)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        "<div style='background-color: #1e2433; padding: 15px; border-radius: 8px; "
        "border: 1px solid #2d3548; color: #e0e6f0; text-align: center;'>"
        "線段向上為上漲（綠），向下為下跌（紅），線段粗細代表當日成交量大小；"
        "Y 軸為收盤價 Z-Score；下方為成交量"
        "</div>",
        unsafe_allow_html=True,
    )
