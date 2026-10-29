import sys
import shlex
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QTextEdit, QLineEdit, QVBoxLayout, QHBoxLayout, QFileDialog,
    QMessageBox
)

from tools.read_file import read_file
from tools.edit_file import edit_file
from tools.run_command import run_command
from tools.run_tests import run_tests
from model_client import chat_with_agent

PROJECT_ROOT = Path(__file__).resolve().parent


class ChatWorker(QThread):
    finished_reply = Signal(str)
    tool_log = Signal(str)
    failed = Signal(str)

    def __init__(self, message, history):
        super().__init__()
        self.message = message
        self.history = history

    def run(self):
        try:
            answer, logs = chat_with_agent(self.message, self.history)
            if logs:
                self.tool_log.emit("\n\n".join(logs))
            self.finished_reply.emit(answer)
        except Exception as exc:
            self.failed.emit(
                f"{type(exc).__name__}: {str(exc)[:800]}"
            )


class CursorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Cursor - DeepSeek 桌面智能体")
        self.resize(1200, 820)

        self.history = []
        self.worker = None

        central = QWidget()
        self.setCentralWidget(central)
        main = QHBoxLayout(central)

        # 左侧：原有本地工具
        left = QVBoxLayout()
        left.addWidget(QLabel("工作区文件"))

        self.path_input = QLineEdit("README.md")
        self.path_input.setPlaceholderText("输入相对路径，例如 app.py")
        left.addWidget(self.path_input)

        self.choose_button = QPushButton("选择文件")
        self.choose_button.clicked.connect(self.choose_file)
        left.addWidget(self.choose_button)

        self.read_button = QPushButton("1. 读取文件")
        self.read_button.clicked.connect(self.read_selected_file)
        left.addWidget(self.read_button)

        self.save_button = QPushButton("2. 保存修改")
        self.save_button.clicked.connect(self.save_selected_file)
        left.addWidget(self.save_button)

        left.addWidget(QLabel("终端命令（仅允许 python、py、git）"))
        self.command_input = QLineEdit("python --version")
        left.addWidget(self.command_input)

        self.command_button = QPushButton("3. 执行命令")
        self.command_button.clicked.connect(self.execute_command)
        left.addWidget(self.command_button)

        self.test_button = QPushButton("4. 运行测试")
        self.test_button.clicked.connect(self.execute_tests)
        left.addWidget(self.test_button)
        left.addStretch()

        # 右侧：文件编辑、工具日志、AI 对话
        right = QVBoxLayout()

        right.addWidget(QLabel("文件编辑区"))
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("读取文件后，可在此编辑。")
        right.addWidget(self.editor, 2)

        right.addWidget(QLabel("工具调用记录 / 执行结果"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText(
            "My Cursor 已启动。\n"
            "本地工具：读取文件、保存修改、执行命令、运行测试。\n"
            "AI 模型：DeepSeek。\n"
            "提示：AI 可自动只读读取工作区文件；不会自动修改文件或执行命令。"
        )
        right.addWidget(self.log, 1)

        right.addWidget(QLabel("DeepSeek AI 对话"))
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("AI 对话内容会显示在这里。")
        right.addWidget(self.chat_display, 2)

        chat_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入问题，按回车或点击发送")
        self.chat_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)

        self.clear_button = QPushButton("清空对话")
        self.clear_button.clicked.connect(self.clear_chat)

        chat_row.addWidget(self.chat_input, 1)
        chat_row.addWidget(self.send_button)
        chat_row.addWidget(self.clear_button)
        right.addLayout(chat_row)

        main.addLayout(left, 1)
        main.addLayout(right, 3)

        self.statusBar().showMessage("已连接配置 | DeepSeek 文本对话模式")

    def log_text(self, message):
        self.log.append("\n" + message)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择工作区文件", str(PROJECT_ROOT),
            "文本文件 (*.py *.md *.txt *.json *.yml *.yaml);;所有文件 (*)"
        )
        if path:
            try:
                relative = Path(path).resolve().relative_to(PROJECT_ROOT)
                self.path_input.setText(relative.as_posix())
                self.read_selected_file()
            except ValueError:
                QMessageBox.warning(
                    self, "路径限制", "只能选择当前 my-cursor 工作区内的文件。"
                )

    def read_selected_file(self):
        relative = self.path_input.text().strip()
        if not relative:
            QMessageBox.warning(self, "提示", "请先填写文件相对路径。")
            return

        result = read_file(PROJECT_ROOT, relative)
        self.log_text("[工具调用] read_file\n" + result)

        prefix = f"读取成功：{relative}\n---\n"
        if result.startswith(prefix):
            self.editor.setPlainText(result[len(prefix):])
            self.statusBar().showMessage(f"已读取：{relative}")
        else:
            QMessageBox.warning(self, "读取失败", result)

    def save_selected_file(self):
        relative = self.path_input.text().strip()
        if not relative:
            QMessageBox.warning(self, "提示", "请先填写文件相对路径。")
            return

        target = (PROJECT_ROOT / relative).resolve()
        if target != PROJECT_ROOT and PROJECT_ROOT not in target.parents:
            QMessageBox.warning(self, "路径限制", "不能修改工作区之外的文件。")
            return

        if not target.is_file():
            QMessageBox.warning(self, "文件不存在", "请先读取一个已有文件。")
            return

        confirm = QMessageBox.question(
            self, "确认修改",
            f"确定要覆盖文件 {relative} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        result = edit_file(PROJECT_ROOT, relative, self.editor.toPlainText())
        self.log_text("[工具调用] edit_file\n" + result)
        self.statusBar().showMessage("修改操作已完成，请检查结果。")

    def execute_command(self):
        raw = self.command_input.text().strip()
        if not raw:
            QMessageBox.warning(self, "提示", "请输入命令。")
            return

        try:
            command = shlex.split(raw)
        except ValueError as exc:
            QMessageBox.warning(self, "命令格式错误", str(exc))
            return

        if not command:
            return

        confirm = QMessageBox.question(
            self, "确认执行命令",
            f"将在项目目录中执行：\n{raw}\n\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        result = run_command(PROJECT_ROOT, command, timeout=15)
        self.log_text("[工具调用] run_command\n命令：" + raw + "\n" + result)

    def execute_tests(self):
        confirm = QMessageBox.question(
            self, "运行测试", "确认运行 tests 目录下的自动测试吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        result = run_tests(PROJECT_ROOT)
        self.log_text("[工具调用] run_tests\n" + result)
        self.statusBar().showMessage("测试执行完毕，请检查结果。")

    def send_message(self):
        message = self.chat_input.text().strip()
        if not message:
            return

        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "请稍候", "上一条消息还在处理中。")
            return

        self.chat_input.clear()

        # 每轮 AI 对话开始时，清空上一轮工具日志。
        self.log.clear()
        self.log.append(f"本轮 AI 工具记录：\n用户请求：{message}\n等待工具调用……")

        self.chat_display.append(f"你：\n{message}\n")
        self.chat_display.append("DeepSeek 正在思考……")
        self.send_button.setEnabled(False)
        self.statusBar().showMessage("正在请求 DeepSeek……")

        # 只把之前已完成的对话作为上下文传入
        history_snapshot = list(self.history)

        self.worker = ChatWorker(message, history_snapshot)
        self.worker.finished_reply.connect(
            lambda answer, msg=message: self.on_reply(msg, answer)
        )
        self.worker.tool_log.connect(self.on_tool_log)
        self.worker.failed.connect(self.on_chat_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_reply(self, message, answer):
        self.chat_display.append(f"DeepSeek：\n{answer}\n")
        self.history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ])
        # 保留最近 10 轮消息，控制上下文长度
        self.history = self.history[-20:]
        self.statusBar().showMessage("DeepSeek 回复完成")

    def on_tool_log(self, logs_text):
        """在主线程日志区显示智能体的只读工具调用记录。"""
        self.log_text("[AI 自动工具记录]\n" + logs_text)

    def on_chat_error(self, error):
        self.chat_display.append(f"请求失败：\n{error}\n")
        self.statusBar().showMessage("模型请求失败，请检查日志和 API 额度")

    def on_worker_finished(self):
        self.send_button.setEnabled(True)
        self.chat_input.setFocus()

    def clear_chat(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(
                self, "请稍候", "模型请求完成后再清空对话。"
            )
            return

        self.history.clear()
        self.chat_display.clear()
        self.statusBar().showMessage("对话历史已清空")

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(
                self, "正在请求模型",
                "请等待 DeepSeek 请求完成后再关闭窗口。"
            )
            event.ignore()
            return
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CursorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
