"""單檔股票 3D 視覺化：波形立體、價量 KD、報酬相位軌跡。"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from waveform import zscore_normalize

# 與 waveform.py 一致的方向色
_DIR_COLOR = {
    1: "#26a69a",
    -1: "#ef5350",
    0: "#8892a4",
}

_LAYOUT_3D = dict(
    paper_bgcolor="#1e2433",
    plot_bgcolor="#0e1117",
    font=dict(color="#e0e6f0"),
    margin=dict(l=0, r=0, t=50, b=0),
    height=560,
    scene=dict(
        bgcolor="#0e1117",
        xaxis=dict(
            backgroundcolor="#0e1117",
            gridcolor="#2d3548",
            zerolinecolor="#2d3548",
            color="#e0e6f0",
        ),
        yaxis=dict(
            backgroundcolor="#0e1117",
            gridcolor="#2d3548",
            zerolinecolor="#2d3548",
            color="#e0e6f0",
        ),
        zaxis=dict(
            backgroundcolor="#0e1117",
            gridcolor="#2d3548",
            zerolinecolor="#2d3548",
            color="#e0e6f0",
        ),
    ),
)

# KD 建議最低交易日數（n=9 後尚需若干日穩定）
KD_MIN_ROWS = 14

FigureResult = Tuple[Optional[go.Figure], Optional[str]]


def _direction_colors(directions) -> list[str]:
    return [_DIR_COLOR.get(int(d), "#8892a4") for d in directions]


def _base_scene_layout(title: str, x_title: str, y_title: str, z_title: str) -> dict:
    layout = {
        **_LAYOUT_3D,
        "title": title,
        "scene": {
            **_LAYOUT_3D["scene"],
            "xaxis": {**_LAYOUT_3D["scene"]["xaxis"], "title": x_title},
            "yaxis": {**_LAYOUT_3D["scene"]["yaxis"], "title": y_title},
            "zaxis": {**_LAYOUT_3D["scene"]["zaxis"], "title": z_title},
        },
    }
    return layout


def plot_waveform_3d(df: pd.DataFrame, ticker: str = "") -> FigureResult:
    """
    波形立體圖：X=交易日序, Y=收盤價 Z-Score, Z=成交量 Z-Score。
    成功回傳 (fig, None)；失敗回傳 (None, 中文錯誤訊息)。
    """
    if df is None or df.empty:
        return None, "無法繪製 3D 波形立體圖：資料為空。"

    required = {"close", "Trading_Volume", "direction", "date"}
    missing = required - set(df.columns)
    if missing:
        return None, f"無法繪製 3D 波形立體圖：缺少欄位 {sorted(missing)}。"

    n = len(df)
    if n < 2:
        return None, "無法繪製 3D 波形立體圖：至少需要 2 筆交易日資料。"

    x_vals = np.arange(n)
    z_close = zscore_normalize(df["close"].to_numpy(dtype=float))
    z_vol = zscore_normalize(df["Trading_Volume"].to_numpy(dtype=float))
    colors = _direction_colors(df["direction"].to_numpy())
    dates = df["date"].dt.strftime("%Y-%m-%d")
    close_vals = df["close"].to_numpy(dtype=float)
    vol_vals = df["Trading_Volume"].to_numpy(dtype=float)
    pct = (
        df["change_pct"].to_numpy(dtype=float)
        if "change_pct" in df.columns
        else np.full(n, np.nan)
    )

    hover = [
        (
            f"日期: {dates.iloc[i]}<br>"
            f"交易日序: {i}<br>"
            f"收盤價: {close_vals[i]:.2f}<br>"
            f"收盤 Z-Score: {z_close[i]:.3f}<br>"
            f"成交量: {vol_vals[i]:,.0f}<br>"
            f"成交量 Z-Score: {z_vol[i]:.3f}<br>"
            f"日漲跌: {pct[i]:.2f}%"
        )
        for i in range(n)
    ]

    # 連線用中性色；端點依漲跌著色（scatter3d 線段不支援逐點多色）
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x_vals,
                y=z_close,
                z=z_vol,
                mode="lines+markers",
                line=dict(color="#4e9af1", width=3),
                marker=dict(size=4, color=colors, line=dict(width=0)),
                text=hover,
                hoverinfo="text",
                showlegend=False,
            )
        ]
    )
    title = f"{ticker} 波形立體圖（最近 {n} 個交易日）" if ticker else f"波形立體圖（最近 {n} 個交易日）"
    fig.update_layout(
        **_base_scene_layout(
            title=title,
            x_title="交易日序",
            y_title="收盤價 Z-Score",
            z_title="成交量 Z-Score",
        )
    )
    return fig, None


def plot_kd_surface_3d(df: pd.DataFrame, ticker: str = "") -> FigureResult:
    """
    價量指標曲面：X=交易日序, Y=收盤價 Z-Score, Z=K 值（需已含 K 欄位）。
    資料筆數 < 14 時回傳錯誤，不靜默填補。
    """
    if df is None or df.empty:
        return None, "無法繪製 3D 價量指標曲面：資料為空。"

    n = len(df)
    if n < KD_MIN_ROWS:
        return (
            None,
            f"觀察交易日數不足，無法計算穩定 KD 值。"
            f"目前資料 {n} 筆，至少需要 {KD_MIN_ROWS} 個交易日"
            f"（KD 使用 9 日 RSV 與 3 日平滑）。請提高側欄「觀察交易日數」後重新產生。",
        )

    if "K" not in df.columns:
        return None, "無法繪製 3D 價量指標曲面：資料尚未計算 K 值，請先執行 calculate_kd。"

    required = {"close", "date", "K"}
    missing = required - set(df.columns)
    if missing:
        return None, f"無法繪製 3D 價量指標曲面：缺少欄位 {sorted(missing)}。"

    valid = df["K"].notna()
    if valid.sum() < 2:
        return (
            None,
            "無法繪製 3D 價量指標曲面：有效 K 值不足 2 筆，"
            "請確認高低價欄位完整且觀察天數足夠。",
        )

    plot_df = df.loc[valid].reset_index(drop=True)
    # 使用原始序號對齊交易日序（非重編後 index）
    x_vals = np.flatnonzero(valid.to_numpy())
    z_close = zscore_normalize(df["close"].to_numpy(dtype=float))
    y_vals = z_close[valid.to_numpy()]
    k_vals = plot_df["K"].to_numpy(dtype=float)
    dates = plot_df["date"].dt.strftime("%Y-%m-%d")
    close_vals = plot_df["close"].to_numpy(dtype=float)
    d_vals = (
        plot_df["D"].to_numpy(dtype=float)
        if "D" in plot_df.columns
        else np.full(len(plot_df), np.nan)
    )

    hover = [
        (
            f"日期: {dates.iloc[i]}<br>"
            f"交易日序: {x_vals[i]}<br>"
            f"收盤價: {close_vals[i]:.2f}<br>"
            f"收盤 Z-Score: {y_vals[i]:.3f}<br>"
            f"K 值: {k_vals[i]:.2f}<br>"
            f"D 值: {d_vals[i]:.2f}"
        )
        for i in range(len(plot_df))
    ]

    # K 值 0-100 colorscale：低（超賣）偏綠、中性灰藍、高（超買）偏紅
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x_vals,
                y=y_vals,
                z=k_vals,
                mode="lines+markers",
                line=dict(color="#8892a4", width=3),
                marker=dict(
                    size=5,
                    color=k_vals,
                    colorscale=[
                        [0.0, "#26a69a"],
                        [0.2, "#26a69a"],
                        [0.2, "#8892a4"],
                        [0.8, "#8892a4"],
                        [0.8, "#ef5350"],
                        [1.0, "#ef5350"],
                    ],
                    cmin=0,
                    cmax=100,
                    colorbar=dict(
                        title=dict(text="K", font=dict(color="#e0e6f0"), side="right"),
                        tickfont=dict(color="#e0e6f0"),
                        bgcolor="#1e2433",
                    ),
                    line=dict(width=0),
                ),
                text=hover,
                hoverinfo="text",
                showlegend=False,
            )
        ]
    )
    title = (
        f"{ticker} 價量指標曲面 KD(9,3,3)（最近 {n} 個交易日）"
        if ticker
        else f"價量指標曲面 KD(9,3,3)（最近 {n} 個交易日）"
    )
    fig.update_layout(
        **_base_scene_layout(
            title=title,
            x_title="交易日序",
            y_title="收盤價 Z-Score",
            z_title="K 值",
        )
    )
    return fig, None


def plot_return_phase_3d(df: pd.DataFrame, ticker: str = "") -> FigureResult:
    """
    報酬相位軌跡：X=今日報酬率, Y=昨日報酬率, Z=成交量變化率。
    捨棄無法計算位移的列；成功時第二個回傳值可帶中文提示。
    """
    if df is None or df.empty:
        return None, "無法繪製 3D 報酬相位軌跡：資料為空。"

    required = {
        "return_today",
        "return_yesterday",
        "volume_change_rate",
        "date",
        "close",
        "Trading_Volume",
    }
    missing = required - set(df.columns)
    if missing:
        return (
            None,
            f"無法繪製 3D 報酬相位軌跡：缺少欄位 {sorted(missing)}，"
            f"請先執行 compute_return_phase_fields。",
        )

    n_raw = len(df)
    valid = (
        df["return_today"].notna()
        & df["return_yesterday"].notna()
        & df["volume_change_rate"].notna()
    )
    dropped = int((~valid).sum())
    plot_df = df.loc[valid].reset_index(drop=True)

    if len(plot_df) < 2:
        return (
            None,
            f"無法繪製 3D 報酬相位軌跡：有效資料不足 2 筆"
            f"（原始 {n_raw} 筆，因缺少前一日基準已捨棄 {dropped} 筆）。"
            f"請增加觀察交易日數後重試。",
        )

    x = plot_df["return_today"].to_numpy(dtype=float) * 100.0
    y = plot_df["return_yesterday"].to_numpy(dtype=float) * 100.0
    z = plot_df["volume_change_rate"].to_numpy(dtype=float) * 100.0
    n = len(plot_df)
    time_idx = np.arange(n)
    dates = plot_df["date"].dt.strftime("%Y-%m-%d")
    close_vals = plot_df["close"].to_numpy(dtype=float)
    vol_vals = plot_df["Trading_Volume"].to_numpy(dtype=float)

    hover = [
        (
            f"日期: {dates.iloc[i]}<br>"
            f"時間序: {i + 1}/{n}<br>"
            f"今日報酬率: {x[i]:.2f}%<br>"
            f"昨日報酬率: {y[i]:.2f}%<br>"
            f"成交量變化率: {z[i]:.2f}%<br>"
            f"收盤價: {close_vals[i]:.2f}<br>"
            f"成交量: {vol_vals[i]:,.0f}"
        )
        for i in range(n)
    ]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines+markers",
                line=dict(color="#4e9af1", width=3),
                marker=dict(
                    size=5,
                    color=time_idx,
                    colorscale="Viridis",
                    colorbar=dict(
                        title=dict(
                            text="時間序 (淺→深)",
                            font=dict(color="#e0e6f0"),
                            side="right",
                        ),
                        tickfont=dict(color="#e0e6f0"),
                        bgcolor="#1e2433",
                    ),
                    line=dict(width=0),
                ),
                text=hover,
                hoverinfo="text",
                showlegend=False,
            )
        ]
    )
    title = (
        f"{ticker} 報酬相位軌跡（有效 {n} 點）"
        if ticker
        else f"報酬相位軌跡（有效 {n} 點）"
    )
    fig.update_layout(
        **_base_scene_layout(
            title=title,
            x_title="今日報酬率 (%)",
            y_title="昨日報酬率 (%)",
            z_title="成交量變化率 (%)",
        )
    )

    info = (
        f"已捨棄無法計算位移的資料共 {dropped} 筆"
        f"（至少需前一日收盤與成交量作為基準；通常含觀察期第一、二個交易日）。"
        f"圖上 marker 顏色由淺至深表示時間先後。"
    )
    return fig, info
