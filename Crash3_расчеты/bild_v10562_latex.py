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
    return data.decode("latin1", errors="ignore").splitlines()


def find_ev5_name(zf: zipfile.ZipFile) -> str:
    for n in zf.namelist():
        if n.lower().endswith(".ev5"):
            return n
    raise FileNotFoundError("EV5 файл не найден в архиве.")


def parse_barrier_xg_channels(ev5_lines: List[str]) -> Dict[BarrierCell, int]:
    pattern = re.compile(r"BARRIER\s+(\d+)-(\d+)\s*$")
    mapping: Dict[BarrierCell, int] = {}

    for ln in ev5_lines:
        if "BARRIER" not in ln: continue
        if "|LC|" not in ln: continue
        if "|XG|" not in ln or "|NWT|" not in ln: continue

        m = pattern.search(ln)
        if not m: continue

        row = int(m.group(1))
        col = int(m.group(2))
        parts = ln.split("|")
        try:
            chan_id = int(parts[1])
        except (IndexError, ValueError):
            continue
        mapping[BarrierCell(row=row, col=col)] = chan_id

    if len(mapping) == 0:
        raise ValueError("Не удалось распознать каналы барьера из EV5.")
    return mapping


def resolve_channel_filename(zf: zipfile.ZipFile, chan_id: int) -> Optional[str]:
    direct = [f"v10562.{chan_id}", f"v10562.{chan_id:03d}"]
    for name in direct:
        if name in zf.namelist(): return name
    suffix1 = f".{chan_id:03d}"
    suffix2 = f".{chan_id}"
    for n in zf.namelist():
        if n.endswith(suffix1) or n.endswith(suffix2): return n
    return None


def read_channel_series(zf: zipfile.ZipFile, chan_id: int) -> np.ndarray:
    fname = resolve_channel_filename(zf, chan_id)
    if not fname: return np.array([], dtype=float)

    lines = read_text_lines(zf, fname)
    values: List[float] = []
    for ln in lines:
        s = ln.strip()
        if not s: continue
        parts = re.split(r"[\t,; ]+", s)
        if len(parts) < 2: continue
        try:
            values.append(float(parts[1]))
        except ValueError: continue

    return np.array(values, dtype=float)


def build_peak_force_matrix(
    zf: zipfile.ZipFile,
    mapping: Dict[BarrierCell, int],
    n_rows: int = 11,
    n_cols: int = 16,
) -> np.ndarray:
    F = np.full((n_rows, n_cols), np.nan, dtype=float)
    for cell, chan_id in mapping.items():
        vals = read_channel_series(zf, chan_id)
        if vals.size == 0: continue
        F[cell.row - 1, cell.col - 1] = float(np.max(np.abs(vals)))
    return F


def reference_value(F_peak: np.ndarray, mode: str = "mean") -> float:
    mask = np.isfinite(F_peak)
    data = F_peak[mask]
    if data.size == 0: raise ValueError("Нет валидных данных.")

    if mode == "mean": return float(np.mean(data))
    if mode == "mean_with_row1_zero":
        Fz = np.nan_to_num(F_peak, nan=0.0)
        return float(np.mean(Fz))
    if mode == "median": return float(np.median(data))
    if mode == "trimmed_10_90":
        s = np.sort(data)
        n = s.size
        i0 = int(np.floor(n * 0.10))
        i1 = int(np.ceil(n * 0.90))
        core = s[i0:i1] if i1 > i0 else s
        return float(np.mean(core))
    raise ValueError(f"Неизвестный mode={mode!r}")


def build_relative_stiffness_matrix(F_peak: np.ndarray, ref_mode: str = "mean") -> np.ndarray:
    F_ref = reference_value(F_peak, mode=ref_mode)
    K = np.zeros_like(F_peak, dtype=float)
    mask = np.isfinite(F_peak)
    K[mask] = F_peak[mask] / F_ref
    return K


def to_dataframe(M: np.ndarray, name: str) -> pd.DataFrame:
    rows = list(range(1, M.shape[0] + 1))
    cols = list(range(1, M.shape[1] + 1))
    df = pd.DataFrame(M, index=rows, columns=cols)
    df.index.name = "Row"
    df.columns.name = "Col"
    df.attrs["name"] = name
    return df


def save_latex_report(
    filepath: Path,
    df_K: pd.DataFrame,
    stats: dict
) -> None:
    """
    Генерирует .tex файл с таблицей (tabular) для компиляции в XeLaTeX.
    """

    # 1. Формируем заголовок таблицы (номера колонок 1..16)
    # Первое поле пустое (для номера строки)
    header_cells = [f"\\textbf{{{c}}}" for c in df_K.columns]
    header_row = " & ".join([""] + header_cells) + r" \\"

    # 2. Формируем строки таблицы
    table_rows = []
    for idx, row in df_K.iterrows():
        # idx - это номер строки (1..11)
        # Форматируем значения
        row_vals = [f"{x:.2f}" for x in row]
        # Собираем строку: "RowNumber & Val1 & Val2 ..."
        row_str = f"\\textbf{{{idx}}} & " + " & ".join(row_vals) + r" \\"
        table_rows.append(row_str)

    table_body = "\n".join(table_rows)

    # 3. Подготовка тела LaTeX документа
    latex_content = f"""\\documentclass[a4paper,12pt]{{article}}

% === Шрифты и Язык ===
\\usepackage{{fontspec}}
\\usepackage{{polyglossia}}
\\setdefaultlanguage{{russian}}

% Шрифты (Если CMU Serif нет, замените на Times New Roman)
\\setmainfont{{Times New Roman}} 
\\setsansfont{{Times New Roman}}
\\setmonofont{{Times New Roman}}

\\usepackage{{amsmath}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}} % Для красивых линий в таблицах
\\usepackage{{array}}

% Уменьшенные поля для широкой таблицы
\\geometry{{left=1cm, right=1cm, top=2cm, bottom=2cm}}

\\title{{\\textbf{{Отчет по расчету жесткости (NHTSA v10562)}}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\section*{{Параметры расчета}}
\\begin{{itemize}}
    \\item \\textbf{{Режим эталона (Ref Mode):}} {stats['ref_mode']}
    \\item \\textbf{{Эталонная сила ($F_{{ref}}$):}} {stats['F_ref']:.2f} Н
    \\item \\textbf{{Максимальный пик:}} Ячейка {stats['max_row']}-{stats['max_col']} ({stats['max_val']:.2f} Н)
\\end{{itemize}}

\\section*{{Таблица относительной жесткости ($K_{{rel}}$)}}
Ниже представлены значения матрицы $11 \\times 16$, нормализованные относительно $F_{{ref}}$.

\\vspace{{0.5cm}}

% Начало таблицы
\\begin{{table}}[h!]
    \\centering
    % Уменьшаем шрифт, чтобы влезло 17 колонок
    \\scriptsize 
    % Уменьшаем отступы между колонками
    \\setlength{{\\tabcolsep}}{{3pt}} 

    % Описание колонок: r (ряд) + 16 c (данные)
    \\begin{{tabular}}{{r *{{16}}{{c}} }}
        \\toprule
        {header_row}
        \\midrule
        {table_body}
        \\bottomrule
    \\end{{tabular}}
    \\caption{{Матрица распределения относительной жесткости}}
\\end{{table}}

\\section*{{Код для Python (Copy-Paste)}}

\\begin{{verbatim}}
K_REL_INF = np.array([
{", ".join(["[" + ", ".join([f"{x:.2f}" for x in row]) + "]" for row in df_K.values]).replace("],", "],\n")}
], dtype=float)
\\end{{verbatim}}

\\end{{document}}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(latex_content)

    print(f"[OK] LaTeX отчет (таблица) сохранен: {filepath.absolute()}")


def main(zip_path: str | Path | None = None, ref_mode: str = "mean") -> None:
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

    # Статистика
    max_pos = np.unravel_index(np.argmax(df_F.values), df_F.values.shape)
    max_row = max_pos[0] + 1
    max_col = max_pos[1] + 1
    max_val = df_F.values[max_pos]
    F_ref_val = reference_value(F_peak, mode=ref_mode)

    print(f"Эталон нормализации ref_mode={ref_mode!r}: F_ref = {F_ref_val:.2f} N")
    print(f"Максимальный пик: ячейка {max_row}-{max_col}, F_peak = {max_val:.2f} N")
    print("\nМатрица относительной жесткости k_ij (см. output в .tex):")
    print(df_K.round(2).to_string())

    # Сохранение
    stats = {
        'ref_mode': ref_mode,
        'F_ref': F_ref_val,
        'max_row': max_row,
        'max_col': max_col,
        'max_val': max_val
    }

    out_name = f"report_{zip_path.stem}.tex"
    save_latex_report(Path(out_name), df_K, stats)


if __name__ == "__main__":
    zip_arg = sys.argv[1] if len(sys.argv) > 1 else None
    mode_arg = sys.argv[2] if len(sys.argv) > 2 else "mean"
    main(zip_path=zip_arg, ref_mode=mode_arg)