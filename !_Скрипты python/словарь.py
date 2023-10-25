# # Открываем файл со словарём
# with open('словарь.txt','r', encoding="UTF-8") as f:
# #
#     dictionary = dict(line.strip().split(',') for line in f)

# Открываем файл с исходным текстом
with open('деталь.txt', 'r', encoding="UTF-8") as f:
    text = f.read()

# Заменяем строки в тексте согласно словарю
# for string, replacement in dictionary.items():
#     text = text.replace(string, replacement)

# Сохраняем изменённый текст в новый файл
with open('output.txt', 'w') as f:
    f.write(text)
import csv

filename = 'словарь.txt'  # Замените на имя вашего файла

with open(filename, 'r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=':')
    dictionary = {row[0].strip(): row[1].strip() for row in reader}

print(dictionary)

# Открываем файл с исходным текстом
with open('деталь.txt', 'r', encoding="UTF-8") as f:
    text = f.read()

# # Заменяем строки в тексте согласно словарю
# for string, replacement in dictionary.items():
#     text = text.replace(string, replacement)

value = dictionary['БОКОВИНА ОКНО СТЕКЛО Л.']  # Accessing value by key
print(value)  # Output: 'Стекло левой боковины'
dictionary['НОВАЯ ЗАПИСЬ'] = 'Значение новой записи'  # Adding a new entry
dictionary['БОКОВИНА ОКНО СТЕКЛО Л.'] = 'Новое значение'  # Updating an existing entry
del dictionary['БОКОВИНА ОКНО СТЕКЛО Л.']  # Deleting an entry
for key, value in dictionary.items():
    print(key, ':', value)
if 'БОКОВИНА ОКНО СТЕКЛО Л.' in dictionary:
    print("Key exists")

keys = list(dictionary.keys())
values = list(dictionary.values())
print("Keys:", keys)
print("Values:", values)
dictionary.clear()
output_filename = 'output.csv'  # Specify the output file name
with open(output_filename, 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file, delimiter=':')
    for key, value in dictionary.items():
        writer.writerow([key, value])

# Сохраняем изменённый текст в новый файл
with open('output.txt', 'w') as f:
    f.write(text)


