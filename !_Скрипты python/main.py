from datetime import datetime
import tkinter as tk
from tkinter import messagebox

def calculate_date_difference():
    try:
        # получаем значения из полей ввода
        date1 = entry1.get()
        date2 = entry2.get()

        # преобразуем строки в объекты datetime
        # date1_obj = datetime.strptime(date1, '%Y-%m-%d')
        # date2_obj = datetime.strptime(date2, '%Y-%m-%d')

        date1_obj = datetime.strptime(date1, '%d.%m.%Y')
        date2_obj = datetime.strptime(date2, '%d.%m.%Y')

        # вычисляем разницу между датами
        delta = date2_obj - date1_obj

        # вычисляем количество лет
        years = delta.days // 365

        # вычисляем количество месяцев+
        months = (delta.days % 365) // 30

        # вычисляем количество дней
        days = (delta.days % 365) % 30

        # выводим результат в поле вывода
        result_label.configure(text=f'{years} год(а)/лет, {months} месяц(ев)/месяцев, {days} день/дней')

    except ValueError:
        messagebox.showerror("Ошибка", "Некорректный формат даты. Используйте дд.мм.гггг")

# создаем окно
window = tk.Tk()
window.title("Разница между датами")

# добавляем поля для ввода дат
label1 = tk.Label(window, text="Введите дату 1 (дд.мм.гггг):")
label1.pack()
entry1 = tk.Entry(window)
entry1.pack()

label2 = tk.Label(window, text="Введите дату 2 (дд.мм.гггг:")
label2.pack()
entry2 = tk.Entry(window)
entry2.pack()

# добавляем кнопку для расчета разницы
button = tk.Button(window, text="Рассчитать", command=calculate_date_difference)
button.pack()

# добавляем поле вывода результата
result_label = tk.Label(window, text="")
result_label.pack()

window.mainloop()