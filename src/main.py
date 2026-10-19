import csv
import getpass
import os
import posixpath
import shlex
import sys

MIN_ARGS_FOR_VFS = 1
MIN_ARGS_FOR_SCRIPT = 2


class VirtualFileSystem:
    """Виртуальная файловая система в оперативной памяти."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.cwd = "/"
        self.entries = {}
        self.load()

    def load(self) -> None:
        """Загрузка файловой структуры из CSV-файла."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Файл VFS не найден: {self.csv_path}")

        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_path = row["path"].strip()
                normalized = posixpath.normpath(raw_path)
                if not normalized.startswith("/"):
                    normalized = "/" + normalized
                self.entries[normalized] = {
                    "type": row["type"].strip(),
                    "content": row.get("content", "")
                }

        if "/" not in self.entries:
            self.entries["/"] = {"type": "dir", "content": ""}

    def resolve_path(self, target: str) -> str:
        """Вычисление нормализованного абсолютного пути."""
        if target.startswith("/"):
            return posixpath.normpath(target)
        return posixpath.normpath(posixpath.join(self.cwd, target))

    def list_dir(self, target: str = "") -> list[str]:
        """Возвращает список элементов внутри каталога."""
        path = self.resolve_path(target) if target else self.cwd

        if path not in self.entries:
            print(f"ls: cannot access '{target}': No such file or directory")
            return []

        if self.entries[path]["type"] != "dir":
            print(f"ls: '{target}': Not a directory")
            return []

        items = set()
        prefix = path.rstrip("/") + "/"
        for entry_path in self.entries:
            if entry_path in ("/", path):
                continue
            if entry_path.startswith(prefix):
                relative = entry_path[len(prefix):]
                top_name = relative.split("/")[0]
                if top_name:
                    items.add(top_name)
        return sorted(items)

    def change_dir(self, target: str = "") -> bool:
        """Переход в указанную директорию."""
        if not target or target == "~":
            self.cwd = "/"
            return True

        new_path = self.resolve_path(target)
        if new_path not in self.entries:
            print(f"cd: no such file or directory: {target}")
            return False

        if self.entries[new_path]["type"] != "dir":
            print(f"cd: not a directory: {target}")
            return False

        self.cwd = new_path
        return True


def execute_command(cmd_line: str, vfs: VirtualFileSystem) -> bool:
    """Выполнение одной команды оболочки."""
    expanded_line = os.path.expandvars(cmd_line.strip())
    if not expanded_line or expanded_line.startswith("#"):
        return True

    try:
        parts = shlex.split(expanded_line)
    except ValueError as err:
        print(f"shell: parse error: {err}")
        return False

    cmd = parts[0]
    args = parts[1:]

    if cmd == "exit":
        return False
    elif cmd == "ls":
        target = args[0] if args else ""
        items = vfs.list_dir(target)
        if items:
            print("  ".join(items))
        return True
    elif cmd == "cd":
        target = args[0] if args else ""
        return vfs.change_dir(target)
    elif cmd == "echo":
        print(" ".join(args))
        return True
    elif cmd == "whoami":
        print(getpass.getuser())
        return True
    elif cmd == "clear":
        print("\033[H\033[J", end="")
        return True
    else:
        print(f"{cmd}: command not found")
        return False


def run_script_file(script_path: str, vfs: VirtualFileSystem,
                    vfs_name: str) -> bool:
    """Пакетное выполнение команд из файла скрипта."""
    if not os.path.exists(script_path):
        print(f"Ошибка: файл скрипта '{script_path}' не найден.")
        return False

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue
            print(f"[{vfs_name}:{vfs.cwd}]$ {clean_line}")
            if not execute_command(clean_line, vfs):
                return False
    return True


def main():
    """Точка входа эмулятора."""
    vfs_path = sys.argv[1] if len(sys.argv) > MIN_ARGS_FOR_VFS else "vfs.csv"
    script_path = (sys.argv[2]
                   if len(sys.argv) > MIN_ARGS_FOR_SCRIPT else None)
    vfs_name = os.path.basename(vfs_path)

    try:
        vfs = VirtualFileSystem(vfs_path)
    except FileNotFoundError as err:
        print(err)
        sys.exit(1)

    if script_path:
        if not run_script_file(script_path, vfs, vfs_name):
            sys.exit(1)

    while True:
        try:
            prompt = f"[{vfs_name}:{vfs.cwd}]$ "
            line = input(prompt)
            if not execute_command(line, vfs):
                break
        except (KeyboardInterrupt, EOFError):
            print()
            break


if __name__ == "__main__":
    main()