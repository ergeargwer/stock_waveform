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
