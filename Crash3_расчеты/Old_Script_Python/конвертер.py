import os

# Список изображений и подписей (можно загрузить из файла или базы данных)
# photos = [
#     {"file": "photo1.jpg", "caption": "Место столкновения"},
#     {"file": "photo2.jpg", "caption": "Повреждения передней части"},
#     {"file": "photo3.jpg", "caption": "Следы торможения"},
#     {"file": "photo4.jpg", "caption": "Общий вид сцены"}
# ]
# Альтернативный вариант: автоматическое сканирование папки
photos = [{"file": f, "caption": f"Фото {i+1}"} for i, f in enumerate(os.listdir()) if f.endswith(".jpg")]

# Начало LaTeX-документа
tex_content = r''

# Добавляем изображения по одному на страницу, парами вертикально
for i in range(0, len(photos), 2):  # Шаг 2, чтобы брать по два фото
    tex_content += r'\begin{figure}[p]' + '\n'  # [p] для отдельной страницы
    tex_content += r'\centering' + '\n'
    
    # Первое изображение
    tex_content += f'\\includegraphics[width=15cm,height=10cm]{{{photos[i]["file"]}}}' + '\n'
    tex_content += f'\\caption{{{photos[i]["caption"]}}}' + '\n'
    tex_content += r'\vspace{1cm}' + '\n'  # Отступ между фото
    
    # Второе изображение (если есть)
    if i + 1 < len(photos):
        tex_content += f'\\includegraphics[width=15cm,height=10cm]{{{photos[i+1]["file"]}}}' + '\n'
        tex_content += f'\\caption{{{photos[i+1]["caption"]}}}' + '\n'
    
    tex_content += r'\end{figure}' + '\n'
    tex_content += r'\clearpage' + '\n'  # Новая страница после каждой пары

# Конец документа
# tex_content += r'\end{document}'

# Записываем в файл
with open("phototable.tex", "w", encoding="utf-8") as f:
    f.write(tex_content)

# Компилируем в PDF (раскомментируй, если нужно)
# os.system("pdflatex phototable.tex")