import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.core import agent_loop, SYSTEM_PROMPT
from agent.memory import ConversationMemory

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "titanic.csv"
SESSIONS_DIR = BASE_DIR / "sessions"
CHARTS_DIR = SESSIONS_DIR / "charts"
SESSIONS_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)

if not DATA_PATH.exists():
    raise FileNotFoundError(f"数据文件不存在: {DATA_PATH}")

# ── Dataset state ──

_loaded_dfs: dict[str, pd.DataFrame] = {}
current_df = pd.read_csv(DATA_PATH)
current_dataset_name = "Titanic"
_loaded_dfs["Titanic"] = current_df


def build_header_html(df: pd.DataFrame) -> str:
    return f"""<div class="app-header">
  <div>
    <h1>TableAgent</h1>
    <div class="sub">搭载数据分析 Skill 的智能 Agent，输入自然语言即可完成数据分析</div>
  </div>
  <div class="header-badges">
    <span class="header-badge">{df.shape[0]:,} 行</span>
    <span class="header-badge">{df.shape[1]} 列</span>
    <span class="header-badge">qwen-plus</span>
    <button class="theme-btn" onclick="toggleTheme()" title="切换暗色 / 亮色模式" aria-label="切换主题"></button>
  </div>
</div>"""


def build_field_grid_html(df: pd.DataFrame) -> str:
    html = '<div class="field-grid">'
    for col, dtype in zip(df.columns, df.dtypes.astype(str)):
        html += f'<div class="f"><span class="n">{col}</span><span class="t">{dtype}</span></div>'
    return html + "</div>"


# ── Session management ──

def session_save(session_id: str, memory: ConversationMemory):
    path = SESSIONS_DIR / f"{session_id}.json"
    msgs = [m for m in memory.messages if m["role"] != "system"]
    data = {"id": session_id, "messages": msgs, "updated_at": datetime.now().isoformat()}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data["created_at"] = json.load(f).get("created_at", data["updated_at"])
    else:
        data["created_at"] = data["updated_at"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def session_load(session_id: str) -> ConversationMemory | None:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    mem = ConversationMemory(SYSTEM_PROMPT)
    for m in data.get("messages", []):
        mem._messages.append(m)
    return mem


def session_preview(session_id: str) -> str:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return "空会话"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for m in reversed(data.get("messages", [])):
        if m["role"] == "user" and m.get("content"):
            txt = str(m["content"])
            return txt[:60] + "…" if len(txt) > 60 else txt
    return "空会话"


def list_sessions() -> list[dict]:
    files = sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        preview = "空会话"
        for m in reversed(data.get("messages", [])):
            if m["role"] == "user" and m.get("content"):
                txt = str(m["content"])
                preview = txt[:60] + "…" if len(txt) > 60 else txt
                break
        dt = (data.get("updated_at") or "")[:16]
        result.append({"id": f.stem, "preview": preview, "time": dt})
    return result


def delete_session(session_id: str):
    (SESSIONS_DIR / f"{session_id}.json").unlink(missing_ok=True)
    for chart in CHARTS_DIR.glob(f"{session_id}_*.png"):
        chart.unlink(missing_ok=True)


def new_session_id() -> str:
    # 精度到秒 + 随机后缀，避免快速连续操作时撞号覆盖
    suffix = uuid.uuid4().hex[:6]
    return f"sess_{datetime.now().strftime('%m%d_%H%M%S')}_{suffix}"


def new_session():
    sid = new_session_id()
    session_save(sid, ConversationMemory(SYSTEM_PROMPT))
    return sid, []


def build_chatbot_messages(memory: ConversationMemory) -> list:
    return [
        {"role": m["role"], "content": m.get("content", "")}
        for m in memory.messages
        if m["role"] in ("user", "assistant")
    ]


# ── Core respond logic ──

def respond(message: str, history: list, session_id: str):
    global current_df
    if not session_id:
        session_id = new_session_id()
    mem = session_load(session_id) or ConversationMemory(SYSTEM_PROMPT)
    try:
        outputs = list(agent_loop(message, current_df, mem))
    except ValueError as e:
        return [*history, {"role": "assistant", "content": f"⚠️ 配置错误: {e}"}], session_id
    except Exception as e:
        return [*history, {"role": "assistant", "content": f"⚠️ 出错了: {e}"}], session_id
    for o in outputs:
        if isinstance(o, str):
            history.append({"role": "assistant", "content": o})
        else:
            name = f"{session_id}_{uuid.uuid4().hex[:8]}.png"
            o.save(str(CHARTS_DIR / name))
            history.append({"role": "assistant", "content": {"path": str(CHARTS_DIR / name)}})
    session_save(session_id, mem)
    return history, session_id


# ── CSS ──
# 设计原则：
# 1. 单一 token 系统：CSS 变量 + 桥接 Gradio 内部变量，亮暗统一
# 2. 不用 100vh 强制（Gradio 6.18 自身有布局），而是给 Chatbot 一个合理高度让输入框可见
# 3. 响应式字体 clamp() 适配 2K + 放大倍率
# 4. sidebar 内容独立滚动

CUSTOM_CSS = """
:root {
  /* 品牌与强调色 */
  --accent: #0284c7; --accent-light: #7dd3fc; --accent-dark: #0369a1;
  --accent-gradient: linear-gradient(135deg, #0284c7 0%, #0e7490 100%);

  /* 中性色阶 */
  --bg: #f8fafc; --surface: #ffffff; --surface-hover: #f1f5f9;
  --border: #e2e8f0; --text: #0f172a; --text-secondary: #475569; --text-muted: #94a3b8;

  /* 对话语泡 */
  --chat-user-bg: #0284c7; --chat-user-text: #ffffff;
  --chat-bot-bg: #ffffff; --chat-bot-border: #e2e8f0;

  /* 形状与阴影 */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px; --radius-full: 9999px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);

  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', 'PingFang SC', sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;

  /* === 桥接 Gradio 内部 token === */
  --background-fill-primary: var(--bg);
  --background-fill-secondary: var(--surface);
  --block-background-fill: var(--surface);
  --block-border-color: var(--border);
  --block-label-background-fill: var(--surface);
  --block-label-text-color: var(--text-secondary);
  --block-title-text-color: var(--text);
  --input-background-fill: var(--surface);
  --input-border-color: var(--border);
  --input-border-color-focus: var(--accent);
  --input-text-color: var(--text);
  --input-placeholder-color: var(--text-muted);
  --input-shadow: none;
  --button-primary-background-fill: var(--accent);
  --button-primary-background-fill-hover: var(--accent-dark);
  --button-primary-text-color: #ffffff;
  --button-secondary-background-fill: var(--surface);
  --button-secondary-background-fill-hover: var(--surface-hover);
  --button-secondary-text-color: var(--text);
  --body-text-color: var(--text);
  --body-text-color-subdued: var(--text-secondary);
  --border-color-primary: var(--border);
  --color-accent: var(--accent);
  --color-accent-soft: rgba(2,132,199,0.12);
  --shadow-drop-lg: var(--shadow-md);
}

[data-theme="dark"] {
  /* 强调色保留 sky 蓝，仅中性色变深 */
  --accent: #38bdf8; --accent-light: #7dd3fc; --accent-dark: #0ea5e9;
  --accent-gradient: linear-gradient(135deg, #0c4a6e 0%, #082f49 100%);

  --bg: #0b1220; --surface: #131c2e; --surface-hover: #1c2740;
  --border: #243049; --text: #e8eef7; --text-secondary: #aab4c5; --text-muted: #6b7689;

  --chat-user-bg: #0e7490; --chat-user-text: #f0f9ff;
  --chat-bot-bg: #131c2e; --chat-bot-border: #243049;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -2px rgba(0,0,0,0.3);

  --block-background-fill: var(--surface);
  --block-border-color: var(--border);
  --input-background-fill: var(--surface);
  --input-border-color: var(--border);
  --button-primary-background-fill: var(--accent);
  --button-primary-background-fill-hover: var(--accent-dark);
  --button-secondary-background-fill: var(--surface);
  --button-secondary-background-fill-hover: var(--surface-hover);
  --color-accent-soft: rgba(56,189,248,0.16);
}

/* === 响应式基础 === */
* { box-sizing: border-box; }
html { font-size: clamp(14px, 1.1vw + 0.6rem, 18px); }
body {
  margin: 0; background: var(--bg) !important; color: var(--text);
  font-family: var(--font-sans); -webkit-font-smoothing: antialiased;
  font-size: 1rem;
}

/* === 主布局：sidebar + chat-col 填满视口，输入框钉底 === */
.app-header { flex: 0 0 auto; }
.main-row {
  height: calc(100vh - 56px) !important;
  max-height: calc(100vh - 56px) !important;
  min-height: 0 !important;
  overflow: hidden;
}
.main-row > .form,
.main-row > div { height: 100% !important; min-height: 0 !important; }

/* sidebar 内容独立滚动，占满 main-row 高度 */
.sidebar {
  background: var(--surface); border-right: 1px solid var(--border);
  padding: 14px; overflow-y: auto; height: 100%;
}

/* 右侧聊天区：纵向 flex，Chatbot 弹性拉伸，input-row 钉底 */
.chat-col { display: flex !important; flex-direction: column !important; min-height: 0 !important; }
.chat-col > .form,
.chat-col > div { display: flex !important; flex-direction: column !important; min-height: 0 !important; flex: 1 1 auto !important; }
.chat-main { flex: 1 1 auto !important; min-height: 200px; }
.chat-main > div { flex: 1 1 auto !important; min-height: 0 !important; }
.input-row { flex: 0 0 auto !important; }

/* === Header === */
.app-header {
  background: var(--accent-gradient);
  padding: 10px 24px; display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 8px;
}
.app-header h1 {
  color: #fff !important; font-size: 1.25rem !important; font-weight: 700 !important;
  letter-spacing: -0.3px; margin: 0 !important; line-height: 1.2;
}
.app-header .sub {
  color: rgba(255,255,255,0.78); font-size: 0.8rem !important; font-weight: 400;
  letter-spacing: 0.1px; margin-top: 1px;
}
.header-badges { display: flex; gap: 6px; align-items: center; }
.header-badge {
  background: rgba(255,255,255,0.14); backdrop-filter: blur(4px);
  border-radius: var(--radius-sm); padding: 3px 10px; color: #fff;
  font-size: 0.75rem !important; font-weight: 500; border: 1px solid rgba(255,255,255,0.1);
}
.theme-btn {
  width: 28px; height: 28px; background: rgba(255,255,255,0.14);
  border: 1px solid rgba(255,255,255,0.2); border-radius: var(--radius-full);
  color: #fff; font-size: 14px; cursor: pointer; transition: background 0.2s;
  line-height: 1; display: inline-flex; align-items: center; justify-content: center;
}
.theme-btn::before { content: "\\263E"; }
[data-theme="dark"] .theme-btn::before { content: "\\2600"; }
.theme-btn:hover { background: rgba(255,255,255,0.26); }

/* === Sidebar 组件 === */
.sidebar-title {
  font-size: 0.7rem !important; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 1px;
  margin: 16px 0 8px 0;
}
.sidebar-title:first-child { margin-top: 0; }
.sidebar hr { border: none; border-top: 1px solid var(--border); margin: 12px 0; }

/* Dataset / field grid */
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 0.8rem; }
.field-grid .f {
  padding: 5px 8px; background: var(--bg); border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.field-grid .f .n { font-weight: 600; color: var(--text); font-size: 0.8rem; }
.field-grid .f .t { color: var(--text-muted); font-family: var(--font-mono); font-size: 0.7rem; }

/* Quick command chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 2px; overflow-x: hidden; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-full); padding: 5px 14px;
  font-size: 0.8rem !important; cursor: pointer; color: var(--text-secondary);
  transition: background 0.15s, border-color 0.15s, color 0.15s; font-family: var(--font-sans);
}
.chip:hover {
  background: var(--surface-hover); border-color: var(--accent); color: var(--text);
}

/* === Gradio Dataset 表格（对话历史）暗色跟随 === */
[data-theme="dark"] .table-wrap table,
[data-theme="dark"] [data-testid="dataset"] table {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}
[data-theme="dark"] .table-wrap table th,
[data-theme="dark"] .table-wrap table td,
[data-theme="dark"] [data-testid="dataset"] table th,
[data-theme="dark"] [data-testid="dataset"] table td {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}
[data-theme="dark"] .table-wrap table tr.tr-head th,
[data-theme="dark"] [data-testid="dataset"] table tr.tr-head th {
  background: var(--bg) !important;
  color: var(--text-secondary) !important;
}
/* Dataset 行 hover 高亮 */
[data-theme="dark"] .table-wrap table tr.tr-body:hover td,
[data-theme="dark"] [data-testid="dataset"] table tr.tr-body:hover td {
  background: var(--surface-hover) !important;
}

/* === Chatbot 气泡跟随主题 === */
[data-testid="chatbot"] { background: transparent !important; border: none !important; }
[data-testid="chatbot"] .message,
[data-testid="chatbot"] .message.bot,
[data-testid="chatbot"] [data-testid="bot"] {
  background: var(--chat-bot-bg) !important;
  border: 1px solid var(--chat-bot-border) !important;
  color: var(--text) !important;
  font-size: 0.95rem !important;
}
[data-testid="chatbot"] .message.user,
[data-testid="chatbot"] [data-testid="user"] {
  background: var(--chat-user-bg) !important;
  color: var(--chat-user-text) !important;
  border: none !important;
}

/* === Input row === */
.input-row {
  display: flex; gap: 8px; padding: 10px 14px;
  border-top: 1px solid var(--border); background: var(--surface); align-items: center;
}

/* === Gradio 通用覆盖 === */
.gradio-container { background: var(--bg) !important; }
footer { display: none !important; }

/* === Scrollbar === */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
[data-theme="dark"] ::-webkit-scrollbar-thumb { background: #475569; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* Dark mode transition（精确选择器，避免通配重绘） */
body, .sidebar, .app-header, .field-grid .f, .chip, .input-row,
.theme-btn, [data-testid="chatbot"] .message,
.table-wrap table, [data-testid="dataset"] table {
  transition: background 0.25s ease, border-color 0.25s ease, color 0.25s ease;
}
"""

# ── UI Build ──

WELCOME_MESSAGES = [{
    "role": "assistant",
    "content": (
        "你好，我是 **TableAgent**，可以帮你读取、统计和可视化数据。\n\n"
        "你可以直接提问，例如：\n"
        "- 数据集有多少行多少列？有哪些字段？\n"
        "- 统计年龄（Age）的分布并画直方图\n"
        "- 不同舱位（Pclass）的存活率如何？\n\n"
        "也可以点击左侧「快捷指令」一键开始。"
    ),
}]

QUICK_CMDS = [
    ("数据概览", "数据集有多少行多少列？有哪些字段？"),
    ("前 5 行", "查看前5行数据"),
    ("年龄分布", "统计年龄（Age）的分布情况"),
    ("分组+柱状图", "不同舱位（Pclass）的票价（Fare）平均值是多少？画柱状图"),
    ("相关性热力图", "年龄和票价的相关性如何？画热力图"),
    ("年龄直方图", "绘制年龄（Age）的直方图"),
    ("分组统计", "按性别（Sex）统计存活率（Survived）"),
    ("条件筛选", "筛选出年龄大于60岁的乘客"),
    ("唯一值分布", "查看 embarked 列的唯一值分布"),
]

CHIPS_HTML = '<div class="chip-row">'
for label, cmd in QUICK_CMDS:
    safe_cmd = cmd.replace("'", "\\'").replace('"', "&quot;").replace("\n", " ")
    CHIPS_HTML += (
        f'<span class="chip" onclick="'
        f'sendCommand(\'{safe_cmd}\')">{label}</span>'
    )
CHIPS_HTML += "</div>"

DARK_MODE_JS = """
<script>
(function() {
  var saved = localStorage.getItem('ta-theme');
  var theme = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
})();
function toggleTheme() {
  var h = document.documentElement;
  var cur = h.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  var next = cur === 'dark' ? 'light' : 'dark';
  h.setAttribute('data-theme', next);
  localStorage.setItem('ta-theme', next);
}
function sendCommand(cmd) {
  var ta = document.querySelector('textarea');
  if (!ta) return;
  ta.value = cmd;
  ta.dispatchEvent(new Event('input', {bubbles:true}));
  setTimeout(function() {
    var btns = document.querySelectorAll('button');
    for (var b of btns) {
      if (b.textContent.includes('发送')) { b.click(); break; }
    }
  }, 60);
}
</script>
"""

with gr.Blocks(title="TableAgent", fill_height=True) as demo:
    session_state = gr.State("")

    header_info = gr.HTML(build_header_html(current_df))

    with gr.Row(equal_height=False, elem_classes="main-row"):
        with gr.Column(scale=1, min_width=240, elem_classes="sidebar"):
            gr.HTML('<div class="sidebar-title">对话历史</div>')
            session_list = gr.Dataset(
                components=["text", "text"], label=None,
                samples=[["暂无会话", ""]], headers=["预览", "时间"],
                type="index",
            )
            with gr.Row():
                new_btn = gr.Button("＋ 新建对话", variant="primary", size="sm", scale=1)
                del_btn = gr.Button("删除", variant="secondary", size="sm", scale=0, min_width=50)

            gr.HTML('<hr>')
            gr.HTML('<div class="sidebar-title">数据集</div>')
            file_input = gr.File(label="导入 CSV", file_types=[".csv"], scale=1)
            dataset_selector = gr.Dropdown(
                choices=["Titanic"], value="Titanic",
                label="切换数据集", interactive=True,
            )
            field_grid = gr.HTML(build_field_grid_html(current_df))

            gr.HTML('<hr>')
            gr.HTML('<div class="sidebar-title">快捷指令</div>')
            gr.HTML(CHIPS_HTML)

        with gr.Column(scale=3, elem_classes="chat-col"):
            chatbot = gr.Chatbot(
                value=list(WELCOME_MESSAGES),
                label=None,
                avatar_images=("🧑", "🤖"),
                buttons=["copy"],
                elem_classes="chat-main",
            )
            with gr.Row(elem_classes="input-row"):
                msg = gr.Textbox(
                    placeholder="输入数据分析问题，例如：统计年龄分布…",
                    show_label=False, container=False, scale=10, max_lines=4,
                )
                send = gr.Button("↵ 发送", variant="primary", scale=0, min_width=80)

    # ── 初始化：启动时即创建一个会话，避免 session_state 为空导致首次对话丢失 ──

    def init_app():
        """启动时创建初始会话并返回 (session_id, welcome_messages, session_list)。"""
        sid = new_session_id()
        session_save(sid, ConversationMemory(SYSTEM_PROMPT))
        return sid, list(WELCOME_MESSAGES), refresh_list()

    def refresh_list():
        sessions = list_sessions()
        if not sessions:
            return [["暂无会话", ""]]
        return [[s["preview"], s["time"]] for s in sessions]

    # ── Dataset events ──

    def handle_dataset_change(dataset_name: str):
        global current_df, current_dataset_name
        if dataset_name not in _loaded_dfs:
            return (build_header_html(current_df), build_field_grid_html(current_df),
                    gr.Dropdown(), list(WELCOME_MESSAGES))
        df = _loaded_dfs[dataset_name]
        current_df = df.copy()
        current_dataset_name = dataset_name
        sid = new_session_id()
        session_save(sid, ConversationMemory(SYSTEM_PROMPT))
        return (build_header_html(current_df), build_field_grid_html(current_df),
                sid, list(WELCOME_MESSAGES))

    def handle_file_upload(file: gr.FileData | None):
        global current_df, current_dataset_name
        if file is None:
            return (gr.Dropdown(), gr.HTML(), gr.HTML(), list(WELCOME_MESSAGES), "")
        import pandas as pd
        name = Path(file.path).stem
        df_new = pd.read_csv(file.path)
        _loaded_dfs[name] = df_new
        current_df = df_new
        current_dataset_name = name
        choices = list(_loaded_dfs.keys())
        sid = new_session_id()
        session_save(sid, ConversationMemory(SYSTEM_PROMPT))
        return (gr.Dropdown(choices=choices, value=name),
                build_header_html(current_df), build_field_grid_html(current_df),
                list(WELCOME_MESSAGES), sid)

    # ── Events ──

    def handle_submit(message, history, sid):
        if not message or not message.strip():
            return history, "", sid, refresh_list()
        user_msg = {"role": "user", "content": message}
        new_hist, new_sid = respond(message, [*history, user_msg], sid)
        return new_hist, "", new_sid, refresh_list()

    inputs = [msg, chatbot, session_state]
    outputs = [chatbot, msg, session_state, session_list]

    msg.submit(handle_submit, inputs, outputs)
    send.click(handle_submit, inputs, outputs)

    def handle_new():
        sid, _, lst = init_app()
        return sid, list(WELCOME_MESSAGES), lst

    new_btn.click(handle_new, None, [session_state, chatbot, session_list])

    def handle_delete(sid, ev: gr.EventData):
        idx = ev.index
        sessions = list_sessions()
        if idx is not None and idx < len(sessions):
            delete_session(sessions[idx]["id"])
        new_sid = new_session_id()
        session_save(new_sid, ConversationMemory(SYSTEM_PROMPT))
        return new_sid, list(WELCOME_MESSAGES), refresh_list()

    del_btn.click(handle_delete, [session_state], [session_state, chatbot, session_list])

    def handle_load(ev: gr.EventData):
        idx = ev.index
        sessions = list_sessions()
        if idx is not None and idx < len(sessions):
            sid = sessions[idx]["id"]
            mem = session_load(sid)
            if mem:
                return sid, build_chatbot_messages(mem)
        return "", list(WELCOME_MESSAGES)

    session_list.click(handle_load, None, [session_state, chatbot])

    # demo.load：初始化 session_state + 刷新列表
    demo.load(init_app, None, [session_state, chatbot, session_list])

    # Dataset event wiring
    dataset_selector.change(
        handle_dataset_change,
        inputs=[dataset_selector],
        outputs=[header_info, field_grid, session_state, chatbot],
    )
    file_input.upload(
        handle_file_upload,
        inputs=[file_input],
        outputs=[dataset_selector, header_info, field_grid, chatbot, session_state],
    )


def launch():
    demo.queue(default_concurrency_limit=5).launch(
        server_name="127.0.0.1", server_port=7860,
        show_error=True,
        theme=gr.themes.Base(font=("system-ui", "sans-serif")),
        head=DARK_MODE_JS,
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    launch()
