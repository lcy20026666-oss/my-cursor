from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import agent


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AgentSearchProjectTests(unittest.TestCase):
    """AI 项目搜索工具的配置、参数和安全边界测试。"""

    def test_01_tool_schema_is_correct(self):
        tool = agent.SEARCH_PROJECT_TOOL["function"]

        self.assertEqual(tool["name"], "search_project")

        parameters = tool["parameters"]
        self.assertEqual(parameters["required"], ["query"])
        self.assertIs(parameters["additionalProperties"], False)
        self.assertIn("query", parameters["properties"])
        self.assertIn("max_results", parameters["properties"])

    def test_02_valid_search_uses_authorized_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "sample.py").write_text(
                "def unique_search_marker():\n    return 1\n",
                encoding="utf-8",
            )

            result = agent._execute_search_project(
                root,
                {"query": "unique_search_marker", "max_results": 10},
            )

            self.assertIn("unique_search_marker", str(result))

    def test_03_reject_non_object_arguments(self):
        for arguments in (None, [], "query"):
            with self.subTest(arguments=arguments):
                result = agent._execute_search_project(
                    PROJECT_ROOT, arguments
                )
                self.assertIn("参数必须是 JSON 对象", result)

    def test_04_reject_empty_or_non_string_query(self):
        for query in ("", "   ", None, 123):
            with self.subTest(query=query):
                result = agent._execute_search_project(
                    PROJECT_ROOT, {"query": query}
                )
                self.assertIn("query", result)

    def test_05_reject_query_over_length_limit(self):
        result = agent._execute_search_project(
            PROJECT_ROOT, {"query": "x" * 201}
        )
        self.assertIn("200", result)

    def test_06_reject_extra_arguments(self):
        result = agent._execute_search_project(
            PROJECT_ROOT,
            {"query": "search", "delete_file": True},
        )
        self.assertIn("不允许的参数", result)

    def test_07_reject_invalid_result_limits(self):
        for value in (True, False, 0, 101, -1, 1.5, "10"):
            with self.subTest(max_results=value):
                result = agent._execute_search_project(
                    PROJECT_ROOT,
                    {"query": "search", "max_results": value},
                )
                self.assertIn("max_results", result)

    def test_08_enforce_authorized_root_argument(self):
        with patch.object(
            agent,
            "search_project",
            return_value="模拟搜索结果",
        ) as mock_search:
            result = agent._execute_search_project(
                PROJECT_ROOT,
                {"query": "read_file", "max_results": 5},
            )

        self.assertEqual(result, "模拟搜索结果")
        mock_search.assert_called_once_with(
            root=PROJECT_ROOT.resolve(),
            query="read_file",
            max_results=5,
            allowed_root=PROJECT_ROOT.resolve(),
        )

    def test_09_tool_call_limit_is_unchanged(self):
        self.assertEqual(agent.MAX_TOOL_CALLS, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
