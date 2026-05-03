# crash3_infiniti_export_with_tex.py
# Экспорт матрицы жесткости и матрицы энергий Infiniti в XeLaTeX
#
# Требования:
#   pip install numpy matplotlib
#
# Выход в папку:
#   crash3_out/

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
import matplotlib.pyplot as plt


# -----------------------------
# Исходные данные
# -----------------------------

GRID = 0.125  # м (как в тестах NHTSA)

M_INFINITI = 2870.0  # кг

# A и B из краш-теста Armada/QX80
A = 1.614e5   # N/m
B = 2.194e6   # N/m^2

# Если вы хотите учитывать порог c0, включите флаг
USE_C0 = False
C0 = 0.074  # м


# -----------------------------
# Последняя исправленная матрица глубин смятия Infiniti QX80, м
# 11 x 16
# -----------------------------

C_INF: List[List[float]] = [
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.55, 0.49, 0.48, 0.47, 0.42, 0.34, 0.18, 0.15, 0.09, 0.07, 0.05, 0.04, 0.03, 0.00, 0.00, 0.00],
    [0.50, 0.48, 0.47, 0.41, 0.30, 0.24, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.05, 0.00, 0.00, 0.00],
    [0.47, 0.47, 0.46, 0.26, 0.26, 0.20, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.00, 0.00, 0.00, 0.00],
    [0.38, 0.38, 0.18, 0.18, 0.26, 0.24, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.00, 0.00, 0.00, 0.00],
    [0.01, 0.27, 0.18, 0.27, 0.24, 0.2, 0.10, 0.05, 0.05, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.10, 0.20, 0.18, 0.15, 0.15, 0.05, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.05, 0.07, 0.02, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.07, 0.02, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
]


# -----------------------------
# Матрица относительных коэффициентов жёсткости k_ij
# 11 x 16
# -----------------------------

K_REL: List[List[float]] = [
    [ 0.000,  0.000,  0.000,  0.000,   0.000,  0.000,  0.000,  0.000,  0.000,  0.000,  0.000,   0.000,  0.000,  0.000,  0.000,  0.000],
      [ 0.171,  0.111,  0.224,  0.264,   0.453,  0.385,  0.233,  0.318,  0.226,  0.221,  0.312,   0.420,  0.344,  0.273,  0.296,  0.254],
      [ 1.025,  0.862,  0.190,  0.289,   0.377,  0.407,  0.586,  0.914,  0.353,  0.609,  0.442,   0.361,  0.284,  0.223,  0.678,  1.146],
      [ 0.287,  0.573,  0.337,  0.297,   0.403,  0.275,  0.425,  0.792,  0.724,  0.423,  0.401,   0.801,  1.117,  0.510,  0.436,  0.423],
      [ 0.936,  0.355,  0.285,  0.505,   0.634,  0.271,  0.873,  1.617,  1.022,  0.281,  0.385,   0.714,  0.827,  0.335,  0.449,  0.351],
      [ 0.292,  0.263,  0.273,  1.131,   0.777,  0.934,  2.087,  5.595,  1.317,  0.750,  0.829,   0.425,  0.984,  0.222,  0.245,  0.167],
      [ 0.276,  0.222,  0.279,  0.929,   4.873,  0.938,  1.059,  2.326,  1.292,  0.372,  1.158,   2.762,  1.418,  0.248,  0.179,  0.237],
      [ 0.410,  1.300,  0.271,  1.380,  15.599,  1.728,  1.494,  1.405,  1.016,  2.038,  1.665,  14.456,  9.341,  0.241,  0.295,  0.639],
      [ 0.224,  0.258,  0.302,  1.433,   6.672,  1.879,  2.421,  1.257,  1.369,  1.917,  2.193,   5.558,  1.632,  0.281,  0.342,  0.305],
      [ 0.194,  0.229,  0.294,  0.313,   0.440,  0.504,  0.562,  0.561,  0.458,  0.429,  0.372,   0.322,  0.270,  0.261,  0.298,  0.294],
      [ 0.318,  0.222,  0.299,  0.400,   0.479,  0.483,  0.517,  0.512,  0.582,  0.473,  0.453,   0.467,  0.379,  0.396,  0.373,  0.355],
]


# -----------------------------
# Проверка размеров
# -----------------------------

def validate_shapes(c: Sequence[Sequence[float]], k: Sequence[Sequence[float]]) -> Tuple[int, int]:
    c_rows = len(c)
    c_cols = len(c[0]) if c_rows else 0
    k_rows = len(k)
    k_cols = len(k[0]) if k_rows else 0
    if c_rows != k_rows or c_cols != k_cols:
        raise ValueError(f"Несовпадение размеров матриц: c={c_rows}x{c_cols}, k={k_rows}x{k_cols}")
    return c_rows, c_cols


# -----------------------------
# Модель энергии по ячейкам
# -----------------------------

def effective_crush(c: float) -> float:
    if not USE_C0:
        return c
    return max(0.0, c - C0)


def cell_energy(c: float, k: float, dx: float) -> float:
    """
    Без усреднений: расчёт строго по значениям c_ij и k_ij.
    Локальная энергия:
        E_ij = k_ij * dx * (A*c + 0.5*B*c^2)
    """
    ce = effective_crush(c)
    if ce <= 0.0 or k <= 0.0:
        return 0.0
    return k * dx * (A * ce + 0.5 * B * ce * ce)


def build_energy_matrix(c_mat, k_mat, dx: float) -> np.ndarray:
    rows, cols = validate_shapes(c_mat, k_mat)
    E = np.zeros((rows, cols), dtype=float)
    for i in range(rows):
        for j in range(cols):
            E[i, j] = cell_energy(float(c_mat[i][j]), float(k_mat[i][j]), dx)
    return E


def ees_from_energy(E_total: float, m: float) -> float:
    return math.sqrt(max(0.0, 2.0 * E_total / m))


# -----------------------------
# XeLaTeX-экспорт
# -----------------------------

def _matrix_to_xelatex(
    M,
    caption: str,
    label: str,
    fmt: str = "{:.3f}",
    row_header: str = "ряд\\textbackslash столбец",
):
    """
    Формирует XeLaTeX-таблицу для матрицы M (list или np.ndarray).
    Никаких преобразований данных, только форматирование.
    """
    # Приводим к обычному списку списков
    if hasattr(M, "tolist"):
        data = M.tolist()
    else:
        data = [list(r) for r in M]

    n_rows = len(data)
    n_cols = len(data[0]) if n_rows else 0

    # Заголовки столбцов 1..n_cols
    col_nums = [str(i) for i in range(1, n_cols + 1)]

    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering")
    lines.append(r"\footnotesize")
    lines.append(r"\caption{" + caption + r"}")
    lines.append(r"\begin{tabular}{c|" + "c" * n_cols + r"}")
    lines.append(r"\hline")
    lines.append(row_header + " & " + " & ".join(col_nums) + r" \\")
    lines.append(r"\hline")

    # Строки матрицы
    for i, row in enumerate(data, start=1):
        formatted = []
        for v in row:
            try:
                formatted.append(fmt.format(float(v)))
            except Exception:
                formatted.append(str(v))
        lines.append(str(i) + " & " + " & ".join(formatted) + r" \\")
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    if label:
        lines.append(r"\label{" + label + r"}")
    lines.append(r"\end{table}")

    return "\n".join(lines) + "\n"


def save_matrix_xelatex(
    M,
    out_path: str | Path,
    caption: str,
    label: str,
    fmt: str = "{:.3f}",
    row_header: str = "ряд\\textbackslash столбец",
):
    """
    Сохраняет матрицу в файл .tex в виде таблицы.
    """
    tex = _matrix_to_xelatex(
        M=M,
        caption=caption,
        label=label,
        fmt=fmt,
        row_header=row_header,
    )
    Path(out_path).write_text(tex, encoding="utf-8")


# -----------------------------
# Тепловые карты
# -----------------------------

def save_heatmap(M, title: str, out_path: str | Path) -> None:
    arr = np.array(M, dtype=float)
    plt.figure()
    # Важно: 1-я строка сверху
    plt.imshow(arr, aspect="auto", origin="upper")
    plt.title(title)
    plt.xlabel("Столбец")
    plt.ylabel("Ряд")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=200)
    plt.close()


# -----------------------------
# main
# -----------------------------

def main() -> None:
    validate_shapes(C_INF, K_REL)

    # Папка вывода
    out_dir = Path(__file__).resolve().parent / "crash3_out"

    out_dir.mkdir(parents=True, exist_ok=True)

    c = np.array(C_INF, dtype=float)
    k = np.array(K_REL, dtype=float)

    # Матрица энергий по ячейкам Infiniti
    E_cells = build_energy_matrix(C_INF, K_REL, GRID)

    # Суммарная энергия и EES
    E_total = float(E_cells.sum())
    v_ees = ees_from_energy(E_total, M_INFINITI)
    v_ees_kmh = v_ees * 3.6

    print("=== Infiniti QX80: расчёт по ячейкам ===")
    print(f"GRID = {GRID:.3f} м")
    print(f"A = {A:.3e} N/m, B = {B:.3e} N/m^2")
    print(f"USE_C0 = {USE_C0}, C0 = {C0:.3f} м")
    print(f"Масса = {M_INFINITI:.1f} кг")
    print(f"Суммарная энергия деформации E = {E_total/1000.0:.2f} кДж")
    print(f"V_EES (по энергии Infiniti) = {v_ees_kmh:.2f} км/ч")

    # Тепловые карты
    save_heatmap(c, "Infiniti QX80: глубины смятия c_ij (м)", out_dir / "heatmap_crush_infiniti.png")
    save_heatmap(k, "Infiniti QX80: относительные коэффициенты жёсткости k_ij", out_dir / "heatmap_k_infiniti.png")
    save_heatmap(E_cells, "Infiniti QX80: энергии по ячейкам E_ij (Дж)", out_dir / "heatmap_energy_infiniti.png")

    # Экспорт в XeLaTeX
    save_matrix_xelatex(
        M=k,
        out_path=out_dir / "k_infiniti_matrix.tex",
        caption=r"Матрица относительных коэффициентов жёсткости $k_{ij}$ для Infiniti QX80",
        label="tab:k_infiniti",
        fmt="{:.2f}",
    )

    save_matrix_xelatex(
        M=E_cells,
        out_path=out_dir / "E_infiniti_cells_matrix.tex",
        caption=r"Матрица энергий деформации по ячейкам для Infiniti QX80",
        label="tab:E_infiniti_cells",
        fmt="{:.1f}",
    )

    print("Файлы сохранены в папку crash3_out:")
    print(" - k_infiniti_matrix.tex")
    print(" - E_infiniti_cells_matrix.tex")
    print(" - heatmap_crush_infiniti.png")
    print(" - heatmap_k_infiniti.png")
    print(" - heatmap_energy_infiniti.png")


if __name__ == "__main__":
    main()
