# My Cursor：桌面智能体课程作业

My Cursor 是一个基于 Python、PySide6 和 DeepSeek 模型接口开发的桌面智能体课程项目。
项目包含桌面交互界面、受限本地工具、只读智能体调用以及自动化测试。

## 功能概览

- 桌面界面：使用 PySide6 提供文件操作、命令执行、测试运行和模型对话入口。
- DeepSeek 对话：通过 OpenAI 兼容接口调用 DeepSeek 模型。
- `read_file`：读取授权工作区内的文本文件。
- `search_project`：在授权工作区内搜索代码关键词。
- `edit_file`：按程序规则修改文件并生成差异信息。
- `run_command`：受限的本地命令执行工具。
- `run_tests`：运行项目的 unittest 测试。
- 自动化测试：覆盖路径安全、参数校验、搜索限制和工具调用次数限制等行为。

## 智能体安全边界

当前智能体自动调用的工具仅包括 `read_file` 和 `search_project`。
智能体会校验工具参数、限制文件访问范围，并限制每轮工具调用次数。
智能体不会自动修改文件、执行终端命令或运行测试。
界面中的文件编辑、命令执行和测试功能属于独立的本地工具入口。

## 环境要求

- Windows
- 已在 Python 3.14.6（Anaconda）环境完成测试
- 可用的 DeepSeek API Key

## 安装依赖

在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
```

## 配置模型

1. 将 `.env.example` 复制为 `.env`。
2. 在 `.env` 中填写自己的 DeepSeek 配置：

```dotenv
DEEPSEEK_API_KEY=填写你自己的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

3. 保存配置后启动程序。

**不要将 `.env`、API Key 或其他凭据提交到 GitHub。** `.env` 已配置为 Git 忽略文件。

## 启动桌面应用

```powershell
python app.py
```

## 运行测试

```powershell
python -m unittest discover -s tests -v
```

最近一次完整测试结果：51 项测试通过。

## MCP 状态

`mcp_client.py` 目前是状态占位模块，尚未连接真实 MCP Server。
因此，本项目当前不宣称已完成 MCP 工具发现或调用。

## 项目目录

```text
my-cursor/
├── app.py
├── agent.py
├── model_client.py
├── mcp_client.py
├── requirements.txt
├── .env.example
├── tools/
├── tests/
└── test_data/
```

## 课程项目说明

本项目用于展示桌面智能体的基础架构、模型接口调用、受限只读工具、异常处理与自动化测试。
尚未实现的功能会在后续迭代中补充，不将占位模块描述为已完成能力。
