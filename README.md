# Stock Waveform

台股股價**波形視覺化**工具：以 Z-Score 標準化收盤價畫成音訊波形風格，顏色表示漲跌、線寬表示成交量。

資料來源：[FinMind](https://finmindtrade.com/) `TaiwanStockPrice` API。

## 功能

- 輸入股票代碼與觀察交易日數（10–120）
- **最新收盤價**、**最新日漲跌**、**區間報酬**、**最大回撤**（peak-to-trough）
- 波形圖 + 成交量（同一張圖、共用 X 軸）
- API 結果快取 1 小時；首次開啟自動載入預設標的（2330）

### 視覺編碼

| 元素 | 含義 |
|------|------|
| Y 軸 | 收盤價 Z-Score（相對觀察期均值） |
| 綠 / 紅 / 灰 | 上漲 / 下跌 / 平盤 |
| 線段粗細 | 當日成交量（Z-Score 分箱） |
| 藍色曲線 | 端點平滑連線 |
| 下方 bar | 成交量 |

### 指標定義

| 指標 | 定義 |
|------|------|
| 最新日漲跌 | 最後一個交易日相對於前一日的漲跌幅 |
| 區間報酬 | 首日收盤 → 末日收盤的報酬率 |
| 最大回撤 | 依時間順序，相對累積最高收盤價的最大跌幅（負值） |

## 環境需求

- Python 3.10+
- FinMind API 金鑰（[註冊](https://finmindtrade.com/)）

## 安裝與執行

```bash
cd stock_waveform
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 設定金鑰
cp .env.example .env
# 編輯 .env，將 FINMIND_API_KEY 改為你的金鑰

streamlit run app.py
```

瀏覽器開啟終端機顯示的本機網址（預設 `http://localhost:8501`）。

## 專案結構

```
stock_waveform/
├── app.py              # Streamlit UI、快取、指標
├── data_loader.py      # FinMind 拉取、日漲跌、區間報酬、最大回撤
├── waveform.py         # Plotly 波形 + 成交量子圖
├── requirements.txt
├── .env.example        # 金鑰範本（勿提交真實金鑰）
├── .env                # 本機金鑰（已 gitignore）
└── README.md
```

## 設定

| 變數 | 說明 |
|------|------|
| `FINMIND_API_KEY` | FinMind token；未設定時仍可能有限額存取，建議填入 |

## 開發備註

- `load_stock_data` 使用 `@st.cache_data(ttl=3600)`，同一標的／天數一小時內不重複打 API。
- 波形 stem 依「方向 × 線寬分箱」合併 trace，避免每個交易日各建 2 條 trace。
- `.env` 已列在 `.gitignore`，請勿把真實金鑰提交到版控。

## License

個人／學習用途。資料權利依 FinMind 服務條款。
