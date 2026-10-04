import tkinter as tk
from time import sleep

class VFS:
    def __init__(self,vfs_name="VFS"):
        self.root = tk.Tk() # корневой объект класса tk
        self.name = vfs_name
        self.allowed_commands = ['ls','cd']

    def setup_ui(self):
        # настройка окна
        self.root.title(self.name)
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.output = tk.Text(self.root, bg="white", fg="green", font=("Monospace", 12),
                 state="disabled", wrap="word") # объект поля вывода

        self.entry = tk.Entry(self.root, font=("Monospace", 12)) # объект поля вывода

        self.output.pack(side="top", fill="both", expand=True) # размещаем поля
        self.entry.pack(side="bottom", fill="x")
        self.entry.bind("<Return>",self.on_enter) # передаем текст из поля ввода в функцию on_enter по нажатию enter
        self.entry.focus_set() # устанавливаем курсор на поле ввода

    def terminal_entry(self, text):
        self.output.config(state="normal") # разрешаем запись
        self.output.insert("end", text) # пишем текст в конец
        self.output.config(state="disabled") # запрещаем запись
        self.output.see("end") # прокручиваем текст в конец

    def on_enter(self, event):
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
    
        if not command: # если пользователь ввел пу
            return
        parts = command.split() # разделение введенной команды по пробелам
        name, args = parts[0], parts[1:] # получение в разные переменные имени команды и аргументов
    
        self.terminal_entry(f"$ {command}\n") # дублирование в терминал введенной команды
        if command == "exit": # обработка команды exit
            self.terminal_entry("Exiting...\n")
            self.root.after(500, self.root.destroy) 
            return
        print(name)
        print(args)
        if name != None and name in self.allowed_commands: # обработка команд
            self.terminal_entry(f"[zaglushka] {name} {' '.join(args)}\n") # заглушка для реализаций команды
        else:
            self.terminal_entry(f"{name}: command not found\n") # вывод ошибки если такой команды нет
    
    def run(self): # функция которая запускает программу
        self.root.mainloop()


my_vfs = VFS()

my_vfs.setup_ui()

if __name__ == "__main__":
    my_vfs.run()