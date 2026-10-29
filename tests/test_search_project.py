import tempfile
import unittest
from pathlib import Path

from tools.search_project import search_project


class TestSearchProject(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_file(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_find_keyword_and_line_number(self):
        self.write_file(
            "sample.py",
            "first line\nfind_this_keyword\nthird line\n",
        )
        result = search_project(self.root, "find_this_keyword")
        self.assertIn("sample.py:2:", result)

    def test_case_insensitive_search(self):
        self.write_file("sample.py", "MAX_TOOL_CALLS = 3\n")
        result = search_project(self.root, "max_tool_calls")
        self.assertIn("sample.py:1:", result)

    def test_empty_query_is_rejected(self):
        result = search_project(self.root, "   ")
        self.assertIn("被拒绝", result)

    def test_non_string_query_is_rejected(self):
        result = search_project(self.root, 123)
        self.assertIn("被拒绝", result)

    def test_query_length_limit(self):
        result = search_project(self.root, "x" * 201)
        self.assertIn("不能超过", result)

    def test_invalid_result_limits_are_rejected(self):
        for value in (0, -1, 101, True, 1.5):
            with self.subTest(value=value):
                result = search_project(self.root, "hello", value)
                self.assertIn("被拒绝", result)

    def test_hidden_directory_is_skipped(self):
        self.write_file(".private/secret.py", "hidden_marker\n")
        result = search_project(self.root, "hidden_marker")
        self.assertNotIn("secret.py", result)

    def test_backup_directory_is_skipped(self):
        self.write_file("backups_test/old.py", "backup_marker\n")
        result = search_project(self.root, "backup_marker")
        self.assertNotIn("old.py", result)

    def test_env_file_is_skipped(self):
        self.write_file(".env", "FAKE_API_KEY_MARKER\n")
        result = search_project(self.root, "FAKE_API_KEY_MARKER")
        self.assertIn("没有找到关键词", result)
        self.assertNotIn(".env:", result)

    def test_unsupported_file_extension_is_skipped(self):
        self.write_file("sample.csv", "csv_only_marker\n")
        result = search_project(self.root, "csv_only_marker")
        self.assertNotIn("sample.csv", result)

    def test_result_limit_is_enforced(self):
        self.write_file(
            "many.txt",
            "needle\nneedle\nneedle\nneedle\n",
        )
        result = search_project(self.root, "needle", max_results=2)
        self.assertLessEqual(result.count("many.txt:"), 2)
        self.assertIn("最多返回 2 条结果", result)

    def test_nonexistent_root_is_handled(self):
        missing_root = self.root / "does_not_exist"
        result = search_project(missing_root, "keyword")
        self.assertIn("不存在", result)

    def test_large_file_is_skipped(self):
        path = self.root / "large.txt"
        path.write_text("x" * 1_000_001, encoding="utf-8")
        result = search_project(self.root, "large_marker")
        self.assertNotIn("large.txt", result)

    def test_allowed_root_accepts_workspace(self):
        self.write_file("demo.py", "allowed_workspace_marker\n")
        result = search_project(
            self.root,
            "allowed_workspace_marker",
            allowed_root=self.root,
        )
        self.assertIn("demo.py:1:", result)

    def test_allowed_root_rejects_outside_directory(self):
        outside = self.root.parent / (
            self.root.name + "_outside_test"
        )
        outside.mkdir(exist_ok=True)
        try:
            (outside / "outside.py").write_text(
                "outside_workspace_marker\n",
                encoding="utf-8",
            )
            result = search_project(
                outside,
                "outside_workspace_marker",
                allowed_root=self.root,
            )
            self.assertIn("超出授权工作区范围", result)
            self.assertNotIn("outside.py:1:", result)
        finally:
            outside_file = outside / "outside.py"
            if outside_file.exists():
                outside_file.unlink()
            if outside.exists():
                outside.rmdir()

    def test_common_credential_files_are_skipped(self):
        names = [
            ".env",
            "credentials.json",
            "secrets.json",
            "secret.json",
            "service-account.json",
            "token.json",
        ]
        for name in names:
            self.write_file(name, "credential_marker\n")

        result = search_project(self.root, "credential_marker")
        self.assertIn("没有找到关键词", result)
        for name in names:
            self.assertNotIn(f"{name}:", result)


if __name__ == "__main__":
    unittest.main()
