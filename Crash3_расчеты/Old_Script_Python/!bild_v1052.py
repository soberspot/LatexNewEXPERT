from pathlib import Path
import sys
import zipfile
import numpy as np
import pandas as pd
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class BarrierCell:
    row: int  # 1..11
    col: int  # 1..16


def read_text_lines(zf: zipfile.ZipFile, name: str) -> List[str]:
    data = zf.read(name)
    # В архивах NHTSA часто встречаются латинские кодировки
    return data.decode("latin1", errors="ignore").splitlines()


def find_ev5_name(zf: zipfile.ZipFile) -> str:
    # Пытаемся найти EV5 файл независимо от регистра/расширения
    for n in zf.namelist():
        if n.lower().endswith(".ev5"):
            return n
    raise FileNotFoundError("EV5 файл не найден в архиве.")


def parse_barrier_xg_channels(ev5_lines: List[str]) -> Dict[BarrierCell, int]:
    """
    Возвращает соответствие ячейка барьера -> ID канала
    для компонент XG с единицами NWT.
    Ожидаем 10*16 = 160 каналов (строки 2..11).
    """
    pattern = re.compile(r"BARRIER\s+(\d+)-(\d+)\s*$")

    mapping: Dict[BarrierCell, int] = {}

    for ln in ev5_lines:
        if "BARRIER" not in ln:
            continue
        if "|LC|" not in ln:
            continue
        # нас интересует только сила по XG в Ньютонах
        if "|XG|" not in ln or "|NWT|" not in ln:
            continue

        m = pattern.search(ln)
        if not m:
            continue

        row = int(m.group(1))
        col = int(m.group(2))

        parts = ln.split("|")
        # По структуре EV5 второй элемент обычно является ID канала
        try:
            chan_id = int(parts[1])
        except (IndexError, ValueError):
            continue

        mapping[BarrierCell(row=row, col=col)] = chan_id

    if len(mapping) == 0:
        raise ValueError("Не удалось распознать каналы барьера из EV5.")

    return mapping


def resolve_channel_filename(zf: zipfile.ZipFile, chan_id: int) -> Optional[str]:
    """
    В архивах NHTSA имена каналов часто выглядят как v10562.107
    или v10562.107 с ведущими нулями для других тестов.
    Пытаемся найти файл по суффиксу .{chan_id}
    """
    # Сначала прямые варианты
    direct = [f"v10562.{chan_id}", f"v10562.{chan_id:03d}"]
    for name in direct:
        if name in zf.namelist():
            return name

    # Затем поиск по суффиксу
    suffix1 = f".{chan_id:03d}"
    suffix2 = f".{chan_id}"
    for n in zf.namelist():
        if n.endswith(suffix1) or n.endswith(suffix2):
            return n

    return None


def read_channel_series(zf: zipfile.ZipFile, chan_id: int) -> np.ndarray:
    """
    Читает временной ряд канала.
    Обычно формат: время <разделитель> значение.
    Берём второй столбец.
    """
    fname = resolve_channel_filename(zf, chan_id)
    if not fname:
        return np.array([], dtype=float)

    lines = read_text_lines(zf, fname)

    values: List[float] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue

        # Универсальный разбор по пробелам/табам/запятым/точкам с запятой
        parts = re.split(r"[\t,; ]+", s)
        if len(parts) < 2:
            continue

        try:
            values.append(float(parts[1]))
        except ValueError:
            continue

    return np.array(values, dtype=float)


def build_peak_force_matrix(
    zf: zipfile.ZipFile,
    mapping: Dict[BarrierCell, int],
    n_rows: int = 11,
    n_cols: int = 16,
) -> np.ndarray:
    """
    Возвращает матрицу пиковых абсолютных сил F_peak (Н),
    где строка 1 оставлена как NaN (если нет данных),
    а строки 2..11 заполняются по данным барьера.
    """
    F = np.full((n_rows, n_cols), np.nan, dtype=float)

    for cell, chan_id in mapping.items():
        vals = read_channel_series(zf, chan_id)
        if vals.size == 0:
            continue
        F[cell.row - 1, cell.col - 1] = float(np.max(np.abs(vals)))

    return F


def reference_value(F_peak: np.ndarray, mode: str = "mean") -> float:
    """
    Задаёт эталон нормализации для k_ij.
    mode:
      - "mean": среднее по инструментированным ячейкам (рекомендуется)
      - "mean_with_row1_zero": считать NaN как 0 и усреднять по 11x16
      - "median": медиана по инструментированным ячейкам
      - "trimmed_10_90": усечённое среднее 10-90% (для диагностики расхождений)
    """
    mask = np.isfinite(F_peak)
    data = F_peak[mask]

    if data.size == 0:
        raise ValueError("Нет валидных данных для вычисления эталона.")

    if mode == "mean":
        return float(np.mean(data))

    if mode == "mean_with_row1_zero":
        Fz = np.nan_to_num(F_peak, nan=0.0)
        return float(np.mean(Fz))

    if mode == "median":
        return float(np.median(data))

    if mode == "trimmed_10_90":
        s = np.sort(data)
        n = s.size
        i0 = int(np.floor(n * 0.10))
        i1 = int(np.ceil(n * 0.90))
        core = s[i0:i1] if i1 > i0 else s
        return float(np.mean(core))

    raise ValueError(f"Неизвестный mode={mode!r}")


def build_relative_stiffness_matrix(
    F_peak: np.ndarray,
    ref_mode: str = "mean",
) -> np.ndarray:
    """
    Строит матрицу k_ij.
    Строка 1 (неинструментированная) превращается в 0.0.
    Остальные ячейки: F_peak / F_ref.
    """
    F_ref = reference_value(F_peak, mode=ref_mode)

    K = np.zeros_like(F_peak, dtype=float)

    # заполняем только те ячейки, где есть данные
    mask = np.isfinite(F_peak)
    K[mask] = F_peak[mask] / F_ref

    # строка 1 останется 0.0 автоматически
    return K


def to_dataframe(M: np.ndarray, name: str) -> pd.DataFrame:
    rows = list(range(1, M.shape[0] + 1))
    cols = list(range(1, M.shape[1] + 1))
    df = pd.DataFrame(M, index=rows, columns=cols)
    df.index.name = "Row"
    df.columns.name = "Col"
    df.attrs["name"] = name
    return df


def main(zip_path: str | Path | None = None, ref_mode: str = "mean") -> None:
    # 1) Если путь не задан — ищем архив рядом со скриптом
    if zip_path is None:
        script_dir = Path(__file__).resolve().parent
        zip_path = script_dir / "v10562.zip"
    else:
        zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(
            f"Не найден архив: {zip_path}\n"
            f"Положите v10562.zip рядом со скриптом или передайте путь аргументом."
        )

    with zipfile.ZipFile(zip_path) as zf:
        ev5_name = find_ev5_name(zf)
        ev5_lines = read_text_lines(zf, ev5_name)

        mapping = parse_barrier_xg_channels(ev5_lines)
        F_peak = build_peak_force_matrix(zf, mapping)

        K = build_relative_stiffness_matrix(F_peak, ref_mode=ref_mode)

    df_F = to_dataframe(np.nan_to_num(F_peak, nan=0.0), "F_peak_N")
    df_K = to_dataframe(K, f"k_rel_{ref_mode}")

    max_pos = np.unravel_index(np.argmax(df_F.values), df_F.values.shape)
    max_row = max_pos[0] + 1
    max_col = max_pos[1] + 1
    max_val = df_F.values[max_pos]

    F_ref_val = reference_value(F_peak, mode=ref_mode)

    print("Источник: временные ряды каналов барьера (XG, NWT).")
    print(f"Эталон нормализации ref_mode={ref_mode!r}: F_ref = {F_ref_val:.3f} N")
    print(f"Максимальный пик: ячейка {max_row}-{max_col}, F_peak = {max_val:.3f} N")
    print()
    print("Матрица относительной жесткости k_ij:")
    print(df_K.round(3).to_string())


if __name__ == "__main__":
    # Использование:
    # 1) python bild_v1052.py
    #    (если v10562.zip лежит рядом со скриптом)
    #
    # 2) python bild_v1052.py "C:\LatexProj\...\v10562.zip"
    #
    # 3) python bild_v1052.py "C:\...\v10562.zip" mean

    zip_arg = sys.argv[1] if len(sys.argv) > 1 else None
    mode_arg = sys.argv[2] if len(sys.argv) > 2 else "mean"

    main(zip_path=zip_arg, ref_mode=mode_arg)