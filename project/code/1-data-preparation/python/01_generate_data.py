"""01 - Membuat data simulasi lini PCBA dengan seed tetap, termasuk fakta yang ditanam dan data kotor.

Output (project/data/raw/):
  daily_output.csv        satu baris = satu operator, satu hari, satu model
  work_hours.csv          satu baris = satu operator, satu hari
  dim_station.csv         standar cycle time per stasiun dan model
  dim_operator.csv        daftar operator
  dirty_injection_log.csv jumlah data kotor yang sengaja disisipkan
Output (project/data/):
  ground_truth.json       kunci jawaban: fakta yang ditanam dan jumlah data kotor
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import (GT_DIR, HOURS_NORMAL, HOURS_OVERTIME, MODELS, N_WORKDAYS,  # noqa: E402
                    RAW_DIR, SEED, START_DATE)

rng = np.random.default_rng(SEED)

# (stasiun, CT standar 2-layer, 4-layer, 8-layer) dalam detik per unit OK
STATIONS = [
    ("Solder Paste Printing", 170, 180, 200),
    ("SPI (Solder Paste Inspection)", 120, 130, 150),
    ("Pick & Place", 150, 165, 185),
    ("Reflow Soldering", 140, 150, 165),
    ("AOI (Automated Optical Inspection)", 110, 115, 130),
    ("THT Insertion", 135, 150, 170),
    ("Wave Soldering", 230, 245, 270),   # bottleneck yang ditanam
    ("ICT", 120, 130, 145),
    ("FCT", 140, 150, 165),
    ("Packing", 90, 95, 105),
]
N_OP_PER_STATION = 4
OT_PROB = 0.25                 # 1 dari 4 hari adalah hari lembur (berlaku untuk seluruh lini)
OT_MULT = 1.05                 # fakta 4: CT hari lembur 5% lebih lambat
ABSENT_PROB = 0.03
NG_RATE = (0.005, 0.03)        # rentang laju NG per baris
PLANT_SLOW_OP = "Op_03"        # fakta 2: operator baru di Solder Paste Printing
PLANT_FAST_OP = "Op_22"        # fakta 3: operator THT Insertion yang lebih cepat
SLOW_STEADY = 1.25             # setelah masa belajar: 25% lebih lambat dari median
SLOW_START = 1.40              # hari pertama, turun linear sampai SLOW_STEADY
LEARN_DAYS = 20                # ±4 minggu kerja
FAST_FACTOR = 0.80             # 20% lebih cepat

# ---------- operator dan tanggal
station_names = [s[0] for s in STATIONS]
ops = []
for si, st in enumerate(station_names):
    for k in range(N_OP_PER_STATION):
        idx = si * N_OP_PER_STATION + k + 1
        ops.append({"operator_id": f"Op_{idx:02d}", "station": st,
                    "shift": "A" if k < N_OP_PER_STATION // 2 else "B"})
dim_op = pd.DataFrame(ops)
start = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 600, len(dim_op)), unit="D")
dim_op["start_date"] = start.strftime("%Y-%m-%d")
dim_op["status"] = "reguler"
dim_op.loc[dim_op["operator_id"] == PLANT_SLOW_OP, ["start_date", "status"]] = [START_DATE, "baru"]

base = {o: rng.normal(1.0, 0.03) for o in dim_op["operator_id"]}   # variasi alami antar operator
days = pd.bdate_range(START_DATE, periods=N_WORKDAYS)
is_ot = {d: bool(rng.random() < OT_PROB) for d in days}

std = {(s[0], m): s[1 + j] for s in STATIONS for j, m in enumerate(MODELS)}
stn_of = dict(zip(dim_op["operator_id"], dim_op["station"]))
shift_of = dict(zip(dim_op["operator_id"], dim_op["shift"]))


def op_factor(op, day_idx):
    if op == PLANT_SLOW_OP:
        return SLOW_STEADY + (SLOW_START - SLOW_STEADY) * max(0.0, 1 - day_idx / LEARN_DAYS)
    if op == PLANT_FAST_OP:
        return FAST_FACTOR
    return 1.0


work_rows, out_rows = [], []
for di, d in enumerate(days):
    ds = d.strftime("%Y-%m-%d")
    for op in dim_op["operator_id"]:
        if rng.random() < ABSENT_PROB:
            continue
        ot = is_ot[d]
        eff = HOURS_OVERTIME if ot else HOURS_NORMAL
        work_rows.append({"date": ds, "operator_id": op, "effective_hours": float(eff),
                          "is_overtime": int(ot)})
        share = rng.dirichlet([4, 4, 4])
        hrs = np.round(share * eff, 2)
        hrs[-1] = round(eff - hrs[:-1].sum(), 2)          # total jam tepat sama dengan jam efektif
        for m, h in zip(MODELS, hrs):
            ct = std[(stn_of[op], m)] * op_factor(op, di) * base[op] * (OT_MULT if ot else 1.0)
            ct *= np.exp(rng.normal(0, 0.04))
            ok = int(round(h * 3600 / ct))
            ng = int(round(ok * rng.uniform(*NG_RATE)))
            out_rows.append({"date": ds, "shift": shift_of[op], "station": stn_of[op], "operator_id": op,
                             "model": m, "run_hours": float(h), "ok_qty": ok, "ng_qty": ng})

work = pd.DataFrame(work_rows)
out = pd.DataFrame(out_rows)
log = []

# ---------- data kotor (±2–3% dari baris) ----------
def pick(df, n):
    return rng.choice(df.index.to_numpy(), size=n, replace=False)

# a. jam kerja hilang, output tetap ada
idx = pick(work, 30)
log.append(("jam kerja hilang (output tetap ada)", "work_hours", len(idx),
            "baris jam kerja dihapus; output operator-hari itu tetap ada"))
work = work.drop(idx)

# b. jam kerja tidak wajar (> 12 jam)
idx = pick(work, 25)
work.loc[idx, "effective_hours"] = np.round(rng.uniform(12.5, 16.0, len(idx)), 1)
log.append(("jam kerja lebih dari 12 jam", "work_hours", len(idx), "effective_hours diubah menjadi 12,5–16"))

# c. output negatif
idx = pick(out, 20)
out.loc[idx, "ok_qty"] = -rng.integers(1, 15, len(idx))
log.append(("ok_qty negatif", "daily_output", len(idx), "ok_qty diubah menjadi nilai negatif"))

# d. baris ganda
idx = pick(out, 40)
out = pd.concat([out, out.loc[idx]], ignore_index=True)
log.append(("baris ganda", "daily_output", len(idx), "baris persis sama disisipkan"))

# e. operator tidak ada di daftar operator
extra = out.sample(10, random_state=SEED).copy()
extra["operator_id"] = "Op_99"
extra["station"] = "Packing"
out = pd.concat([out, extra], ignore_index=True)
log.append(("operator tidak ada di dim_operator", "daily_output", len(extra), "operator_id = Op_99"))

# f. operator tanpa stasiun (di dim_operator station kosong)
blank_days = days[:5]
ex_out = pd.DataFrame([{"date": d.strftime("%Y-%m-%d"), "shift": "B", "station": "Packing",
                        "operator_id": "Op_41", "model": MODELS[0], "run_hours": 2.67,
                        "ok_qty": 110, "ng_qty": 2} for d in blank_days])
ex_work = pd.DataFrame([{"date": d.strftime("%Y-%m-%d"), "operator_id": "Op_41",
                         "effective_hours": 8.0, "is_overtime": 0} for d in blank_days])
out = pd.concat([out, ex_out], ignore_index=True)
work = pd.concat([work, ex_work], ignore_index=True)
dim_op = pd.concat([dim_op, pd.DataFrame([{"operator_id": "Op_41", "station": None, "shift": "B",
                                           "start_date": "2025-06-01", "status": "reguler"}])],
                   ignore_index=True)
log.append(("operator tanpa stasiun (dim_operator)", "dim_operator", 1,
            "Op_41 tanpa stasiun; 5 hari output dan jam kerja ikut ada"))

# ---------- simpan ----------
out = out.sort_values(["date", "station", "operator_id", "model"]).reset_index(drop=True)
work = work.sort_values(["date", "operator_id"]).reset_index(drop=True)
dim_station = pd.DataFrame([{"station": s[0], "sequence": i + 1, "ct_std_2layer_s": s[1],
                             "ct_std_4layer_s": s[2], "ct_std_8layer_s": s[3], "n_operator": N_OP_PER_STATION}
                            for i, s in enumerate(STATIONS)])

RAW_DIR.mkdir(parents=True, exist_ok=True)
out.to_csv(RAW_DIR / "daily_output.csv", index=False)
work.to_csv(RAW_DIR / "work_hours.csv", index=False)
dim_station.to_csv(RAW_DIR / "dim_station.csv", index=False)
dim_op.to_csv(RAW_DIR / "dim_operator.csv", index=False)
pd.DataFrame(log, columns=["jenis", "tabel", "jumlah_baris", "catatan"]).to_csv(
    RAW_DIR / "dirty_injection_log.csv", index=False)

gt = {
    "seed": SEED,
    "bottleneck_utama": "Wave Soldering",
    "bottleneck_kedua": "Solder Paste Printing",
    "operator_lambat": {"operator_id": PLANT_SLOW_OP, "station": "Solder Paste Printing",
                        "faktor_steady": SLOW_STEADY, "faktor_awal": SLOW_START,
                        "hari_belajar": LEARN_DAYS, "status": "baru"},
    "operator_cepat": {"operator_id": PLANT_FAST_OP, "station": "THT Insertion", "faktor": FAST_FACTOR},
    "lembur": {"faktor_ct": OT_MULT, "jam_normal": HOURS_NORMAL, "jam_lembur": HOURS_OVERTIME,
               "hari_lembur": int(sum(is_ot.values()))},
    "data_kotor": [{"jenis": r[0], "tabel": r[1], "jumlah_baris": int(r[2])} for r in log],
    "jumlah_baris": {"daily_output": int(len(out)), "work_hours": int(len(work)), "dim_operator": int(len(dim_op))},
}
(GT_DIR / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print("daily_output", len(out), "work_hours", len(work), "operator", len(dim_op))
