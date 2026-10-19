import os
import unittest
from unittest.mock import patch
from io import StringIO
from src.main import VirtualFileSystem, execute_command


class TestStage4Commands(unittest.TestCase):
    """Тестирование функциональности 4-го этапа."""

    def setUp(self):
        """Создание временного тестового файла VFS."""
        self.test_csv = "test_vfs.csv"
        with open(self.test_csv, "w", encoding="utf-8") as f:
            f.write("path,type,content\n")
            f.write("/,dir,\n")
            f.write("/home,dir,\n")
            f.write("/home/user,dir,\n")
            f.write("/home/user/file.txt,file,test_data\n")
        self.vfs = VirtualFileSystem(self.test_csv)

    def tearDown(self):
        """Удаление тестового файла VFS."""
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def test_whoami_command(self):
        """Проверка команды whoami."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            success = execute_command("whoami", self.vfs)
            self.assertTrue(success)
            self.assertTrue(len(fake_out.getvalue().strip()) > 0)

    def test_clear_command(self):
        """Проверка команды clear."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            success = execute_command("clear", self.vfs)
            self.assertTrue(success)
            self.assertIn("\033[H\033[J", fake_out.getvalue())

    def test_ls_and_cd(self):
        """Проверка навигации ls и cd."""
        self.assertEqual(self.vfs.list_dir(), ["home"])
        self.assertTrue(self.vfs.change_dir("home"))
        self.assertEqual(self.vfs.cwd, "/home")
        self.assertEqual(self.vfs.list_dir(), ["user"])

    def test_cd_invalid_directory(self):
        """Проверка ошибки перехода в несуществующую директорию."""
        self.assertFalse(self.vfs.change_dir("nonexistent"))
        self.assertFalse(self.vfs.change_dir("/home/user/file.txt"))


if __name__ == "__main__":
    unittest.main()
