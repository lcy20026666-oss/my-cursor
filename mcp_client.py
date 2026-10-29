"""MCP 客户端阶段占位。此模块目前不会启动外部服务器。"""

def mcp_status() -> str:
    return (
        "MCP 尚未连接。后续需根据课程要求选择一个真实 MCP Server，"
        "再使用对应 Python SDK 配置连接、列出工具并执行一次调用。"
    )
