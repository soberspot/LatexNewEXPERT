import tkinter as tk
from tkinter import filedialog
from docx import Document

def docx_to_latex(docx_file, latex_file):
    # Открываем .docx файл
    doc = Document(docx_file)

    # Открываем выходной .tex файл
    with open(latex_file, 'w', encoding='utf-8') as f:
        # Записываем преамбулу для документа LaTeX
        f.write(r'\input{preamble}' + '\n')
        f.write(r'\begin{document}' + '\n')
        f.write(r'\input{var}' + '\n')
        f.write(r'\input{data}' + '\n')
        f.write(r'\input{pereopr}' + '\n')
        f.write(r'\input{колонтитулы}' + '\n')
        f.write(r'\input{водянойзнак}' + '\n')
        f.write(r'\thispagestyle{empty}' + '\n')
        f.write(r'\include{titul/шапкаАЭИип}' + '\n\n')

        # Проходим по всем параграфам в документе
        for para in doc.paragraphs:
            text = para.text
            # Заменяем специальные символы LaTeX
            text = text.replace('&', '\\&')
            text = text.replace('%', '\\%')
            text = text.replace('$', '\\$')
            text = text.replace('#', '\\#')
            text = text.replace('_', '\\_')
            text = text.replace('{', '\\{')
            text = text.replace('}', '\\}')
            text = text.replace('~', '\\textasciitilde{}')
            text = text.replace('^', '\\textasciicircum{}')
            text = text.replace('\\', '\\textbackslash{}')
            f.write(text + '\n\n')

        f.write(r'\end{document}' + '\n')

def select_file():
    # Открываем окно выбора файла
    file_path = filedialog.askopenfilename(filetypes=[("Word files", "*.docx")])
    if file_path:
        # Открываем окно выбора места сохранения файла
        output_path = filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("LaTeX files", "*.tex")])
        if output_path:
            # Конвертируем файл
            docx_to_latex(file_path, output_path)
            print(f"Файл {output_path} успешно создан.")
             # Закрываем главное окно
        root.destroy()
# Создаем главное окно
root = tk.Tk()
root.title("Конвертер DOCX в LaTeX")
root.geometry("300x150")

# Добавляем кнопку для выбора файла
button = tk.Button(root, text="Выберите файл DOCX", command=select_file)
button.pack(expand=True)

# Запускаем главный цикл событий
root.mainloop()
