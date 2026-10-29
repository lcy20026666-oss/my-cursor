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


def make_search_call():
    return SimpleNamespace(
        id="call-search-1",
        type="function",
        function=SimpleNamespace(
            name="search_project",
            arguments=json.dumps({
                "query": "unique_test_keyword",
                "max_results": 5,
            }),
        ),
    )


class AgentSearchDispatchTests(unittest.TestCase):
    def test_search_project_tool_is_dispatched(self):
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
            patch.object(
                agent,
                "search_project",
                return_value="模拟搜索结果：unique_test_keyword",
            ) as mock_search,
        ):
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create.side_effect = [
                make_response(tool_calls=[make_search_call()]),
                make_response(content="已完成项目搜索"),
            ]

            answer, logs = agent.agent_chat(
                "请搜索 unique_test_keyword",
                history=[],
                workspace_root=PROJECT_ROOT,
            )

        self.assertEqual(answer, "已完成项目搜索")
        mock_search.assert_called_once_with(
            root=PROJECT_ROOT.resolve(),
            query="unique_test_keyword",
            max_results=5,
            allowed_root=PROJECT_ROOT.resolve(),
        )
        self.assertTrue(
            any("search_project" in log for log in logs),
            "工具日志中应记录 search_project 调用",
        )
        self.assertEqual(
            mock_client.chat.completions.create.call_count, 2
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
