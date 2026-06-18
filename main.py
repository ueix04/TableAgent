"""TableAgent 入口：Gradio Web UI（默认）或命令行对话模式。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main_cli():
    """命令行交互模式（通过 --cli 启用）。"""
    import pandas as pd

    from agent.core import agent_loop, SYSTEM_PROMPT
    from agent.memory import ConversationMemory

    DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "titanic.csv")

    if not os.path.exists(DATA_PATH):
        print(f"错误：数据文件不存在 ({DATA_PATH})")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"TableAgent 已就绪 | 数据集: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"列: {', '.join(df.columns)}")
    print("输入 'exit' 退出，输入 'reset' 重置对话\n")

    memory = ConversationMemory(SYSTEM_PROMPT)

    while True:
        try:
            user_input = input(">> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input.strip():
            continue
        if user_input.lower() == "exit":
            break
        if user_input.lower() == "reset":
            memory.reset()
            print("对话已重置\n")
            continue

        for output in agent_loop(user_input, df, memory):
            if isinstance(output, str):
                print(output)
            else:
                output.save("temp_chart.png")
                print("[图表已保存为 temp_chart.png]")


def main():
    if "--cli" in sys.argv:
        main_cli()
        return

    try:
        from ui.app import launch
    except ModuleNotFoundError as e:
        print(f"错误：缺少依赖模块 — {e}")
        print("提示：请使用 conda 环境运行：")
        print("  conda activate pytorch && python main.py")
        print("  或：conda run -n pytorch python main.py")
        sys.exit(1)

    launch()


if __name__ == "__main__":
    main()
