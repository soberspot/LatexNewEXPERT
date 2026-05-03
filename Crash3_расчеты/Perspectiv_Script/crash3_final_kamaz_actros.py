#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crash3_final_kamaz_actros.py

Полная реконструкция столкновения Infiniti QX80 и КАМАЗ (MB Actros).

Особенности модели:
1. Используется матричный метод (Grid Method) 11x16 для обоих ТС.
2. Infiniti QX80:
   - Жесткость по тесту NHTSA V10562.
   - Учет лонжеронов рамы через матрицу K_rel (пиковые силы).
3. КАМАЗ (Actros):
   - Двухуровневая модель жесткости: мягкая кабина vs жесткий брус FUP.
   - Параметры жесткости для COE Heavy Truck (SAE 2008-01-0168).
4. Учет работы на смещение (Post-impact displacement) КАМАЗа.
"""

from __future__ import annotations

import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. ПАРАМЕТРЫ INFINITI QX80 (АВТОМОБИЛЬ 1 - ПУЛЯ)
# ==============================================================================

# Глобальные коэффициенты (NHTSA V10562)
A_INF = 1.614e5      # Н/м
B_INF = 2.194e6      # Н/м^2
C0_INF = 0.074       # м
CELL_W_INF = 0.125   # м

M_INF_FACT = 2870.0  # кг (фактическая масса)

# Матрица глубин C_INF (11x16) - Данные замера
C_INF = np.array([
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
], dtype=float)

# Матрица жесткости INFINITI (K_REL) по пику силы
K_REL_INF = np.array([
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
], dtype=float)


# ==============================================================================
# 2. ПАРАМЕТРЫ КАМАЗ (MB ACTROS / COE HEAVY TRUCK)
# ==============================================================================

# Жесткость современного европейского тягача (SAE 2008-01-0168)
# Базовая жесткость определяется системой FUP (Front Underrun Protection)
A_KAMAZ = 7.50e5     # Н/м (750 кН/м) - очень высокая жесткость
B_KAMAZ = 2.50e6     # Н/м^2
C0_KAMAZ = 0.02    # м (пластиковая облицовка бампера) !! 0,02

CELL_W_KAMAZ = 0.125 # м (такая же сетка, как у Infiniti)

# ------------------------------------------------------------------
# МАТРИЦА ГЛУБИНЫ C_KAMAZ (11x16)
# ------------------------------------------------------------------
# C_KAMAZ = np.zeros((11, 16), dtype=float)

# # Задаем повреждение левой части (столбцы 0-3).
# # Глубина убывает от центра удара (столбец 0) к периферии.
# # По высоте удар приходится в зону бампера/бруса (ряды 6-9).
# C_KAMAZ[6:10, 0] = [0.15, 0.15, 0.15, 0.15] # Максимум слева
# C_KAMAZ[6:10, 1] = [0.10, 0.10, 0.10, 0.10]
# C_KAMAZ[6:10, 2] = [0.05, 0.05, 0.05, 0.05]
# C_KAMAZ[6:10, 3] = [0.01, 0.01, 0.01, 0.01]

# ------------------------------------------------------------------
# 2.1. МАТРИЦА ГЛУБИНЫ C_KAMAZ (11x16)
# ------------------------------------------------------------------
# Имитируем повреждение левой передней части (Left Front Corner).
# Ширина 46 см ~ 4 столбца (4 * 12.5 = 50 см).
# Профиль: Градиент от глубокого (слева) к нулю (к центру).

C_KAMAZ = np.array([
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.05, 0.03, 0.01, 0.01, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.15, 0.10, 0.10, 0.05, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    [0.15, 0.10, 0.10, 0.05, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Верх бампера
    [0.25, 0.18, 0.13, 0.10, 0.055, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер (жестко)
    [0.35, 0.35, 0.20, 0.15, 0.050, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер
    [0.55, 0.48, 0.31, 0.20, 0.055, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер
    [0.01, 0.01, 0.01, 0.01, 0.005, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Бампер
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Низ / противоподкат
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], # Низ
    [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
], dtype=float)


# ------------------------------------------------------------------
# МАТРИЦА ЖЕСТКОСТИ K_REL_KAMAZ (Структура Actros)
# ------------------------------------------------------------------
# 1. Фон (Кабина, радиатор) - мягкие (20% от жесткости бруса)
# K_REL_KAMAZ = np.full((11, 16), 0.2, dtype=float)

# # 2. Зона FUP (Противоподкатный брус) - ряды 7-9.
# # Это стальная балка. Принимаем за 1.0 (базовая жесткость 750 кН/м)
# K_REL_KAMAZ[7:10, :] = 1.0 

# # 3. Крепления FUP к раме - ряды 7-9, столбцы 4-5 и 10-11.
# # Здесь жесткость максимальная (1.5 от базы).
# K_REL_KAMAZ[7:10, 4:6] = 1.5
# K_REL_KAMAZ[7:10, 10:12] = 1.5

# # 4. Юбка бампера (ряд 10) - мягкая
# K_REL_KAMAZ[10, :] = 0.1

K_REL_KAMAZ = np.array([
    [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4], # Кабина верх
    [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
    [0.2, 0.4, 0.4, 0.4, 7.0, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
    [0.2, 1.0, 3.0, 3.0, 7.0, 2.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0], # Переход
    [7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0], # БАМПЕР + РАМА
    [0.2, 0.2, 3.0, 7.0, 7.0, 4.0, 2.0, 2.0, 2.0, 2.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0], # БАМПЕР + РАМА
    [0.2, 0.2, 3.0, 5.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0], # БАМПЕР + РАМА
    [7, 7.0, 7.0, 7.0,7.0, 7.0, 2.0, 2.0, 2.0, 2.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0], # БАМПЕР + РАМА (Ряд 7)
    [0.2, 0.2, 2.0, 2.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0], # БАМПЕР + РАМА (Ряд 8)
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], # Противоподкатный брус (Ряд 9)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # Низ / Подвеска (Ряд 10)
], dtype=float)



# ==============================================================================
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

def build_k_norm(k_rel: np.ndarray) -> np.ndarray:
    """Нормировка коэффициентов жесткости."""
    k_rel = np.asarray(k_rel, dtype=float)
    mask = k_rel > 0.0
    if not np.any(mask):
        return np.zeros_like(k_rel)
    mean_pos = float(k_rel[mask].mean())
    k_norm = np.zeros_like(k_rel)
    k_norm[mask] = k_rel[mask] / mean_pos
    return k_norm

def crash3_energy_matrix(
    c: np.ndarray,
    k_rel: np.ndarray,
    A_global: float,
    B_global: float,
    c0: float,
    cell_width: float,
) -> np.ndarray:
    """Расчет энергии E_ij по ячейкам."""
    c = np.asarray(c, dtype=float)
    c_eff = np.maximum(0.0, c - c0)

    # Нормируем жесткость
    k_norm = build_k_norm(np.asarray(k_rel, dtype=float))
    Aij = A_global * k_norm
    Bij = B_global * k_norm

    E = cell_width * (0.5 * Aij * c_eff**2 + (1.0 / 3.0) * Bij * c_eff**3)
    return E

def analyze_airbag_deployment(ees_kmh: float) -> str:
    """Вердикт по SRS."""
    if ees_kmh < 15.0:
        return "НЕТ (EES < 15 км/ч - зона No Fire)"
    elif 15.0 <= ees_kmh < 25.0:
        return "СЕРАЯ ЗОНА (EES 15-25 км/ч - зона неопределенности)"
    else:
        return "ДА (EES > 25 км/ч - зона Must Fire)"

def draw_profile_plot(c_inf, c_kam, width_step, out_dir):
    """
    Рисует линейный график профиля деформации (вид сверху).
    Берет максимальную глубину в каждом столбце.
    """
    # Вычисляем макс. глубину по столбцам (схлопываем высоту)
    # axis=0 ищет максимум в каждом столбце (сверху вниз)
    profile_inf = np.max(c_inf, axis=0)
    profile_kam = np.max(c_kam, axis=0)

    # Ось X в метрах
    x_axis = np.arange(len(profile_inf)) * width_step

    plt.figure(figsize=(10, 6))

    # Рисуем линии
    plt.plot(x_axis, profile_inf, label='Infiniti QX80', color='blue', linewidth=3, marker='o')
    plt.plot(x_axis, profile_kam, label='КАМАЗ (Actros)', color='red', linewidth=3, marker='s', linestyle='--')

    # Настройка
    plt.title('Сравнительный профиль деформаций (Вид сверху)', fontsize=14)
    plt.xlabel('Ширина по фронту (м)', fontsize=12)
    plt.ylabel('Глубина деформации (м)', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)

    # Заливка под графиком для красоты
    plt.fill_between(x_axis, profile_inf, color='blue', alpha=0.1)
    plt.fill_between(x_axis, profile_kam, color='red', alpha=0.1)

    plt.tight_layout()

    # Сохранение
    save_path = out_dir / "damage_profile_lines.png"
    plt.savefig(save_path, dpi=300)
    print(f"[OK] Линейный профиль сохранен: {save_path}")


def plot_3d_damage(c_inf, c_kam, cell_w, out_dir):
    """
    Строит 3D-модели поверхностей деформации для обоих автомобилей.
    Ось Y привязана к физической высоте от земли.
    """
    # 1. Подготовка координат
    rows, cols = c_inf.shape

    # X: Ширина от 0 до 2.0 м
    x = np.linspace(0, cols * cell_w, cols)

    # Y: Высота. ВАЖНО:
    # В матрице ряд 0 - это ВЕРХ (1.375 м), ряд 10 - это НИЗ (0 м).
    # np.linspace(Start, Stop). Мы идем от Верха к Низу, чтобы совпало с индексами матрицы.
    y = np.linspace(rows * cell_w, 0, rows) 

    # Создаем сетку
    X, Y = np.meshgrid(x, y)

    # 2. Настройка графика
    fig = plt.figure(figsize=(18, 8))

    # --- График 1: Infiniti ---
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    # Используем Z = c_inf (глубина). 
    # cmap='viridis' (сине-зелено-желтый) или 'plasma' (фиолетово-оранжевый)
    surf1 = ax1.plot_surface(X, Y, c_inf, cmap='viridis', edgecolor='none', alpha=0.9)

    ax1.set_title('Infiniti QX80: Профиль повреждений (3D)', fontsize=14)
    ax1.set_xlabel('Ширина (м)')
    ax1.set_ylabel('Высота от земли (м)') # Теперь 0 внизу, 1.4 вверху
    ax1.set_zlabel('Глубина смятия (м)')
    ax1.view_init(elev=30, azim=-120) # Угол обзора (повернем для наглядности)
    ax1.set_zlim(0, 0.6) # Фиксируем масштаб Z
    fig.colorbar(surf1, ax=ax1, shrink=0.5, aspect=10, label='Глубина (м)')

    # --- График 2: КАМАЗ ---
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    surf2 = ax2.plot_surface(X, Y, c_kam, cmap='viridis', edgecolor='none', alpha=0.9)

    ax2.set_title('КАМАЗ: Профиль повреждений (3D)', fontsize=14)
    ax2.set_xlabel('Ширина (м)')
    ax2.set_ylabel('Высота от земли (м)')
    ax2.set_zlabel('Глубина смятия (м)')
    ax2.view_init(elev=30, azim=-60) # Другой угол для КАМАЗа
    ax2.set_zlim(0, 0.6)
    fig.colorbar(surf2, ax=ax2, shrink=0.5, aspect=10, label='Глубина (м)')

    plt.tight_layout()

    # 3. Сохранение
    save_path = out_dir / "damage_3d_view.png"
    plt.savefig(save_path, dpi=300)
    print(f"[OK] 3D-график сохранен: {save_path}")


def plot_3d_energy(e_inf, e_kam, cell_w, out_dir):
    """
    Строит 3D-модели распределения ЭНЕРГИИ (кДж).
    Позволяет увидеть "пики" энергопоглощения (лонжероны, жесткие узлы).
    """
    rows, cols = e_inf.shape

    # Координаты (как в графике глубины)
    # X: 0 .. 2.0 м
    x = np.linspace(0, cols * cell_w, cols)
    # Y: 1.375 .. 0 м (сверху вниз, чтобы соответствовать индексам матрицы)
    y = np.linspace(rows * cell_w, 0, rows)

    X, Y = np.meshgrid(x, y)

    # Переводим Джоули в кДж для наглядности
    Z_inf = e_inf / 1000.0
    Z_kam = e_kam / 1000.0

    fig = plt.figure(figsize=(18, 8))

    # --- Infiniti ---
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    # cmap='magma' - очень красиво показывает энергию (от черного к яркому)
    surf1 = ax1.plot_surface(X, Y, Z_inf, cmap='magma', edgecolor='none', alpha=0.95)

    ax1.set_title('Infiniti: Энергия деформации (кДж)', fontsize=14)
    ax1.set_xlabel('Ширина (м)')
    ax1.set_ylabel('Высота от земли (м)')
    ax1.set_zlabel('Энергия (кДж)')
    ax1.view_init(elev=35, azim=-130) # Разворот, чтобы видеть "вмятину"

    fig.colorbar(surf1, ax=ax1, shrink=0.5, aspect=10, label='кДж')

    # --- КАМАЗ ---
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    # cmap='inferno' - тоже "огненная" палитра
    surf2 = ax2.plot_surface(X, Y, Z_kam, cmap='inferno', edgecolor='none', alpha=0.95)

    ax2.set_title('КАМАЗ: Энергия деформации (кДж)', fontsize=14)
    ax2.set_xlabel('Ширина (м)')
    ax2.set_ylabel('Высота от земли (м)')
    ax2.set_zlabel('Энергия (кДж)')
    ax2.view_init(elev=35, azim=-50)

    fig.colorbar(surf2, ax=ax2, shrink=0.5, aspect=10, label='кДж')

    plt.tight_layout()

    # Сохранение
    save_path = out_dir / "energy_3d_view.png"
    plt.savefig(save_path, dpi=300)
    print(f"[OK] 3D-график энергии сохранен: {save_path}")    

# ==============================================================================
# 4. MAIN
# ==============================================================================

def main() -> None:
    # Папка для вывода
    out_dir = Path(__file__).parent / "crash3_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== РЕКОНСТРУКЦИЯ ДТП: INFINITI QX80 vs КАМАЗ (ACTROS) ===")

    # 1. Расчет энергии деформации
    E_mat_inf = crash3_energy_matrix(C_INF, K_REL_INF, A_INF, B_INF, C0_INF, CELL_W_INF)
    E_inf_joules = float(E_mat_inf.sum())

    E_mat_kam = crash3_energy_matrix(C_KAMAZ, K_REL_KAMAZ, A_KAMAZ, B_KAMAZ, C0_KAMAZ, CELL_W_KAMAZ)
    E_kam_joules = float(E_mat_kam.sum())

    # 2. Расчет работы на смещение (Post-impact displacement)
    M_KAMAZ_FULL = 34000.0  # кг (Тягач+Прицеп+Груз)
    S_KAMAZ = 0.1         # м (смещение 10 см)
    MU_FRICTION = 0.70      # к-т трения (блокировка колес)

    W_disp = MU_FRICTION * M_KAMAZ_FULL * 9.81 * S_KAMAZ

    # 3. Итоги
    E_total = E_inf_joules + E_kam_joules + W_disp

    # Скорость удара (Impact Speed) - Infiniti должен погасить ВСЮ эту энергию
    # V = sqrt(2 * E_total / m1)
    v_impact_ms = math.sqrt(2 * E_total / M_INF_FACT)
    v_impact_kmh = v_impact_ms * 3.6

    # EES Infiniti (только деформация Infiniti)
    ees_inf_ms = math.sqrt(2 * E_inf_joules / M_INF_FACT)
    ees_inf_kmh = ees_inf_ms * 3.6

    print(f"\n1. ЭНЕРГЕТИЧЕСКИЙ БАЛАНС:")
    print(f"   - Деформация Infiniti:  {E_inf_joules/1000.0:8.2f} кДж")
    print(f"   - Деформация КАМАЗа:    {E_kam_joules/1000.0:8.2f} кДж")
    print(f"   - Работа на смещение:   {W_disp/1000.0:8.2f} кДж")
    print(f"   -----------------------------------------")
    print(f"   - ПОЛНАЯ ЭНЕРГИЯ:       {E_total/1000.0:8.2f} кДж")

    print(f"\n2. РАСЧЕТНЫЕ ПАРАМЕТРЫ:")
    print(f"   - Скорость удара (V_impact): {v_impact_kmh:.2f} км/ч")
    print(f"     (Минимальная скорость Infiniti перед контактом)")

    print(f"   - EES Infiniti (Delta-V equiv): {ees_inf_kmh:.2f} км/ч")
    print(f"     (Параметр тяжести удара для кузова Infiniti)")

    verdict = analyze_airbag_deployment(ees_inf_kmh)
    print(f"\n3. АНАЛИЗ SRS (AIRBAG):")
    print(f"   - Вердикт: {verdict}")



    # ==========================================================================
    # 4. ВИЗУАЛИЗАЦИЯ И СОХРАНЕНИЕ
    # ==========================================================================

    # Подготовка размеров для осей (в метрах)
    # extent = [left, right, bottom, top]
    # Для origin='upper' (0,0 в левом верхнем углу):
    # X идет от 0 до 2.0 м
    # Y идет от 1.375 м (низ) до 0 (верх)

    W_REAL = 16 * 0.125  # 2.0 метра
    H_REAL = 11 * 0.125  # 1.375 метра
    EXTENT = [0, W_REAL, H_REAL, 0] 

    try:
        plt.style.use('ggplot')
    except:
        pass

    fig, axs = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(f"Реконструкция: V_impact={v_impact_kmh:.1f} км/ч | EES_Inf={ees_inf_kmh:.1f} км/ч", fontsize=16)

    
        # Функция для отрисовки с правильными осями
        # Функция для отрисовки с правильными осями
    def plot_map(ax, data, title, cmap, vmin=None, vmax=None):
        # Используем origin='lower' и переворачиваем данные по вертикали
        # data[::-1, :] - переворачивает матрицу по вертикали
        im = ax.imshow(data[::-1, :], origin='lower', cmap=cmap, 
                      extent=[0, W_REAL, 0, H_REAL], vmin=vmin, vmax=vmax)
        ax.set_title(title)
        ax.set_xlabel('Ширина, м')
        ax.set_ylabel('Высота от земли, м')
        
        # Сетка каждые 0.25м (2 клетки)
        ax.set_xticks(np.arange(0, W_REAL + 0.01, 0.25))
        ax.set_yticks(np.arange(0, H_REAL + 0.01, 0.25))
        ax.grid(visible=True, color='white', linestyle='--', linewidth=0.5, alpha=0.5)
        
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        return im
    

    
    # # --- ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ОДНОГО ГРАФИКА ---
    # def plot_map(ax, data, title, cmap, vmin=None, vmax=None):
    #     im = ax.imshow(data, origin='upper', cmap=cmap, extent=EXTENT, vmin=vmin, vmax=vmax)
    #     ax.set_title(title)
    #     ax.set_xlabel('Ширина, м')
    #     ax.set_ylabel('Высота (от верха), м')
    #     # Включаем сетку, чтобы видеть ячейки 125 мм
    #     ax.grid(visible=True, color='white', linestyle='--', linewidth=0.5, alpha=0.5)
    #     # Устанавливаем тики (деления) каждые 0.5 метра для наглядности
    #     ax.set_xticks(np.arange(0, W_REAL + 0.1, 0.5))
    #     ax.set_yticks(np.arange(0, H_REAL + 0.1, 0.5))
    #     fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # --- РИСУЕМ ГРАФИКИ ---

    # Ряд 1: Infiniti
    plot_map(axs[0,0], C_INF, 'Infiniti: Глубина (м)', 'Blues', vmin=0, vmax=0.6)
    plot_map(axs[0,1], K_REL_INF, 'Infiniti: Жесткость (K_rel)', 'Greys')
    plot_map(axs[0,2], E_mat_inf/1000.0, 'Infiniti: Энергия (кДж)', 'hot')

    # Ряд 2: КАМАЗ
    plot_map(axs[1,0], C_KAMAZ, 'KAMAZ: Глубина (м)', 'Blues', vmin=0, vmax=0.6)
    plot_map(axs[1,1], K_REL_KAMAZ, 'KAMAZ: Жесткость (K_rel)', 'Greys')
    plot_map(axs[1,2], E_mat_kam/1000.0, 'KAMAZ: Энергия (кДж)', 'hot')

    plt.tight_layout()

    # --- СОХРАНЕНИЕ (ИСПРАВЛЯЕМ ПУСТУЮ ПАПКУ) ---

    # 1. Сохраняем картинку
    plot_path = out_dir / "reconstruction_viz.png"
    plt.savefig(plot_path, dpi=300)
    print(f"\n[OK] График сохранен: {plot_path}")

    # 2. Сохраняем текстовый отчет
    report_path = out_dir / "report_final.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== РЕЗУЛЬТАТЫ РАСЧЕТА (Crash3 Grid Method) ===\n")
        f.write(f"Дата: {__import__('datetime').datetime.now()}\n\n")
        f.write(f"1. БАЛАНС ЭНЕРГИЙ:\n")
        f.write(f"   Infiniti (деформация): {E_inf_joules:.1f} Дж\n")
        f.write(f"   КАМАЗ (деформация):    {E_kam_joules:.1f} Дж\n")
        f.write(f"   Работа на смещение:    {W_disp:.1f} Дж\n")
        f.write(f"   ИТОГО (Total):         {E_total:.1f} Дж\n\n")
        f.write(f"2. СКОРОСТИ:\n")
        f.write(f"   V_impact (Сближение):  {v_impact_kmh:.2f} км/ч\n")
        f.write(f"   EES Infiniti (SRS):    {ees_inf_kmh:.2f} км/ч\n\n")
        f.write(f"3. ВЫВОДЫ:\n")
        f.write(f"   Вердикт SRS: {verdict}\n")
    print(f"[OK] Отчет сохранен: {report_path}")

    # Показываем на экране
    draw_profile_plot(C_INF, C_KAMAZ, CELL_W_INF, out_dir)
     # 1. Строим 3D Глубину
    plot_3d_damage(C_INF, C_KAMAZ, CELL_W_INF, out_dir)
     # 2. Строим 3D Энергию (НОВОЕ)
    plot_3d_energy(E_mat_inf, E_mat_kam, CELL_W_INF, out_dir)
    plt.show()

if __name__ == "__main__":
    main()