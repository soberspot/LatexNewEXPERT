import re
import zipfile
from pathlib import Path
import numpy as np

# ------------ I/O helpers ------------

def find_v10562_zip():
    here = Path(__file__).resolve().parent
    candidates = [
        here / "v10562.zip",
        Path.cwd() / "v10562.zip",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Файл v10562.zip не найден. Поместите его рядом со скриптом "
        "или в текущую рабочую папку."
    )

def read_text_from_zip(zf, name):
    return zf.read(name).decode("latin1", errors="ignore")

def read_channel_series(zf, ch):
    fname = f"v10562.{ch:03d}"
    raw = read_text_from_zip(zf, fname).splitlines()
    vals = []
    for ln in raw:
        ln = ln.strip()
        if not ln:
            continue
        parts = re.split(r"\s+", ln)
        if len(parts) < 2:
            continue
        try:
            _t = float(parts[0])
            v = float(parts[1])
        except ValueError:
            continue
        vals.append(v)
    return np.array(vals, dtype=float)

# ------------ EV5 parsing ------------

def parse_barrier_channel_map(ev5_lines):
    """
    Возвращает словарь:
      channel_seq_number -> (row, col)
    Ищет строки, оканчивающиеся на 'BARRIER r-c'.
    """
    mapping = {}
    for ln in ev5_lines:
        if "BARRIER" not in ln.upper():
            continue
        m = re.search(r"BARRIER\s+(\d+)-(\d+)\s*$", ln)
        if not m:
            continue

        parts = ln.split("|")
        if len(parts) < 2:
            continue
        try:
            ch = int(parts[1])
        except ValueError:
            continue

        r = int(m.group(1))
        c = int(m.group(2))
        mapping[ch] = (r, c)

    return mapping

# ------------ Main computation ------------

def build_k_matrix_from_v10562(zip_path: Path):
    with zipfile.ZipFile(zip_path) as zf:
        ev5 = read_text_from_zip(zf, "v10562.EV5")
        lines = ev5.splitlines()

        ch_map = parse_barrier_channel_map(lines)

        # Матрица 11x16. В EV5 реально встречаются ряды 2..11.
        F_peak = np.zeros((11, 16), dtype=float)

        for ch, (r, c) in ch_map.items():
            if not (1 <= r <= 11 and 1 <= c <= 16):
                continue
            try:
                s = read_channel_series(zf, ch)
            except KeyError:
                continue
            if s.size == 0:
                continue

            peak = float(np.max(np.abs(s)))
            F_peak[r-1, c-1] = peak

        nz = F_peak[F_peak > 0]
        if nz.size == 0:
            raise RuntimeError("Не удалось извлечь данные по ячейкам барьера.")

        ref = float(nz.mean())
        K = np.zeros_like(F_peak)
        K[F_peak > 0] = F_peak[F_peak > 0] / ref

        return K

def main():
    zip_path = find_v10562_zip()
    K = build_k_matrix_from_v10562(zip_path)

    np.set_printoptions(precision=3, suppress=True)
    print("v10562.zip:", zip_path)
    print("K shape:", K.shape)
    print("K nonzero mean:", K[K > 0].mean())
    print("K min/max:", K.min(), K.max())
    print("\nK matrix (rows 1..11, cols 1..16):")
    print(K)

if __name__ == "__main__":
    main()
