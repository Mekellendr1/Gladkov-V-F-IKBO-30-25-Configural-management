import tkinter as tk
import argparse as ap
from datetime import datetime
from vfs_storage import VFSStorage, VFSError
from vfs_storage import normalize_path, parent_of

EXIT_DELAY_MS = 500
SCRIPT_DELAY_MS = 100
WINDOW_SIZE = "800x600"

class VFS:
    def __init__(self,vfs_name="VFS"):
        """Инициализирует корневой объект класса tk, имя файловой системы и список разрешенных команд."""
        self.root = tk.Tk()
        self.name = vfs_name
        self.allowed_commands = ['ls','cd']
        self.args = None
        self.storage = VFSStorage()
        self.allowed_commands = ['ls', 'cd', 'vfs-save']
        self.handlers = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'rev': self.cmd_rev,
            'date': self.cmd_date,
            'vfs-save': self.cmd_vfs_save,
        }

    def execute_command(self, command):
        """Разбирает команду и передаёт её обработчику."""
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

    def cmd_vfs_save(self, args):
        if not args:
            self.terminal_entry("vfs-save: укажите путь для сохранения\n")
            return False
        path = args[0]
        try:
            self.storage.save(path)
            self.terminal_entry(f"VFS сохранена в {path}\n")
            return True
        except OSError as e:
            self.terminal_entry(f"vfs-save: ошибка записи: {e}\n")
            return False

    def setup_ui(self):
        """Настраивает окно, создает объекты поля вывода и поля ввода, размещает поля, привязывает передачу текста из поля ввода в функцию on_enter по нажатию Enter и устанавливает курсор на поле ввода."""
        self.root.title(self.name)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        self.output = tk.Text(self.root, bg="white", fg="green", font=("Monospace", 12),
                 state="disabled", wrap="word")

        self.entry = tk.Entry(self.root, font=("Monospace", 12))

        self.output.pack(side="top", fill="both", expand=True)
        self.entry.pack(side="bottom", fill="x")
        self.entry.bind("<Return>",self.on_enter)
        self.entry.focus_set()

    def terminal_entry(self, text):
        """Разрешает запись в поле вывода, вставляет текст в конец, запрещает запись и прокручивает текст в конец."""
        self.output.config(state="normal")
        self.output.insert("end", text)
        self.output.config(state="disabled")
        self.output.see("end")

    def on_enter(self, event):
        """Обрабатывает ввод команды: пропускает пустой ввод, разделяет команду по пробелам, получает имя и аргументы, дублирует введенную команду в терминал, обрабатывает команду exit, разрешенные команды и выводит ошибку для неизвестной команды."""
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        self.execute_command(command)
    
        

    def execute_command(self,command):
        """Основная логика обработки команды. Используется и для ручного ввода, и для скрипта."""
        if not command:
            return True

        parts = command.split()
        name, args = parts[0], parts[1:]

        self.terminal_entry(f"$ {command}\n")

        if name == "exit":
            self.terminal_entry("Exiting...\n")
            self.root.after(EXIT_DELAY_MS, self.root.destroy)
            return True

        if name in self.allowed_commands:
            self.terminal_entry(f"[zaglushka] {name} {' '.join(args)}\n")
            return True
        else:
            self.terminal_entry(f"{name}: command not found\n")
            return False

    def run_script(self,path):
        """Выполняет команды из файла. Останавливается при первой ошибке."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.terminal_entry(f"Ошибка: файл скрипта не найден: {path}\n")
            return

        for line_num, line in enumerate(lines, 1):
            command = line.strip()
            if not command or command.startswith('#'):   
                continue

            ok = self.execute_command(command)
            if not ok:
                self.terminal_entry(f"\n!!! Ошибка в скрипте на строке {line_num}. Выполнение остановлено.\n")
                return

    
    def run(self):
        """Функция, которая запускает программу."""
        self.root.mainloop()

    def args_parser(self):
        """Парсинг аргументов."""
        parser = ap.ArgumentParser(description="Эмулятор VFS")
        parser.add_argument("--vfs-path", help="Путь к физическому расположению VFS")
        parser.add_argument("--script", help="Путь к стартовому скрипту")
        self.args = parser.parse_args()

    def cmd_ls(self, args):
        """Выводит содержимое каталога VFS."""
        target = self.storage.cwd
        if args:
            target = normalize_path(args[0], self.storage.cwd)
        node = self.storage.nodes.get(target)
        if node is None:
            self.terminal_entry(
                f"ls: cannot access '{args[0]}': "
                "No such file or directory\n"
            )
            return False
        if node['type'] == 'file':
            self.terminal_entry(target.rsplit('/', 1)[-1] + '\n')
            return True
        names = sorted(
            p.rsplit('/', 1)[-1]
            for p in self.storage.nodes
            if parent_of(p) == target
        )
        self.terminal_entry('  '.join(names) + '\n')
        return True

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
            vfs_message = f"VFS загружена из {my_vfs.args.vfs_path}: узлов={count}"
        except VFSError as e:
            vfs_message = f"ОШИБКА загрузки VFS: {e}"
        print(vfs_message)

    my_vfs.setup_ui()

    if vfs_message:
        my_vfs.terminal_entry(vfs_message + "\n")

    if my_vfs.args.script:
        my_vfs.root.after(SCRIPT_DELAY_MS, my_vfs.run_script, my_vfs.args.script)

    my_vfs.run()