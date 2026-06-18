import pandas as pd


def load_csv(path: str) -> str:
    try:
        df = pd.read_csv(path)
        return f"成功加载数据: {df.shape[0]} 行 × {df.shape[1]} 列"
    except Exception as e:
        return f"加载失败: {e}"


def get_overview(df: pd.DataFrame) -> str:
    cols_info = "\n".join(
        f"  [{i+1}] {col} ({dtype})"
        for i, (col, dtype) in enumerate(zip(df.columns, df.dtypes))
    )
    return (
        f"数据集概览:\n"
        f"  行数: {df.shape[0]}\n"
        f"  列数: {df.shape[1]}\n"
        f"  列列表:\n{cols_info}"
    )


def get_info(df: pd.DataFrame) -> str:
    info_lines = ["每列信息:"]
    for col in df.columns:
        non_null = df[col].notna().sum()
        dtype = df[col].dtype
        info_lines.append(f"  {col}: {non_null} 非空值, 类型={dtype}")
    return "\n".join(info_lines)


def get_missing(df: pd.DataFrame) -> str:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) == 0:
        return "数据集中没有缺失值。"
    total = len(df)
    lines = ["缺失值统计:"]
    for col, count in missing.items():
        pct = count / total * 100
        lines.append(f"  {col}: {count} 个缺失 ({pct:.1f}%)")
    return "\n".join(lines)


def get_head(df: pd.DataFrame, n: int = 5) -> str:
    if df.empty:
        return "数据集中没有任何数据。"
    n = max(1, min(n, len(df)))
    return f"前 {n} 行数据:\n{df.head(n).to_string(index=False)}"


def get_unique(df: pd.DataFrame, col: str) -> str:
    if col not in df.columns:
        return f"错误: 数据中不存在列 '{col}'"
    counts = df[col].value_counts()
    n_unique = counts.shape[0]
    lines = [f"列 '{col}' 的唯一值: {n_unique} 个"]
    for val, cnt in counts.items():
        pct = cnt / len(df) * 100
        lines.append(f"  {val}: {cnt} 条 ({pct:.1f}%)")
    return "\n".join(lines)
