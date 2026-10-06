import os
import readline
import sys

MIN_ARGS_FOR_VFS = 1
MIN_ARGS_FOR_SCRIPT = 2


def do_command(user_input):
    """Выполняет команду.

    Возвращает True при успехе и False при ошибке/выходе.
    """
    expanded = os.path.expandvars(user_input)
    parts = expanded.split()

    if not parts:
        return True

    cmd = parts[0]
    args = parts[1:]

    if cmd == "exit":
        return False
    elif cmd == "ls":
        print(f"ls: {args}")
        return True
    elif cmd == "cd":
        print(f"cd: {args}")
        return True
    elif cmd == "echo":
        print(" ".join(args))
        return True
    else:
        print(f"Ошибка: {cmd}: command not found")
        return False


def run_script_file(script_path, vfs_name):
    """Выполняет стартовый скрипт построчно."""
    if not os.path.exists(script_path) or os.path.isdir(script_path):
        print(f"Ошибка: скрипт '{script_path}' не найден!")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            print(f"[{vfs_name}]$ {line}")

            status = do_command(line)
            if not status:
                print("Скрипт остановлен из-за ошибки!")
                sys.exit(1)


def main():
    """Точка входа эмулятора."""
    has_vfs = len(sys.argv) > MIN_ARGS_FOR_VFS
    has_script = len(sys.argv) > MIN_ARGS_FOR_SCRIPT

    vfs_path = sys.argv[1] if has_vfs else "vfs.csv"
    script_path = sys.argv[2] if has_script else None
    vfs_name = os.path.basename(vfs_path)

    print("=== ПАРАМЕТРЫ ===")
    print("VFS:", vfs_path)
    print("Скрипт:", script_path)
    print("=================")

    if script_path:
        run_script_file(script_path, vfs_name)

    while True:
        try:
            user_input = input(f"[{vfs_name}]$ ")
            if not user_input.strip():
                continue

            if user_input.strip() == "exit":
                break

            do_command(user_input)

        except (EOFError, KeyboardInterrupt):
            print("\nexit")
            break


if __name__ == "__main__":
    main()
