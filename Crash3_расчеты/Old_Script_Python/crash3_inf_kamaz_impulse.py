"""
CRASH3: Infiniti QX80 vs KamAZ
Воспроизводимый расчёт:
1) k_ij по импульсу ячейки барьера V10562 (11x16),
2) энергия деформации Infiniti по CRASH3 с шагом 0.125 м,
3) распределённая карта энергий по k_ij,
4) тепловые карты: глубины, k_ij, энергии,
5) базовый энергетический баланс.

Авторский принцип повторяемости:
- Нормировка k_ij всегда по среднему импульсу ненулевых ячеек.
- Энергия Infiniti считается в постановке CRASH3 "на единицу ширины",
  поэтому высота матрицы crush НЕ используется как множитель энергии.
"""

from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

import numpy as np
import matplotlib.pyplot as plt
import math
from pathlib import Path


# -----------------------------
# 1. Исходные данные пользователя
# -----------------------------

C_INFINITI = np.array([
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

M_INFINITI = 2870.0  # кг
DX = 0.125  # м

# CRASH3 коэффициенты для Armada/QX80 (из испытания V10562)
A = 1.614e5  # N/m
B = 2.194e6  # N/m^2
C0 = 0.074   # м


# -----------------------------
# 2. Утилиты
# -----------------------------

def effective_crush(c: np.ndarray, c0: float = C0) -> np.ndarray:
    return np.maximum(0.0, c - c0)


def column_profile_mean_nonzero(C: np.ndarray) -> np.ndarray:
    """
    Репрезентативная глубина по столбцам.
    Важно для методической корректности CRASH3:
    A/B заданы "на единицу ширины", потому высота
    используется для получения профиля, а не как множитель энергии.
    """
    prof = []
    for j in range(C.shape[1]):
        col = C[:, j]
        nz = col[col > 0]
        prof.append(float(nz.mean()) if nz.size else 0.0)
    return np.array(prof, dtype=float)


def crash3_energy_per_column(c_col: np.ndarray, dx: float = DX,
                             A_: float = A, B_: float = B, c0: float = C0) -> np.ndarray:
    c_eff = effective_crush(c_col, c0)
    return dx * (A_ * c_eff + 0.5 * B_ * c_eff ** 2)


def crash3_total_energy(C: np.ndarray, dx: float = DX,
                        A_: float = A, B_: float = B, c0: float = C0) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Возвращает:
    - суммарную энергию (Дж),
    - профиль c_j,
    - энергии по столбцам E_j.
    """
    c_col = column_profile_mean_nonzero(C)
    E_col = crash3_energy_per_column(c_col, dx=dx, A_=A_, B_=B_, c0=c0)
    return float(E_col.sum()), c_col, E_col


def ees_from_energy(E: float, m: float) -> float:
    # V = sqrt(2E/m), м/с
    return math.sqrt(max(0.0, 2.0 * E / m))


# -----------------------------
# 3. k_ij по импульсу из V10562
# -----------------------------

@dataclass
class BarrierCellSignal:
    row: int
    col: int
    time: np.ndarray
    force: np.ndarray


def parse_barrier_channels_from_text(text: str) -> Dict[Tuple[int, int], List[Tuple[float, float]]]:
    """
    Универсальный парсер на случай, если EV5/ASCII содержит
    таблицу "time, channel_name, value" или близкий формат.

    Эта функция намеренно консервативна:
    вы можете адаптировать regex под реальный формат файлов V10562,
    но логика расчёта импульса останется неизменной.

    Ожидаемые варианты имён:
      "BARRIER 8-12", "BARRIER 7-5" и т.п.
    """
    data: Dict[Tuple[int, int], List[Tuple[float, float]]] = {}

    # Примерный шаблон строк: time ... BARRIER r-c ... value
    # Для стабильности пытаемся вылавливать "BARRIER <row>-<col>" и два числа.
    line_re = re.compile(
        r"(?P<t>-?\d+(?:\.\d+)?)"
        r".*?BARRIER\s+(?P<r>\d+)[\-](?P<c>\d+)"
        r".*?(?P<v>-?\d+(?:\.\d+)?)\s*$"
    )

    for line in text.splitlines():
        m = line_re.search(line)
        if not m:
            continue
        t = float(m.group("t"))
        r = int(m.group("r"))
        c = int(m.group("c"))
        v = float(m.group("v"))
        key = (r, c)
        data.setdefault(key, []).append((t, v))

    return data


def build_kij_from_impulse(zip_path: str,
                           expected_shape: Tuple[int, int] = (11, 16),
                           verbose: bool = True) -> np.ndarray:
    """
    Пытается извлечь временные ряды сил ячеек барьера из архива V10562,
    вычисляет импульсы и формирует k_ij.

    Если структура архива отличается, адаптируйте часть чтения файлов,
    не меняя формулы импульса и нормировки.
    """
    rows, cols = expected_shape
    impulse = np.zeros((rows, cols), dtype=float)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Читаем все текстовые файлы, где потенциально есть EV5/каналы барьера
        names = [n for n in zf.namelist()
                 if n.lower().endswith((".txt", ".csv", ".asc"))]

        if verbose:
            print("Файлы-кандидаты в архиве:", *names, sep="\n  ")

        raw_points: Dict[Tuple[int, int], List[Tuple[float, float]]] = {}

        for name in names:
            try:
                content = zf.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue

            parsed = parse_barrier_channels_from_text(content)
            for key, pts in parsed.items():
                raw_points.setdefault(key, []).extend(pts)

        # Сборка импульсов
        for (r, c), pts in raw_points.items():
            if not (1 <= r <= rows and 1 <= c <= cols):
                continue
            pts_sorted = sorted(pts, key=lambda x: x[0])
            t = np.array([p[0] for p in pts_sorted], dtype=float)
            f = np.array([p[1] for p in pts_sorted], dtype=float)

            # Уберём дубликаты времени
            uniq_t, idx = np.unique(t, return_index=True)
            f = f[idx]
            t = uniq_t

            if t.size < 2:
                continue

            J = np.trapz(f, t)  # Н*с
            impulse[r - 1, c - 1] = max(0.0, J)

    nz = impulse[impulse > 0]
    if nz.size == 0:
        raise RuntimeError(
            "Не удалось извлечь силы барьера из архива. "
            "Проверьте формат исходных файлов V10562 и адаптируйте парсер."
        )

    J_mean = float(nz.mean())
    kij = impulse / J_mean

    return kij


# -----------------------------
# 4. Карта энергий по ячейкам Infiniti
# -----------------------------

def distribute_energy_by_k(C: np.ndarray, kij: np.ndarray,
                           dx: float = DX, A_: float = A, B_: float = B, c0: float = C0) -> Tuple[np.ndarray, float]:
    """
    Строит матрицу энергий E_ij без изменения суммарной энергии:
    - сначала считаем E_j по профилю CRASH3,
    - затем распределяем E_j по строкам через веса kij.

    Это устраняет методическую ошибку "умножения на высоту",
    но даёт физически правдоподобную карту локальной работы структуры.
    """
    E_total, c_col, E_col = crash3_total_energy(C, dx=dx, A_=A_, B_=B_, c0=c0)

    rows, cols = C.shape
    Eij = np.zeros_like(C, dtype=float)

    for j in range(cols):
        # если по столбцу энергии нет, пропускаем
        if E_col[j] <= 0:
            continue

        column_k = kij[:, j].copy()
        # ограничим только те строки, где есть деформация
        mask = C[:, j] > 0
        column_k = column_k * mask

        s = column_k.sum()
        if s <= 0:
            # если импульсных данных нет, распределим равномерно по деформированным ячейкам
            idx = np.where(mask)[0]
            if idx.size:
                Eij[idx, j] = E_col[j] / idx.size
            continue

        w = column_k / s
        Eij[:, j] = w * E_col[j]

    return Eij, E_total


# -----------------------------
# 5. Визуализация
# -----------------------------

def heatmap(matrix: np.ndarray, title: str, out_path: Optional[str] = None):
    """
    Важно: ориентация:
    - строка 1 должна быть сверху,
    - строка 11 — снизу.
    Поэтому используем origin='upper'.
    """
    plt.figure()
    plt.imshow(matrix, origin="upper", aspect="auto")
    plt.title(title)
    plt.xlabel("Столбец")
    plt.ylabel("Ряд")
    plt.colorbar()
    if out_path:
        plt.tight_layout()
        plt.savefig(out_path, dpi=200)
    else:
        plt.show()
    plt.close()


# -----------------------------
# 6. Базовый энергетический баланс
# -----------------------------

def estimate_speed_infiniti_vs_rigid(E_inf: float, m_inf: float) -> float:
    """
    Базовая оценка скорости для случая, когда противодействующая сторона
    значительно более жёсткая (КамАЗ+прицеп).
    """
    v = ees_from_energy(E_inf, m_inf)  # м/с
    return v



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





    # --- NEW: экспорт матрицы жесткости и матрицы энергий Infiniti в XeLaTeX ---
    # ВАЖНО: используйте здесь ваши реальные имена переменных

    save_matrix_xelatex(
        M=k_infiniti,  # <-- замените на фактическое имя вашей матрицы k_ij для Infiniti
        out_path="k_infiniti_matrix.tex",
        caption=r"Матрица относительных коэффициентов жёсткости $k_{ij}$ для Infiniti QX80",
        label="tab:k_infiniti",
        fmt="{:.2f}",
    )

    save_matrix_xelatex(
        M=E_infiniti_cells,  # <-- замените на фактическое имя вашей матрицы энергий по ячейкам Infiniti
        out_path="E_infiniti_cells_matrix.tex",
        caption=r"Матрица энергий деформации по ячейкам для Infiniti QX80",
        label="tab:E_infiniti_cells",
        fmt="{:.1f}",
    )




# -----------------------------
# 7. Главная функция
# -----------------------------

def main(zip_path: Optional[str] = None,
         make_plots: bool = True,
         out_dir: str = "crash3_out"):

    os.makedirs(out_dir, exist_ok=True)

    # 7.1. Энергия Infiniti по CRASH3
    E_inf, c_col, E_col = crash3_total_energy(C_INFINITI)
    v_ees = ees_from_energy(E_inf, M_INFINITI)

    print("Infiniti QX80:")
    print(f"  Масса: {M_INFINITI:.1f} кг")
    print(f"  Шаг по ширине: {DX:.3f} м")
    print(f"  A={A:.3e} N/m, B={B:.3e} N/m^2, c0={C0:.3f} м")
    print(f"  Суммарная энергия деформации (по профилю): {E_inf/1000:.2f} кДж")
    print(f"  V_EES (удар о жёсткое препятствие): {v_ees*3.6:.2f} км/ч")

    kij = None
    Eij = None

    # 7.2. k_ij по импульсу из V10562 (если архив указан)
    if zip_path:
        try:
            kij = build_kij_from_impulse(zip_path)
            print("Матрица k_ij по импульсу успешно сформирована.")
        except Exception as e:
            print("Не удалось сформировать k_ij по импульсу:", str(e))

    # 7.3. Распределённая карта энергий по k_ij
    if kij is not None:
        Eij, E_inf_check = distribute_energy_by_k(C_INFINITI, kij)
        print(f"  Контроль суммарной энергии по E_ij: {E_inf_check/1000:.2f} кДж")

    # 7.4. Базовая оценка скорости в столкновении с КамАЗ
    v_inf_vs_kamaz = estimate_speed_infiniti_vs_rigid(E_inf, M_INFINITI)
    print(f"  Оценка скорости Infiniti в столкновении с КамАЗ (базовый сценарий): {v_inf_vs_kamaz*3.6:.2f} км/ч")

    # 7.5. Плоты
    if make_plots:
        heatmap(C_INFINITI, "Infiniti QX80: глубины смятия c_ij, м",
                os.path.join(out_dir, "infiniti_crush.png"))

        # Профиль и энергии по ширине
        plt.figure()
        x = np.arange(1, C_INFINITI.shape[1] + 1)
        plt.plot(x, c_col, marker="o")
        plt.title("Infiniti QX80: репрезентативный профиль c_j по столбцам")
        plt.xlabel("Столбец")
        plt.ylabel("c_j, м")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "infiniti_profile.png"), dpi=200)
        plt.close()

        plt.figure()
        plt.plot(x, E_col/1000, marker="o")
        plt.title("Infiniti QX80: энергия по столбцам E_j")
        plt.xlabel("Столбец")
        plt.ylabel("E_j, кДж")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "infiniti_energy_columns.png"), dpi=200)
        plt.close()

        if kij is not None:
            heatmap(kij, "V10562: относительные коэффициенты k_ij по импульсу",
                    os.path.join(out_dir, "kij_impulse.png"))

        if Eij is not None:
            heatmap(Eij/1000, "Infiniti QX80: распределённая энергия E_ij, кДж",
                    os.path.join(out_dir, "infiniti_energy_cells.png"))

    print(f"\nФайлы сохранены в папку: {out_dir}")

    


if __name__ == "__main__":
    # Укажите путь к вашему архиву V10562 на локальной машине при необходимости:
    # main(zip_path=r"C:\\...\\v10562.zip")
    main(zip_path=None)
