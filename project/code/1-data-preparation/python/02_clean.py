"""02 - Membersihkan data simulasi dan mencatat setiap baris yang dibuang (Q12).

Input : project/data/raw/*.csv
Output: project/data/clean/daily_output_clean.csv, work_hours_clean.csv, dim_operator_clean.csv (tidak di-commit)
        project/results/1-data-preparation/02_cleaning_log.csv   (jumlah baris per aturan)
        project/results/1-data-preparation/02_dropped_rows.csv   (satu baris per baris yang dibuang)
        project/results/1-data-preparation/02_profile.csv        (profil mentah per tabel)
        project/results/1-data-preparation/02_cleaning_impact.csv (angka KPI sebelum dan sesudah cleaning)

Urutan aturan penting: jam kerja diperiksa dulu, lalu output yang kehilangan jam kerja ikut dibuang.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_DIR, MAX_HOURS_VALID, RAW_DIR, RES_PREP  # noqa: E402

out = pd.read_csv(RAW_DIR / "daily_output.csv")
wrk = pd.read_csv(RAW_DIR / "work_hours.csv")
dim_op = pd.read_csv(RAW_DIR / "dim_operator.csv")
dim_st = pd.read_csv(RAW_DIR / "dim_station.csv")

# ---------- profil mentah
prof = []
for name, d in [("daily_output", out), ("work_hours", wrk), ("dim_operator", dim_op), ("dim_station", dim_st)]:
    prof.append({"tabel": name, "baris": len(d), "kolom": d.shape[1],
                 "kosong_total": int(d.isna().sum().sum()),
                 "tanggal_min": d["date"].min() if "date" in d else "",
                 "tanggal_max": d["date"].max() if "date" in d else ""})
pd.DataFrame(prof).to_csv(RES_PREP / "02_profile.csv", index=False)

log, dropped = [], []


def drop(df, mask, rule, tabel, note=""):
    """Buang baris yang cocok dengan mask, catat jumlahnya, kembalikan df sisa."""
    sub = df[mask]
    log.append({"langkah": rule, "tabel": tabel, "status": "dibuang", "baris": int(len(sub)), "catatan": note})
    for r in sub.itertuples(index=False):
        dropped.append({"tabel": tabel, "aturan": rule, "date": getattr(r, "date", ""),
                        "operator_id": getattr(r, "operator_id", ""), "model": getattr(r, "model", ""),
                        "ok_qty": getattr(r, "ok_qty", ""), "effective_hours": getattr(r, "effective_hours", "")})
    return df[~mask]


log.append({"langkah": "baris mentah daily_output", "tabel": "daily_output", "status": "total",
            "baris": len(out), "catatan": ""})
log.append({"langkah": "baris mentah work_hours", "tabel": "work_hours", "status": "total",
            "baris": len(wrk), "catatan": ""})

# ---------- 1. jam kerja
wrk = drop(wrk, wrk["effective_hours"] > MAX_HOURS_VALID, "jam kerja lebih dari 12 jam", "work_hours",
           "dibuang; output operator-hari itu ikut dibuang (lihat 'output tanpa jam kerja')")
wrk = drop(wrk, wrk["effective_hours"] <= 0, "jam kerja nol atau negatif", "work_hours")
dup_w = wrk.duplicated(["date", "operator_id"], keep="first")
wrk = drop(wrk, dup_w, "jam kerja ganda (operator dan tanggal sama)", "work_hours")

# ---------- 2. operator
op_ok = dim_op.dropna(subset=["station"])
no_station = set(dim_op.loc[dim_op["station"].isna(), "operator_id"])
wrk = drop(wrk, wrk["operator_id"].isin(no_station), "operator tanpa stasiun", "work_hours")

# ---------- 3. output
out = drop(out, out.duplicated(keep="first"), "baris ganda (semua kolom sama)", "daily_output")
out = drop(out, ~out["operator_id"].isin(dim_op["operator_id"]), "operator tidak ada di dim_operator",
           "daily_output", "operator_id tidak terdaftar")
out = drop(out, out["operator_id"].isin(no_station), "operator tanpa stasiun", "daily_output")
out = drop(out, (out["ok_qty"] < 0) | (out["ng_qty"] < 0), "ok atau ng negatif", "daily_output")
out = drop(out, out["run_hours"] <= 0, "run_hours nol atau negatif", "daily_output")

# ---------- 4. kaitan output dan jam kerja
key_w = set(zip(wrk["date"], wrk["operator_id"]))
key_w_all = set(zip(pd.read_csv(RAW_DIR / "work_hours.csv")["date"],
                    pd.read_csv(RAW_DIR / "work_hours.csv")["operator_id"]))
orphan = pd.Series([k not in key_w for k in zip(out["date"], out["operator_id"])], index=out.index)
orphan_raw_lost = orphan & pd.Series([k in key_w_all for k in zip(out["date"], out["operator_id"])],
                                     index=out.index)
log.append({"langkah": "output tanpa jam kerja akibat jam kerja dibuang", "tabel": "daily_output",
            "status": "rincian", "baris": int(orphan_raw_lost.sum()),
            "catatan": "jam kerja-nya ada di data mentah tetapi dibuang di langkah 1 atau 2"})
out = drop(out, orphan, "output tanpa jam kerja", "daily_output",
           "termasuk yang jam kerjanya dihapus dari sumber (lihat log)")

# ---------- 5. cek konsistensi: jumlah run_hours = jam efektif (hanya operator-hari yang tidak tersentuh pembuangan)
touched = {(d["date"], d["operator_id"]) for d in dropped}
s = out.groupby(["date", "operator_id"])["run_hours"].sum().round(2)
e = wrk.set_index(["date", "operator_id"])["effective_hours"]
joined = pd.concat([s.rename("run"), e.rename("eff")], axis=1).dropna()
joined = joined[[k not in touched for k in joined.index]]
mismatch = int((abs(joined["run"] - joined["eff"]) > 0.05).sum())
log.append({"langkah": "cek: jumlah run_hours = jam efektif (operator-hari tanpa baris dibuang)",
            "tabel": "daily_output", "status": "dicatat", "baris": mismatch,
            "catatan": f"operator-hari dicek: {len(joined)}; 0 = konsisten"})

# ---------- simpan
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
out = out.sort_values(["date", "station", "operator_id", "model"]).reset_index(drop=True)
wrk = wrk.sort_values(["date", "operator_id"]).reset_index(drop=True)
out.to_csv(CLEAN_DIR / "daily_output_clean.csv", index=False)
wrk.to_csv(CLEAN_DIR / "work_hours_clean.csv", index=False)
op_ok.to_csv(CLEAN_DIR / "dim_operator_clean.csv", index=False)

log.append({"langkah": "baris bersih daily_output", "tabel": "daily_output", "status": "total",
            "baris": len(out), "catatan": ""})
log.append({"langkah": "baris bersih work_hours", "tabel": "work_hours", "status": "total",
            "baris": len(wrk), "catatan": ""})
pd.DataFrame(log).to_csv(RES_PREP / "02_cleaning_log.csv", index=False)
pd.DataFrame(dropped).to_csv(RES_PREP / "02_dropped_rows.csv", index=False)

# ---------- dampak cleaning terhadap angka KPI (Q12)
def kpi(o):
    o = o.copy()
    o["ct"] = o["run_hours"] * 3600 / o["ok_qty"].where(o["ok_qty"] > 0)
    st = o.groupby("station")["ct"].median()
    return {"total_ok": int(o.loc[o["ok_qty"] > 0, "ok_qty"].sum()),
            "median_ct_wave_s": round(float(st.get("Wave Soldering", float("nan"))), 1),
            "median_ct_spp_s": round(float(st.get("Solder Paste Printing", float("nan"))), 1),
            "baris_ok_negatif": int((o["ok_qty"] < 0).sum())}


raw_out = pd.read_csv(RAW_DIR / "daily_output.csv")
impact = pd.DataFrame([{"ukuran": k, "sebelum_cleaning": v, "sesudah_cleaning": kpi(out)[k]}
                       for k, v in kpi(raw_out).items()])
impact.to_csv(RES_PREP / "02_cleaning_impact.csv", index=False)
print(pd.DataFrame(log)[["langkah", "status", "baris"]].to_string(index=False))
print(impact.to_string(index=False))
