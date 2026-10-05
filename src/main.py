import tkinter as tk
from time import sleep

class VFS:
    def __init__(self,vfs_name="VFS"):
        """Инициализирует корневой объект класса tk, имя файловой системы и список разрешенных команд."""
        self.root = tk.Tk()
        self.name = vfs_name
        self.allowed_commands = ['ls','cd']

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
    
        if not command:
            return
        parts = command.split()
        name, args = parts[0], parts[1:]
    
        self.terminal_entry(f"$ {command}\n")
        if command == "exit":
            self.terminal_entry("Exiting...\n")
            self.root.after(500, self.root.destroy) 
            return
        print(name)
        print(args)
        if name != None and name in self.allowed_commands:
            self.terminal_entry(f"[zaglushka] {name} {' '.join(args)}\n")
        else:
            self.terminal_entry(f"{name}: command not found\n")
    
    def run(self):
        """Функция, которая запускает программу."""
        self.root.mainloop()


my_vfs = VFS()

my_vfs.setup_ui()

if __name__ == "__main__":
    my_vfs.run()