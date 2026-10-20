"""Эмулятор командной строки UNIX-подобной ОС с поддержкой VFS."""

import csv
import getpass
import os
import posixpath
import shlex
import sys

MIN_ARGS_FOR_VFS = 1
MIN_ARGS_FOR_SCRIPT = 2
MIN_ARGS_FOR_TOUCH = 1
MIN_ARGS_FOR_MV = 2
MIN_ARGS_FOR_LOAD = 1


class VirtualFileSystem:
    """Виртуальная файловая система в оперативной памяти."""

    def __init__(self, csv_path: str):
        """Инициализация VFS и загрузка файловой структуры."""
        self.csv_path = csv_path
        self.cwd = "/"
        self.entries = {}
        self.load(csv_path)

    def load(self, csv_path: str) -> None:
        """Загрузка файловой структуры из CSV-файла."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Файл VFS не найден: {csv_path}")

        loaded_entries = {}
        with open(csv_path, mode="r", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                raw_path = row["path"].strip()
                norm = posixpath.normpath(raw_path)
                if not norm.startswith("/"):
                    norm = "/" + norm
                loaded_entries[norm] = {
                    "type": row["type"].strip(),
                    "content": row.get("content", "")
                }

        if "/" not in loaded_entries:
            loaded_entries["/"] = {"type": "dir", "content": ""}

        self.entries = loaded_entries
        self.csv_path = csv_path
        self.cwd = "/"

    def resolve_path(self, target: str) -> str:
        """Вычисление нормализованного абсолютного пути."""
        if target.startswith("/"):
            return posixpath.normpath(target)
        return posixpath.normpath(posixpath.join(self.cwd, target))

    def list_dir(self, target: str = "") -> list[str]:
        """Возвращает список элементов внутри каталога."""
        path = self.resolve_path(target) if target else self.cwd

        if path not in self.entries:
            print(f"ls: cannot access '{target}': "
                  "No such file or directory")
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

    def touch(self, target: str) -> bool:
        """Создание нового пустого файла в памяти VFS."""
        if not target:
            print("touch: missing file operand")
            return False

        file_path = self.resolve_path(target)
        parent_dir = posixpath.dirname(file_path)

        if parent_dir not in self.entries:
            print(f"touch: cannot touch '{target}': "
                  "No such file or directory")
            return False

        if self.entries[parent_dir]["type"] != "dir":
            print(f"touch: cannot touch '{target}': Not a directory")
            return False

        if file_path not in self.entries:
            self.entries[file_path] = {"type": "file", "content": ""}
        return True

    def _remap_dir_entries(self, src: str, dst: str) -> None:
        """Переименование дочерних путей директории в VFS."""
        prefix = src.rstrip("/") + "/"
        keys_to_update = [k for k in self.entries if k.startswith(prefix)]
        for old_key in sorted(keys_to_update):
            rel = old_key[len(prefix):]
            new_key = posixpath.join(dst, rel)
            self.entries[new_key] = self.entries.pop(old_key)

    def move(self, src_arg: str, dst_arg: str) -> bool:
        """Перемещение или переименование объекта в памяти VFS."""
        src = self.resolve_path(src_arg)
        if src not in self.entries:
            print(f"mv: cannot stat '{src_arg}': No such file or directory")
            return False

        dst = self.resolve_path(dst_arg)
        if dst in self.entries and self.entries[dst]["type"] == "dir":
            dst = posixpath.join(dst, posixpath.basename(src))

        if src == dst:
            print(f"mv: '{src_arg}' and '{dst_arg}' are the same file")
            return False

        parent_dst = posixpath.dirname(dst)
        if parent_dst not in self.entries:
            print(f"mv: cannot move to '{dst_arg}': No such file or directory")
            return False

        is_dir = self.entries[src]["type"] == "dir"
        self.entries[dst] = self.entries.pop(src)
        if is_dir:
            self._remap_dir_entries(src, dst)
            if self.cwd == src:
                self.cwd = dst
            elif self.cwd.startswith(src + "/"):
                self.cwd = dst + self.cwd[len(src):]
        return True


def print_help() -> None:
    """Вывод списка поддерживаемых команд эмулятора."""
    commands = [
        ("ls [каталог]", "вывод содержимого директории"),
        ("cd [каталог]", "смена текущего рабочего каталога"),
        ("echo [строка]", "вывод аргументов на экран"),
        ("whoami", "вывод имени текущего пользователя"),
        ("clear", "очистка экрана терминала"),
        ("touch <файл>", "создание пустого файла в VFS"),
        ("mv <исх> <цель>", "перемещение или переименование объекта VFS"),
        ("vfs-load <путь>", "загрузка нового CSV-образа VFS"),
        ("help", "вывод справки по доступным командам"),
        ("exit", "завершение работы эмулятора"),
    ]
    print("Доступные команды эмулятора:")
    for name, desc in commands:
        print(f"  {name:<20} - {desc}")


def dispatch_command(cmd: str, args: list[str],
                     vfs: VirtualFileSystem) -> bool:
    """Маршрутизация вызова команд эмулятора."""
    if cmd == "exit":
        return False
    if cmd == "ls":
        target = args[0] if len(args) >= MIN_ARGS_FOR_VFS else ""
        items = vfs.list_dir(target)
        if items:
            print("  ".join(items))
        return True
    if cmd == "cd":
        target = args[0] if len(args) >= MIN_ARGS_FOR_VFS else ""
        return vfs.change_dir(target)
    if cmd == "echo":
        print(" ".join(args))
        return True
    if cmd == "whoami":
        print(getpass.getuser())
        return True
    if cmd == "clear":
        print("\033[H\033[J", end="")
        return True
    if cmd == "touch":
        if len(args) < MIN_ARGS_FOR_TOUCH:
            print("touch: missing file operand")
            return False
        return vfs.touch(args[0])
    if cmd == "mv":
        if len(args) < MIN_ARGS_FOR_MV:
            print("mv: missing destination file operand")
            return False
        return vfs.move(args[0], args[1])
    if cmd == "vfs-load":
        if len(args) < MIN_ARGS_FOR_LOAD:
            print("vfs-load: missing CSV path operand")
            return False
        try:
            vfs.load(args[0])
            return True
        except FileNotFoundError as err:
            print(f"vfs-load: {err}")
            return False
    if cmd == "help":
        print_help()
        return True

    print(f"{cmd}: command not found")
    return False


def execute_command(cmd_line: str, vfs: VirtualFileSystem) -> bool:
    """Выполнение одной команды оболочки."""
    expanded = os.path.expandvars(cmd_line.strip())
    if not expanded or expanded.startswith("#"):
        return True

    try:
        parts = shlex.split(expanded)
    except ValueError as err:
        print(f"shell: parse error: {err}")
        return False

    cmd, args = parts[0], parts[1:]
    return dispatch_command(cmd, args, vfs)


def run_script_file(script_path: str, vfs: VirtualFileSystem) -> bool:
    """Пакетное выполнение команд из файла стартового скрипта."""
    if not os.path.exists(script_path):
        print(f"Ошибка: файл скрипта '{script_path}' не найден.")
        return False

    with open(script_path, "r", encoding="utf-8") as file_obj:
        for line in file_obj:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue
            vfs_name = os.path.basename(vfs.csv_path)
            print(f"[{vfs_name}:{vfs.cwd}]$ {clean_line}")
            if not execute_command(clean_line, vfs):
                return False
    return True


def main():
    """Точка входа эмулятора."""
    vfs_path = sys.argv[1] if len(sys.argv) > MIN_ARGS_FOR_VFS else "vfs.csv"
    script_path = (sys.argv[2]
                   if len(sys.argv) > MIN_ARGS_FOR_SCRIPT else None)

    try:
        vfs = VirtualFileSystem(vfs_path)
    except FileNotFoundError as err:
        print(err)
        sys.exit(1)

    if script_path and not run_script_file(script_path, vfs):
        sys.exit(1)

    while True:
        try:
            vfs_name = os.path.basename(vfs.csv_path)
            prompt = f"[{vfs_name}:{vfs.cwd}]$ "
            line = input(prompt)
            if not execute_command(line, vfs):
                break
        except (KeyboardInterrupt, EOFError):
            print()
            break


if __name__ == "__main__":
    main()