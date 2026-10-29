import tempfile
import unittest
from pathlib import Path
from tools.read_file import read_file
from tools.edit_file import edit_file
from tools.run_command import run_command

class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_file(self):
        (self.root / "hello.txt").write_text("hello", encoding="utf-8")
        self.assertIn("hello", read_file(self.root, "hello.txt"))

    def test_edit_file(self):
        result = edit_file(self.root, "hello.txt", "new text")
        self.assertIn("修改成功", result)
        self.assertEqual((self.root / "hello.txt").read_text(encoding="utf-8"), "new text")

    def test_reject_sensitive_files(self):
        sensitive_files = [
            ".env",
            ".env.local",
            ".env.production",
            "id_rsa",
            "private.pem",
        ]

        for filename in sensitive_files:
            with self.subTest(filename=filename):
                target = self.root / filename
                original_content = "FAKE_TEST_SECRET_DO_NOT_USE"
                target.write_text(original_content, encoding="utf-8")

                result = edit_file(
                    self.root,
                    filename,
                    "attempted modification"
                )

                self.assertIn("修改失败", result)
                self.assertIn("敏感", result)
                self.assertEqual(
                    target.read_text(encoding="utf-8"),
                    original_content
                )

    def test_prevent_path_escape(self):
        result = read_file(self.root, "../outside.txt")
        self.assertIn("失败", result)

    def test_reject_unapproved_command(self):
        result = run_command(self.root, ["powershell", "-Command", "echo unsafe"])
        self.assertIn("拒绝执行", result)

if __name__ == "__main__":
    unittest.main()
