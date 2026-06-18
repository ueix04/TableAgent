# TableAgent

搭载数据分析 Skill 的表格智能 Agent。用户输入自然语言即可完成数据探索、统计分析和可视化绘图。

基于通用 LLM + Function Call + Pandas + Gradio 构建，不依赖 LangChain 等高级框架。

---

## 功能

- **数据读取与探查** — 加载 CSV、预览数据、查看字段信息、缺失值统计
- **统计分析** — 描述性统计、频次分布、分组聚合、相关性分析、条件筛选、排序
- **可视化绘图** — 直方图、柱状图、箱线图、热力图、散点图、配对图矩阵
- **链式调用** — "统计不同舱位的票价平均值并画柱状图" 等复合指令自动多步执行

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
# 在 .env 文件中设置你的 API Key：
# DASHSCOPE_API_KEY=your_api_key_here

# 4. 启动 Web UI
python main.py
# 浏览器访问 http://127.0.0.1:7860
```

## 目录结构

```
TableAgent/
├── agent/          # Agent 主循环、Tool Schema、对话管理
│   ├── core.py     # Function Call 主循环
│   ├── schema.py   # 18 个 Tool JSON Schema
│   └── memory.py   # 对话历史管理
├── skills/         # 三大 Skill
│   ├── reader.py   # DataReader — 6 个函数
│   ├── analyst.py  # Analyst — 6 个函数
│   └── visualizer.py # Visualizer — 6 个函数
├── ui/             # Gradio 界面
│   └── app.py
├── data/           # 示例数据集
├── tests/          # 42 个单元测试
├── main.py         # 入口
└── AGENTS.md       # 项目知识库
```

## 技术栈

| 层 | 选型 |
|---|------|
| LLM | 通用 LLM (Function Call) |
| Agent 机制 | 手搭 Function Call（OpenAI SDK） |
| 数据处理 | pandas + numpy |
| 可视化 | matplotlib + seaborn |
| 界面 | Gradio |

## 预设指令

启动后在左侧「快捷指令」面板一键触发：

- 数据概览 / 前 5 行 / 年龄分布
- 分组+柱状图 / 相关性热力图 / 年龄直方图
- 分组统计 / 条件筛选 / 唯一值分布

## 运行测试

```bash
python -m pytest tests/ -v
```
