import xml.etree.ElementTree as ET
import zipfile
from tkinter import filedialog
import tkinter as tk


def replace_lines(input_file, dictionary_file, output_file):
    # Считываем словарь
    dictionary = {}
    with open(dictionary_file, 'r', encoding="UTF-8") as dict_file:
        for line in dict_file:
            key, value = line.strip().split(':')
            dictionary[key] = value
# Заменяем строки в файле
    with open(input_file, 'r', encoding="UTF-8") as input_file, open(output_file, 'w', encoding="UTF-8") as output_file:
        for line in input_file:
            for key, value in dictionary.items():
                line = line.replace(key, value)
            output_file.write(line)

 
# создаем окно приложения
root = tk.Tk()
root.withdraw()

# открываем диалоговое окно для выбора файла .docx
file_path = filedialog.askopenfilename(filetypes=[("vxs", "*.zip")])

# если файл был выбран, выполняем конвертацию
if file_path:
    zip_path = file_path  # Замените на путь к вашему ZIP-архиву
    file_to_open = 'vxs.xml'  # Замените на имя файла, который вы хотите открыть


with zipfile.ZipFile(zip_path, 'r') as zip_file:
    for file_info in zip_file.infolist():
        if file_info.filename.count('/') == 3:  # Замените на нужный уровень вложенности
            if file_info.filename.endswith(file_to_open):
                with zip_file.open(file_info) as file:
                    xml_string = file.read().decode('utf-8')  # Чтение содержимого файла в формате UTF-8
                break

# with zipfile.ZipFile(zip_path, 'r') as zip_file:
#     with zip_file.open(file_to_open) as file:
        # content = file.read().decode('utf-8')  # Чтение содержимого файла в формате UTF-8

# with open("vxs.xml", "r", encoding="UTF-8") as f:
#     xml_string = f.read()

root = ET.fromstring(xml_string)
namespace = {"ns2": "http://www.dat.de/vxs"}

print("Таблица ремонтных воздействий")
with open("Ремонтные воздействия.txt", "w", encoding="UTF-8") as ff:
    for dossier in root.findall(".//ns2:RepairPosition", namespace):
        repear_type = dossier.find("ns2:RepairType", namespace).text
        parts_name = dossier.find("ns2:Description", namespace).text
        if repear_type == "replace":
            print("Заменить " + parts_name)
            ff.write("Заменить " + parts_name + "\n")
        if repear_type == "lacquer":
            print("Окрасить " + parts_name)
            ff.write("Окрасить " + parts_name + "\n")
        if repear_type == "repeare":
            print("Ремонтировать " + parts_name)
            ff.write("Ремонтировать " + parts_name + "\n")

print("Перечень заменяемых деталей: n")
with open("Перечень заменяемых деталей.txt", "w", encoding="UTF-8") as ff:
    for dossier in root.findall(".//ns2:MaterialPosition", namespace):
        part_namber = dossier.find("ns2:DATPartNumber", namespace).text
        parts_name = dossier.find("ns2:Description", namespace).text
        # print("Деталь:   " + parts_name.ljust(35) + " Артикул:   " + part_namber)
        print(parts_name.ljust(35) + "  " + part_namber)
        ff.write(parts_name.ljust(35) + "  " + part_namber + "\n")

# Пример использования
# replace_lines('деталь.txt', 'словарь.txt', 'output.txt')