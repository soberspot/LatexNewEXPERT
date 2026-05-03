#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crash3_infiniti_energy.py

Расчёт энергии деформации Infiniti QX80 по методике CRASH3
с использованием матрицы относительных коэффициентов жёсткости k_ij,
полученных из барьерного испытания NHTSA V10562 (Nissan Armada / Infiniti QX80),
и матрицы глубин смятия c_ij, измеренной для рассматриваемого ДТП.

Скрипт:
  * считает распределение энергии по ячейкам фронта;
  * суммирует энергию деформации;
  * вычисляет эквивалентную скорость удара о жёсткий барьер (EES);
  * экспортирует матрицы c_ij, k_ij и E_ij в виде XeLaTeX-таблиц в папку crash3_out.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import matplotlib.pyplot as plt


# ------------------------------
# 1. Глобальные параметры CRASH3
# ------------------------------

# Параметры A, B и c0 для Infiniti (по результатам обработки теста V10562)
A_GLOBAL = 1.614e5      # Н/м
B_GLOBAL = 2.194e6      # Н/м^2
C0 = 0.074              # м, пороговая деформация (смещение начала силовой характеристики)
CELL_WIDTH = 0.125      # м, ширина одной ячейки фронта по методу CRASH3

# Масса автомобиля
M_INFINITI_TEST = 2778.0   # кг, масса в краш-тесте (V10562)
M_INFINITI_FACT = 2870.0   # кг, ориентировочная масса автомобиля в ДТП


# -----------------------------------
# 2. Матрицы глубин смятия и жёсткости
# -----------------------------------

# Матрица глубин смятия c_ij (Infiniti QX80) — финальная, уточнённая
C_INF = np.array([
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.47, 0.47, 0.47, 0.47, 0.32, 0.22, 0.10, 0.18, 0.10, 0.10, 0.05, 0.05, 0.05, 0.03, 0.00, 0.00],
    [0.47, 0.47, 0.47, 0.39, 0.32, 0.32, 0.18, 0.18, 0.10, 0.10, 0.05, 0.05, 0.05, 0.03, 0.00, 0.00],
    [0.47, 0.47, 0.47, 0.39, 0.32, 0.32, 0.18, 0.18, 0.10, 0.10, 0.05, 0.05, 0.05, 0.03, 0.00, 0.00],
    [0.38, 0.38, 0.38, 0.33, 0.32, 0.32, 0.18, 0.18, 0.10, 0.10, 0.05, 0.05, 0.05, 0.03, 0.00, 0.00],
    [0.00, 0.27, 0.27, 0.27, 0.24, 0.22, 0.10, 0.05, 0.05, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.20, 0.20, 0.18, 0.15, 0.15, 0.05, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.13, 0.07, 0.07, 0.07, 0.03, 0.02, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.10, 0.05, 0.04, 0.03, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
], dtype=float)

# Матрица относительных коэффициентов жёсткости k_ij (по данным барьерного теста V10562)
K_REL = np.array([
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.01, 0.03, 0.01, 0.01, 0.23, 0.06, 0.08, 0.11, 0.18, 0.13, 0.13, 0.11, 0.16, 0.05, 0.03, 0.02],
    [0.81, 0.59, 0.10, 0.12, 0.28, 0.30, 0.24, 0.41, 0.17, 0.32, 0.24, 0.27, 0.22, 0.16, 0.42, 0.91],
    [0.18, 0.57, 0.28, 0.17, 0.30, 0.07, 0.34, 0.79, 0.54, 0.48, 0.31, 0.68, 0.58, 0.54, 0.51, 0.13],
    [0.25, 0.27, 0.11, 0.58, 0.88, 0.19, 0.54, 1.06, 1.09, 0.11, 0.12, 1.22, 1.04, 0.20, 0.16, 0.27],
    [0.21, 0.05, 0.12, 1.67, 1.09, 0.82, 1.46, 3.98, 1.46, 1.04, 0.83, 0.47, 1.40, 0.16, 0.10, 0.10],
    [0.11, 0.05, 0.02, 0.65, 2.94, 1.12, 0.78, 3.16, 1.65, 0.35, 1.25, 1.95, 0.73, 0.12, 0.07, 0.01],
    [0.54, 0.31, 0.07, 2.15, 27.86, 2.97, 3.09, 1.84, 1.34, 1.80, 2.79, 18.63, 9.25, 0.00, 0.12, 0.83],
    [0.18, 0.22, 0.27, 0.99, 4.52, 2.49, 4.89, 1.09, 0.30, 3.25, 4.56, 6.38, 2.66, 0.36, 0.45, 0.48],
    [0.11, 0.07, 0.03, 0.01, 0.01, 0.15, 0.12, 0.39, 0.28, 0.02, 0.04, 0.03, 0.02, 0.07, 0.03, 0.15],
    [0.02, 0.02, 0.01, 0.00, 0.04, 0.03, 0.02, 0.03, 0.02, 0.07, 0.03, 0.03, 0.02, 0.01, 0.01, 0.03],
], dtype=float)


# ------------------------------
# 3. Вспомогательные функции
# ------------------------------

def build_k_norm(k_rel: np.ndarray) -> np.ndarray:
    """
    Нормирует относительные коэффициенты жёсткости так,
    чтобы среднее по всем положительным k_ij было равно 1.0.
    Это обеспечивает согласование с глобальными A_GLOBAL, B_GLOBAL,
    полученными из интегрального краш-теста.
    """
    k_rel = np.asarray(k_rel, dtype=float)
    mask = k_rel > 0.0
    if not np.any(mask):
        raise ValueError("Во входной матрице k_rel нет положительных значений.")
    mean_pos = float(k_rel[mask].mean())
    k_norm = np.zeros_like(k_rel)
    k_norm[mask] = k_rel[mask] / mean_pos
    return k_norm


def crash3_energy_matrix(
    c: np.ndarray,
    k_rel: np.ndarray | None,
    A_global: float,
    B_global: float,
    c0: float,
    cell_width: float,
) -> np.ndarray:
    """
    Вычисляет матрицу энергии деформации E_ij по формуле CRASH3:
        F(c) = A_ij * (c* - c0) + B_ij * (c* - c0)^2
        E_ij = Δw * ∫_0^{c*} F(c) dc
             = Δw * [ 0.5 A_ij (c*)^2 + (1/3) B_ij (c*)^3 ],
    где c* = max(0, c_ij - c0).

    Здесь A_ij = A_global * k_ij^norm, B_ij = B_global * k_ij^norm.
    """
    c = np.asarray(c, dtype=float)
    c_eff = np.maximum(0.0, c - c0)

    if k_rel is None:
        Aij = np.full_like(c_eff, A_global)
        Bij = np.full_like(c_eff, B_global)
    else:
        k_norm = build_k_norm(np.asarray(k_rel, dtype=float))
        Aij = A_global * k_norm
        Bij = B_global * k_norm

    E = cell_width * (0.5 * Aij * c_eff**2 + (1.0 / 3.0) * Bij * c_eff**3)
    return E


def ees_from_energy(E: float, m: float) -> float:
    """
    Эквивалентная скорость удара о жёсткий барьер (EES),
    исходя из кинематического равенства:
        E = 0.5 * m * v^2  =>  v = sqrt(2E/m)
    """
    if E <= 0.0 or m <= 0.0:
        return 0.0
    return math.sqrt(2.0 * E / m)


# ------------------------------
# 4. Экспорт матриц в XeLaTeX
# ------------------------------

def _matrix_to_xelatex(
    M: Iterable[Iterable[float]],
    caption: str,
    label: str,
    fmt: str = "{:.3f}",
    row_header: str = "ряд\\textbackslash столбец",
) -> str:
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

    lines: list[str] = []
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
        formatted: list[str] = []
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
    M: Iterable[Iterable[float]],
    out_path: Path,
    caption: str,
    label: str,
    fmt: str = "{:.3f}",
    row_header: str = "ряд\\textbackslash столбец",
) -> None:
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
    out_path = Path(out_path)
    out_path.write_text(tex, encoding="utf-8")


# ------------------------------
# 5. Основная функция
# ------------------------------

def main() -> None:
    # Папка для вывода таблиц
    out_dir = Path(__file__).parent / "crash3_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 5.1. Энергия деформации Infiniti по уточнённой матрице c_ij и k_ij
    E_matrix = crash3_energy_matrix(
        c=C_INF,
        k_rel=K_REL,
        A_global=A_GLOBAL,
        B_global=B_GLOBAL,
        c0=C0,
        cell_width=CELL_WIDTH,
    )
    E_total = float(E_matrix.sum())  # Дж

    # Эквивалентные скорости (для массы тестовой и фактической)
    v_ees_test = ees_from_energy(E_total, M_INFINITI_TEST)
    v_ees_fact = ees_from_energy(E_total, M_INFINITI_FACT)

    print("=== Энергия деформации Infiniti QX80 по CRASH3 ===")
    print(f"Суммарная энергия деформации: {E_total/1000.0:8.3f} кДж")
    print(f"Эквивалентная скорость (масса {M_INFINITI_TEST:.0f} кг): "
          f"{v_ees_test*3.6:5.2f} км/ч")
    print(f"Эквивалентная скорость (масса {M_INFINITI_FACT:.0f} кг): "
          f"{v_ees_fact*3.6:5.2f} км/ч")

    # 5.2. Экспорт матриц в XeLaTeX
    save_matrix_xelatex(
        M=C_INF,
        out_path=out_dir / "cij_infiniti_m.tex",
        caption="Матрица глубин смятия $c_{ij}$ для Infiniti QX80, м",
        label="tab:cij_infiniti_m",
        fmt="{:.3f}",
    )

    save_matrix_xelatex(
        M=K_REL,
        out_path=out_dir / "kij_infiniti_rel.tex",
        caption="Относительные коэффициенты жёсткости $k_{ij}$ "
                "по данным барьерного испытания V10562",
        label="tab:kij_infiniti_rel",
        fmt="{:.2f}",
    )

    # В таблицу энергии выведем значения в кДж по ячейкам
    save_matrix_xelatex(
        M=E_matrix / 1000.0,
        out_path=out_dir / "Eij_infiniti_kJ.tex",
        caption="Распределение энергии деформации $E_{ij}$ по ячейкам фронта "
                "Infiniti QX80, кДж",
        label="tab:Eij_infiniti_kJ",
        fmt="{:.3f}",
    )

    # 5.3. Визуализация (ИСПРАВЛЕНО: перенесено внутрь main)
    # Используем стиль 'ggplot' или дефолтный, если нет предпочтений
    # plt.style.use('ggplot') 

    fig, axs = plt.subplots(1, 3, figsize=(18, 5))

    # График 1: Глубины
    im0 = axs[0].imshow(C_INF, origin='upper', cmap='viridis')
    axs[0].set_title('Глубина деформаций, м')
    fig.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)

    # График 2: Жесткости
    im1 = axs[1].imshow(K_REL, origin='upper', cmap='plasma')
    axs[1].set_title('Относительная жёсткость k_ij')
    fig.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)

    # График 3: Энергия (ИСПРАВЛЕНО: используем E_matrix)
    im2 = axs[2].imshow(E_matrix / 1000.0, origin='upper', cmap='viridis')
    axs[2].set_title('Энергия деформаций, кДж')
    fig.colorbar(im2, ax=axs[2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    print("Отображение графиков...")
    plt.show()


if __name__ == "__main__":
    main()