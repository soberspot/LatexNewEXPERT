import csv
from tkinter import filedialog
import tkinter as tk

# создаем окно приложения
root = tk.Tk()
root.withdraw()

# открываем диалоговое окно для выбора файла .csv
file_path = filedialog.askopenfilename(filetypes=[("Таблица", "*.csv")])

# если файл был выбран, выполняем конвертацию
if file_path:
    # Открытие файла csv и чтение данных
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    # Открытие файла LaTeX для записи
    with open("latex_table.tex", "w", encoding="utf-8") as f:
        # Начало окружения tabular
        f.write("\\begin{longtable}{"+ '\n')
        f.write("\\caption[]{\\footnotesize{Наименование таблицы}}"+ '\n')
        f.write("\\label{tb: }" + '\n')
        f.write("\\hline\n")
        
        # Определение выравнивания столбцов по центру
        if rows:
            f.write("|" + "|".join(["l"] * len(rows[0])) + "|")
        f.write("}\n")

        # Перебор строк таблицы
        for i, row in enumerate(rows):
            cleaned_row = [cell.replace(';', '&') for cell in row]
            # Запись значений строк
            f.write("\\Rownum ")
            # Запись значений ячеек через &
            # f.write(" & ".join(row))
            f.write(" & ".join(cleaned_row))
            # Запись \\ для перехода на новую строку
            f.write(" \\\\\n")
            # Запись \hline для рисования горизонтальной линии
            f.write("\\hline\n")

        # Конец окружения tabular
        f.write("\\end{longtable}")

    print("Конвертация завершена")
else:
    print("Файл не выбран.")
