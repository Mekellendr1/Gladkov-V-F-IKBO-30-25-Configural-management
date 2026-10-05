import tkinter as tk
import argparse as ap

class VFS:
    def __init__(self,vfs_name="VFS"):
        """Инициализирует корневой объект класса tk, имя файловой системы и список разрешенных команд."""
        self.root = tk.Tk()
        self.name = vfs_name
        self.allowed_commands = ['ls','cd']
        self.args = None

    def setup_ui(self):
        """Настраивает окно, создает объекты поля вывода и поля ввода, размещает поля, привязывает передачу текста из поля ввода в функцию on_enter по нажатию Enter и устанавливает курсор на поле ввода."""
        self.root.title(self.name)
        self.root.geometry("800x600")
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
            self.root.after(500, self.root.destroy)
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




if __name__ == "__main__":
    my_vfs = VFS()

    my_vfs.args_parser()

    print("=== Отладочный вывод параметров ===")
    print(f"Путь к VFS: {my_vfs.args.vfs_path}")
    print(f"Путь к скрипту: {my_vfs.args.script}")
    print("===================================")
    if my_vfs.args.script:
        my_vfs.root.after(100, lambda: my_vfs.run_script(my_vfs.args.script))
    my_vfs.setup_ui()
    my_vfs.run()