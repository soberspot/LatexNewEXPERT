import tkinter as tk
from tkinter import filedialog, messagebox

def load_replacements(replacements_file):
    replacements = {}
    with open(replacements_file, "r", encoding="UTF-8") as file:
        for line in file:
            parts = line.split(",")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                replacements[key] = value
    return replacements

def replace_phrases_in_file(input_file, output_file, replacements):
    with open(input_file, "r", encoding="UTF-8") as file:
        lines = file.readlines()

    with open(output_file, "w", encoding="UTF-8") as file:
        for line in lines:
            for key, value in replacements.items():
                line = line.replace(key, value)
            file.write(line)

def select_files():
    input_file = filedialog.askopenfilename(title="Выберите входной файл", filetypes=[("Текстовые файлы", "*.txt"), ("TeX файлы", "*.tex")])
    if not input_file:
        messagebox.showwarning("Предупреждение", "Входной файл не выбран.")
        return

    output_file = filedialog.asksaveasfilename(title="Выберите выходной файл", defaultextension=".tex", filetypes=[("TeX файлы", "*.tex"), ("Текстовые файлы", "*.txt")])
    if not output_file:
        messagebox.showwarning("Предупреждение", "Выходной файл не выбран.")
        return

    replacements_file = "словарь.txt"  # Путь к файлу с заменами
    replacements = load_replacements(replacements_file)
    replace_phrases_in_file(input_file, output_file, replacements)
    messagebox.showinfo("Успех", "Замены выполнены успешно.")

# Создание графического интерфейса
root = tk.Tk()
root.title("Замена словосочетаний")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

select_button = tk.Button(frame, text="Выбрать файлы", command=select_files)
select_button.pack(pady=10)

root.mainloop()
