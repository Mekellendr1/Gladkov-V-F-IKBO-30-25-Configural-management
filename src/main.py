import tkinter as tk
import argparse as ap
from datetime import datetime
from vfs_storage import VFSStorage, VFSError
from vfs_storage import normalize_path, parent_of

EXIT_DELAY_MS = 500
SCRIPT_DELAY_MS = 100
WINDOW_SIZE = "800x600"
FONT = ("Monospace", 12)
BG_COLOR = "white"
FG_COLOR = "green"
CHOWN_ARG_COUNT = 2


class VFS:
    """GUI-эмулятор оболочки UNIX-подобной ОС с VFS."""

    def __init__(self, vfs_name="VFS"):
        """Инициализирует корень tk, имя ФС, хранилище
        и словарь обработчиков команд."""
        self.root = tk.Tk()
        self.name = vfs_name
        self.args = None
        self.storage = VFSStorage()
        self.handlers = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'rev': self.cmd_rev,
            'date': self.cmd_date,
            'vfs-save': self.cmd_vfs_save,
            'mkdir': self.cmd_mkdir,
            'chown': self.cmd_chown,
        }

    def setup_ui(self):
        """Настраивает окно, создаёт поля вывода и ввода,
        размещает их, привязывает Enter и ставит курсор."""
        self.root.title(self.name)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        self.output = tk.Text(
            self.root, bg=BG_COLOR, fg=FG_COLOR,
            font=FONT, state="disabled", wrap="word",
        )
        self.entry = tk.Entry(self.root, font=FONT)

        self.output.pack(side="top", fill="both", expand=True)
        self.entry.pack(side="bottom", fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

    def terminal_entry(self, text):
        """Разрешает запись, вставляет текст в конец,
        запрещает запись и прокручивает до конца."""
        self.output.config(state="normal")
        self.output.insert("end", text)
        self.output.config(state="disabled")
        self.output.see("end")

    def on_enter(self, event):
        """Читает команду из поля ввода, очищает поле
        и передаёт команду на выполнение."""
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        self.execute_command(command)

    def execute_command(self, command):
        """Разбирает команду и передаёт обработчику.
        Возвращает True при успехе."""
        if not command:
            return True
        parts = command.split()
        name, args = parts[0], parts[1:]

        self.terminal_entry(f"{self.storage.cwd}$ {command}\n")

        if name == 'exit':
            self.terminal_entry("Exiting...\n")
            self.root.after(EXIT_DELAY_MS, self.root.destroy)
            return True

        handler = self.handlers.get(name)
        if handler is not None:
            return handler(args)

        self.terminal_entry(f"{name}: command not found\n")
        return False

    def run_script(self, path):
        """Выполняет команды из файла построчно.
        Останавливается при первой ошибке."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.terminal_entry(
                f"Ошибка: файл скрипта не найден: {path}\n"
            )
            return

        for line_num, line in enumerate(lines, 1):
            command = line.strip()
            if not command or command.startswith('#'):
                continue
            if not self.execute_command(command):
                self.terminal_entry(
                    f"\n!!! Ошибка в скрипте на строке "
                    f"{line_num}. Выполнение остановлено.\n"
                )
                return
        self.terminal_entry("\nСкрипт выполнен успешно.\n")

    def cmd_ls(self, args):
        """Выводит содержимое каталога VFS,
        флаг -l для подробного списка."""
        long_fmt = '-l' in args
        rest = [a for a in args if a != '-l']
        target = self.storage.cwd
        if rest:
            target = normalize_path(rest[0], self.storage.cwd)
        node = self.storage.nodes.get(target)
        if node is None:
            self.terminal_entry(
                f"ls: cannot access '{rest[0]}': "
                "No such file or directory\n"
            )
            return False
        if node['type'] == 'file':
            if long_fmt:
                self.terminal_entry(
                    self.format_node(target, node) + '\n'
                )
            else:
                self.terminal_entry(
                    target.rsplit('/', 1)[-1] + '\n'
                )
            return True
        children = sorted(
            p for p in self.storage.nodes
            if parent_of(p) == target
        )
        if long_fmt:
            lines = [
                self.format_node(p, self.storage.nodes[p])
                for p in children
            ]
            self.terminal_entry('\n'.join(lines) + '\n')
        else:
            names = [p.rsplit('/', 1)[-1] for p in children]
            self.terminal_entry('  '.join(names) + '\n')
        return True

    def format_node(self, path, node):
        """Форматирует одну строку вывода ls -l."""
        kind = 'd' if node['type'] == 'dir' else '-'
        name = path.rsplit('/', 1)[-1]
        return f"{kind} {node['owner']:>8}  {name}"

    def cmd_cd(self, args):
        """Меняет текущий каталог VFS."""
        label = args[0] if args else '/'
        target = '/' if not args else normalize_path(
            args[0], self.storage.cwd
        )
        node = self.storage.nodes.get(target)
        if node is None:
            self.terminal_entry(
                f"cd: {label}: No such file or directory\n"
            )
            return False
        if node['type'] != 'dir':
            self.terminal_entry(f"cd: {label}: Not a directory\n")
            return False
        self.storage.cwd = target
        return True

    def cmd_rev(self, args):
        """Переворачивает строку из аргументов."""
        if not args:
            self.terminal_entry("rev: missing operand\n")
            return False
        self.terminal_entry(' '.join(args)[::-1] + '\n')
        return True

    def cmd_date(self, args):
        """Выводит текущие дату и время."""
        now = datetime.now()
        self.terminal_entry(
            now.strftime('%a %b %d %H:%M:%S %Y') + '\n'
        )
        return True

    def cmd_mkdir(self, args):
        """Создаёт новый каталог в VFS (только в памяти)."""
        if not args:
            self.terminal_entry("mkdir: missing operand\n")
            return False
        label = args[0]
        target = normalize_path(label, self.storage.cwd)
        if target in self.storage.nodes:
            self.terminal_entry(
                f"mkdir: cannot create directory '{label}': "
                "File exists\n"
            )
            return False
        parent = parent_of(target)
        if parent not in self.storage.nodes:
            self.terminal_entry(
                f"mkdir: cannot create directory '{label}': "
                "No such file or directory\n"
            )
            return False
        if self.storage.nodes[parent]['type'] != 'dir':
            self.terminal_entry(
                f"mkdir: cannot create directory '{label}': "
                "Not a directory\n"
            )
            return False
        self.storage.nodes[target] = {
            'type': 'dir', 'owner': 'root', 'content': b'',
        }
        return True

    def cmd_chown(self, args):
        """Меняет владельца узла VFS (только в памяти)."""
        if len(args) != CHOWN_ARG_COUNT:
            self.terminal_entry(
                "chown: usage: chown <owner> <path>\n"
            )
            return False
        owner, label = args
        target = normalize_path(label, self.storage.cwd)
        node = self.storage.nodes.get(target)
        if node is None:
            self.terminal_entry(
                f"chown: cannot access '{label}': "
                "No such file or directory\n"
            )
            return False
        node['owner'] = owner
        self.terminal_entry(
            f"chown: owner of '{label}' is now '{owner}'\n"
        )
        return True

    def cmd_vfs_save(self, args):
        """Сохраняет состояние VFS на диск в CSV."""
        if not args:
            self.terminal_entry(
                "vfs-save: укажите путь для сохранения\n"
            )
            return False
        path = args[0]
        try:
            self.storage.save(path)
            self.terminal_entry(f"VFS сохранена в {path}\n")
            return True
        except OSError as e:
            self.terminal_entry(f"vfs-save: ошибка записи: {e}\n")
            return False

    def run(self):
        """Запускает главный цикл программы."""
        self.root.mainloop()

    def args_parser(self):
        """Разбирает аргументы командной строки."""
        parser = ap.ArgumentParser(description="Эмулятор VFS")
        parser.add_argument(
            "--vfs-path",
            help="Путь к физическому расположению VFS",
        )
        parser.add_argument(
            "--script",
            help="Путь к стартовому скрипту",
        )
        self.args = parser.parse_args()


if __name__ == "__main__":
    my_vfs = VFS()
    my_vfs.args_parser()

    print("=== Отладочный вывод параметров ===")
    print(f"Путь к VFS: {my_vfs.args.vfs_path}")
    print(f"Путь к скрипту: {my_vfs.args.script}")
    print("===================================")

    vfs_message = None
    if my_vfs.args.vfs_path:
        try:
            count = my_vfs.storage.load(my_vfs.args.vfs_path)
            vfs_message = (
                f"VFS загружена из {my_vfs.args.vfs_path}: "
                f"узлов={count}"
            )
        except VFSError as e:
            vfs_message = f"ОШИБКА загрузки VFS: {e}"
        print(vfs_message)

    my_vfs.setup_ui()

    if vfs_message:
        my_vfs.terminal_entry(vfs_message + "\n")

    if my_vfs.args.script:
        my_vfs.root.after(
            SCRIPT_DELAY_MS,
            my_vfs.run_script,
            my_vfs.args.script,
        )

    my_vfs.run()