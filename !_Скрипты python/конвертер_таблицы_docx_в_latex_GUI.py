import docx
from tkinter import filedialog
import tkinter as tk

# создаем окно приложения
root = tk.Tk()
root.withdraw()

# открываем диалоговое окно для выбора файла .docx
file_path = filedialog.askopenfilename(filetypes=[("Таблица", "*.docx")])

# если файл был выбран, выполняем конвертацию
if file_path:
# Открытие файла docx с таблицей
    doc = docx.Document(file_path)
# Получение первой таблицы из документа
    table = doc.tables[0]
# Открытие файла latex для записи
with open("latex_table.tex", "w", encoding="utf-8") as f:
    # Начало окружения tabular
    f.write("\\begin{longtable}{"+ '\n')
    f.write("\\caption[]{\footnotesize {Наименование таблицы}}" + '\n')
    f.write("\\label{tb: }\\" + '\n')
    f.write("\\hline\n")
    # Определение выравнивания столбцов по центру
    f.write("|".join(["l"] * len(table.columns)))
    f.write("}\n")
    # Перебор строк таблицы
    for i, row in enumerate(table.rows):
         # Запись значений счетчика строк, начиная с 1
        f.write("\Rownum ")
        # Запись значений ячеек через &
        f.write("& ".join([cell.text for cell in row.cells]))
        # Запись \\ для перехода на новую строку
        f.write(" \\\\\n")
        # Запись \hline для рисования горизонтальной линии
        f.write("\\hline\n")
    # Конец окружения tabular
    f.write("\\end{longtable}")

print("Конвертация завершена")
    # else:
# print("Файл не выбран.")