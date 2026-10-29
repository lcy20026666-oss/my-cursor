import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import agent


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def make_response(tool_calls=None, content="模拟模型回复"):
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls or [],
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )


def make_unknown_tool_call():
    return SimpleNamespace(
        id="call-unknown-1",
        type="function",
        function=SimpleNamespace(
            name="unauthorized_tool",
            arguments=json.dumps({"query": "test"}),
        ),
    )


class AgentUnknownToolDispatchTests(unittest.TestCase):
    def test_unknown_tool_is_rejected_without_executing_tools(self):
        fake_config = {
            "api_key": "fake-test-key",
            "base_url": "https://example.invalid",
            "model": "fake-test-model",
        }

        with (
            patch.object(
                agent, "get_model_config", return_value=fake_config
            ),
            patch.object(agent, "OpenAI") as mock_openai,
            patch.object(agent, "_execute_read_file") as mock_read,
            patch.object(agent, "search_project") as mock_search,
        ):
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create.side_effect = [
                make_response(tool_calls=[make_unknown_tool_call()]),
                make_response(content="已拒绝未经授权的工具"),
            ]

            answer, logs = agent.agent_chat(
                "请调用一个未经授权的工具",
                history=[],
                workspace_root=PROJECT_ROOT,
            )

        self.assertEqual(answer, "已拒绝未经授权的工具")

        mock_read.assert_not_called()
        mock_search.assert_not_called()

        self.assertTrue(
            any(
                "[拒绝调用] unauthorized_tool" in log
                and "只读工具白名单" in log
                for log in logs
            ),
            "日志应明确记录未经授权工具被拒绝",
        )

        self.assertEqual(
            mock_client.chat.completions.create.call_count, 2
        )




    def test_malformed_tool_call_missing_function_is_handled(self):
        fake_config = {
            "api_key": "fake-test-key",
            "base_url": "https://example.invalid",
            "model": "fake-test-model",
        }
        malformed_call = SimpleNamespace(
            id="call-missing-function",
            type="function",
        )

        with (
            patch.object(
                agent, "get_model_config", return_value=fake_config
            ),
            patch.object(agent, "OpenAI") as mock_openai,
            patch.object(agent, "_execute_read_file") as mock_read,
            patch.object(agent, "_execute_search_project") as mock_search,
        ):
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create.side_effect = [
                make_response(tool_calls=[malformed_call]),
            ]

            try:
                answer, logs = agent.agent_chat(
                    "测试缺少 function 的工具调用",
                    history=[],
                    workspace_root=PROJECT_ROOT,
                )
            except AttributeError as exc:
                self.fail(f"缺少 function 不应导致 AttributeError：{exc}")

            mock_read.assert_not_called()
            mock_search.assert_not_called()

    def test_malformed_tool_call_missing_arguments_is_handled(self):
        fake_config = {
            "api_key": "fake-test-key",
            "base_url": "https://example.invalid",
            "model": "fake-test-model",
        }
        malformed_call = SimpleNamespace(
            id="call-missing-arguments",
            type="function",
            function=SimpleNamespace(name="read_file"),
        )

        with (
            patch.object(
                agent, "get_model_config", return_value=fake_config
            ),
            patch.object(agent, "OpenAI") as mock_openai,
            patch.object(agent, "_execute_read_file") as mock_read,
            patch.object(agent, "_execute_search_project") as mock_search,
        ):
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create.side_effect = [
                make_response(tool_calls=[malformed_call]),
            ]

            try:
                answer, logs = agent.agent_chat(
                    "测试缺少 arguments 的工具调用",
                    history=[],
                    workspace_root=PROJECT_ROOT,
                )
            except AttributeError as exc:
                self.fail(f"缺少 arguments 不应导致 AttributeError：{exc}")

            mock_read.assert_not_called()
            mock_search.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
