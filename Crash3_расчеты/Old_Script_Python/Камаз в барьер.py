import numpy as np
import math
import pandas as pd

# ---------------------------------------------------------
# Универсальные функции CRASH3
# ---------------------------------------------------------

def e_unit(A: float, B: float, c: np.ndarray) -> np.ndarray:
    """
    Энергия на единицу ширины по CRASH3:
    e = A/2 * c^2 + B/3 * c^3
    """
    return 0.5 * A * c**2 + (1.0/3.0) * B * c**3


def calc_cell_energy(
    c_matrix: np.ndarray,
    k_matrix: np.ndarray,
    dw: float,
    A: float,
    B: float,
    c0: float = 0.0,
    use_c0: bool = True
):
    """
    Возвращает:
      E_cell — матрица энергий по ячейкам (Дж)
      E_total — суммарная энергия (Дж)

    Логика согласована с вашим требованием:
      - без усреднений
      - строго по c_ij и k_ij
      - при необходимости применяем порог c0 как часть набора параметров

    Формула:
      c* = max(0, c - c0) при use_c0=True
      E_ij = k_ij * dw * e_unit(A,B,c*)
    """
    if use_c0:
        c_eff = np.clip(c_matrix - c0, 0.0, None)
    else:
        c_eff = c_matrix.copy()

    E_cell = k_matrix * dw * e_unit(A, B, c_eff)
    return E_cell, float(E_cell.sum())


def ees_from_energy(E_total: float, mass: float):
    """EES/эквивалентная скорость по энергии: v = sqrt(2E/m)."""
    if E_total <= 0:
        return 0.0, 0.0
    v_ms = math.sqrt(2.0 * E_total / mass)
    return v_ms, v_ms * 3.6


def collision_speed_energy_balance(
    m_inf: float,
    E_inf: float,
    E_kam: float,
    E_other: float = 0.0
):
    """
    Энергетический баланс:
      1/2 * m_inf * v^2 = E_inf + E_kam + E_other

    Возвращает v (м/с, км/ч).
    """
    E_sum = E_inf + E_kam + E_other
    if E_sum <= 0:
        return 0.0, 0.0
    v_ms = math.sqrt(2.0 * E_sum / m_inf)
    return v_ms, v_ms * 3.6


# ---------------------------------------------------------
# Параметры сетки
# ---------------------------------------------------------

dw = 0.125  # м — шаг по ширине как  приняли для NHTSA


# ---------------------------------------------------------
# 1) ШАБЛОН ДАННЫХ ПО КАМАЗ
# ---------------------------------------------------------
# ВАЖНО:
# Для методически строгого расчёта КАМАЗ вам нужно задать:
#   - собственные A_k, B_k, c0_k для зоны повреждения КАМАЗ
#   - матрицу его относительных/локальных коэффициентов жесткости k_kamaz
#   - матрицу глубин c_kamaz
#
# Без этого код останется корректным вычислителем, но не источником "готовых чисел".

A_k = 0.0     # N/m   <-- заменить на валидированные значения для КАМАЗ
B_k = 0.0     # N/m^2 <-- заменить
c0_k = 0.0    # m     <-- заменить (если применимо)
use_c0_k = True

# Пример: если вы пока не имеете k_ij по КАМАЗ,
# задайте свою матрицу. Ниже — пустой шаблон на 3x4.
# Ряд 1 должен быть верхним, как вы требовали ранее.
c_kamaz = np.array([
    [0.0, 0.0, 0.0, 0.0],  # верх
    [0.0, 0.0, 0.0, 0.0],  # середина
    [0.0, 0.0, 0.0, 0.0],  # низ
], dtype=float)

k_kamaz = np.ones_like(c_kamaz, dtype=float)  # <-- заменить на вашу матрицу k_ij КАМАЗ


# ---------------------------------------------------------
# 2) ОПЦИОНАЛЬНЫЙ ГЕНЕРАТОР ЧЕРНОВОЙ МАТРИЦЫ c_ij КАМАЗ
# ---------------------------------------------------------
# Это НЕ "строгий" шаг, а заготовка по вашему словесному описанию градиента.
# Используйте только если хотите быстрее перейти к ручной верификации.

def build_kamaz_crush_3xN(
    width: float,
    dw: float,
    upper_left: float,
    upper_right: float,
    mid_left: float,
    mid_right: float,
    low_left: float,
    low_right: float
):
    """
    Создаёт 3xN матрицу глубин:
      row1 = верх, row2 = середина, row3 = низ
    Линейная интерполяция слева направо.

    Параметры глубин в метрах.
    """
    n_cols = int(math.ceil(width / dw))
    x = np.linspace(0.0, 1.0, n_cols)

    upper = upper_left + (upper_right - upper_left) * x
    mid   = mid_left   + (mid_right   - mid_left)   * x
    low   = low_left   + (low_right   - low_left)   * x

    return np.vstack([upper, mid, low])


# Пример подстановки В КАЧЕСТВЕ ЧЕРНОВИКА:
# ВНИМАНИЕ: ваши исходные числа по верхней зоне имеют неоднозначность ("0,05 см").
# Поэтому здесь стоит только демонстрационный шаблон.
#
# width_k = 0.441
# c_kamaz = build_kamaz_crush_3xN(
#     width=width_k, dw=dw,
#     upper_left=0.05, upper_right=0.01,   # <-- проверьте единицы!
#     mid_left=0.238,  mid_right=0.215,    # <-- уточнить правый край
#     low_left=0.314,  low_right=0.10
# )
# k_kamaz = np.ones_like(c_kamaz)  # временно, пока вы не зададите k_ij КАМАЗ


# ---------------------------------------------------------
# 3) РАСЧЁТ ЭНЕРГИИ КАМАЗ
# ---------------------------------------------------------

E_cell_kamaz, E_tot_kamaz = calc_cell_energy(
    c_matrix=c_kamaz,
    k_matrix=k_kamaz,
    dw=dw,
    A=A_k,
    B=B_k,
    c0=c0_k,
    use_c0=use_c0_k
)

print("=== КАМАЗ ===")
print(f"E_kamaz = {E_tot_kamaz/1000:.3f} кДж")
print("Матрица энергий КАМАЗ (кДж):")
print(pd.DataFrame(E_cell_kamaz/1000).round(3))


# ---------------------------------------------------------
# 4) СВЯЗКА С INFINITI И ИТОГОВАЯ СКОРОСТЬ
# ---------------------------------------------------------
# Если вы хотите, можно импортировать сюда уже посчитанное E_inf
# (например, из вашего кода для Infiniti).

m_inf = 2870.0  # кг

# Пример: подставьте ваше итоговое значение энергии Infiniti
# (в корректной методике с c0 по Armada/QX80)
E_inf = 48.05e3  # Дж  <-- заменить на вычисленное в вашем скрипте

# Прочие потери энергии, если вы захотите их учитывать отдельной строкой:
E_other = 0.0

v_ms, v_kmh = collision_speed_energy_balance(
    m_inf=m_inf,
    E_inf=E_inf,
    E_kam=E_tot_kamaz,
    E_other=E_other
)

print("\n=== Энергетический баланс ===")
print(f"E_inf   = {E_inf/1000:.3f} кДж")
print(f"E_kamaz = {E_tot_kamaz/1000:.3f} кДж")
print(f"E_other = {E_other/1000:.3f} кДж")
print(f"v = {v_kmh:.2f} км/ч")
