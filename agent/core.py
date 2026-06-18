import json
import logging
import os
from typing import Generator

import pandas as pd
from openai import OpenAI
from openai import APIError as OpenAIAPIError
from PIL.Image import Image

from agent.memory import ConversationMemory
from agent.schema import SKILL_SCHEMAS, VISUAL_FUNCTIONS
from skills.reader import (
    load_csv,
    get_overview,
    get_info,
    get_missing,
    get_head,
    get_unique,
)
from skills.analyst import (
    describe,
    value_counts,
    groupby_agg,
    correlation,
    filter_data,
    sort_data,
)
from skills.visualizer import (
    histogram,
    bar_chart,
    box_plot,
    heatmap,
    scatter,
    pairplot,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 TableAgent，一个搭载了数据分析工具箱的 AI 助手。

## 核心规则
1. 用户问任何数据相关的问题，你必须**先调用 Skill 函数**获取数据，再基于数据回答。禁止直接编造数据。
2. 如果用户没有指定数据集，默认使用已加载的 Titanic 数据集。
3. 你不确定数据结构时，先调用 get_overview 或 get_info 了解后再回答。
4. 你可以链式调用多个函数（如先 groupby_agg 统计，再用结果画 bar_chart）。
5. 如果函数返回错误（如列名不存在），根据错误信息修正参数后重试，不要向用户展示原始错误。
6. 每个问题应独立分析——不要假设上一轮的列名在本轮仍然有效。

## 工具分类
- DataReader（数据探查）：load_csv, get_overview, get_info, get_missing, get_head, get_unique
- Analyst（统计分析）：describe, value_counts, groupby_agg, correlation, filter_data, sort_data
- Visualizer（可视化绘图）：histogram, bar_chart, box_plot, heatmap, scatter, pairplot

可视化函数会直接返回图片，用户可以看到图表。"""

SKILL_DISPATCH = {
    "load_csv": load_csv,
    "get_overview": get_overview,
    "get_info": get_info,
    "get_missing": get_missing,
    "get_head": get_head,
    "get_unique": get_unique,
    "describe": describe,
    "value_counts": value_counts,
    "groupby_agg": groupby_agg,
    "correlation": correlation,
    "filter_data": filter_data,
    "sort_data": sort_data,
    "histogram": histogram,
    "bar_chart": bar_chart,
    "box_plot": box_plot,
    "heatmap": heatmap,
    "scatter": scatter,
    "pairplot": pairplot,
}

_MODEL = "qwen-plus"
_MAX_TOKENS = 8192
_MAX_ITERATIONS = 15


def _load_api_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        return api_key
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DASHSCOPE_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise ValueError("DASHSCOPE_API_KEY 未设置，请在 .env 中配置")


def _init_client() -> OpenAI:
    return OpenAI(
        api_key=_load_api_key(),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def dispatch_skill(func_name: str, args: dict, df: pd.DataFrame):
    func = SKILL_DISPATCH.get(func_name)
    if func is None:
        return f"错误: 未知函数 '{func_name}'"
    try:
        return func(df, **args)
    except Exception as e:
        logger.warning("函数 %s 执行失败: %s", func_name, e)
        return f"函数 '{func_name}' 执行失败: {e}"


def agent_loop(
    user_input: str,
    df: pd.DataFrame,
    memory: ConversationMemory,
) -> Generator[str | Image, None, None]:
    client = _init_client()
    mem = memory
    mem.add_user(user_input)

    for iteration in range(_MAX_ITERATIONS):
        try:
            response = client.chat.completions.create(
                model=_MODEL,
                messages=mem.messages,
                tools=SKILL_SCHEMAS,
                tool_choice="auto",
                max_tokens=_MAX_TOKENS,
            )
        except OpenAIAPIError as e:
            yield f"⚠️ API 调用失败: {e}"
            return

        msg = response.choices[0].message

        if not msg.tool_calls:
            content = msg.content or ""
            mem.add_assistant(content)
            if content:
                yield content
            return

        mem.add_assistant(msg.content or "")

        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = dispatch_skill(func_name, args, df)

            if func_name in VISUAL_FUNCTIONS:
                mem.add_tool("[图片已生成]", tool_call.id)
                yield result
            else:
                result_str = result if isinstance(result, str) else str(result)
                mem.add_tool(result_str, tool_call.id)

        if len(mem.messages) > 100:
            mem.trim()

    yield "⚠️ 分析步骤过多，已自动终止。请简化你的问题，或分步提问。"
