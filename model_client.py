"""DeepSeek 模型接口：负责配置读取与文本对话。"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parent


def get_model_config():
    """读取项目 .env 中的 DeepSeek 配置。"""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    return {
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com"
        ),
        "model": os.getenv(
            "DEEPSEEK_MODEL",
            "deepseek-flash"
        ),
    }


def check_model_config() -> str:
    """检查必要的模型配置是否齐全。"""
    cfg = get_model_config()
    missing = [
        name for name, value in cfg.items()
        if not value
    ]

    if missing:
        return (
            "模型配置不完整，请检查项目 .env 文件。"
            "需要配置 DEEPSEEK_API_KEY、"
            "DEEPSEEK_BASE_URL、DEEPSEEK_MODEL。"
        )

    return "DeepSeek 模型配置字段已齐全。"


def chat_with_model(message, history=None):
    """
    发送一条消息并返回模型回复。
    history 为可选的历史对话列表。
    此函数只进行文本对话，不执行本地工具。
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("消息不能为空。")

    cfg = get_model_config()

    if not cfg["api_key"]:
        raise RuntimeError(
            "没有读取到 DEEPSEEK_API_KEY，"
            "请检查项目 .env 文件。"
        )

    client = OpenAI(
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        timeout=60.0,
        max_retries=1,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是 My Cursor，一个运行在用户电脑上的"
                "中文桌面智能助手。请清晰、准确地回答问题。"
                "不要声称自己已经读取或修改本地文件，"
                "除非程序明确提供了相关操作结果。"
            ),
        }
    ]

    # 仅接收格式正确的用户和助手历史消息
    if history:
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": content,
                })

    messages.append({"role": "user", "content": message.strip()})

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=messages,
        max_tokens=1000,
        stream=False,
    )

    answer = response.choices[0].message.content
    if not answer:
        return "模型没有返回文本内容。"

    return answer.strip()


def chat_with_agent(message, history=None):
    """调用只读智能体；保留原有 chat_with_model() 接口。"""
    # 延迟导入，避免 agent.py 与 model_client.py 相互导入时
    # 发生模块初始化循环。
    from agent import agent_chat

    return agent_chat(
        message=message,
        history=history,
        workspace_root=PROJECT_ROOT,
    )
