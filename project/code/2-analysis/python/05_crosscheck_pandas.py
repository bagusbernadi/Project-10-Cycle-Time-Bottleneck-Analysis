"""05 - Cek silang SQL vs pandas: CT per operator, kapasitas stasiun, dan rasio CT per standar.

Output: project/results/2-analysis/04_crosscheck_sql_pandas.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_DIR, HOURS_NORMAL, RES_ANALYSIS  # noqa: E402

o = pd.read_csv(CLEAN_DIR / "daily_output_clean.csv")
w = pd.read_csv(CLEAN_DIR / "work_hours_clean.csv")
d = pd.read_csv(CLEAN_DIR / "dim_operator_clean.csv")
st = pd.read_csv(Path(CLEAN_DIR).parents[1] / "data" / "raw" / "dim_station.csv")
o = o[o["ok_qty"] > 0].merge(w[["date", "operator_id", "is_overtime"]], on=["date", "operator_id"])
o["ct"] = o["run_hours"] * 3600 / o["ok_qty"]
std_map = {"2-layer": "ct_std_2layer_s", "4-layer": "ct_std_4layer_s", "8-layer": "ct_std_8layer_s"}
o["ct_std"] = [st.set_index("station").loc[s, std_map[m]] for s, m in zip(o["station"], o["model"])]

# CT median per operator (hari >= 5)
days = o.groupby(["operator_id", "station", "model"])["date"].nunique().rename("n_hari").reset_index()
med = o.groupby(["operator_id", "station", "model"])["ct"].median().rename("ct_median_s").reset_index()
op = med.merge(days, on=["operator_id", "station", "model"])
op = op[op["n_hari"] >= 5]
sql_op = pd.read_csv(RES_ANALYSIS / "q4_operator.csv")
m = op.merge(sql_op, on=["operator_id", "station", "model"], suffixes=("_pd", "_sql"))
max_diff_op = float((m["ct_median_s_pd"].round(1) - m["ct_median_s_sql"]).abs().max())

# Kapasitas stasiun-model
stm = o.groupby(["station", "model"])["ct"].median().rename("ct_med").reset_index()
nop = op.groupby(["station", "model"]).size().rename("n").reset_index()
cap = stm.merge(nop, on=["station", "model"])
cap["kap"] = cap["n"] * HOURS_NORMAL * 3600 / cap["ct_med"]
sql_cap = pd.read_csv(RES_ANALYSIS / "q1_capacity.csv")
c = cap.merge(sql_cap, on=["station", "model"])
max_diff_cap = float((c["kap"] - c["kapasitas_unit_per_hari"]).abs().max())

# Rasio CT per standar, normal vs lembur, per shift
sql7 = pd.read_csv(RES_ANALYSIS / "q7_shift_overtime.csv")
r = (o.assign(rasio=o["ct"] / o["ct_std"])
       .groupby(["shift", "is_overtime"])["rasio"].median().round(3).reset_index())
r["kondisi"] = r["is_overtime"].map({1: "lembur (10 jam)", 0: "normal (8 jam)"})
mm = r.merge(sql7, on=["shift", "kondisi"])
max_diff_ratio = float((mm["rasio"] - mm["rasio_ct_per_standar"]).abs().max())

out = pd.DataFrame([
    {"cek": "CT median per operator (q4) vs pandas", "jumlah_nilai": len(m), "selisih_maks": round(max_diff_op, 2),
     "toleransi": 0.05, "status": "PASS" if max_diff_op <= 0.05 else "FAIL"},
    {"cek": "kapasitas stasiun-model (q1) vs pandas", "jumlah_nilai": len(c), "selisih_maks": round(max_diff_cap, 2),
     "toleransi": 0.05, "status": "PASS" if max_diff_cap <= 0.05 else "FAIL"},
    {"cek": "rasio CT per standar shift x lembur (q7) vs pandas", "jumlah_nilai": len(mm),
     "selisih_maks": round(max_diff_ratio, 3), "toleransi": 0.001,
     "status": "PASS" if max_diff_ratio <= 0.001 else "FAIL"},
])
out.to_csv(RES_ANALYSIS / "04_crosscheck_sql_pandas.csv", index=False)
print(out.to_string(index=False))
