import pandas as pd


def describe(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if cols:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            return f"错误: 以下列不存在: {', '.join(missing)}"
        non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            return f"错误: 以下列不是数值类型，无法统计: {', '.join(non_numeric)}"
        target = df[cols]
    else:
        target = df.select_dtypes(include="number")
    if target.empty:
        return "没有可统计的数值列。"
    if target.dropna(how="all").empty:
        return "数值列全部为空，无法统计。"
    stats = target.describe().round(3)
    return f"统计信息:\n{stats.to_string()}"


def value_counts(df: pd.DataFrame, col: str) -> str:
    if col not in df.columns:
        return f"错误: 数据中不存在列 '{col}'"
    counts = df[col].value_counts()
    total = counts.sum()
    lines = [f"列 '{col}' 的频次分布 (共 {total} 条):"]
    for val, cnt in counts.items():
        pct = cnt / total * 100
        lines.append(f"  {val}: {cnt} ({pct:.1f}%)")
    return "\n".join(lines)


def groupby_agg(
    df: pd.DataFrame, group_col: str, agg_col: str, func: str
) -> str:
    if group_col not in df.columns:
        return f"错误: 分组列 '{group_col}' 不存在"
    if agg_col not in df.columns:
        return f"错误: 聚合列 '{agg_col}' 不存在"
    try:
        result = df.groupby(group_col)[agg_col].agg(func).round(3)
        return f"按 '{group_col}' 分组, 对 '{agg_col}' 执行 '{func}' 聚合:\n{result.to_string()}"
    except Exception as e:
        return f"聚合失败: {e}"


def correlation(df: pd.DataFrame, method: str = "pearson") -> str:
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return "至少需要 2 个数值列才能计算相关性。"
    if method not in ("pearson", "spearman"):
        return f"不支持的方法 '{method}'，请使用 pearson 或 spearman。"
    corr = numeric.corr(method=method).round(3)
    return f"{method} 相关性矩阵:\n{corr.to_string()}"


def filter_data(df: pd.DataFrame, condition: str) -> str:
    if not condition or not condition.strip():
        return "错误: 过滤条件不能为空。示例: 'age > 60'、'sex == \"female\"'"
    try:
        result = df.query(condition)
        return f"条件 '{condition}' 过滤结果: {len(result)} 行\n{result.head(10).to_string(index=False)}"
    except KeyError as e:
        return f"过滤失败: 条件中引用了不存在的列名 {e}。可用的列有: {', '.join(df.columns)}"
    except Exception as e:
        return f"过滤失败: {e}。条件示例: 'age > 60'、'sex == \"female\"'"


def sort_data(df: pd.DataFrame, col: str, asc: bool = True) -> str:
    if col not in df.columns:
        return f"错误: 列 '{col}' 不存在"
    result = df.sort_values(by=col, ascending=asc)
    return f"按 '{col}' {'升序' if asc else '降序'} 排列:\n{result.head(10).to_string(index=False)}"
