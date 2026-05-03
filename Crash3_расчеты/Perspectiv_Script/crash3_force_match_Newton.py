#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crash3_force_match_Newton.py

Реконструкция с ПОЛНЫМ СОГЛАСОВАНИЕМ СИЛ (Newton's 3rd Law Match).
Матрицы не меняются.
Для визуализации сил используется принцип "Reaction Force":
Если Infiniti бьет с силой F, КАМАЗ испытывает силу F (даже если не помялся).
"""

from __future__ import annotations

import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. ПАРАМЕТРЫ (ИСХОДНЫЕ, НЕ МЕНЯЕМ)
# ==============================================================================

# INFINITI
A_INF = 1.614e5
B_INF = 2.194e6
C0_INF = 0.074
CELL_W_INF = 0.125
M_INF_FACT = 2870.0

C_INF = np.array([
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.55, 0.49, 0.48, 0.47, 0.42, 0.34, 0.18, 0.15, 0.09, 0.07, 0.05, 0.04, 0.03, 0.00, 0.00, 0.00],
    [0.50, 0.48, 0.47, 0.41, 0.30, 0.24, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.05, 0.00, 0.00, 0.00],
    [0.47, 0.47, 0.46, 0.26, 0.26, 0.20, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.00, 0.00, 0.00, 0.00],
    [0.38, 0.38, 0.18, 0.18, 0.26, 0.24, 0.18, 0.13, 0.10, 0.10, 0.05, 0.05, 0.00, 0.00, 0.00, 0.00],
    [0.01, 0.27, 0.18, 0.27, 0.24, 0.2, 0.10, 0.05, 0.05, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.10, 0.20, 0.18, 0.15, 0.15, 0.05, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.05, 0.07, 0.02, 0.05, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.07, 0.02, 0.02, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
], dtype=float)

K_REL_INF = np.array([
      [ 0.000,  0.000,  0.000,  0.000,   0.000,  0.000,  0.000,  0.000,  0.000,  0.000,  0.000,   0.000,  0.000,  0.000,  0.000,  0.000],
      [ 0.171,  0.111,  0.224,  0.264,   0.453,  0.385,  0.233,  0.318,  0.226,  0.221,  0.312,   0.420,  0.344,  0.273,  0.296,  0.254],
      [ 1.025,  0.862,  0.190,  0.289,   0.377,  0.407,  0.586,  0.914,  0.353,  0.609,  0.442,   0.361,  0.284,  0.223,  0.678,  1.146],
      [ 0.287,  0.573,  0.337,  0.297,   0.403,  0.275,  0.425,  0.792,  0.724,  0.423,  0.401,   0.801,  1.117,  0.510,  0.436,  0.423],
      [ 0.936,  0.355,  0.285,  0.505,   0.634,  0.271,  0.873,  1.617,  1.022,  0.281,  0.385,   0.714,  0.827,  0.335,  0.449,  0.351],
      [ 0.292,  0.263,  0.273,  1.131,   0.777,  0.934,  2.087,  5.595,  1.317,  0.750,  0.829,   0.425,  0.984,  0.222,  0.245,  0.167],
      [ 0.276,  0.222,  0.279,  0.929,   4.873,  0.938,  1.059,  2.326,  1.292,  0.372,  1.158,   2.762,  1.418,  0.248,  0.179,  0.237],
      [ 0.410,  1.300,  0.271,  1.380,  15.599,  2.728,  1.494,  1.405,  1.016,  2.038,  1.665,  14.456,  9.341,  0.241,  0.295,  0.639],
      [ 0.224,  0.258,  0.302,  1.433,   6.672,  1.879,  2.421,  1.257,  1.369,  1.917,  2.193,   5.558,  1.632,  0.281,  0.342,  0.305],
      [ 0.194,  0.229,  0.294,  0.313,   0.440,  0.504,  0.562,  0.561,  0.458,  0.429,  0.372,   0.322,  0.270,  0.261,  0.298,  0.294],
      [ 0.318,  0.222,  0.299,  0.400,   0.479,  0.483,  0.517,  0.512,  0.582,  0.473,  0.453,   0.467,  0.379,  0.396,  0.373,  0.355],
], dtype=float)

# KAMAZ
A_KAMAZ = 7.50e5
B_KAMAZ = 2.50e6
C0_KAMAZ = 0.02
CELL_W_KAMAZ = 0.125

C_KAMAZ = np.array([
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.15, 0.08, 0.05, 0.03, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Верх бампера
    [0.25, 0.18, 0.13, 0.10, 0.055, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер (жестко)
    [0.33, 0.33, 0.20, 0.25, 0.050, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер
    [0.40, 0.30, 0.25, 0.20, 0.055, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Средняя поперечина
    [0.41, 0.41, 0.31, 0.01, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер + нижняя поперечина 
    [0.41, 0.41, 0.31, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Противоподкатный брус
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Низ
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.00, 0.00, 0.00, 0.00, 0.000, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
], dtype=float)

# ------------------------------------------------------------------
# МАТРИЦА ЖЕСТКОСТИ K_REL_KAMAZ (Структура Actros)
# ------------------------------------------------------------------
K_REL_KAMAZ = np.array([
    [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2], # Кабина верх
    [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
    [0.2, 0.4, 0.4, 0.4, 2.5, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
    [0.2, 0.2, 0.2, 2.0, 2.5, 0.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], # Переход
    [0.2, 0.2, 0.2, 0.2, 3.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 3.2, 0.2, 0.2, 0.2, 0.2], # БАМПЕР + РАМА
    [0.2, 0.2, 0.2, 0.2, 3.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 3.0, 0.2, 0.2, 0.2, 0.2], # БАМПЕР + РАМА
    [0.2, 0.2, 0.2, 0.2, 3.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2], # БАМПЕР + РАМА (Ряд 7)
    [2.0, 3.0, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.0, 2.0], # БАМПЕР + РАМА
    [0.2, 0.2, 0.2, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0.2, 0.2], # БАМПЕР + РАМА (Ряд 8)
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], # Противоподкатный брус (Ряд 9)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # Низ / Подвеска (Ряд 10)
], dtype=float)

# ==============================================================================
# ФУНКЦИИ РАСЧЕТА И ЭКСПОРТА
# ==============================================================================

def build_k_norm(k_rel: np.ndarray) -> np.ndarray:
    k_rel = np.asarray(k_rel, dtype=float)
    mask = k_rel > 0.0
    if not np.any(mask): return np.zeros_like(k_rel)
    mean_pos = float(k_rel[mask].mean())
    k_norm = np.zeros_like(k_rel)
    k_norm[mask] = k_rel[mask] / mean_pos
    return k_norm

def crash3_energy_matrix(c, k_rel, A_global, B_global, c0, cell_width, balance_factor=1.0):
    c = np.asarray(c, dtype=float)
    c_eff = np.maximum(0.0, c - c0)
    k_norm = build_k_norm(np.asarray(k_rel, dtype=float))
    Aij = A_global * k_norm * balance_factor
    Bij = B_global * k_norm * balance_factor
    E = cell_width * (0.5 * Aij * c_eff**2 + (1.0 / 3.0) * Bij * c_eff**3)
    return E

def crash3_force_matrix(c, k_rel, A_global, B_global, c0, cell_width, balance_factor=1.0):
    c = np.asarray(c, dtype=float)
    c_eff = np.maximum(0.0, c - c0)
    k_norm = build_k_norm(np.asarray(k_rel, dtype=float))
    Aij = A_global * k_norm * balance_factor
    Bij = B_global * k_norm * balance_factor
    F = cell_width * (Aij * c_eff + Bij * c_eff**2)
    return F

def save_matrix_to_latex(matrix, filename, caption, label):
    """
    Сохраняет numpy матрицу в файл .tex в формате таблицы LaTeX.
    """
    rows, cols = matrix.shape

    # Формируем контент для xelatex/latex
    content = []
    content.append(r"\begin{table}[h!]")
    content.append(r"\centering")
    content.append(f"\\caption{{{caption}}}")
    content.append(f"\\label{{{label}}}")
    # Используем resizebox, чтобы широкая таблица влезла на страницу
    content.append(r"\resizebox{\textwidth}{!}{")

    # Определение столбцов (например, |c|c|...|)
    col_str = "|" + "c|" * cols
    content.append(f"\\begin{{tabular}}{{{col_str}}}")
    content.append(r"\hline")

    for i in range(rows):
        # Форматируем числа: 2 знака после запятой
        row_str = " & ".join([f"{val:.2f}" for val in matrix[i]])
        content.append(row_str + r" \\ \hline")

    content.append(r"\end{tabular}")
    content.append(r"}") # закрываем resizebox
    content.append(r"\end{table}")

    # Запись в файл
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    print(f"Saved LaTeX table: {filename.name}")

def draw_profile_plot(c_inf, c_kam, width_step, out_dir):
    profile_inf = np.max(c_inf, axis=0)
    profile_kam = np.max(c_kam, axis=0)
    x_axis = np.arange(len(profile_inf)) * width_step
    plt.figure(figsize=(10, 6))
    plt.plot(x_axis, profile_inf, label='Infiniti QX80', color='blue', linewidth=3, marker='o')
    plt.plot(x_axis, profile_kam, label='КАМАЗ (Actros)', color='red', linewidth=3, marker='s', linestyle='--')
    plt.title('Профиль деформаций', fontsize=14)
    plt.xlabel('Ширина (м)')
    plt.ylabel('Глубина (м)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "damage_profile_lines.png", dpi=300)

def plot_3d_damage(c_inf, c_kam, cell_w, out_dir):
    rows, cols = c_inf.shape
    x = np.linspace(0, cols * cell_w, cols)
    y = np.linspace(rows * cell_w, 0, rows) 
    X, Y = np.meshgrid(x, y)
    fig = plt.figure(figsize=(18, 8))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.plot_surface(X, Y, c_inf, cmap='viridis', edgecolor='none', alpha=0.9)
    ax1.set_title('Infiniti: 3D Глубина')
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.plot_surface(X, Y, c_kam, cmap='viridis', edgecolor='none', alpha=0.9)
    ax2.set_title('КАМАЗ: 3D Глубина')
    plt.tight_layout()
    plt.savefig(out_dir / "damage_3d_view.png", dpi=300)

def plot_3d_energy(e_inf, e_kam, cell_w, out_dir):
    rows, cols = e_inf.shape
    x = np.linspace(0, cols * cell_w, cols)
    y = np.linspace(rows * cell_w, 0, rows)
    X, Y = np.meshgrid(x, y)
    fig = plt.figure(figsize=(18, 8))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.plot_surface(X, Y, e_inf/1000.0, cmap='magma', edgecolor='none', alpha=0.95)
    ax1.set_title('Infiniti: 3D Энергия (кДж)')
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.plot_surface(X, Y, e_kam/1000.0, cmap='inferno', edgecolor='none', alpha=0.95)
    ax2.set_title('КАМАЗ: 3D Энергия (кДж)')
    plt.tight_layout()
    plt.savefig(out_dir / "energy_3d_view.png", dpi=300)

# ==============================================================================
# MAIN
# ==============================================================================

def main() -> None:
    out_dir = Path(__file__).parent / "crash3_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("=== РЕКОНСТРУКЦИЯ С ЯЧЕЕЧНЫМ СОГЛАСОВАНИЕМ СИЛ (CELL-BY-CELL MATCH) ===\n")

    # 1. Расчеты
    E_mat_inf = crash3_energy_matrix(C_INF, K_REL_INF, A_INF, B_INF, C0_INF, CELL_W_INF)
    F_mat_inf = crash3_force_matrix(C_INF, K_REL_INF, A_INF, B_INF, C0_INF, CELL_W_INF)

    # Считаем КАМАЗ с авто-балансировкой по сумме (чтобы масштаб был верным)
    F_mat_kam_raw = crash3_force_matrix(C_KAMAZ, K_REL_KAMAZ, A_KAMAZ, B_KAMAZ, C0_KAMAZ, CELL_W_KAMAZ, balance_factor=1.0)
    F_inf_sum = F_mat_inf.sum()
    F_kam_sum = F_mat_kam_raw.sum()
    balance_factor = F_inf_sum / F_kam_sum if F_kam_sum > 0 else 1.0

    E_mat_kam = crash3_energy_matrix(C_KAMAZ, K_REL_KAMAZ, A_KAMAZ, B_KAMAZ, C0_KAMAZ, CELL_W_KAMAZ, balance_factor=balance_factor)
    # Это сила, которую сгенерировал КАМАЗ своей малой деформацией:
    F_mat_kam_generated = crash3_force_matrix(C_KAMAZ, K_REL_KAMAZ, A_KAMAZ, B_KAMAZ, C0_KAMAZ, CELL_W_KAMAZ, balance_factor=balance_factor)

    # 2. [NEW] FORCE INTERACTION LOGIC
    # --------------------------------
    # Для визуализации взаимодействия мы берем МАКСИМУМ силы в каждой ячейке.
    # Если Infiniti [5,5] давит 100 кН, а Камаз [5,5] давит 0 (потому что жесткий),
    # то РЕАЛЬНАЯ сила в точке контакта = 100 кН.

    F_interaction_map = np.maximum(F_mat_inf, F_mat_kam_generated)

    print(f"Force Sum (Infiniti Generated): {F_inf_sum/1000.0:.1f} kN")
    print(f"Force Sum (KAMAZ Generated):    {F_mat_kam_generated.sum()/1000.0:.1f} kN (Balanced Total)")
    print(f"Force Sum (Interaction/Max):    {F_interaction_map.sum()/1000.0:.1f} kN (Physically Real)")

    # Расчет скорости и EES
    E_inf_joules = float(E_mat_inf.sum())
    E_kam_joules = float(E_mat_kam.sum())
    W_disp = 0.70 * 34000.0 * 9.81 * 0.1
    E_total = E_inf_joules + E_kam_joules + W_disp
    v_impact_kmh = math.sqrt(2 * E_total / M_INF_FACT) * 3.6

    # ==========================================================================
    # СОХРАНЕНИЕ РЕЗУЛЬТАТОВ И ТАБЛИЦ
    # ==========================================================================

    # 1. Сохранение текстового отчета о подсчете энергий
    results_file = out_dir / "calculation_results.txt"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write("=== RESULT CALCULATION REPORT ===\n")
        f.write(f"Energy Infiniti (Deformation): {E_inf_joules:.2f} J\n")
        f.write(f"Energy KAMAZ (Deformation):    {E_kam_joules:.2f} J\n")
        f.write(f"Energy Displacement (W_disp):  {W_disp:.2f} J\n")
        f.write(f"----------------------------------------\n")
        f.write(f"TOTAL ENERGY (E_total):        {E_total:.2f} J\n")
        f.write(f"Impact Velocity (Calculated):  {v_impact_kmh:.2f} km/h\n")
        f.write(f"\n--- Force Balance Parameters ---\n")
        f.write(f"KAMAZ Stiffness Balance Factor: {balance_factor:.4f}\n")
    print(f"\n[OK] Результаты расчетов сохранены в: {results_file.name}")

    # 2. Сохранение таблиц в формате LaTeX (xelatex)
    # Матрицы Infiniti
    save_matrix_to_latex(C_INF, out_dir / "table_infiniti_depth.tex", 
                         "Матрица глубин деформации Infiniti (м)", "tab:inf_depth")
    save_matrix_to_latex(K_REL_INF, out_dir / "table_infiniti_stiffness.tex", 
                         "Матрица коэффициентов жесткости Infiniti", "tab:inf_stiff")
    save_matrix_to_latex(E_mat_inf, out_dir / "table_infiniti_energy.tex", 
                         "Матрица энергий деформации Infiniti (Дж)", "tab:inf_energy")

    # Матрицы KAMAZ (K_REL_KAMAZ сохраняем с учетом балансировочного фактора, т.к. это реальная жесткость в расчете)
    save_matrix_to_latex(C_KAMAZ, out_dir / "table_kamaz_depth.tex", 
                         "Матрица глубин деформации KAMAZ (м)", "tab:kam_depth")
    save_matrix_to_latex(K_REL_KAMAZ * balance_factor, out_dir / "table_kamaz_stiffness.tex", 
                         "Матрица коэффициентов жесткости KAMAZ (с балансировкой)", "tab:kam_stiff")
    save_matrix_to_latex(E_mat_kam, out_dir / "table_kamaz_energy.tex", 
                         "Матрица энергий деформации KAMAZ (Дж)", "tab:kam_energy")

    print("[OK] Таблицы LaTeX сохранены в папку crash3_out")

    # ==========================================================================
    # ВИЗУАЛИЗАЦИЯ
    # ==========================================================================
    W_REAL = 16 * 0.125
    H_REAL = 11 * 0.125

    try: plt.style.use('ggplot')
    except: pass

    fig, axs = plt.subplots(2, 4, figsize=(22, 10))
    fig.suptitle(f"Реконструкция: V_impact={v_impact_kmh:.1f} км/ч | Interaction Force Map", fontsize=16)

    def plot_map(ax, data, title, cmap, vmin=None, vmax=None):
        im = ax.imshow(data[::-1, :], origin='lower', cmap=cmap, 
                      extent=[0, W_REAL, 0, H_REAL], vmin=vmin, vmax=vmax)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Ширина, м')
        ax.set_xticks(np.arange(0, W_REAL + 0.01, 0.5))
        ax.set_yticks(np.arange(0, H_REAL + 0.01, 0.5))
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        return im

    # Определяем общий масштаб для силы, чтобы цвета совпадали
    f_max_val = F_interaction_map.max() / 1000.0

    # Ряд 1: Infiniti
    plot_map(axs[0,0], C_INF, 'Infiniti: Глубина (м)', 'Blues', vmin=0, vmax=0.6)
    plot_map(axs[0,1], K_REL_INF, 'Infiniti: Жесткость', 'Greys')
    plot_map(axs[0,2], E_mat_inf/1000.0, 'Infiniti: Энергия (кДж)', 'hot')

    # [NEW] Рисуем F_interaction_map (Сила, которую испытывает Infiniti в контакте)
    plot_map(axs[0,3], F_interaction_map/1000.0, 'Infiniti: СИЛА КОНТАКТА (кН)', 'Reds', vmin=0, vmax=f_max_val)

    # Ряд 2: КАМАЗ
    plot_map(axs[1,0], C_KAMAZ, 'KAMAZ: Глубина (м)', 'Blues', vmin=0, vmax=0.6)
    plot_map(axs[1,1], K_REL_KAMAZ * balance_factor, f'KAMAZ: Жесткость (Corrected x{balance_factor:.1f})', 'Greys')
    plot_map(axs[1,2], E_mat_kam/1000.0, 'KAMAZ: Энергия (кДж)', 'hot')

    # [NEW] Рисуем ТУ ЖЕ F_interaction_map (Сила реакции, действующая на КАМАЗ)
    # Это визуализирует 3-й закон Ньютона: карта сил зеркально идентична (по модулю)
    plot_map(axs[1,3], F_interaction_map/1000.0, 'KAMAZ: СИЛА РЕАКЦИИ (кН)', 'Reds', vmin=0, vmax=f_max_val)

    plt.tight_layout()
    plt.savefig(out_dir / "reconstruction_matched_force.png", dpi=300)
    print(f"\n[OK] График сохранен: reconstruction_matched_force.png")

    draw_profile_plot(C_INF, C_KAMAZ, CELL_W_INF, out_dir)
    plot_3d_damage(C_INF, C_KAMAZ, CELL_W_INF, out_dir)
    plot_3d_energy(E_mat_inf, E_mat_kam, CELL_W_INF, out_dir)
    plt.show()

if __name__ == "__main__":
    main()