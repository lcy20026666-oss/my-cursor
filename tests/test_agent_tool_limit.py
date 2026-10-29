from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import unittest

import agent


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def fake_tool_call(call_id, relative_path="tools/read_file.py"):
    """构造模拟的文件读取请求。"""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(
            name="read_file",
            arguments=json.dumps({
                "relative_path": relative_path,
                "start_line": 1,
                "line_count": 1,
            }),
        ),
    )


def fake_response(tool_calls=None, content="模拟模型回复"):
    """构造模拟的模型响应。"""
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls or [],
    )

    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )


class AgentToolLimitTests(unittest.TestCase):

    def setUp(self):
        # 使用虚构配置，不读取真实 API Key
        self.config_patch = patch.object(
            agent,
            "get_model_config",
            return_value={
                "api_key": "fake-test-key",
                "base_url": "https://example.invalid",
                "model": "fake-test-model",
            },
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

        # 替换 OpenAI 客户端，不会发送网络请求
        self.client_patch = patch.object(agent, "OpenAI")
        self.mock_openai = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)

        self.mock_client = self.mock_openai.return_value

        # 替换文件读取函数，统计实际调用次数
        self.read_patch = patch.object(
            agent,
            "read_file",
            return_value="模拟文件内容",
        )
        self.mock_read_file = self.read_patch.start()
        self.addCleanup(self.read_patch.stop)

    def test_01_three_calls_are_allowed(self):
        self.mock_client.chat.completions.create.side_effect = [
            fake_response([
                fake_tool_call("call-1"),
                fake_tool_call("call-2"),
                fake_tool_call("call-3"),
            ]),
            fake_response(content="三次读取完成"),
        ]

        answer, logs = agent.agent_chat(
            "请读取文件",
            history=[],
            workspace_root=PROJECT_ROOT,
        )

        self.assertEqual(answer, "三次读取完成")
        self.assertEqual(self.mock_read_file.call_count, 3)
        self.assertEqual(
            self.mock_client.chat.completions.create.call_count,
            2,
        )

    def test_02_four_calls_are_rejected_before_execution(self):
        self.mock_client.chat.completions.create.return_value = (
            fake_response([
                fake_tool_call("call-1"),
                fake_tool_call("call-2"),
                fake_tool_call("call-3"),
                fake_tool_call("call-4"),
            ])
        )

        answer, logs = agent.agent_chat(
            "请读取很多文件",
            history=[],
            workspace_root=PROJECT_ROOT,
        )

        self.assertIn("超过安全上限", answer)
        self.assertEqual(self.mock_read_file.call_count, 0)
        self.assertEqual(
            self.mock_client.chat.completions.create.call_count,
            1,
        )
        self.assertTrue(
            any("安全限制" in log for log in logs)
        )

    def test_03_cumulative_calls_cannot_exceed_three(self):
        self.mock_client.chat.completions.create.side_effect = [
            fake_response([
                fake_tool_call("call-1"),
                fake_tool_call("call-2"),
            ]),
            fake_response([
                fake_tool_call("call-3"),
                fake_tool_call("call-4"),
            ]),
        ]

        answer, logs = agent.agent_chat(
            "请分批读取文件",
            history=[],
            workspace_root=PROJECT_ROOT,
        )

        self.assertIn("超过安全上限", answer)
        self.assertEqual(self.mock_read_file.call_count, 2)
        self.assertEqual(
            self.mock_client.chat.completions.create.call_count,
            2,
        )
        self.assertTrue(
            any("安全限制" in log for log in logs)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
