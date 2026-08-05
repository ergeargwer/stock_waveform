import datetime
import os

import numpy as np
import pandas as pd
import requests


def get_stock_data(ticker: str, n_days: int) -> pd.DataFrame:
    end_date = datetime.date.today()
    # 日曆日約 2 倍，涵蓋週末／假日後再取最近 n 個交易日
    start_date = end_date - datetime.timedelta(days=n_days * 2)

    url = "https://api.finmindtrade.com/api/v4/data"
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": str(ticker).strip(),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }

    token = os.getenv("FINMIND_API_KEY")
    if token and token != "your_api_key_here":
        parameter["token"] = token

    headers = {
        "User-Agent": "StockWaveform/1.0 (FinMind client)"
    }

    try:
        resp = requests.get(url, params=parameter, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("msg") != "success":
            raise ValueError(f"FinMind API 錯誤: {data.get('msg')}")

        records = data.get("data", [])
        if not records:
            raise ValueError(f"查無股票代碼 {ticker} 的交易資料")

        df = pd.DataFrame(records)

        cols_to_keep = ["date", "open", "max", "min", "close", "Trading_Volume"]
        df = df[[c for c in cols_to_keep if c in df.columns]].copy()

        df["date"] = pd.to_datetime(df["date"])

        numeric_cols = ["open", "max", "min", "close", "Trading_Volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 缺價不填 0（會扭曲 Z-Score），改以前值填補後再丟棄仍無效的列
        df = df.ffill()
        df = df.dropna(subset=["close", "Trading_Volume"])

        df = df.sort_values("date").reset_index(drop=True)
        df = df.tail(n_days).reset_index(drop=True)

        if df.empty:
            raise ValueError(f"查無近期資料 (代碼: {ticker})")

        return df

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"資料取得失敗: {str(e)}") from e


def compute_daily_change(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["change_pct"] = (df["close"] - df["close"].shift(1)) / df["close"].shift(1) * 100
    df.loc[df.index[0], "change_pct"] = 0.0
    df["change_pct"] = df["change_pct"].fillna(0)

    df["direction"] = 0
    df.loc[df["change_pct"] > 0, "direction"] = 1
    df.loc[df["change_pct"] < 0, "direction"] = -1
    df.loc[df.index[0], "direction"] = 0

    return df


def period_return_pct(close: pd.Series) -> float:
    """區間報酬：觀察期首日收盤 → 末日收盤的報酬率（%）。"""
    if close is None or len(close) < 1:
        return 0.0
    first = float(close.iloc[0])
    if first == 0 or pd.isna(first):
        return 0.0
    last = float(close.iloc[-1])
    if pd.isna(last):
        return 0.0
    return (last / first - 1.0) * 100.0


def max_drawdown_pct(close: pd.Series) -> float:
    """
    最大回撤（peak-to-trough）：依時間順序，相對歷史最高收盤的最大跌幅（%）。
    回傳值為負數或 0（例如 -12.5 表示回撤 12.5%）。
    """
    if close is None or len(close) < 1:
        return 0.0
    s = close.astype(float)
    peak = s.cummax()
    # 僅在 peak > 0 時計算，避免除以 0
    valid = peak > 0
    if not valid.any():
        return 0.0
    dd = pd.Series(np.nan, index=s.index, dtype=float)
    dd.loc[valid] = (s.loc[valid] - peak.loc[valid]) / peak.loc[valid] * 100.0
    val = dd.min(skipna=True)
    if pd.isna(val):
        return 0.0
    return float(val)


def calculate_kd(
    df: pd.DataFrame,
    n: int = 9,
    k_period: int = 3,
    d_period: int = 3,
) -> pd.DataFrame:
    """
    計算標準 KD(n, k_period, d_period)，預設 KD(9,3,3)。

    - RSV = (收盤 - n 日最低) / (n 日最高 - n 日最低) * 100
    - K = (1 - 1/k_period) * 前K + (1/k_period) * RSV
    - D = (1 - 1/d_period) * 前D + (1/d_period) * K
    初始 K、D 以 50 起算（台股常見看盤軟體慣例）。

    回傳含欄位 K、D 的新 DataFrame；前 n-1 筆 RSV 無效時 K、D 為 NaN。
    不在此處以預設值填補缺資料；呼叫端應檢查筆數是否足夠（建議 >= 14）。
    """
    if df is None or df.empty:
        raise ValueError("無法計算 KD：資料為空")

    required = {"close", "max", "min"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"無法計算 KD：缺少欄位 {sorted(missing)}")

    out = df.copy()
    low_n = out["min"].rolling(window=n, min_periods=n).min()
    high_n = out["max"].rolling(window=n, min_periods=n).max()
    denom = high_n - low_n

    rsv = pd.Series(np.nan, index=out.index, dtype=float)
    valid_range = denom > 0
    rsv.loc[valid_range] = (
        (out.loc[valid_range, "close"] - low_n.loc[valid_range])
        / denom.loc[valid_range]
        * 100.0
    )
    # 區間高低相等時 RSV 無定義方向；採看盤軟體常見作法設為 50（非缺值填補）
    zero_range = denom.eq(0) & high_n.notna()
    rsv.loc[zero_range] = 50.0

    k_alpha = 1.0 / k_period
    d_alpha = 1.0 / d_period
    k_list: list[float] = []
    d_list: list[float] = []
    k_prev = 50.0
    d_prev = 50.0
    started = False

    for val in rsv.to_numpy(dtype=float):
        if np.isnan(val):
            k_list.append(np.nan)
            d_list.append(np.nan)
            continue
        if not started:
            # 第一個有效 RSV：仍用遞迴平滑，自 50 起算
            started = True
        k = (1.0 - k_alpha) * k_prev + k_alpha * float(val)
        d = (1.0 - d_alpha) * d_prev + d_alpha * k
        k_list.append(k)
        d_list.append(d)
        k_prev = k
        d_prev = d

    out["K"] = k_list
    out["D"] = d_list
    out["RSV"] = rsv.to_numpy(dtype=float)
    return out


def compute_return_phase_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算報酬相位軌跡所需欄位（不丟棄列，由繪圖端處理缺值）：

    - return_today：今日報酬率 (close_t / close_{t-1} - 1)
    - return_yesterday：昨日報酬率（return_today 位移一天）
    - volume_change_rate：成交量變化率 (vol_t / vol_{t-1} - 1)
    """
    if df is None or df.empty:
        raise ValueError("無法計算報酬相位欄位：資料為空")

    out = df.copy()
    close = out["close"].astype(float)
    vol = out["Trading_Volume"].astype(float)

    out["return_today"] = close / close.shift(1) - 1.0
    out["return_yesterday"] = out["return_today"].shift(1)
    # 成交量為 0 時變化率無意義，維持 NaN，不填 0
    prev_vol = vol.shift(1)
    out["volume_change_rate"] = np.where(
        prev_vol.to_numpy(dtype=float) > 0,
        vol.to_numpy(dtype=float) / prev_vol.to_numpy(dtype=float) - 1.0,
        np.nan,
    )
    return out
