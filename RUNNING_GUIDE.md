# My Cursor 运行指南

本文档介绍如何在 Windows 环境中安装依赖、配置 DeepSeek API、启动 My Cursor 桌面应用、使用本地工具并运行自动化测试。文中的项目路径仅为示例，使用时应替换为自己的实际项目目录。

## 1. 环境准备

- 操作系统：Windows 10 / Windows 11
- Python：建议使用 Python 3.14.6（项目开发环境）
- 桌面界面：PySide6
- 模型接口：DeepSeek OpenAI 兼容接口

请确认 Python 已安装。在 Jupyter Notebook 中运行：

```python
import sys
print(sys.version)
```

## 2. 安装项目依赖

在 Jupyter Notebook 中运行：

```python
from pathlib import Path
import subprocess
import sys

project = Path(r'C:\Users\Administrator\Desktop\本周python作业\my-cursor')
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
    cwd=project,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)
print(result.stdout)
print(result.stderr)
print('安装返回代码：', result.returncode)
```

返回代码为 0 表示依赖安装命令执行成功。

## 3. 配置 DeepSeek API

### 3.1 创建本地配置文件

在项目根目录找到 `.env.example`，复制一份，并将副本命名为 `.env`。

### 3.2 填写模型配置

使用文本编辑器打开 `.env`，填写自己的配置：

```dotenv
DEEPSEEK_API_KEY=填写自己的API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

**安全提示：不要将真实 API Key 或 `.env` 上传到 GitHub。**

## 4. 检查项目文件

```python
from pathlib import Path
project = Path(r'C:\Users\Administrator\Desktop\本周python作业\my-cursor')
required_files = ['app.py', 'agent.py', 'model_client.py', 'requirements.txt', '.env', '.env.example', 'tools', 'tests']
for name in required_files:
    path = project / name
    print(name, '存在' if path.exists() else '缺失')
```

注意：`.env` 应由用户在本机自行创建，不应从公开仓库下载。

## 5. 启动桌面应用

在 Jupyter Notebook 中运行：

```python
from pathlib import Path
import subprocess
import sys
project = Path(r'C:\Users\Administrator\Desktop\本周python作业\my-cursor')
process = subprocess.Popen([sys.executable, 'app.py'], cwd=project)
print('My Cursor 启动进程 PID：', process.pid)
```

正常情况下会打开 My Cursor 桌面窗口。

## 6. 运行自动化测试

```python
from pathlib import Path
import subprocess
import sys
project = Path(r'C:\Users\Administrator\Desktop\本周python作业\my-cursor')
result = subprocess.run(
    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
    cwd=project, capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
print(result.stderr)
print('返回代码：', result.returncode)
print('测试是否通过：', result.returncode == 0)
```

返回代码为 0 且测试结果显示 `OK`，表示本次自动化测试通过。

## 7. 常见问题

### 7.1 找不到模块

检查当前 Python 环境：

```python
import sys
print(sys.executable)
```

确保安装依赖和启动程序使用的是同一个 Python 环境。

### 7.2 DeepSeek 请求失败

- 检查 `.env` 是否位于项目根目录。
- 检查 API Key 是否填写正确。
- 检查网络是否能够访问 DeepSeek API。
- 检查模型名称和接口地址。

### 7.3 桌面窗口无法启动

检查 PySide6 是否安装成功，并查看 Jupyter 输出的错误信息。

## 8. 功能与安全边界

当前版本提供桌面交互、DeepSeek 对话、本地工具和只读智能体工具调用。

智能体自动调用范围限于文件读取和项目搜索。文件修改、命令执行和测试运行仍需通过桌面界面的独立操作入口完成。

`mcp_client.py` 当前为状态占位模块，不代表已经完成真实 MCP Server 集成。


## 9. 桌面工具使用说明

当前桌面应用提供以下操作入口：

| 功能 | 说明 |
|---|---|
| 读取文件 | 读取授权工作区内的文本文件 |
| 保存修改 | 保存编辑器中的文件内容，操作前需要确认 |
| 执行命令 | 在受限命令白名单范围内执行，并通过确认机制控制 |
| 运行测试 | 调用项目自动化测试 |
| DeepSeek 对话 | 向模型发送自然语言消息并显示回复 |
| 工具日志 | 查看工具执行过程和相关结果 |

智能体自动调用目前限定为 read_file 和 search_project 两个只读工具。
文件修改、命令执行和测试运行仍通过桌面界面的独立操作入口完成。

## 10. 常见问题补充

### 10.1 依赖安装失败

- 确认当前 Python 解释器路径正确。
- 确认网络能够访问 Python 软件包源。
- 检查 requirements.txt 是否存在。
- 查看 pip 输出中的具体错误信息。

### 10.2 API 请求失败

- 确认 .env 位于项目根目录。
- 检查 API Key 是否有效。
- 检查模型名称和 API 地址。
- 检查网络连接及账户 API 服务状态。
- 排查时不要打印或公开真实 API Key。

### 10.3 自动化测试失败

- 查看失败测试的名称和错误信息。
- 检查最近修改的工具代码。
- 确认 tests 和测试数据目录完整。
- 修复问题后重新运行完整测试。

## 11. 项目功能边界补充

智能体自动调用目前仅限 read_file 和 search_project 两个只读工具；文件修改、命令执行和测试运行仍需通过桌面界面的独立操作入口完成。

mcp_client.py 当前仍为状态占位模块，尚未完成真实 MCP Server 集成。

项目此前一次完整回归测试执行了 54 项测试，全部通过，失败数量为 0，错误数量为 0。
后续修改代码后应重新运行测试，并以实际测试结果为准。
