from pathlib import Path
import tempfile
import unittest

from tools.read_file import read_file


class ReadFileRegressionTests(unittest.TestCase):
    """文件读取功能回归测试。"""

    def setUp(self):
        self.temp_context = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_context.name)
        self.test_file = self.root / "sample.txt"

        self.test_file.write_text(
            "第一行\n第二行\n第三行\n第四行\n第五行\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_context.cleanup()

    def test_01_read_whole_file(self):
        result = read_file(self.root, "sample.txt")

        self.assertIn("读取成功", result)
        self.assertIn("第一行", result)
        self.assertIn("第五行", result)

    def test_02_read_line_range(self):
        result = read_file(
            self.root,
            "sample.txt",
            start_line=2,
            line_count=2,
        )

        self.assertIn("读取行范围：2-3", result)
        self.assertIn("第二行", result)
        self.assertIn("第三行", result)
        self.assertNotIn("第一行", result)
        self.assertNotIn("第四行", result)

    def test_03_start_beyond_file(self):
        result = read_file(
            self.root,
            "sample.txt",
            start_line=100,
            line_count=3,
        )

        self.assertIn("没有可读取的内容", result)

    def test_04_reject_outside_path(self):
        result = read_file(self.root, "../outside.txt")

        self.assertIn("读取失败", result)
        self.assertIn("工作区之外", result)

    def test_05_reject_invalid_start_line(self):
        result = read_file(
            self.root,
            "sample.txt",
            start_line=0,
        )

        self.assertIn("start_line 必须大于等于 1", result)

    def test_06_reject_invalid_line_count(self):
        result = read_file(
            self.root,
            "sample.txt",
            line_count=-1,
        )

        self.assertIn("line_count 必须是正整数", result)

    def test_07_truncate_long_content(self):
        result = read_file(
            self.root,
            "sample.txt",
            max_chars=5,
        )

        self.assertIn("内容已截断", result)
        self.assertIn("提示：内容超过字符上限", result)

    def test_08_missing_file(self):
        result = read_file(self.root, "missing.txt")

        self.assertIn("文件不存在", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
