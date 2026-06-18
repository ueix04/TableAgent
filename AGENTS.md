# TableAgent — 数据分析表格智能 Agent

**目标：** AI Agent 应用方向实习作品集项目
**选题：** 人工智能课程设计 题17 — 搭载数据分析 Skill 的表格智能 Agent
**难度：** ★★ 中等 | Function Call 实战

---

## 技术栈

| 层 | 选型 | 原因 |
|---|------|------|
| LLM | 通义千问 qwen-plus API | 免费额度、中文好、Function Call 稳定 |
| Agent 机制 | **手搭 Function Call**（openai SDK） | 面试底层追问能答、完全可控 |
| 数据处理 | pandas 3.0.2 + numpy | 已安装，生态成熟 |
| 可视化 | matplotlib 3.10.x + seaborn 0.13.x | seaborn 语法简洁、美观 |
| 界面 | Gradio（gr.ChatInterface） | 3 行代码出对话 UI，演示友好 |
| 环境 | conda env `pytorch` (D:\develop_tools\anaconda3\envs\pytorch) | torch 2.6.0+cu124（GPU 可用） |

---

## 目录结构

```
TableAgent/
├── AGENTS.md              # 本文件 — 项目知识库
├── requirements.txt       # 依赖清单
├── main.py                # 入口：启动 Gradio
│
├── agent/
│   ├── __init__.py
│   ├── core.py            # Agent 主循环（hand-built Function Call）
│   ├── schema.py          # Tool Schema 定义（JSON Schema）
│   └── memory.py          # 对话历史管理
│
├── skills/
│   ├── __init__.py
│   ├── reader.py          # Skill 1: 数据读取与探查
│   ├── analyst.py         # Skill 2: 统计分析
│   └── visualizer.py      # Skill 3: 可视化绘图
│
├── ui/
│   ├── __init__.py
│   └── app.py             # Gradio 界面配置
│
├── data/
│   └── titanic.csv        # 泰坦尼克数据集
│
└── notebooks/
    └── explore.ipynb      # 数据探索和原型验证
```

---

## 架构

```
用户输入（自然语言）
     │
     ▼
┌─────────────────────────────┐
│  agent/core.py 主循环        │
│                              │
│  ① 构造 messages + tools     │
│  ② 调用 qwen-plus (chat)     │
│  ③ 解析 response:           │
│     ├─ 直接回答 → 返回用户    │
│     └─ tool_calls → 执行 Skill│
│        → 结果追加回 messages  │
│        → 回到 ② (继续循环)    │
└─────────────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│ reader │  │ analyst  │  │visualizer│
│ .py    │  │ .py      │  │ .py      │
└────────┘  └──────────┘  └──────────┘
     │              │              │
     ▼              ▼              ▼
┌─────────────────────────────────────┐
│           pandas DataFrame           │
│         (全局状态，同一份数据)        │
└─────────────────────────────────────┘
```

---

## 三大 Skill 定义

### Skill 1: DataReader（数据读取与探查）

| Function | 参数 | 返回 |
|----------|------|------|
| `load_csv(path)` | 文件路径 | 成功/失败消息 |
| `get_overview()` | 无 | 行数列数、字段列表 |
| `get_info()` | 无 | 每列类型、非空数 |
| `get_missing()` | 无 | 缺失值统计表 |
| `get_head(n)` | 行数（默认5） | 前 n 行数据 |
| `get_unique(col)` | 列名 | 唯一值及频次 |

### Skill 2: Analyst（统计分析）

| Function | 参数 | 返回 |
|----------|------|------|
| `describe(cols)` | 列名列表（可选） | 数值统计（均值、标准差等） |
| `value_counts(col)` | 列名 | 频次分布 |
| `groupby_agg(group, agg_col, func)` | 分组列、聚合列、函数 | 分组聚合结果 |
| `correlation(method)` | 方法（pearson/spearman） | 相关性矩阵 |
| `filter_data(condition)` | 条件表达式 | 过滤后行数、示例 |
| `sort_data(col, asc)` | 列名、升序/降序 | 排序结果 |

### Skill 3: Visualizer（可视化绘图）

| Function | 参数 | 返回 |
|----------|------|------|
| `histogram(col, bins)` | 列名、分箱数 | 直方图（PIL Image） |
| `bar_chart(x, y)` | x列、y列 | 柱状图 |
| `box_plot(col, by)` | 数值列、分组列 | 箱线图 |
| `heatmap(method)` | 相关方法 | 相关性热力图 |
| `scatter(x, y, hue)` | x列、y列、颜色分组 | 散点图 |
| `pairplot(cols)` | 列名列表 | 配对图矩阵 |

---

## Agent 核心逻辑（hand-built Function Call）

```python
# agent/core.py 核心循环（伪码）

def agent_loop(user_input: str, df: DataFrame) -> Generator[str | Image]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}]

    while True:
        response = openai.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=ALL_TOOL_SCHEMAS,      # 全部 Skill 定义
            tool_choice="auto"
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:           # LLM 直接回答了
            yield msg.content
            break

        for tool_call in msg.tool_calls: # 可能有多个并行调用
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            result = dispatch_skill(func_name, args, df)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
        # 继续循环，让 LLM 处理工具返回的结果
```

**要点：**
- 每个 tool_call 执行后结果送回 LLM
- LLM 可能多次调工具（链式调用）
- 图表 skill 返回图片路径而非文字，需特殊处理展示

---

## 环境配置

```bash
# 激活 pytorch 环境
conda activate pytorch

# 安装依赖
pip install openai seaborn gradio
```

**通义千问 API Key：** 配置环境变量 `DASHSCOPE_API_KEY` 或在代码中读取 `.env` 文件。

---

## 开发路线（按顺序）

| 阶段 | 内容 | 预计 |
|------|------|------|
| **P0** 环境 + 数据 | 装依赖、下载 Titanic 数据、`explore.ipynb` 探索 | ✅ 完成 |
| **P1** 三大 Skill | 实现 reader.py / analyst.py / visualizer.py，单测通过 | ✅ 完成 |
| **P2** Function Call | 实现 agent/core.py 主循环 + schema.py，端到端跑通 | ✅ 完成 |
| **P3** Gradio UI | 用 gr.ChatInterface 包装，能交互演示 | 1天 |
| **P4** 打磨 | 边界情况处理、多轮对话连贯性、预设 demo 指令 | 1天 |
| **P5** 报告 | 按课程设计模板写报告 + 答辩准备 | 2天 |

---

## 质量要求

- 每个 Skill function 有独立测试（notebook 或 pytest）
- Agent 能正确处理：单步调用、链式调用、参数错误恢复
- LLM 不直接回答数据问题 — 必须通过调用 Skill 获取数据后再回答
- UI 展示：对话记录 + 图表嵌入显示
- 至少准备 5 条预设演示指令（覆盖三大 Skill 组合场景）

---

## 关键约束

- **不**使用 LangChain AgentExecutor / AutoGen 等高阶框架
- **不**用 `as any` / `@ts-ignore` 类绕过（Python 同理：不静默 except）
- LLM 仅用于意图识别和自然语言生成 — **所有数据操作必须经过 Skill 函数**
- 图表返回 PIL Image 而非 save 到磁盘（Gradio 可直接展示）
