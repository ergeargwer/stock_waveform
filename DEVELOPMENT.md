# Stock Waveform 開發歷程

本文記錄本專案從原型、指標修正、開源發布、3D 擴充到 GitHub 可執行環境的演進。  
對應倉庫：https://github.com/ergeargwer/stock_waveform

| 項目 | 說明 |
|------|------|
| 技術棧 | Python、Streamlit、Plotly、pandas、numpy、requests、FinMind API |
| 主要分支 | `main` |
| 文件目的 | 保存決策背景、里程碑與 commit 對照，便於後續維護與交接 |

---

## 時間線總覽

| 階段 | 大約時間 | 重點 |
|------|----------|------|
| 0. 原型雛形 | 2026-04 前後 | 本機 Streamlit + FinMind + 2D 波形 |
| 1. 品質與指標修正 | 2026-08-05 | 回撤／區間報酬語意、快取、圖表效能、README |
| 2. 開源與雲端部署準備 | 2026-08-05 | GitHub public repo、Secrets、Streamlit Cloud 說明 |
| 3. 單檔 3D 視圖 | 2026-08-05 | 四 tab：2D + 三種 3D |
| 4. GitHub 直接執行 | 2026-08-05 | Codespaces Dev Container、轉發埠 8501 |

---

## 階段 0：原型雛形（開源前）

### 目標

以「音訊波形」隱喻呈現台股單檔波動：收盤價做 Z-Score 當波形高度，成交量影響線寬，漲跌以綠／紅著色。

### 初期模組分工

| 檔案 | 職責 |
|------|------|
| `app.py` | Streamlit UI、深色主題、側欄輸入、指標卡 |
| `data_loader.py` | FinMind `TaiwanStockPrice` 拉取、日漲跌 |
| `waveform.py` | Plotly 2D 波形與成交量 |
| `.env` | `FINMIND_API_KEY`（本機，不進版控） |

### 已知限制（後續改善動機）

1. **最大回撤**用區間 `(min − max) / max`，未依時間 peak-to-trough  
2. **「近期漲跌幅」**實為最後一日漲跌，易誤解  
3. 無 API 快取，重繪易打爆額度  
4. 必須按按鈕才載入，首屏空白  
5. 每個交易日多條 Plotly trace，天數一多變慢  
6. 缺 README／`.env.example`，不易重現環境  

---

## 階段 1：正確性、體驗、效能、可維護性

### 1.1 指標語意（正確性）

| 指標 | 修正前 | 修正後 |
|------|--------|--------|
| 最新日漲跌 | 標成「近期漲跌幅」 | 明確為最後交易日漲跌 |
| 區間報酬 | 無 | 首日收盤 → 末日收盤 |
| 最大回撤 | `(min−max)/max` | `cummax` peak-to-trough（通常為負或 0） |

實作位置：`data_loader.period_return_pct`、`data_loader.max_drawdown_pct`。

驗證例：價格路徑 `100 → 80 → 150 → 120`  
- 舊算法約 −46.7%  
- 新算法 −20%（相對歷史高點 150 回檔至 120 不構成此路徑最大回撤；最大發生在 100→80）

### 1.2 體驗

- `@st.cache_data(ttl=3600)` 包住 API 拉取  
- 首次進入自動載入預設 **2330 / 30 交易日**  
- 側欄改稱「觀察交易日數」  

### 1.3 圖表效能

- 2D 改為 `make_subplots`：波形 + 成交量共用 X 軸  
- Stem 依「方向 × 線寬分箱」合併 trace（約固定少數 traces，而非 O(N)）  
- 新進入點：`build_stock_figure()`  

### 1.4 可維護性

- 新增 `README.md`、`.env.example`  
- 強化 `.gitignore`（`.env`、`__pycache__`、`.venv`、secrets 等）  
- 缺價避免一律 `fillna(0)`，改 ffill + 必要 dropna  

---

## 階段 2：發布 GitHub 與雲端部署準備

### 2.1 首次開源

| 項目 | 內容 |
|------|------|
| 遠端 | https://github.com/ergeargwer/stock_waveform |
| 可見性 | Public |
| 初始 commit | `ab1201a` Initial release |

**刻意不進版控**：`.env` 與真實 `FINMIND_API_KEY`。

### 2.2 Streamlit Community Cloud 就緒

| 改動 | 說明 |
|------|------|
| `st.secrets` | 線上金鑰；本機仍可用 `.env` |
| 金鑰可選 | 無 key 時限額模式，側欄提示而非硬擋 |
| `.streamlit/config.toml` | 深色主題、headless |
| README | 一鍵 deploy 連結與 Secrets 範例 |

相關 commit：`3b04c3f` Enable Streamlit Community Cloud deployment。

### 2.3 Dev Container 初稿

遠端新增 `.devcontainer/`（`003eb3c`），為後續 Codespaces 一鍵執行鋪路。

---

## 階段 3：單檔股票 3D 視覺化

### 需求摘要

在既有 2D 之外，以 **tab** 增加三個 **單一股票** 3D 視圖；不改天數上下限、不改 2D 與快取邏輯。

### 分頁規格

| Tab | 內容 | 座標 |
|-----|------|------|
| 2D 波形圖 | 原圖（維持） | — |
| 3D 波形立體圖 | `scatter3d` lines+markers | X 日序 / Y 收盤 Z-Score / Z 量 Z-Score；端點依漲跌色 |
| 3D 價量指標曲面 | K 值軌跡 | X 日序 / Y 收盤 Z-Score / Z=K；K 分區著色 |
| 3D 報酬相位軌跡 | 相位空間 | X 今日報酬 / Y 昨日報酬 / Z 量變化率；時間漸層 |

### 資料層新增（`data_loader.py`）

1. **`calculate_kd(df, n=9, k_period=3, d_period=3)`**  
   - RSV = (收−n 日低) / (n 日高−n 日低) × 100  
   - K、D 以 `1/period` 權重遞迴平滑，初值 50（台股常見慣例）  
   - 資料 **&lt; 14 筆**時由繪圖端明確中文警示，**不**靜默填假資料  

2. **`compute_return_phase_fields(df)`**  
   - `return_today`、`return_yesterday`、`volume_change_rate`  
   - 缺前一日基準的列由繪圖端捨棄並提示  

### 圖表層（新檔 `waveform_3d.py`）

| 函式 | 回傳 |
|------|------|
| `plot_waveform_3d` | `(Figure \| None, 錯誤訊息 \| None)` |
| `plot_kd_surface_3d` | 同上；&lt; 14 筆必失敗並說明 |
| `plot_return_phase_3d` | 成功時第二值可為「已捨棄 N 筆」資訊 |

原則：**不可靜默 fallback**；錯誤與不足一律中文提示。

### UI（`app.py`）

```
st.tabs([
  "2D 波形圖",
  "3D 波形立體圖",
  "3D 價量指標曲面",
  "3D 報酬相位軌跡",
])
```

- 2D：`displayModeBar=False`（維持簡潔）  
- 3D：`displayModeBar=True`（旋轉／縮放）  
- 程式與 UI **不使用 emoji**（規範）  

相關 commit：`99aa277` Add single-stock 3D views。

---

## 階段 4：在 GitHub 上直接執行

### 背景

GitHub 倉庫頁無法內嵌長期跑 Python；實務路徑：

1. **GitHub Codespaces** — 在 GitHub 雲端 IDE 裡跑 Streamlit  
2. **Streamlit Community Cloud** — 公開 `*.streamlit.app`  

### Codespaces  hardening（`22febd7`）

| 設定 | 值／行為 |
|------|----------|
| Image | `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm` |
| postCreate / updateContent | `pip3 install --user -r requirements.txt` |
| postAttach | `streamlit run app.py` 綁定 `0.0.0.0:8501` |
| CORS / XSRF | 關閉（轉發埠預覽必要） |
| forwardPorts | 8501，`openPreview` |

### 使用者入口

- Codespaces：https://codespaces.new/ergeargwer/stock_waveform?quickstart=1  
- Streamlit 部署：https://share.streamlit.io/deploy?repository=ergeargwer/stock_waveform&branch=main&mainModule=app.py  

金鑰：Codespaces 用倉庫 Codespaces Secrets；Streamlit Cloud 用 App Secrets；本機用 `.env`。

---

## Git Commit 對照表

| Commit | 日期 | 摘要 |
|--------|------|------|
| `ab1201a` | 2026-08-05 | 初始開源：2D 波形、指標、README、requirements |
| `3b04c3f` | 2026-08-05 | Streamlit Cloud：secrets、config、部署文件 |
| `003eb3c` | 2026-08-05 | 新增 Dev Container 資料夾 |
| `99aa277` | 2026-08-05 | 3D 三視圖 + KD／相位欄位 + tabs |
| `22febd7` | 2026-08-05 | Codespaces 一鍵執行與 README 雙入口說明 |

（後續 commit 請以 `git log` 為準並同步更新本表。）

---

## 目前架構快照

```
stock_waveform/
├── app.py                 # UI、快取、指標卡、四 tab
├── data_loader.py         # API、漲跌、報酬、回撤、KD、相位欄位
├── waveform.py            # 2D Plotly
├── waveform_3d.py         # 3D Plotly × 3
├── requirements.txt
├── .devcontainer/         # Codespaces
├── .streamlit/config.toml
├── .env.example
├── README.md              # 使用與部署
└── DEVELOPMENT.md         # 本開發歷程
```

### 資料流（簡圖）

```
側欄 ticker / n_days
        │
        ▼
load_stock_data  (@st.cache_data ttl=3600)
        │
        ▼
compute_daily_change
        │
        ├── metrics: 收盤 / 日漲跌 / 區間報酬 / 最大回撤
        │
        ├── Tab 2D ── build_stock_figure
        ├── Tab 3D 波形 ── plot_waveform_3d
        ├── Tab 3D KD ── calculate_kd → plot_kd_surface_3d
        └── Tab 3D 相位 ── compute_return_phase_fields → plot_return_phase_3d
```

---

## 設計原則（約定）

1. **繁體中文** UI、警示與說明  
2. **無 emoji** 於程式與輸出  
3. **錯誤要明示**：資料不足、API 失敗不可靜默帶過  
4. **不輕易加依賴**：3D 沿用既有 Plotly  
5. **秘密不進 Git**：`.env` / secrets.toml 一律 ignore  
6. **快取優先**：同一標的與天數一小時內不重打 FinMind  

---

## 已知限制與後續可做

| 項目 | 說明 |
|------|------|
| 觀察天數 vs 交易日 | 以日曆日約 2 倍回溯再 `tail(n)`，長假／停牌時可能不足 |
| KD 與券商微差 | 初值、除權、平滑公式細節可能與特定看盤軟體差 1 檔 |
| Codespaces 額度 | 免費時數有限，長期 Demo 建議 Streamlit Cloud |
| 多股比較 | 尚未支援 |
| 單元測試檔 | 核心函式曾以腳本抽查，尚未固定 `tests/` 套件 |
| 技術指標擴充 | 例如 MA、RSI、布林帶疊圖 |

---

## 如何更新本文件

每次有意義的功能或架構變更時：

1. 在「時間線總覽」加一列階段（若屬新階段）  
2. 寫清**動機 → 作法 → 影響檔案**  
3. 在「Git Commit 對照表」補上 hash 與一句話  
4. 若對外行為改變，同步改 `README.md`  

```bash
# 建議提交訊息範例
git add DEVELOPMENT.md README.md
git commit -m "docs: update development history for <topic>"
```

---

## License 與資料來源

- 程式：個人／學習用途（見 README）  
- 行情資料：依 [FinMind](https://finmindtrade.com/) 服務條款  
- 請勿將 API token 寫入本文件或任何 commit  

---

*文件建立：2026-08-05。最後對應 `main` 上已知 commit 至 `22febd7`。*
