from pathlib import Path
import unittest

import agent


class AgentSafetyRegressionTests(unittest.TestCase):
    """Agent 参数校验与安全配置回归测试。"""

    def test_01_valid_line_range(self):
        result = agent._execute_read_file(
            PROJECT_ROOT,
            {
                "relative_path": "tools/read_file.py",
                "start_line": 1,
                "line_count": 3,
            },
        )

        self.assertIn("读取成功", result)
        self.assertIn("读取行范围：1-3", result)

    def test_02_reject_invalid_start_line(self):
        result = agent._execute_read_file(
            PROJECT_ROOT,
            {
                "relative_path": "tools/read_file.py",
                "start_line": 0,
            },
        )

        self.assertIn("读取请求被拒绝", result)
        self.assertIn("start_line", result)

    def test_03_reject_invalid_line_count(self):
        result = agent._execute_read_file(
            PROJECT_ROOT,
            {
                "relative_path": "tools/read_file.py",
                "line_count": -1,
            },
        )

        self.assertIn("读取请求被拒绝", result)
        self.assertIn("line_count", result)

    def test_04_reject_extra_arguments(self):
        result = agent._execute_read_file(
            PROJECT_ROOT,
            {
                "relative_path": "tools/read_file.py",
                "delete_file": True,
            },
        )

        self.assertIn("工具参数错误", result)

    def test_05_reject_outside_path(self):
        result = agent._execute_read_file(
            PROJECT_ROOT,
            {
                "relative_path": "../outside.txt",
            },
        )

        self.assertIn("读取请求被拒绝", result)

    def test_06_tool_configuration_has_safety_limits(self):
        self.assertEqual(
            agent.READ_FILE_TOOL["function"]["name"],
            "read_file",
        )

        self.assertEqual(agent.MAX_TOOL_CALLS, 3)

        properties = (
            agent.READ_FILE_TOOL["function"]["parameters"]["properties"]
        )

        self.assertIn("relative_path", properties)
        self.assertIn("start_line", properties)
        self.assertIn("line_count", properties)

        self.assertIs(
            agent.READ_FILE_TOOL["function"]["parameters"][
                "additionalProperties"
            ],
            False,
        )


# 测试时使用项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    unittest.main(verbosity=2)
