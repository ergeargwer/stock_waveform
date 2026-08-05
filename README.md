# Stock Waveform

台股股價**波形視覺化**工具：以 Z-Score 標準化收盤價畫成音訊波形風格，顏色表示漲跌、線寬表示成交量。

資料來源：[FinMind](https://finmindtrade.com/) `TaiwanStockPrice` API。

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=ergeargwer/stock_waveform&branch=main&mainModule=app.py)

## 線上執行（Streamlit Community Cloud）

免費託管，推送 `main` 後會自動重新部署。

### 一鍵部署

1. 用 **GitHub 帳號**登入 [Streamlit Community Cloud](https://share.streamlit.io)
2. 點開下方連結（或點 README 上方徽章）：

   **https://share.streamlit.io/deploy?repository=ergeargwer/stock_waveform&branch=main&mainModule=app.py**

3. 確認：
   - Repository：`ergeargwer/stock_waveform`
   - Branch：`main`
   - Main file path：`app.py`
4. （建議）**Advanced settings → Secrets** 貼上：

   ```toml
   FINMIND_API_KEY = "你的_FinMind_金鑰"
   ```

5. 按 **Deploy**，約 1–3 分鐘後取得 `*.streamlit.app` 公開網址

> 未設定金鑰時 FinMind 仍可能以限額模式運作；流量大時請填 Secrets。

### 之後更新

```bash
git push origin main
```

Cloud 會自動偵測並重新部署。

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

## 本機安裝與執行

```bash
git clone https://github.com/ergeargwer/stock_waveform.git
cd stock_waveform
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 選用：設定金鑰
cp .env.example .env
# 編輯 .env，填入 FINMIND_API_KEY

streamlit run app.py
```

瀏覽器開啟終端機顯示的本機網址（預設 `http://localhost:8501`）。

## 專案結構

```
stock_waveform/
├── app.py                 # Streamlit UI、快取、指標
├── data_loader.py         # FinMind 拉取、日漲跌、區間報酬、最大回撤
├── waveform.py            # Plotly 波形 + 成交量子圖
├── requirements.txt
├── .streamlit/config.toml # 雲端／本機主題與 server 設定
├── .env.example           # 金鑰範本（勿提交真實金鑰）
├── .env                   # 本機金鑰（已 gitignore）
└── README.md
```

## 設定

| 變數 / Secret | 說明 |
|---------------|------|
| `FINMIND_API_KEY` | FinMind token。本機：`.env`；線上：Streamlit **Secrets** |

未設定時仍可能有限額存取；公開站建議在 Cloud Secrets 填入，訪客不需自備金鑰。

## 開發備註

- `load_stock_data` 使用 `@st.cache_data(ttl=3600)`，同一標的／天數一小時內不重複打 API。
- 波形 stem 依「方向 × 線寬分箱」合併 trace，避免每個交易日各建 2 條 trace。
- `.env` 已列在 `.gitignore`，請勿把真實金鑰提交到版控。

## License

個人／學習用途。資料權利依 FinMind 服務條款。
