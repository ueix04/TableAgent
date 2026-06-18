"""Tool Schema 定义 — 18 个 Function 的 OpenAI JSON Schema。"""

SKILL_SCHEMAS = [
    # ===== Skill 1: DataReader =====
    {
        "type": "function",
        "function": {
            "name": "load_csv",
            "description": "加载 CSV 文件到系统。首次使用或切换数据集时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "CSV 文件路径"}
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_overview",
            "description": "获取数据集总体概览：行数、列数、每列名称和类型。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_info",
            "description": "获取每列的非空值数量和数据类型。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_missing",
            "description": "获取数据集中所有列的缺失值统计。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_head",
            "description": "查看数据集的前 N 行数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "行数（默认 5）",
                        "default": 5,
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unique",
            "description": "查看指定列的唯一值及每个值的出现频次。",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {"type": "string", "description": "列名"}
                },
                "required": ["col"],
                "additionalProperties": False,
            },
        },
    },
    # ===== Skill 2: Analyst =====
    {
        "type": "function",
        "function": {
            "name": "describe",
            "description": "对数值列进行统计描述（均值、标准差、四分位数等）。不传 cols 则统计所有数值列。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要统计的列名列表（可选，不传则统计所有数值列）",
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "value_counts",
            "description": "统计指定列的频次分布。",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {"type": "string", "description": "列名"}
                },
                "required": ["col"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "groupby_agg",
            "description": "按分组列聚合统计。例如：按 pclass 分组计算 fare 的平均值。",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_col": {"type": "string", "description": "分组列名"},
                    "agg_col": {"type": "string", "description": "要聚合的列名"},
                    "func": {
                        "type": "string",
                        "description": "聚合函数：mean、sum、count、min、max、std",
                        "enum": ["mean", "sum", "count", "min", "max", "std"],
                    },
                },
                "required": ["group_col", "agg_col", "func"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "correlation",
            "description": "计算数值列之间的相关性矩阵。",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "相关方法",
                        "enum": ["pearson", "spearman"],
                        "default": "pearson",
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_data",
            "description": "按条件过滤数据，返回匹配的行。使用 pandas 查询语法，例如：'age > 60'、'sex == \"female\"'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "过滤条件表达式，如 'age > 60'",
                    }
                },
                "required": ["condition"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sort_data",
            "description": "按指定列排序数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {"type": "string", "description": "排序列名"},
                    "asc": {
                        "type": "boolean",
                        "description": "是否升序（默认 True，False 为降序）",
                        "default": True,
                    },
                },
                "required": ["col"],
                "additionalProperties": False,
            },
        },
    },
    # ===== Skill 3: Visualizer =====
    {
        "type": "function",
        "function": {
            "name": "histogram",
            "description": "绘制指定列的直方图。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {"type": "string", "description": "列名"},
                    "bins": {
                        "type": "integer",
                        "description": "分箱数（默认 30）",
                        "default": 30,
                    },
                },
                "required": ["col"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bar_chart",
            "description": "绘制柱状图，显示 y 列按 x 列分组的平均值。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "string", "description": "X 轴列名（分类列）"},
                    "y": {"type": "string", "description": "Y 轴列名（数值列）"},
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "box_plot",
            "description": "绘制箱线图。可选按分组列拆分。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {"type": "string", "description": "数值列名"},
                    "by": {
                        "type": "string",
                        "description": "分组列名（可选）",
                    },
                },
                "required": ["col"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "heatmap",
            "description": "绘制相关性热力图。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "相关方法",
                        "enum": ["pearson", "spearman"],
                        "default": "pearson",
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scatter",
            "description": "绘制散点图。可指定颜色分组。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "string", "description": "X 轴列名"},
                    "y": {"type": "string", "description": "Y 轴列名"},
                    "hue": {
                        "type": "string",
                        "description": "颜色分组列名（可选）",
                    },
                },
                "required": ["x", "y"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pairplot",
            "description": "绘制多列间的配对图矩阵。返回图表图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要分析的列名列表",
                    }
                },
                "required": ["cols"],
                "additionalProperties": False,
            },
        },
    },
]

# 视觉类 Skill 函数名集合 — 它们的返回结果是 PIL Image，需要特殊处理
VISUAL_FUNCTIONS = {
    "histogram", "bar_chart", "box_plot", "heatmap", "scatter", "pairplot",
}
