"""07 - Skenario kapasitas (Q9-Q11) dan cek fakta yang ditanam (Q13).

Dua basis kapasitas (dipisah agar tidak tercampur dalam satu perbandingan):
- standar : n × 8 jam × 3600 ÷ CT median stasiun-model. Dipakai untuk peringkat bottleneck dan output lini.
- efektif : n ÷ Σ(1 ÷ CT operator) = CT harmonik. Dipakai untuk skenario operator (Q10), karena
            kapasitas operator dijumlahkan dari masing-masing operator. Baseline ikut basis efektif.
Semua angka skenario diberi label estimated.

Output: results/2-analysis/capacity_scenarios.csv (Q9-Q11)
        results/2-analysis/q13_ground_truth_check.csv (Q13)
"""
import json
import math
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, GT_DIR, HOURS_NORMAL, MODELS, RAW_DIR, RES_ANALYSIS, RES_PREP  # noqa: E402

SEC = HOURS_NORMAL * 3600
con = duckdb.connect(str(DB_PATH), read_only=True)
cap = con.sql("SELECT * FROM v_station_capacity").df()
op = con.sql("SELECT * FROM v_operator_ct WHERE n_hari >= 5").df()
con.close()
PLANT_SLOW, PLANT_FAST = "Op_03", "Op_22"


def line_output(caps):
    """caps: dict stasiun -> kapasitas. Output lini = kapasitas stasiun terendah."""
    s = min(caps, key=caps.get)
    return caps[s], s


rows = []
for m in MODELS:
    c = cap[cap["model"] == m]
    std = dict(zip(c["station"], c["kapasitas_unit_per_hari"]))
    base_out, bn_name = line_output(std)
    bn = c[c["station"] == bn_name].iloc[0]
    second_name = sorted(std, key=std.get)[1]
    second = c[c["station"] == second_name].iloc[0]

    def add(skenario, stasiun, ct_lama, ct_baru, caps_new, base, note, kenaikan_st=None):
        out_new, bn_new = line_output(caps_new)
        rows.append({"model": m, "skenario": skenario, "stasiun": stasiun,
                     "ct_lama_s": round(ct_lama, 1), "ct_baru_s": round(ct_baru, 1),
                     "kenaikan_kapasitas_stasiun": round(kenaikan_st if kenaikan_st is not None
                                                         else ct_lama / ct_baru - 1, 4),
                     "output_lini_baru": round(out_new, 1), "kenaikan_output_lini": round(out_new / base - 1, 4),
                     "bottleneck_baru": bn_new, "catatan": note})

    # A. CT bottleneck turun 10/20/30% (basis standar)
    for x in (0.10, 0.20, 0.30):
        ct_new = bn["ct_median_s"] * (1 - x)
        caps = dict(std)
        caps[bn_name] = bn["n_operator_aktif"] * SEC / ct_new
        add(f"bottleneck CT turun {int(x * 100)}%", bn_name, bn["ct_median_s"], ct_new, caps, base_out,
            "estimated; bottleneck berpindah jika kapasitasnya melewati stasiun kedua" if x == 0.30 else "estimated")

    # B. Stasiun kedua (bukan bottleneck) CT turun 30%: output tidak naik
    ct_new = second["ct_median_s"] * 0.70
    caps = dict(std)
    caps[second_name] = second["n_operator_aktif"] * SEC / ct_new
    add("stasiun bukan bottleneck CT turun 30%", second_name, second["ct_median_s"], ct_new, caps, base_out,
        "estimated; output tidak naik karena bottleneck tetap")

    # C. Operator bottleneck mencapai median / tercepat (basis efektif)
    ops = op[(op["model"] == m) & (op["station"] == bn_name)].sort_values("ct_median_s")
    n = len(ops)
    ct_eff = lambda ct: n / (1 / ct).sum()  # noqa: E731
    ct_lama = ct_eff(ops["ct_median_s"])
    med = ops["ct_median_s"].median()
    base_eff_caps = dict(std)
    base_eff_caps[bn_name] = n * SEC / ct_lama
    base_eff, _ = line_output(base_eff_caps)
    for label, ct_new, note in [
        ("operator bottleneck mencapai median", ct_eff(ops["ct_median_s"].clip(upper=med)),
         "operator di atas median turun ke median"),
        ("operator bottleneck mencapai tercepat", ops["ct_median_s"].min(),
         "semua operator setara dengan operator tercepat"),
    ]:
        caps = dict(std)
        caps[bn_name] = n * SEC / ct_new
        add(label, bn_name, ct_lama, ct_new, caps, base_eff, "estimated; " + note)
        rows[-1]["kenaikan_kapasitas_stasiun"] = round(ct_lama / ct_new - 1, 4)

    # D. Operator tambahan untuk target output +10% (basis standar)
    target = base_out * 1.10
    cap_per_op = SEC / bn["ct_median_s"]
    need = max(0, math.ceil(target / cap_per_op) - int(bn["n_operator_aktif"]))
    caps = dict(std)
    caps[bn_name] = (int(bn["n_operator_aktif"]) + need) * cap_per_op
    out_new, bn_new = line_output(caps)
    other_min = min(v for k, v in std.items() if k != bn_name)
    rows.append({"model": m, "skenario": "operator tambahan minimal untuk target output +10%", "stasiun": bn_name,
                 "ct_lama_s": round(bn["ct_median_s"], 1), "ct_baru_s": round(bn["ct_median_s"], 1),
                 "kenaikan_kapasitas_stasiun": round(need / bn["n_operator_aktif"], 4),
                 "output_lini_baru": round(out_new, 1), "kenaikan_output_lini": round(out_new / base_out - 1, 4),
                 "bottleneck_baru": bn_new,
                 "catatan": f"estimated; tambahan {need} operator; kapasitas stasiun kedua {second_name} "
                            f"{other_min:.0f}/hari" if target <= other_min else
                            f"estimated; tambahan {need} operator tidak cukup, bottleneck pindah ke {second_name}"})

out = pd.DataFrame(rows)
out.to_csv(RES_ANALYSIS / "capacity_scenarios.csv", index=False)
print(out[["model", "skenario", "stasiun", "ct_lama_s", "ct_baru_s", "output_lini_baru",
           "kenaikan_output_lini", "bottleneck_baru"]].to_string(index=False))

# ---------- Q13: cek fakta yang ditanam
gt = json.loads((GT_DIR / "ground_truth.json").read_text(encoding="utf-8"))
q1 = pd.read_csv(RES_ANALYSIS / "q1_capacity.csv")
q4 = pd.read_csv(RES_ANALYSIS / "q4_operator.csv")
q7 = pd.read_csv(RES_ANALYSIS / "q7_shift_overtime.csv")
clean_log = pd.read_csv(RES_PREP / "02_cleaning_log.csv")

avg_rank = q1.groupby("station")["peringkat_bottleneck"].mean().sort_values()
per_model = lambda st, fn: q4[q4["station"] == st].groupby("model")["deviasi"].agg(fn).index  # noqa: E731
spp = q4[q4["station"] == "Solder Paste Printing"]
tht = q4[q4["station"] == "THT Insertion"]
top_spp = spp.loc[spp.groupby("model")["deviasi"].idxmax(), "operator_id"]
low_tht = tht.loc[tht.groupby("model")["deviasi"].idxmin(), "operator_id"]
ot = q7.pivot_table(index="shift", columns="kondisi", values="rasio_ct_per_standar")
ot_ratio = ot["lembur (10 jam)"] / ot["normal (8 jam)"] - 1


def dropped(rule):
    r = clean_log[(clean_log["langkah"] == rule) & (clean_log["status"] == "dibuang")]
    return int(r["baris"].iloc[0]) if len(r) else 0


def rincian(rule):
    r = clean_log[(clean_log["langkah"] == rule) & (clean_log["status"] == "rincian")]
    return int(r["baris"].iloc[0]) if len(r) else 0


orphan_hilang = dropped("output tanpa jam kerja") - rincian("output tanpa jam kerja akibat jam kerja dibuang")
checks = [
    ("bottleneck utama: Wave Soldering", gt["bottleneck_utama"], avg_rank.index[0],
     avg_rank.index[0] == gt["bottleneck_utama"]),
    ("bottleneck kedua: Solder Paste Printing", gt["bottleneck_kedua"], avg_rank.index[1],
     avg_rank.index[1] == gt["bottleneck_kedua"]),
    ("operator lambat Op_03 di SPP: deviasi terbesar di 3 model", f"+{gt['operator_lambat']['faktor_steady'] - 1:.0%} (steady)",
     f"deviasi rata-rata {spp.loc[spp['operator_id'] == PLANT_SLOW, 'deviasi'].mean():+.1%}; terbesar di {int((top_spp == PLANT_SLOW).sum())} dari 3 model",
     bool((top_spp == PLANT_SLOW).all())),
    ("operator cepat Op_22 di THT: deviasi terkecil di 3 model", f"−{1 - gt['operator_cepat']['faktor']:.0%}",
     f"deviasi rata-rata {tht.loc[tht['operator_id'] == PLANT_FAST, 'deviasi'].mean():+.1%}; terkecil di {int((low_tht == PLANT_FAST).sum())} dari 3 model",
     bool((low_tht == PLANT_FAST).all())),
    ("lembur ±5% lebih lambat dari normal (kedua shift)", f"+{gt['lembur']['faktor_ct'] - 1:.0%}",
     f"A {ot_ratio['A']:+.1%}; B {ot_ratio['B']:+.1%}",
     bool(((ot_ratio > 0.03) & (ot_ratio < 0.07)).all())),
    ("data kotor: jam kerja > 12 jam", 25, dropped("jam kerja lebih dari 12 jam"),
     dropped("jam kerja lebih dari 12 jam") == 25),
    ("data kotor: ok negatif", 20, dropped("ok atau ng negatif"), dropped("ok atau ng negatif") == 20),
    ("data kotor: baris ganda", 40, dropped("baris ganda (semua kolom sama)"),
     dropped("baris ganda (semua kolom sama)") == 40),
    ("data kotor: operator tidak terdaftar (Op_99)", 10, dropped("operator tidak ada di dim_operator"),
     dropped("operator tidak ada di dim_operator") == 10),
    ("data kotor: jam kerja hilang → output tanpa jam kerja (30 × 3 model)", 90, orphan_hilang,
     orphan_hilang == 90),
]
res = pd.DataFrame(checks, columns=["fakta", "ground_truth", "temuan_analisis", "status"])
res["status"] = res["status"].map({True: "DITEMUKAN", False: "TIDAK"})
res.to_csv(RES_ANALYSIS / "q13_ground_truth_check.csv", index=False)
print(res.to_string(index=False))
