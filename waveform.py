import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 方向 → 顏色
_DIR_COLOR = {
    1: "#26a69a",
    -1: "#ef5350",
    0: "#8892a4",
}

# 成交量線寬離散分箱（減少 trace 數量：最多 3 色 × 3 寬 = 9 條 stem）
_WIDTH_BINS = (1.5, 3.5, 5.5)


def zscore_normalize(series) -> np.ndarray:
    series = np.asarray(series, dtype=float)
    std = np.std(series)
    if std == 0 or np.isnan(std):
        return np.zeros_like(series, dtype=float)
    return (series - np.mean(series)) / std


def get_width_from_zscore(z: float) -> float:
    if np.isnan(z):
        return 3.0
    if z <= -1:
        return 1.0
    if z >= 1:
        return 6.0
    if z < 0:
        return 3.0 + 2.0 * z
    return 3.0 + 3.0 * z


def _width_bin(z: float) -> float:
    w = get_width_from_zscore(z)
    if w <= 2.0:
        return _WIDTH_BINS[0]
    if w <= 4.0:
        return _WIDTH_BINS[1]
    return _WIDTH_BINS[2]


def build_stock_figure(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    單一 Figure：上方波形 + 下方成交量（shared x-axis）。
    垂直 stem 依 (方向顏色, 線寬分箱) 合併 trace，避免 O(N) traces。
    """
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.06,
        subplot_titles=(None, None),
    )

    if df.empty:
        return fig

    n = len(df)
    x_vals = np.arange(n)

    close_vals = df["close"].to_numpy(dtype=float)
    vol_vals = df["Trading_Volume"].to_numpy(dtype=float)
    directions = df["direction"].to_numpy()
    change_pcts = df["change_pct"].to_numpy(dtype=float)

    z_close = zscore_normalize(close_vals)
    z_vol = zscore_normalize(vol_vals)

    dates_str = df["date"].dt.strftime("%m/%d")
    dates_full = df["date"].dt.strftime("%Y-%m-%d")
    tickvals = list(np.arange(0, n, max(1, n // 8)))
    ticktext = [dates_str.iloc[i] for i in tickvals]

    # --- stems：依顏色 × 線寬分箱合併，None 斷開各日線段 ---
    for direction, color in _DIR_COLOR.items():
        for wb in _WIDTH_BINS:
            xs: list = []
            ys: list = []
            for i in range(n):
                if int(directions[i]) != direction:
                    continue
                if _width_bin(float(z_vol[i])) != wb:
                    continue
                xs.extend([x_vals[i], x_vals[i], None])
                ys.extend([0.0, float(z_close[i]), None])
            if not xs:
                continue
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="lines",
                    line=dict(color=color, width=wb),
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

    # --- 端點 markers + hover（單一 trace）---
    marker_colors = []
    marker_sizes = []
    marker_line_colors = []
    marker_line_widths = []
    hover_texts = []
    for i in range(n):
        d = int(directions[i])
        color = _DIR_COLOR.get(d, "#8892a4")
        if d == 0:
            marker_colors.append("#0e1117")
            marker_sizes.append(3)
            marker_line_colors.append("#8892a4")
            marker_line_widths.append(1)
        else:
            marker_colors.append(color)
            marker_sizes.append(4)
            marker_line_colors.append(color)
            marker_line_widths.append(0)
        hover_texts.append(
            f"日期: {dates_full.iloc[i]}<br>"
            f"收盤價: {close_vals[i]:.2f}<br>"
            f"成交量: {vol_vals[i]:,.0f}<br>"
            f"日漲跌: {change_pcts[i]:.2f}%"
        )

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=z_close,
            mode="markers",
            marker=dict(
                size=marker_sizes,
                color=marker_colors,
                line=dict(color=marker_line_colors, width=marker_line_widths),
            ),
            hoverinfo="text",
            text=hover_texts,
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # --- 平滑連線 ---
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=z_close,
            mode="lines",
            line=dict(color="#4e9af1", width=1.5, shape="spline"),
            opacity=0.6,
            hoverinfo="skip",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # --- 成交量 bar ---
    bar_colors = [_DIR_COLOR.get(int(d), "#8892a4") for d in directions]
    fig.add_trace(
        go.Bar(
            x=x_vals,
            y=vol_vals,
            marker_color=bar_colors,
            hovertemplate="成交量: %{y:,.0f}<extra></extra>",
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#2d3548",
        line_width=1,
        row=1,
        col=1,
    )

    fig.update_layout(
        title=f"{ticker} 股價波形視覺化（最近 {n} 個交易日）",
        paper_bgcolor="#1e2433",
        plot_bgcolor="#0e1117",
        font=dict(color="#e0e6f0"),
        height=680,
        showlegend=False,
        margin=dict(l=60, r=30, t=60, b=40),
        barmode="relative",
    )

    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        gridcolor="#2d3548",
        row=1,
        col=1,
    )
    fig.update_xaxes(
        title_text="交易日",
        tickvals=tickvals,
        ticktext=ticktext,
        gridcolor="#2d3548",
        row=2,
        col=1,
    )
    fig.update_yaxes(
        title_text="Z-Score（標準化收盤價）",
        gridcolor="#2d3548",
        zeroline=True,
        zerolinecolor="#4e9af1",
        zerolinewidth=1,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="成交量",
        gridcolor="#2d3548",
        row=2,
        col=1,
    )

    return fig


# 向後相容：若外部仍分別呼叫
def build_waveform_figure(df: pd.DataFrame, ticker: str, mode: str = "single") -> go.Figure:
    """僅波形（無成交量子圖）；內部仍使用合併 stem traces。"""
    fig = build_stock_figure(df, ticker)
    # 隱藏第二列：改為只回傳完整圖較單純，此處仍回傳完整 subplot
    _ = mode
    return fig


def build_volume_bar_figure(df: pd.DataFrame, ticker: str) -> go.Figure:
    """保留相容；建議改用 build_stock_figure。"""
    _ = ticker
    fig = go.Figure()
    if df.empty:
        return fig
    n = len(df)
    x_vals = np.arange(n)
    colors = [_DIR_COLOR.get(int(d), "#8892a4") for d in df["direction"]]
    dates_str = df["date"].dt.strftime("%m/%d")
    tickvals = list(np.arange(0, n, max(1, n // 8)))
    ticktext = [dates_str.iloc[i] for i in tickvals]
    fig.add_trace(
        go.Bar(x=x_vals, y=df["Trading_Volume"], marker_color=colors, showlegend=False)
    )
    fig.update_layout(
        paper_bgcolor="#1e2433",
        plot_bgcolor="#0e1117",
        font=dict(color="#e0e6f0"),
        xaxis=dict(tickvals=tickvals, ticktext=ticktext, gridcolor="#2d3548"),
        yaxis=dict(title="成交量", gridcolor="#2d3548"),
        height=180,
        margin=dict(l=60, r=30, t=10, b=20),
    )
    return fig
