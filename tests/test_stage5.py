"""Модульные тесты для команд 5-го этапа эмулятора."""

from io import StringIO
import os
import unittest
from unittest.mock import patch

from src.main import VirtualFileSystem, execute_command


class TestStage5Commands(unittest.TestCase):
    """Набор тестов для проверки команд touch, mv, vfs-load и help."""

    def setUp(self):
        """Инициализация тестовых файлов и экземпляра VFS."""
        self.csv_main = "test_main.csv"
        self.csv_alt = "test_alt.csv"

        with open(self.csv_main, "w", encoding="utf-8") as file_obj:
            file_obj.write("path,type,content\n")
            file_obj.write("/,dir,\n")
            file_obj.write("/docs,dir,\n")
            file_obj.write("/docs/file1.txt,file,data1\n")

        with open(self.csv_alt, "w", encoding="utf-8") as file_obj:
            file_obj.write("path,type,content\n")
            file_obj.write("/,dir,\n")
            file_obj.write("/new_folder,dir,\n")

        self.vfs = VirtualFileSystem(self.csv_main)

    def tearDown(self):
        """Очистка временных файлов после прохождения тестов."""
        for path in (self.csv_main, self.csv_alt):
            if os.path.exists(path):
                os.remove(path)

    def test_touch_new_file(self):
        """Проверка создания нового пустого файла."""
        self.assertTrue(self.vfs.touch("docs/file2.txt"))
        self.assertIn("/docs/file2.txt", self.vfs.entries)
        entry = self.vfs.entries["/docs/file2.txt"]
        self.assertEqual(entry["type"], "file")
        self.assertEqual(entry["content"], "")

    def test_touch_in_missing_dir(self):
        """Проверка ошибки touch в несуществующей директории."""
        self.assertFalse(self.vfs.touch("/missing_dir/file.txt"))

    def test_mv_rename_file(self):
        """Проверка переименования файла."""
        res = self.vfs.move("/docs/file1.txt", "/docs/renamed.txt")
        self.assertTrue(res)
        self.assertNotIn("/docs/file1.txt", self.vfs.entries)
        self.assertIn("/docs/renamed.txt", self.vfs.entries)

    def test_mv_dir_hierarchy(self):
        """Проверка перемещения каталога со всем содержимым."""
        self.assertTrue(self.vfs.move("/docs", "/archive"))
        self.assertNotIn("/docs", self.vfs.entries)
        self.assertIn("/archive", self.vfs.entries)
        self.assertIn("/archive/file1.txt", self.vfs.entries)

    def test_vfs_load_command(self):
        """Проверка перезагрузки VFS из нового CSV-файла."""
        cmd = f"vfs-load {self.csv_alt}"
        self.assertTrue(execute_command(cmd, self.vfs))
        self.assertEqual(self.vfs.cwd, "/")
        self.assertIn("/new_folder", self.vfs.entries)
        self.assertNotIn("/docs", self.vfs.entries)

    def test_help_command(self):
        """Проверка вывода справочной информации по команде help."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            self.assertTrue(execute_command("help", self.vfs))
            output = fake_out.getvalue()
            self.assertIn("touch", output)
            self.assertIn("mv", output)
            self.assertIn("vfs-load", output)
            self.assertIn("help", output)


if __name__ == "__main__":
    unittest.main()