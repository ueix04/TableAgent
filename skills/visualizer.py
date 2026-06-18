import io
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image

# 中文字体配置
for font_name in ["SimHei", "Microsoft YaHei"]:
    try:
        matplotlib.font_manager.findfont(font_name, fallback_to_default=False)
        matplotlib.rcParams["font.sans-serif"] = [font_name, "DejaVu Sans"]
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False

warnings.filterwarnings("ignore", category=UserWarning, module="PIL")


def _fig_to_pil(fig: plt.Figure) -> Image.Image:
    """将 matplotlib 图形转换为 PIL Image。"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


def histogram(df: pd.DataFrame, col: str, bins: int = 30) -> Image.Image:
    if col not in df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"列 '{col}' 不存在", ha="center", va="center", fontsize=14)
        ax.set_title("错误")
        return _fig_to_pil(fig)
    if not pd.api.types.is_numeric_dtype(df[col]):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"'{col}' 不是数值列，无法绘制直方图", ha="center", va="center", fontsize=12)
        ax.set_title("错误")
        return _fig_to_pil(fig)
    data = df[col].dropna()
    if len(data) == 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"列 '{col}' 没有有效数据", ha="center", va="center", fontsize=14)
        ax.set_title("错误")
        return _fig_to_pil(fig)
    bins = max(2, bins)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(data, bins=bins, edgecolor="white", color="#3498db", alpha=0.7)
    ax.set_xlabel(col)
    ax.set_ylabel("频数")
    ax.set_title(f"{col} 分布直方图")
    return _fig_to_pil(fig)


def _error_fig(text: str) -> Image.Image:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12)
    ax.set_title("错误")
    return _fig_to_pil(fig)


def bar_chart(df: pd.DataFrame, x: str, y: str) -> Image.Image:
    if x not in df.columns:
        return _error_fig(f"列 '{x}' 不存在")
    if y not in df.columns:
        return _error_fig(f"列 '{y}' 不存在")
    if not pd.api.types.is_numeric_dtype(df[y]):
        return _error_fig(f"'{y}' 不是数值列，无法绘制柱状图")
    data = df.groupby(x)[y].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(data[x].astype(str), data[y], color="#00b894", edgecolor="white")
    ax.set_xlabel(x)
    ax.set_ylabel(f"平均 {y}")
    ax.set_title(f"{y} 按 {x} 的平均值")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return _fig_to_pil(fig)


def box_plot(
    df: pd.DataFrame, col: str, by: str | None = None
) -> Image.Image:
    if col not in df.columns:
        return _error_fig(f"列 '{col}' 不存在")
    if not pd.api.types.is_numeric_dtype(df[col]):
        return _error_fig(f"'{col}' 不是数值列，无法绘制箱线图")
    if by and by not in df.columns:
        return _error_fig(f"分组列 '{by}' 不存在")
    fig, ax = plt.subplots(figsize=(8, 5))
    if by and by in df.columns:
        sns.boxplot(data=df, x=by, y=col, hue=by, palette="Set2", legend=False, ax=ax)
        ax.set_title(f"{col} 按 {by} 的箱线图")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    else:
        valid = df[col].dropna()
        if len(valid) == 0:
            plt.close(fig)
            return _error_fig(f"列 '{col}' 没有有效数据")
        ax.boxplot(
            valid,
            patch_artist=True,
            boxprops=dict(facecolor="#3498db", alpha=0.7),
        )
        ax.set_title(f"{col} 箱线图")
        ax.set_xticks([])
    ax.set_ylabel(col)
    return _fig_to_pil(fig)


def heatmap(
    df: pd.DataFrame, method: str = "pearson"
) -> Image.Image:
    if method not in ("pearson", "spearman"):
        return _error_fig(f"不支持的方法 '{method}'，请使用 pearson 或 spearman")
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return _error_fig("至少需要 2 个数值列才能计算相关性")
    if numeric.dropna(how="all").empty:
        return _error_fig("没有足够的有效数据计算相关性")
    corr = numeric.corr(method=method)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(f"{method} 相关性热力图")
    fig.tight_layout()
    return _fig_to_pil(fig)


def scatter(
    df: pd.DataFrame, x: str, y: str, hue: str | None = None
) -> Image.Image:
    if x not in df.columns:
        return _error_fig(f"列 '{x}' 不存在")
    if y not in df.columns:
        return _error_fig(f"列 '{y}' 不存在")
    if not pd.api.types.is_numeric_dtype(df[x]):
        return _error_fig(f"'{x}' 不是数值列，无法绘制散点图")
    if not pd.api.types.is_numeric_dtype(df[y]):
        return _error_fig(f"'{y}' 不是数值列，无法绘制散点图")
    if hue and hue not in df.columns:
        return _error_fig(f"颜色分组列 '{hue}' 不存在")
    fig, ax = plt.subplots(figsize=(8, 6))
    if hue and hue in df.columns:
        for label, group in df.groupby(hue):
            ax.scatter(
                group[x],
                group[y],
                label=label,
                alpha=0.6,
                edgecolors="white",
                linewidth=0.5,
            )
        ax.legend(title=hue)
    else:
        ax.scatter(
            df[x],
            df[y],
            alpha=0.6,
            edgecolors="white",
            linewidth=0.5,
            color="#3498db",
        )
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"{x} vs {y} 散点图")
    return _fig_to_pil(fig)


def pairplot(df: pd.DataFrame, cols: list[str]) -> Image.Image:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return _error_fig(f"以下列不存在: {', '.join(missing)}")
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) < 2:
        return _error_fig("至少需要 2 个数值列才能绘制配对图")
    data = df[numeric_cols].dropna()
    if len(data) == 0:
        return _error_fig("所选列没有有效数据")
    if "survived" in df.columns and "survived" not in numeric_cols:
        hue = "survived"
        palette = {0: "#ff6b6b", 1: "#51cf66"}
        plot_data = df[numeric_cols + ["survived"]].dropna()
    else:
        hue = None
        palette = None
        plot_data = data
    g = sns.pairplot(plot_data, hue=hue, palette=palette, diag_kind="hist")
    g.fig.suptitle("配对图矩阵", y=1.02)
    pil_img = _fig_to_pil(g.fig)
    plt.close("all")
    return pil_img
