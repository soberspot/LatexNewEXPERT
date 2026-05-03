import argparse
import zipfile
import re
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1) Исходные данные (зафиксированные в скрипте)
# ============================================================

# 1.1. Infiniti QX80 — матрица глубин смятия c_ij (м), 11x16
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

# 1.2. КамАЗ — исходное описание градиента смятия (м)
KAMAZ_LOW_LR  = (0.314, 0.10)  # низ: слева -> справа
KAMAZ_MID_LR  = (0.238, 0.02)  # середина
KAMAZ_HIGH_LR = (0.050, 0.01)  # верх

KAMAZ_CONTACT_WIDTH = 0.441  # m
KAMAZ_DAMAGE_HEIGHT = 1.57   # m

# 1.3. CRASH3 A/B/c0 для Infiniti (по тесту V10562)
A_INF  = 1.614e5   # N/m
B_INF  = 2.194e6   # N/m^2
C0_INF = 0.074     # m

# 1.4. Масса Infiniti (по вашей постановке)
M_INF = 2870.0     # kg

# 1.5. Шаг сетки, согласованный с NHTSA нагрузочной стенкой
DX_NHTSA = 0.125   # m


# ============================================================
# 2) Парсинг EV5 и построение k_ij по импульсу
# ============================================================

def load_ev5_lines(zf, name="v10562.EV5"):
    txt = zf.read(name).decode("utf-8", errors="ignore")
    return txt.splitlines()


def get_barrier_force_channels(ev5_lines):
    """
    Возвращает список (канал, ряд, столбец) для продольных
    силовых каналов XG (ед. NWT) нагрузочной стенки.
    """
    out = []
    for ln in ev5_lines:
        if "BARRIER" not in ln:
            continue
        parts = ln.split("|")
        if len(parts) < 9:
            continue
        try:
            ch = int(parts[1])
        except ValueError:
            continue

        axis = parts[5].strip()
        unit = parts[7].strip()
        desc = parts[-1].strip()

        m = re.search(r"BARRIER\s+(\d+)-(\d+)", desc)
        if not m:
            continue
        row = int(m.group(1))
        col = int(m.group(2))

        if axis == "XG" and unit == "NWT":
            out.append((ch, row, col))
    return out


def read_channel(zf, num, prefix="v10562"):
    raw = zf.read(f"{prefix}.{num:03d}").decode("utf-8", errors="ignore").strip().splitlines()
    arr = np.array([list(map(float, ln.split())) for ln in raw], dtype=float)
    return arr[:, 0], arr[:, 1]


def compute_impulse_abs(zf, ch, t0=0.0, t1=0.150, prefix="v10562"):
    """
    Импульс по модулю в фиксированном окне времени:
      baseline = mean(F) при t < t0
      F_corr   = F - baseline
      I        = ∫_{t0}^{t1} |F_corr(t)| dt
    """
    t, f = read_channel(zf, ch, prefix=prefix)

    pre = t < t0
    baseline = f[pre].mean() if np.any(pre) else 0.0
    f_corr = f - baseline

    mask = (t >= t0) & (t <= t1)
    t_sel = t[mask]
    f_sel = f_corr[mask]

    if t_sel.size < 2:
        return 0.0

    return float(np.trapz(np.abs(f_sel), t_sel))


def build_kij_from_impulse(zf, ev5_lines, shape=(11, 16), t0=0.0, t1=0.150, prefix="v10562"):
    """
    Строит:
      I_ij  — матрицу импульсов,
      k_ij  — относительную матрицу жесткости:
              k_ij = I_ij / mean(I_ij) по ненулевым ячейкам.

    Индексация соответствует схеме:
      ряд 1 — верх, ряд 11 — низ.
    """
    chans = get_barrier_force_channels(ev5_lines)
    I = np.zeros(shape, dtype=float)

    for ch, row, col in chans:
        r = row - 1
        c = col - 1
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            I[r, c] = compute_impulse_abs(zf, ch, t0=t0, t1=t1, prefix=prefix)

    nz = I[I > 0]
    mean_I = float(nz.mean()) if nz.size else 1.0

    k = np.zeros_like(I)
    k[I > 0] = I[I > 0] / mean_I
    return k, I, mean_I


# ============================================================
# 3) CRASH3 энергия — профильный вариант
# ============================================================

def column_profile_nonzero_mean(c_mat):
    """
    Для каждого столбца берется среднее по ненулевым c_ij.
    """
    n_cols = c_mat.shape[1]
    prof = np.zeros(n_cols, dtype=float)
    for j in range(n_cols):
        vals = c_mat[:, j]
        nz = vals[vals > 0]
        prof[j] = float(nz.mean()) if nz.size else 0.0
    return prof


def crash3_energy_from_profile(profile, A, B, c0, dx):
    """
    Энергия деформации по CRASH3 для дискретного профиля:
        delta = max(0, c - c0)
        E = Σ dx * (A*delta + 0.5*B*delta^2)
    """
    delta = np.maximum(0.0, profile - c0)
    return float(np.sum(dx * (A * delta + 0.5 * B * delta**2)))


def ees_speed_kmh(E, mass):
    return math.sqrt(2.0 * E / mass) * 3.6


# ============================================================
# 4) КамАЗ — построение геометрической матрицы смятия (3x16)
# ============================================================

def build_kamaz_crush_matrix(n_cols=16,
                            low_lr=KAMAZ_LOW_LR,
                            mid_lr=KAMAZ_MID_LR,
                            high_lr=KAMAZ_HIGH_LR):
    """
    Формирует 3xN матрицу смятия КамАЗ:
      верх/середина/низ — линейная интерполяция слева направо.
    """
    def lin(a, b):
        return np.linspace(a, b, n_cols)

    high = lin(*high_lr)
    mid  = lin(*mid_lr)
    low  = lin(*low_lr)
    return np.vstack([high, mid, low])


# ============================================================
# 5) Визуализация
# ============================================================

def save_heatmap(mat, title, out_path, vmin=None, vmax=None):
    plt.figure()
    plt.imshow(mat, origin="upper", vmin=vmin, vmax=vmax)
    plt.title(title)
    plt.colorbar()
    plt.xlabel("Столбец")
    plt.ylabel("Ряд")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# ============================================================
# 6) Главный расчет
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Reproducible CRASH3 workflow with impulse-based k_ij for Infiniti–KamAZ."
    )
    parser.add_argument("--v10562-zip", type=str, default="v10562.zip",
                        help="Путь к zip-файлу теста NHTSA V10562.")
    parser.add_argument("--t0", type=float, default=0.0,
                        help="Начало окна интегрирования импульса, с.")
    parser.add_argument("--t1", type=float, default=0.150,
                        help="Конец окна интегрирования импульса, с.")
    parser.add_argument("--outdir", type=str, default="out",
                        help="Каталог для сохранения результатов.")

    # При наличии коэффициентов для КамАЗ их можно передать явно
    parser.add_argument("--A-kamaz", type=float, default=None, help="A для КамАЗ, N/m.")
    parser.add_argument("--B-kamaz", type=float, default=None, help="B для КамАЗ, N/m^2.")
    parser.add_argument("--c0-kamaz", type=float, default=0.0, help="c0 для КамАЗ, м (если известно).")

    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 6.1. k_ij по импульсу из V10562
    zip_path = Path(args.v10562_zip)
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path.resolve()}")

    with zipfile.ZipFile(zip_path) as zf:
        ev5_lines = load_ev5_lines(zf)
        k_ij, I_ij, mean_I = build_kij_from_impulse(
            zf, ev5_lines, t0=args.t0, t1=args.t1
        )

    # 6.2. Сохранение матриц
    pd.DataFrame(k_ij).to_csv(outdir / "kij_impulse.csv", index=False, header=False)
    pd.DataFrame(I_ij).to_csv(outdir / "impulses_raw.csv", index=False, header=False)

    # 6.3. Тепловые карты
    save_heatmap(C_INFINITI, "Infiniti QX80: c_ij, м", outdir / "infiniti_crush.png")
    save_heatmap(k_ij, "Относительная жесткость k_ij (по импульсу, V10562)", outdir / "kij_impulse.png")
    save_heatmap(I_ij, "Импульсы I_ij, Н*с (V10562)", outdir / "impulses_raw.png")

    # 6.4. Infiniti — энергия по CRASH3 (профиль)
    prof_inf = column_profile_nonzero_mean(C_INFINITI)
    E_inf = crash3_energy_from_profile(prof_inf, A_INF, B_INF, C0_INF, DX_NHTSA)
    v_ees_inf = ees_speed_kmh(E_inf, M_INF)

    pd.DataFrame({"col": np.arange(1, 17), "c_mean_nonzero": prof_inf}).to_csv(
        outdir / "infiniti_profile.csv", index=False
    )

    # 6.5. КамАЗ — модельная матрица смятия (геометрия)
    c_kamaz = build_kamaz_crush_matrix(n_cols=16)
    pd.DataFrame(c_kamaz).to_csv(outdir / "kamaz_crush_3x16.csv", index=False, header=False)
    save_heatmap(c_kamaz, "КамАЗ: модельная матрица смятия (3 зоны), м", outdir / "kamaz_crush.png")

    # 6.6. При наличии A/B КамАЗ — расчет его энергии
    E_kamaz = None
    v_ees_total = None
    if args.A_kamaz is not None and args.B_kamaz is not None:
        dx_kamaz = KAMAZ_CONTACT_WIDTH / 16.0
        prof_kamaz = c_kamaz.mean(axis=0)
        E_kamaz = crash3_energy_from_profile(prof_kamaz, args.A_kamaz, args.B_kamaz, args.c0_kamaz, dx_kamaz)

        # Упрощенный баланс: суммарная энергия смятия получена из кинетики Infiniti
        E_total = E_inf + E_kamaz
        v_ees_total = ees_speed_kmh(E_total, M_INF)

    # 6.7. Печать результатов
    print("=== k_ij ПО ИМПУЛЬСУ (V10562) ===")
    print(f"Окно интегрирования: [{args.t0:.3f}; {args.t1:.3f}] с")
    print(f"Средний импульс по ненулевым ячейкам: {mean_I:.3f} Н*с")
    print()

    print("=== INFINITI QX80 (CRASH3, профиль) ===")
    print(f"A = {A_INF:.3e} Н/м, B = {B_INF:.3e} Н/м^2, c0 = {C0_INF:.3f} м")
    print(f"dx = {DX_NHTSA:.3f} м, масса = {M_INF:.1f} кг")
    print(f"Энергия смятия: {E_inf/1000:.2f} кДж")
    print(f"EES (как к жесткому препятствию): {v_ees_inf:.2f} км/ч")
    print()

    if E_kamaz is not None:
        print("=== КАМАЗ (CRASH3, при заданных A/B) ===")
        print(f"A_kamaz = {args.A_kamaz:.3e} Н/м, B_kamaz = {args.B_kamaz:.3e} Н/м^2, c0_kamaz = {args.c0_kamaz:.3f} м")
        print(f"Энергия смятия КамАЗ: {E_kamaz/1000:.2f} кДж")
        print()
        print("=== УПРОЩЕННЫЙ ЭНЕРГЕТИЧЕСКИЙ БАЛАНС ===")
        print(f"Суммарная энергия смятия (Infiniti + КамАЗ): {(E_inf+E_kamaz)/1000:.2f} кДж")
        print(f"Оценка скорости Infiniti по суммарной энергии: {v_ees_total:.2f} км/ч")
        print()

    print("Результаты сохранены в:", outdir.resolve())


if __name__ == "__main__":
    main()
