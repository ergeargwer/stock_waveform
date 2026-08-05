# Stock Waveform

台股股價**波形視覺化**工具：以 Z-Score 標準化收盤價畫成音訊波形風格，顏色表示漲跌、線寬表示成交量。

資料來源：[FinMind](https://finmindtrade.com/) `TaiwanStockPrice` API。

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ergeargwer/stock_waveform?quickstart=1)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=ergeargwer/stock_waveform&branch=main&mainModule=app.py)

## 在 GitHub 上直接執行

有兩種方式，**不必在本機安裝 Python**。

| 方式 | 適合 | 說明 |
|------|------|------|
| **GitHub Codespaces** | 開發、在 GitHub 網頁裡跑 | 開 Codespace 後會自動安裝依賴並啟動 Streamlit（埠 8501） |
| **Streamlit Community Cloud** | 分享公開網址給別人 | 部署成 `*.streamlit.app`，訪客免登入 GitHub |

---

### 方式 A：GitHub Codespaces（推薦「在 GitHub 上執行」）

1. 開啟倉庫：https://github.com/ergeargwer/stock_waveform  
2. 點綠色 **Code** → **Codespaces** → **Create codespace on main**  
   或直接點上方 **Open in GitHub Codespaces** 徽章：  
   https://codespaces.new/ergeargwer/stock_waveform?quickstart=1  
3. 首次建立約需 1–3 分鐘（安裝 `requirements.txt`）  
4. 容器就緒後會**自動**執行 `streamlit run app.py`，並在預覽／轉發埠 **8501** 開啟介面  
5. 若預覽未自動跳出：左側 **Ports** → 找到 `8501` → **Open in Browser**

#### Codespaces 金鑰（選用）

1. 倉庫 **Settings** → **Secrets and variables** → **Codespaces**  
2. 新增 `FINMIND_API_KEY`（值為你的 FinMind token）  
3. **重建** Codespace 後環境變數才會生效  

未設定時仍可能以 FinMind 限額模式運作。

> 免費額度依 GitHub 帳號方案而定；用完可改用下方 Streamlit Cloud。

---

### 方式 B：Streamlit Community Cloud（公開 Demo）

1. 用 GitHub 登入 [share.streamlit.io](https://share.streamlit.io)  
2. 一鍵部署：  
   https://share.streamlit.io/deploy?repository=ergeargwer/stock_waveform&branch=main&mainModule=app.py  
3. 確認 Main file 為 `app.py`  
4. **Advanced settings → Secrets**（建議）：

   ```toml
   FINMIND_API_KEY = "你的_FinMind_金鑰"
   ```

5. 按 **Deploy**，取得 `https://xxxx.streamlit.app` 公開網址  

之後 `git push origin main` 會自動重新部署。

---

## 功能

- 輸入股票代碼與觀察交易日數（10–120）
- **最新收盤價**、**最新日漲跌**、**區間報酬**、**最大回撤**（peak-to-trough）
- 四個分頁視圖：
  - **2D 波形圖**：Z-Score 波形 + 成交量（共用 X 軸）
  - **3D 波形立體圖**：交易日 × 收盤 Z-Score × 成交量 Z-Score
  - **3D 價量指標曲面**：交易日 × 收盤 Z-Score × KD(9,3,3) 的 K 值（需至少 14 個交易日）
  - **3D 報酬相位軌跡**：今日報酬 × 昨日報酬 × 成交量變化率（時間漸層）
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

瀏覽器開啟 `http://localhost:8501`。

## 專案結構

```
stock_waveform/
├── app.py                      # Streamlit UI、快取、指標、分頁
├── data_loader.py              # FinMind、日漲跌、區間報酬、回撤、KD、相位欄位
├── waveform.py                 # Plotly 2D 波形 + 成交量子圖
├── waveform_3d.py              # Plotly 3D：波形立體、KD 曲面、報酬相位
├── requirements.txt
├── .devcontainer/
│   └── devcontainer.json       # GitHub Codespaces：自動安裝並啟動 Streamlit
├── .streamlit/config.toml      # 伺服器與深色主題（相容 Codespaces 轉發）
├── .env.example                # 金鑰範本（勿提交真實金鑰）
├── .env                        # 本機金鑰（已 gitignore）
└── README.md
```

## 設定

| 變數 / Secret | 本機 | Codespaces | Streamlit Cloud |
|---------------|------|------------|-----------------|
| `FINMIND_API_KEY` | `.env` | 倉庫 Codespaces Secrets | App Secrets（TOML） |

未設定時仍可能有限額存取；公開站建議填入金鑰，訪客不需自備 API key。

## 開發備註

- `load_stock_data` 使用 `@st.cache_data(ttl=3600)`，同一標的／天數一小時內不重複打 API。
- 波形 stem 依「方向 × 線寬分箱」合併 trace，避免每個交易日各建 2 條 trace。
- Codespaces 透過 `.devcontainer/devcontainer.json` 的 `postAttachCommand` 自動啟動 Streamlit，並轉發 8501。
- `.env` 已列在 `.gitignore`，請勿把真實金鑰提交到版控。

## 開發歷程

完整里程碑、指標修正理由、3D 規格與 commit 對照見：

**[DEVELOPMENT.md](./DEVELOPMENT.md)**

## License

個人／學習用途。資料權利依 FinMind 服務條款。
