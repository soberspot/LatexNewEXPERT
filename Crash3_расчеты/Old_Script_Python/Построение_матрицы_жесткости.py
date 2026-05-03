import re
import zipfile
import numpy as np

zf = zipfile.ZipFile("v10562.zip")
ev5 = zf.read("v10562.EV5").decode("latin1", errors="ignore").splitlines()

bar = {}  # (row, col) -> channel_id

for ln in ev5:
    if "BARRIER" not in ln:
        continue

    parts = ln.split("|")
    if len(parts) < 9:
        continue

    ch_id = int(parts[1])
    axis = parts[5]   # XG / YG / ZG
    unit = parts[7]   # NWT / NWM ...

    if axis != "XG" or unit != "NWT":
        continue

    m = re.search(r'BARRIER\s+(\d+)-(\d+)', ln)
    if not m:
        continue

    r, c = int(m.group(1)), int(m.group(2))
    bar[(r, c)] = ch_id

def read_channel(ch):
    name = f"v10562.{ch:03d}"
    rows = zf.read(name).decode("latin1", errors="ignore").splitlines()
    vals = []
    for row in rows:
        p = re.split(r'[\t, ]+', row.strip())
        if len(p) >= 2:
            vals.append(float(p[1]))
    return np.array(vals)

Fpeak = {}
for (r, c), ch in bar.items():
    v = read_channel(ch)
    Fpeak[(r, c)] = np.max(np.abs(v)) if v.size else 0.0

# Выбор эталона нормализации
vals = np.array([x for x in Fpeak.values() if x > 0])
Fref = np.mean(vals)  # либо median, либо geometric mean

k = np.zeros((11, 16))
for r in range(2, 12):
    for c in range(1, 17):
        fp = Fpeak.get((r, c), 0.0)
        k[r-1, c-1] = fp / Fref if fp > 0 else 0.0

# ЗАПИСЬ РЕЗУЛЬТАТОВ В ФАЙЛ
output_filename = "normalized_amplitudes.txt"

with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(f"Нормализованные амплитуды вибрации\n")
    f.write(f"Эталонное значение Fref = {Fref:.6f}\n")
    f.write(f"Формат: строка 2-12 -> индексы 0-10, столбец 1-16 -> индексы 0-15\n")
    f.write(f"Всего измерений: {len(Fpeak)}, ненулевых: {len(vals)}\n")
    f.write("=" * 60 + "\n\n")
    
    f.write("Матрица нормализованных амплитуд k[11,16]:\n")
    f.write("Столбцы: 1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16\n")
    f.write("-" * 75 + "\n")
    
    for i in range(11):
        # Номер строки в исходных данных (2-12)
        row_num = i + 2
        f.write(f"Строка {row_num:2d}: ")
        
        for j in range(16):
            value = k[i, j]
            # Форматирование: 3 знака после запятой
            if value == 0:
                f.write("  0.000  ")
            else:
                f.write(f"{value:7.3f} ")
        
        # Добавляем статистику по строке
        row_vals = k[i, :]
        non_zero = row_vals[row_vals > 0]
        if len(non_zero) > 0:
            f.write(f"  | ср={np.mean(non_zero):.3f}")
        f.write("\n")

    f.write("\n" + "=" * 60 + "\n")
    f.write("Сводная статистика:\n")
    f.write(f"Минимальное значение: {np.min(k[k>0]):.4f}\n")
    f.write(f"Максимальное значение: {np.max(k):.4f}\n")
    f.write(f"Среднее значение (ненулевых): {np.mean(k[k>0]):.4f}\n")
    f.write(f"Медиана (ненулевых): {np.median(k[k>0]):.4f}\n")
    f.write(f"Стандартное отклонение: {np.std(k[k>0]):.4f}\n")

# Также можно сохранить в формате CSV для удобства импорта
csv_filename = "normalized_amplitudes.csv"
np.savetxt(csv_filename, k, delimiter=',', fmt='%.6f', 
           header='Нормализованные амплитуды вибрации (строка 2-12, столбец 1-16)')

print(f"Результаты сохранены в файлы:")
print(f"1. {output_filename} - форматированный текстовый отчет")
print(f"2. {csv_filename} - данные в формате CSV для импорта")
print(f"\nСоздана матрица размером {k.shape[0]}x{k.shape[1]}")
print(f"Ненулевых элементов: {np.count_nonzero(k)}")
print(f"Эталонное значение: {Fref:.6f}")

# Закрытие zip-файла
zf.close()