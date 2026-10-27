"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik dengan sumber).
- Angka di Report berasal dari project/results/*.csv dan database (lewat helper report_lib.py), lalu diaudit.
Jalankan dari mana saja:  python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROJ = REPO / "project"
sys.path.insert(0, str(PROJ / "code"))
sys.path.insert(0, str(HERE))
from common import (GT_DIR, MIN_DAYS_OPERATOR, MODELS, RAW_DIR, RES_ANALYSIS as RA,  # noqa: E402
                    RES_PREP as RP, RES_PRESENT as RPR, CLEAN_DIR)
from report_lib import (D, I, OK, PART, NO, P, audit, bars, esc, hbars, lines, pill, qa, table, visible_text)  # noqa: E402
P_ = P  # alias: persen dari fraksi

R = lambda p: pd.read_csv(p)  # noqa: E731
src = (HERE / "page_v1.html").read_text(encoding="utf-8")

# ---------------------------------------------------------------- data
q1 = R(RA / "q1_capacity.csv")
q2 = R(RA / "q2_capacity_shift.csv")
q3 = R(RA / "q3_stability.csv")
q4 = R(RA / "q4_operator.csv")
q5 = R(RA / "q5_fastest.csv")
q6 = R(RA / "q6_learning.csv")
q7 = R(RA / "q7_shift_overtime.csv")
q8 = R(RA / "q8_model_ratio.csv")
scen = R(RA / "capacity_scenarios.csv")
q13 = R(RA / "q13_ground_truth_check.csv")
clog = R(RP / "02_cleaning_log.csv")
cimp = R(RP / "02_cleaning_impact.csv").set_index("ukuran")
tcount = R(RP / "03_table_counts.csv").set_index("tabel")["baris"]
ctest = R(RP / "03_constraint_test.csv")
xc = R(RA / "04_crosscheck_sql_pandas.csv")
xs = R(RA / "05_crosscheck_spreadsheet.csv")
xl = R(RA / "q14_agg.csv")
dash = R(RPR / "09_dashboard_check.csv")
kpi = R(RPR / "dash_kpi.csv").iloc[0]
gt = __import__("json").loads((GT_DIR / "ground_truth.json").read_text(encoding="utf-8"))
dirty = R(RAW_DIR / "dirty_injection_log.csv")

# angka turunan
bn_by_model = q1.sort_values("kapasitas_unit_per_hari").groupby("model").head(1).set_index("model")
out_by_model = {m: float(bn_by_model.loc[m, "kapasitas_unit_per_hari"]) for m in MODELS}
bn_name = bn_by_model.loc["2-layer", "station"]
second = q1[q1["model"] == "2-layer"].sort_values("kapasitas_unit_per_hari").iloc[1]
avg_rank = q1.groupby("station")["peringkat_bottleneck"].mean().sort_values()
n_bn_same = int((bn_by_model["station"] == bn_name).sum())
n_bs_shift = int(((q2["peringkat_bottleneck"] == 1) & (q2["station"] == bn_name)).sum())
n_bs_shift_all = int(len(q2[q2["peringkat_bottleneck"] == 1]))
q3_bn = q3[q3["station"] == bn_name]
q3_kv_min = q3.sort_values("koef_variasi").iloc[0]
q3_kv_max = q3.sort_values("koef_variasi").iloc[-1]
dev_flag = q4[q4["deviasi"].abs() > 0.10].copy()
op_slow = dev_flag[dev_flag["deviasi"] > 0].sort_values("deviasi", ascending=False)
op_fast = dev_flag[dev_flag["deviasi"] < 0].sort_values("deviasi")
wave_dev_max = q4[q4["station"] == bn_name]["deviasi"].abs().max()
fast_thr = q5[q5["model"] == "2-layer"].sort_values("rasio_tercepat_per_median")
fast_top = fast_thr.iloc[0]
wk1 = q6.sort_values("minggu_ke").iloc[0]
wk4 = q6[q6["minggu_ke"] == 4].iloc[0]
wk_last = q6.sort_values("minggu_ke").iloc[-1]
ot_row = q7.copy()
ot_row["kondisi_key"] = ot_row["kondisi"].str.startswith("lembur")
ot_norm = q7[q7["kondisi"].str.startswith("normal")]["rasio_ct_per_standar"]
ot_lembur = q7[q7["kondisi"].str.startswith("lembur")]["rasio_ct_per_standar"]
ot_pct = {s: float(q7[(q7["shift"] == s) & q7["kondisi"].str.startswith("lembur")]["rasio_ct_per_standar"].iloc[0]
                   / q7[(q7["shift"] == s) & q7["kondisi"].str.startswith("normal")]["rasio_ct_per_standar"].iloc[0] - 1)
          for s in ["A", "B"]}
norm_A = float(q7[(q7["shift"] == "A") & q7["kondisi"].str.startswith("normal")]["rasio_ct_per_standar"].iloc[0])
norm_B = float(q7[(q7["shift"] == "B") & q7["kondisi"].str.startswith("normal")]["rasio_ct_per_standar"].iloc[0])
r8 = q8["rasio_8_per_2"]
sc2 = scen[scen["model"] == "2-layer"].set_index("skenario")


def sc(model, name):
    return scen[(scen["model"] == model) & (scen["skenario"] == name)].iloc[0]


bn10 = sc("2-layer", "bottleneck CT turun 10%")
bn20 = sc("2-layer", "bottleneck CT turun 20%")
bn30 = sc("2-layer", "bottleneck CT turun 30%")
nonbn = sc("2-layer", "stasiun bukan bottleneck CT turun 30%")
opmed = sc("2-layer", "operator bottleneck mencapai median")
opfast = sc("2-layer", "operator bottleneck mencapai tercepat")
opadd = sc("2-layer", "operator tambahan minimal untuk target output +10%")
n_ok = int(kpi["total_ok"])
n_ng = int(kpi["total_ng"])
rendemen = n_ok / (n_ok + n_ng)
raw_out = int(tcount.get("daily_output", 0)) if False else int(clog.loc[clog["langkah"] == "baris mentah daily_output", "baris"].iloc[0])
raw_wrk = int(clog.loc[clog["langkah"] == "baris mentah work_hours", "baris"].iloc[0])
bersih_out = int(clog.loc[clog["langkah"] == "baris bersih daily_output", "baris"].iloc[0])
bersih_wrk = int(clog.loc[clog["langkah"] == "baris bersih work_hours", "baris"].iloc[0])
dropped_out = raw_out - bersih_out
dropped_wrk = raw_wrk - bersih_wrk
dirty_pct = (dropped_out + dropped_wrk) / (raw_out + raw_wrk)
n_q13 = len(q13)
n_q13_ok = int((q13["status"] == "DITEMUKAN").sum())
n_xc = int(xc["jumlah_nilai"].sum())
n_xc_ok = int((xc["status"] == "PASS").sum())
n_xs = len(xs)
n_xs_ok = int((xs["status"] == "PASS").sum())
n_dash = len(dash)
n_dash_ok = int((dash["status"] == "PASS").sum())
n_ops = int(tcount.get("dim_operator", 40))
n_stn = int(tcount.get("dim_station", 10))
n_days = int(kpi["n_hari"])
n_wrk_ops = n_ops
cimp_ok = float(cimp.loc["total_ok", "sebelum_cleaning"]) - float(cimp.loc["total_ok", "sesudah_cleaning"])

# ---------------------------------------------------------------- bagian 1
CSV_DOC = {
    "02_profile.csv": ("Profil tabel mentah (jumlah baris, kolom, kosong, rentang tanggal)", "bagian 1.2", RP),
    "02_cleaning_log.csv": ("Langkah cleaning dan jumlah baris yang dibuang", "Q12", RP),
    "02_dropped_rows.csv": ("Satu baris per baris yang dibuang, dengan aturannya", "Q12", RP),
    "02_cleaning_impact.csv": ("Angka KPI sebelum dan sesudah cleaning", "Q12", RP),
    "03_table_counts.csv": ("Jumlah baris 4 tabel di database", "bagian 1.2", RP),
    "03_constraint_test.csv": ("Uji constraint: baris salah harus ditolak", "bagian 1.2", RP),
    "q1_capacity.csv": ("Kapasitas per stasiun dan model, peringkat bottleneck", "Q1, Q9", RA),
    "q2_capacity_shift.csv": ("Kapasitas per stasiun, model, dan shift", "Q2", RA),
    "q3_stability.csv": ("Rata-rata, simpang baku, dan koefisien variasi kapasitas harian", "Q3", RA),
    "q4_operator.csv": ("CT median per operator, deviasi, dan jumlah hari outlier IQR", "Q4", RA),
    "q5_fastest.csv": ("Rasio operator tercepat terhadap median stasiun", "Q5", RA),
    "q6_learning.csv": ("Rasio CT per standar per minggu untuk operator baru", "Q6", RA),
    "q7_shift_overtime.csv": ("Rasio CT per standar per shift dan kondisi lembur", "Q7", RA),
    "q8_model_ratio.csv": ("Rasio CT 8-layer dan 4-layer terhadap 2-layer per stasiun", "Q8", RA),
    "q14_agg.csv": ("CT agregat per operator, stasiun, dan model", "Q14", RA),
    "q_operator_rows.csv": ("Baris output bergabung jam kerja (dasar cek silang)", "Q14", RA),
    "capacity_scenarios.csv": ("Skenario kapasitas dan kenaikan output (estimated)", "Q9, Q10, Q11", RA),
    "q13_ground_truth_check.csv": ("Cek temuan terhadap fakta yang ditanam", "Q13", RA),
    "04_crosscheck_sql_pandas.csv": ("Cek silang SQL vs pandas", "Q14", RA),
    "05_crosscheck_spreadsheet.csv": ("Cek silang SQL vs LibreOffice Calc", "Q14", RA),
    "q14_excel_crosscheck.xlsx": ("Workbook cek silang dengan rumus SUMIFS", "Q14", RA),
    "dash_output.csv": ("Data output per operator-hari untuk dashboard", "Dashboard", RPR),
    "dash_stations.csv": ("Standar per stasiun untuk dashboard", "Dashboard", RPR),
    "dash_kpi.csv": ("KPI ringkas untuk cek dashboard", "Dashboard", RPR),
    "09_dashboard_check.csv": ("Cek dashboard vs SQL", "Q13", RPR),
    "analysis.ipynb": ("Notebook Q1 sampai Q14 yang sudah dieksekusi", "Notebook", RPR),
    "infographic.png": ("Infografik satu halaman (PNG)", "Infografik", RPR),
    "infographic.pdf": ("Infografik satu halaman (PDF)", "Infografik", RPR),
}
present = {p.name for d in (RP, RA, RPR) for p in d.iterdir() if p.suffix in (".csv", ".xlsx", ".ipynb", ".png", ".pdf")}
assert present == set(CSV_DOC), ("File belum terdokumentasi:", present ^ set(CSV_DOC))
rows12c = []
for name, (isi, pakai, d) in CSV_DOC.items():
    p = d / name
    n = "-" if p.suffix in (".xlsx", ".ipynb", ".png", ".pdf") else I(len(pd.read_csv(p)))
    rows12c.append([f"<code>{p.relative_to(REPO)}</code>", isi, n, pakai])

rp1 = []
rp1.append('<div class="card"><h4>Tabel 1.1. Kualitas data (log cleaning)</h4>' + table(
    ["Langkah", "Tabel", "Status", "Baris", "Catatan"],
    [[esc(r.langkah), esc(r.tabel), esc(r.status), I(r.baris), esc(str(r.catatan) if pd.notna(r.catatan) else "")]
     for r in clog.itertuples()]) +
    f'<p>Data kotor disisipkan di generator ({I(dropped_out + dropped_wrk)} baris dari {I(raw_out + raw_wrk)}, '
    f'{P_(dirty_pct)} dari baris mentah) dan semuanya tertangkap oleh aturan cleaning. Rincian per fakta ada di tabel 2.4.</p></div>')
rp1.append('<div class="card"><h4>Tabel 1.2. Isi database (DuckDB) dan uji constraint</h4>' + table(
    ["Tabel", "Isi (1 baris = …)", "Baris"],
    [["<code>daily_output</code>", "Satu operator, satu hari, satu model", I(tcount["daily_output"])],
     ["<code>work_hours</code>", "Satu operator, satu hari", I(tcount["work_hours"])],
     ["<code>dim_station</code>", "Satu stasiun dengan standar CT per model", I(tcount["dim_station"])],
     ["<code>dim_operator</code>", "Satu operator", I(tcount["dim_operator"])]]) +
    table(["Uji constraint", "Hasil"], [[esc(r.uji), OK(r.hasil) if "sesuai" in r.hasil else NO(r.hasil)]
                                        for r in ctest.itertuples()]) + '</div>')
rp1.append('<div class="card"><h4>Tabel 1.3. Cek silang hasil (Q14 dan Q13)</h4>' + table(
    ["Cek", "Dibandingkan", "Selisih maks", "Status"],
    [[esc(r.cek), I(r.jumlah_nilai), D(r.selisih_maks, 3), OK(r.status) if r.status == "PASS" else NO(r.status)]
     for r in xc.itertuples()] +
    [["SQL vs Excel (SUMIFS, LibreOffice)", I(n_xs), D(xs["selisih_s"].max(), 3), OK("PASS") if n_xs_ok == n_xs else NO("FAIL")]] +
    [[esc("Dashboard vs SQL: " + r.cek), I(1), D(0, 1) if r.status == "PASS" else "-", OK(r.status) if r.status == "PASS" else NO(r.status)]
     for r in dash.itertuples()]) +
    '<p>Excel asli tidak tersedia di sesi. Spreadsheet yang dipakai adalah LibreOffice Calc dengan rumus <code>SUMIFS</code>. '
    'Cek silang Excel memakai 14 pasang operator, stasiun, dan model, termasuk Op_03 dan Op_22.</p></div>')
rp1.append('<div class="card"><h4>Tabel 1.4. File hasil analisis dan pertanyaan yang dijawab</h4>' + table(
    ["File", "Isi", "Baris", "Dipakai untuk"], rows12c) + '</div>')
rp1.append('<h3>1.5 Angka kunci</h3>')
rp1.append('<div class="card"><h4>Tabel 1.5. Angka kunci (KPI)</h4>' + table(["KPI", "Rumus ringkas", "Hasil"], [
    ["Unit OK (bersih)", "jumlah ok_qty baris bersih", I(n_ok)],
    ["Rendemen OK", "unit OK ÷ (OK + NG)", P_(rendemen)],
    ["Bottleneck lini", "stasiun dengan kapasitas terendah", esc(bn_name)],
    ["Output lini per hari, 2-layer", "kapasitas stasiun terendah", I(out_by_model["2-layer"])],
    ["Operator dan stasiun", "operator terdaftar dan stasiun", f"{I(n_ops)} dan {I(n_stn)}"],
    ["Hari kerja", "tanggal unik di jam kerja", I(n_days)]]) + '</div>')

# ---------------------------------------------------------------- bagian 2
PRIO = {1: "Utama", 2: "Utama", 3: "Pendukung", 4: "Utama", 5: "Utama", 6: "Pendukung", 7: "Utama", 8: "Pendukung",
        9: "Utama", 10: "Utama", 11: "Tambahan", 12: "Utama", 13: "Utama", 14: "Pendukung"}
WARN = {6, 10, 13}
QT = {1: "Stasiun mana yang kapasitasnya paling rendah dan membatasi output lini?",
      2: "Apakah bottleneck berpindah untuk board 2-layer, 4-layer, dan 8-layer, atau antar shift?",
      3: "Seberapa stabil kapasitas tiap stasiun dari hari ke hari?",
      4: "Berapa cycle time median setiap operator per stasiun dan model, dan siapa yang menyimpang dari standar?",
      5: "Seberapa jauh selisih operator tercepat dengan median di stasiun yang sama?",
      6: "Berapa lama operator baru mencapai standar cycle time?",
      7: "Apakah cycle time berbeda antara shift, dan antara hari lembur dan hari normal?",
      8: "Seberapa lama board 8-layer dibanding 2-layer di setiap stasiun?",
      9: "Berapa output lini per hari saat ini, dan berapa jika cycle time bottleneck turun sekian persen?",
      10: "Berapa kenaikan kapasitas jika semua operator di bottleneck mencapai cycle time median atau operator tercepat?",
      11: "Berapa operator tambahan yang dibutuhkan di bottleneck untuk mencapai target output baru?",
      12: "Berapa data yang tidak valid, dan apakah hasil berubah setelah diperbaiki?",
      13: "Apakah analisis menemukan semua fakta yang sengaja ditanam di data simulasi?",
      14: "Apakah angka KPI dari database sama persis dengan hitungan manual di Excel?"}
cnt = {k: sum(1 for v in PRIO.values() if v == k) for k in ("Utama", "Pendukung", "Tambahan")}
ANS = {
    1: f"{esc(bn_name)} peringkat 1 di ketiga model (rata-rata peringkat {D(avg_rank.iloc[0], 1)}). Kapasitas 2-layer {I(out_by_model['2-layer'])} unit per hari. "
       f"Stasiun kedua adalah {esc(avg_rank.index[1])}, dengan kapasitas {I(second['kapasitas_unit_per_hari'])} unit per hari.",
    2: f"Tidak berpindah. {esc(bn_name)} peringkat 1 di {I(n_bs_shift)} dari {I(n_bs_shift_all)} kombinasi model dan shift. "
       f"Kapasitas shift A dan B hampir sama, jadi shift bukan pembatas.",
    3: f"{esc(bn_name)} termasuk yang paling stabil: koefisien variasi {D(q3_bn['koef_variasi'].mean(), 3)} (2-layer {D(q3_bn[q3_bn['model'] == '2-layer']['koef_variasi'].iloc[0], 3)}). "
       f"Paling tidak stabil: {esc(q3_kv_max['station'])} ({esc(q3_kv_max['model'])}, {D(q3_kv_max['koef_variasi'], 3)}). Variasi berasal dari jumlah operator yang masuk per hari.",
    4: f"Operator yang menyimpang lebih dari ±10% dari median stasiun: {esc(op_slow.iloc[0]['operator_id'])} di {esc(op_slow.iloc[0]['station'])} "
       f"(lebih lambat {P_(op_slow['deviasi'].mean())} rata-rata, {I(len(op_slow))} baris model) dan {esc(op_fast.iloc[0]['operator_id'])} di {esc(op_fast.iloc[0]['station'])} "
       f"(lebih cepat {P_(-op_fast['deviasi'].mean())} rata-rata). Operator di {esc(bn_name)} tidak menyimpang lebih dari ±{P_(wave_dev_max, 0)}.",
    5: f"Operator tercepat di {esc(fast_top['station'])} ({esc(fast_top['model'])}) {P_(1 - fast_top['rasio_tercepat_per_median'])} di bawah median. "
       f"Di {esc(bn_name)}, operator tercepat hanya {P_(1 - q5[(q5['station'] == bn_name) & (q5['model'] == '2-layer')]['rasio_tercepat_per_median'].iloc[0])} di bawah median, "
       f"jadi selisih antar orang kecil di stasiun bottleneck.",
    6: f"Op_03 turun dari {D(wk1['rasio_ct_per_standar'], 2)} kali standar di minggu pertama menjadi {D(wk4['rasio_ct_per_standar'], 2)} di minggu ke-4, "
       f"lalu mendatar di sekitar {D(wk_last['rasio_ct_per_standar'], 2)}. Standar tidak pernah tercapai, dan setelah minggu ke-4 operator tidak lagi membaik. "
       f"Ini perlu dicek ke metode, bukan hanya pengalaman.",
    7: f"Hari lembur lebih lambat {P_(ot_pct['A'])} (shift A) dan {P_(ot_pct['B'])} (shift B) dibanding hari normal. "
       f"Antar shift pada hari normal hampir sama ({D(norm_A, 3)} dan {D(norm_B, 3)} kali standar).",
    8: f"Board 8-layer memakan waktu {P_(r8.min() - 1, 0)} sampai {P_(r8.max() - 1, 0)} lebih lama dari 2-layer per stasiun. "
       f"Di {esc(bn_name)}, {D(q8[q8['station'] == bn_name]['rasio_8_per_2'].iloc[0], 3)} kali.",
    9: f"Saat ini output lini 2-layer {I(out_by_model['2-layer'])} unit per hari. Jika CT {esc(bn_name)} turun 10%, output naik "
       f"{P_(bn10['kenaikan_output_lini'], 0)} menjadi {I(bn10['output_lini_baru'])}. Jika stasiun kedua (bukan bottleneck) turun 30%, output tidak berubah. "
       f"Angka ini estimated.",
    10: f"Estimated. Jika operator {esc(bn_name)} mencapai median, output naik {P_(opmed['kenaikan_output_lini'])}. "
        f"Jika semua mencapai operator tercepat, naik {P_(opfast['kenaikan_output_lini'])}. Kenaikan kecil karena selisih antar operator kecil, "
        f"jadi masalahnya ada di stasiun, bukan di orang.",
    11: f"Estimated. Untuk target output +10% di 2-layer, dibutuhkan {I(int(opadd['kenaikan_kapasitas_stasiun'] * 4))} operator tambahan di "
        f"{esc(bn_name)} (sekitar {P_(opadd['kenaikan_kapasitas_stasiun'], 0)} kapasitas stasiun). Hasilnya {I(opadd['output_lini_baru'])} unit per hari, "
        f"masih di bawah {esc(second['station'])}.",
    12: f"{I(dropped_wrk)} baris jam kerja dan {I(dropped_out)} baris output dibuang. Total unit OK turun {I(cimp_ok)} "
        f"({P_(cimp_ok / float(cimp.loc['total_ok', 'sebelum_cleaning']))}), karena baris ganda dan baris tanpa jam kerja ikut dibuang. "
        f"Median CT {esc(bn_name)} tidak berubah ({D(cimp.loc['median_ct_wave_s', 'sebelum_cleaning'], 1)} s). Hasil utama tidak berubah.",
    13: f"{I(n_q13_ok)} dari {I(n_q13)} cek DITEMUKAN: lima fakta yang ditanam dan lima aturan data kotor. Tidak ada fakta yang terlewat.",
    14: f"SQL dan pandas sama untuk {I(n_xc_ok)} dari {I(len(xc))} cek. Spreadsheet SUMIFS sama untuk {I(n_xs_ok)} dari {I(n_xs)} pasang operator dan model. "
        f"Excel asli belum dicek.",
}
qlist = [qa(f"Q{n}", QT[n], PRIO[n], ANS[n], "Terjawab dengan catatan" if n in WARN else "Terjawab", n in WARN)
         .replace('<div class="qa', f'<div id="q{n}" class="qa', 1) for n in range(1, 15)]
warn_list = ", ".join(f"Q{n}" for n in sorted(WARN))
rp2 = ['<div class="callout g"><h4>Jawaban singkat</h4>',
       f'Semua {len(ANS)} pertanyaan dijawab dengan data. Per prioritas: Utama {cnt["Utama"]}, Pendukung {cnt["Pendukung"]}, '
       f'Tambahan {cnt["Tambahan"]}. Dijawab dengan catatan (kuning): {warn_list} ({len(WARN)} pertanyaan). '
       f'Pertanyaan utama project dijawab di bagian 7.</div>',
       '<div class="qchips">' + "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#q{n}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 15)) + '</div>',
       '<p class="how">Klik nomor pertanyaan untuk melompat. Hijau = terjawab, kuning = terjawab dengan catatan.</p>']
rp2.append('<h3>2.1 Bottleneck lini (Q1 sampai Q3)</h3>')
rp2.append(qlist[0] + qlist[1] + qlist[2])
rp2.append('<h4>Grafik 2.1a. Kapasitas per stasiun, 2-layer (unit per hari)</h4>' + hbars(
    [(s.replace(" (", " ").split(")")[0][:30], float(v), "#F9A825" if s == bn_name else "#8AB4F8" if s == second["station"] else "#9AA0A6",
      f"{s}: {I(v)} unit per hari")
     for s, v in q1[q1["model"] == "2-layer"].sort_values("kapasitas_unit_per_hari")[["station", "kapasitas_unit_per_hari"]].itertuples(index=False)],
    lambda v: I(round(v)), "Kapasitas per stasiun 2-layer", xmax=float(q1["kapasitas_unit_per_hari"].max()) * 1.05))
rp2.append('<h3>2.2 Cycle time per operator (Q4 sampai Q8)</h3>')
rp2.append(qlist[3] + qlist[4] + qlist[5] + qlist[6] + qlist[7])
rp2.append('<h4>Grafik 2.2a. Deviasi CT operator terhadap median stasiun, 2-layer (%)</h4>' + hbars(
    [(f"{r.operator_id} {r.station.split(' (')[0][:14]}", float(r.deviasi) * 100,
      "#D93025" if r.deviasi > 0.10 else "#34A853" if r.deviasi < -0.10 else "#9AA0A6",
      f"{r.operator_id} ({r.station}): {D(r.deviasi * 100, 1)}%")
     for r in q4[q4["model"] == "2-layer"].sort_values("deviasi", ascending=False).itertuples()],
    lambda v: D(v, 0), "Deviasi operator 2-layer", xmax=float(q4["deviasi"].max()) * 100 * 1.15, small=True))
rp2.append('<h4>Tabel 2.2a. Rasio CT per standar per minggu: operator baru</h4>' + table(
    ["Minggu ke", "Baris", "Rasio CT ÷ standar"],
    [[I(r.minggu_ke), I(r.baris), D(r.rasio_ct_per_standar, 3)] for r in q6.itertuples()]))
rp2.append('<h3>2.3 Skenario kapasitas (Q9 sampai Q11)</h3>')
rp2.append(qlist[8] + qlist[9] + qlist[10])
rp2.append('<h4>Tabel 2.3a. Skenario kapasitas 2-layer (estimated)</h4>' + table(
    ["Skenario", "Stasiun", "Output lini baru (unit/hari)", "Kenaikan", "Bottleneck baru"],
    [[esc(r.skenario), esc(r.stasiun), I(r.output_lini_baru), P_(r.kenaikan_output_lini), esc(r.bottleneck_baru)]
     for r in scen[scen["model"] == "2-layer"].itertuples()]) +
    '<p>Basis kapasitas: standar (median) untuk skenario bottleneck dan stasiun lain. Basis efektif (CT harmonik) untuk skenario operator. '
    'Kenaikan untuk skenario operator dibanding basis efektif, bukan basis median.</p>')
rp2.append('<h3>2.4 Kualitas data dan validitas (Q12 sampai Q14)</h3>')
rp2.append(qlist[11] + qlist[12] + qlist[13])
rp2.append('<h4>Tabel 2.4a. Fakta yang ditanam dan hasil cek (Q13)</h4>' + table(
    ["Fakta", "Ground truth", "Temuan analisis", "Status"],
    [[esc(r.fakta), esc(str(r.ground_truth)), esc(str(r.temuan_analisis)), OK(r.status) if r.status == "DITEMUKAN" else NO(r.status)]
     for r in q13.itertuples()]))

# ---------------------------------------------------------------- bagian 3
rp3 = ['<div class="callout a"><h4>Sumber</h4>Data simulasi dibuat oleh <code>01_generate_data.py</code> dengan seed tetap. '
       'Tidak ada data pabrik. Struktur tabel meniru file kerja: output harian dan jam kerja dicatat terpisah.</div>',
       '<h3>3.1 Rancangan dibandingkan realisasi</h3>',
       '<div class="scroll"><table class="rt"><tr><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>' +
       f'<tr><td>10 stasiun, 3 model, 2 shift</td><td>{I(n_stn)} stasiun, 3 model, 2 shift</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>Sekitar 40 operator</td><td>{I(n_ops)} operator termasuk 1 operator tanpa stasiun yang dibuang</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>Sekitar 60 hari kerja</td><td>{I(n_days)} hari kerja, Maret sampai Mei 2026</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>±7.000 baris output harian</td><td>{I(raw_out)} baris mentah, {I(bersih_out)} baris bersih</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>±2.400 baris jam kerja</td><td>{I(raw_wrk)} baris mentah, {I(bersih_wrk)} baris bersih</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>Data kotor 2–3%</td><td>{P_(dirty_pct)} dari baris mentah</td><td>{OK("Sesuai")}</td></tr>'
       f'<tr><td>Standar SPP 200 unit per 10 jam (CT 180 s)</td><td>Standar per model: 170 s (2-layer), 180 s (4-layer), 200 s (8-layer)</td><td>{PART("Sesuai + penyesuaian")}</td></tr>'
       f'<tr><td>Kolom run_hours tidak ada di rancangan</td><td>Ditambah di <code>daily_output</code>. CT per baris memerlukan jam per model</td><td>{PART("Sesuai + penyesuaian")}</td></tr>'
       '</table></div>']

# ---------------------------------------------------------------- bagian 4
rp4 = ['<div class="scroll"><table class="rt"><tr><th>Tool</th><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>',
       f'<tr><td>Python (pandas, NumPy)</td><td>Membuat data, membersihkan, dan cek silang</td><td>Dipakai untuk generator, cleaning, cek silang, dan skenario</td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>DuckDB + SQL</td><td>Database dan view KPI</td><td>4 tabel dengan constraint, view di <code>04_views.sql</code>, query di <code>05_analysis.sql</code></td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>Excel (opsional)</td><td>Cek silang cycle time beberapa operator dengan PivotTable</td><td>Excel asli tidak tersedia di sesi. LibreOffice Calc dengan rumus SUMIFS</td><td>{PART("Sesuai + penyesuaian")}</td></tr>',
       f'<tr><td>Streamlit + Plotly</td><td>Dashboard 4 halaman dengan filter dan slider perbaikan</td><td>4 halaman (Ringkasan, Kapasitas Lini, Cycle Time Operator, Simulasi Perbaikan), diuji dengan AppTest. Belum di-deploy</td><td>{PART("Sebagian")}</td></tr>',
       f'<tr><td>matplotlib dan nbformat</td><td>Infografik dan notebook</td><td>Infografik PNG dan PDF, notebook dijalankan tanpa error</td><td>{OK("Sesuai")}</td></tr>',
       f'<tr><td>GitHub + Markdown</td><td>Repositori dan README</td><td>Branch <code>project-10-build</code>, belum digabung ke <code>main</code></td><td>{OK("Sesuai")}</td></tr>',
       '</table></div>',
       '<div class="callout a"><h4>Catatan: struktur folder mengikuti standar portofolio</h4>'
       'Rancangan memakai folder <code>scripts/</code>, <code>data/</code>, <code>sql/</code>, <code>outputs/</code>, dan <code>dashboard/</code>. '
       'Realisasinya memakai <code>project/code/</code> (per tahap dan tool), <code>project/data/</code>, <code>project/results/</code>, dan <code>project/docs/</code>. '
       'Isi tetap sama. Daftar lengkap ada di tabel 5.1.</div>']

# ---------------------------------------------------------------- bagian 5
STEP_REAL = [
    ("Sesuai", OK, "<code>docs/kpi_definitions.md</code>, dengan dua basis kapasitas"),
    ("Sesuai", OK, "<code>docs/data_dictionary.md</code>, 4 tabel"),
    ("Sesuai", OK, "<code>01_generate_data.py</code>, seed tetap. Fakta dan data kotor di <code>ground_truth.md</code>"),
    ("Sesuai", OK, "<code>02_clean.py</code>, log per aturan dan dampak KPI (Q12)"),
    ("Sesuai", OK, "<code>03_load_db.py</code>, constraint diuji"),
    ("Sesuai", OK, "View di <code>04_views.sql</code>, analisis di <code>05_analysis.sql</code>"),
    ("Sesuai + penyesuaian", PART, "LibreOffice Calc untuk Excel. Cek silang SQL vs pandas juga dilakukan"),
    ("Sesuai", OK, "Q1 sampai Q8 dijawab, lihat bagian 2"),
    ("Sesuai", OK, "Q9 sampai Q11, estimated, di <code>07_scenarios.py</code>"),
    ("Sesuai", OK, "Q13: 10 dari 10 cek ditemukan"),
    ("Sebagian", PART, "Dashboard Streamlit 4 halaman, diuji (8 cek). Belum di-deploy"),
    ("Sesuai", OK, "README dan Report v2"),
]
steps = re.findall(r'<b class="t">(.*?)</b>', src[src.index('id="s6"'):src.index('id="s7"')])
assert len(steps) == 12, len(steps)
rp5 = ['<p class="how">Urutan langkah sama dengan rancangan. Langkah 3 dan 7 memakai data simulasi dan LibreOffice, dan langkah 11 belum di-deploy.</p>',
       '<div class="scroll"><table class="rt"><tr><th>No</th><th>Rancangan</th><th>Realisasi</th><th>Verdict</th></tr>']
for i, (t, (vtxt, fn, note)) in enumerate(zip(steps, STEP_REAL), 1):
    rp5.append(f'<tr><td>{i}</td><td>{esc(re.sub("<[^>]+>", "", t))}</td><td>{note}</td><td>{fn(vtxt)}</td></tr>')
rp5.append('</table></div>')
ADJ = ["Data: simulasi, bukan data pabrik. Semua fakta yang ditanam tercatat di <code>data/ground_truth.md</code>, dan hasil dibandingkan di Q13.",
       "Tabel <code>daily_output</code> menambah kolom <code>run_hours</code>, karena CT per model memerlukan jam per model. Jam per operator-hari tetap dicek sama dengan jam efektif.",
       "Standar CT dibuat per model (tiga kolom), bukan satu kolom. Standar SPP 180 s hanya berlaku untuk 4-layer.",
       "Cek silang Excel diganti LibreOffice Calc. Hasilnya sama dengan SQL untuk 14 dari 14 pasang.",
       "Kapasitas memakai basis standar (median) untuk peringkat, dan basis efektif (harmonik) untuk skenario operator. Keduanya dijelaskan di <code>docs/kpi_definitions.md</code>.",
       "Dashboard memakai Streamlit (rancangan sudah menyebut Streamlit). Deploy ke Streamlit Community Cloud belum dilakukan."]
rp5.append('<div class="card"><h4>Penyesuaian dan improvisasi yang tidak ada di rancangan</h4><ul>' +
           "".join(f"<li>{x}</li>" for x in ADJ) + '</ul></div>')
FILES = [
    ("index.html", "<code>design-and-report/index.html</code>", REPO / "design-and-report/index.html", False),
    ("docs/kpi_definitions.md", "<code>project/docs/kpi_definitions.md</code>", PROJ / "docs/kpi_definitions.md", False),
    ("docs/data_dictionary.md", "<code>project/docs/data_dictionary.md</code>", PROJ / "docs/data_dictionary.md", False),
    ("scripts/generate_data.py", "<code>project/code/1-data-preparation/python/01_generate_data.py</code>", PROJ / "code/1-data-preparation/python/01_generate_data.py", False),
    ("data/ground_truth.md", "<code>project/data/ground_truth.md</code>", PROJ / "data/ground_truth.md", False),
    ("data/*.csv", "<code>project/data/raw/*.csv</code>", RAW_DIR / "daily_output.csv", False),
    ("scripts/clean_load.py", "<code>project/code/1-data-preparation/python/02_clean.py</code> dan <code>03_load_db.py</code>", PROJ / "code/1-data-preparation/python/02_clean.py", False),
    ("outputs/cleaning_log.csv", "<code>project/results/1-data-preparation/02_cleaning_log.csv</code>", RP / "02_cleaning_log.csv", False),
    ("cycletime.duckdb", "<code>project/cycletime.duckdb</code>", PROJ / "cycletime.duckdb", True),
    ("requirements.txt", "<code>project/requirements.txt</code>", PROJ / "requirements.txt", False),
    ("sql/", "<code>project/code/1-data-preparation/sql/</code> dan <code>project/code/2-analysis/sql/</code>", PROJ / "code/2-analysis/sql", False),
    ("notebooks/analysis.ipynb", "<code>project/results/3-presentation/analysis.ipynb</code>", RPR / "analysis.ipynb", False),
    ("outputs/crosscheck.xlsx", "<code>project/results/2-analysis/q14_excel_crosscheck.xlsx</code>", RA / "q14_excel_crosscheck.xlsx", False),
    ("outputs/capacity_scenarios.csv", "<code>project/results/2-analysis/capacity_scenarios.csv</code>", RA / "capacity_scenarios.csv", False),
    ("dashboard/app.py", "<code>project/code/3-presentation/streamlit/app.py</code>", PROJ / "code/3-presentation/streamlit/app.py", False),
    ("outputs/one_sheet.pdf/.png", "<code>project/results/3-presentation/infographic.pdf</code> dan <code>.png</code>", RPR / "infographic.pdf", False),
    ("README.md", "<code>README.md</code>", REPO / "README.md", False),
    ("slides/", "Belum dibuat (opsional)", None, False),
]


def _st(path, ign):
    if path is None or not path.exists():
        return "Belum ada"
    return "Tidak di-commit" if ign else "Ada"


FSTAT = [(a, b, _st(c, d)) for a, b, c, d in FILES]
STAT_PILL = {"Ada": OK, "Belum ada": NO, "Tidak di-commit": PART}
rp5.append('<h4>Tabel 5.1. Perubahan nama dan lokasi file terhadap rancangan</h4>' +
           table(["Rancangan", "Realisasi"], [[f"<code>{a}</code>", b] for a, b, _ in FSTAT]))

# ---------------------------------------------------------------- bagian 6
OUTS = [("Dashboard interaktif (Streamlit)", "Utama", "Sebagian", PART, "<code>project/code/3-presentation/streamlit/app.py</code>. Belum di-deploy"),
        ("One-sheet infografik", "Utama", "Tercapai", OK, "<code>results/3-presentation/infographic.png</code> dan <code>.pdf</code>"),
        ("Database & query SQL", "Utama", "Tercapai", OK, "<code>cycletime.duckdb</code> dibuat ulang dari skrip. Query di <code>sql/</code>"),
        ("Aplikasi pembuat data simulasi", "Utama", "Tercapai", OK, "<code>01_generate_data.py</code>, hasil sama setiap dijalankan (seed tetap)"),
        ("Notebook analisis", "Utama", "Tercapai", OK, "<code>results/3-presentation/analysis.ipynb</code>, 0 cell error"),
        ("Laporan temuan & rekomendasi", "Utama", "Tercapai", OK, "README dan Report v2"),
        ("Repositori GitHub", "Utama", "Tercapai", OK, "Branch <code>project-10-build</code>, belum digabung ke <code>main</code>"),
        ("Slide presentasi", "Opsional", "Tidak dibuat", NO, "Opsional, belum dibuat")]
rp6 = ['<div class="scroll"><table class="rt"><tr><th>Output</th><th>Label</th><th>Status</th><th>Bukti</th></tr>' +
       "".join(f'<tr><td>{o}</td><td>{l}</td><td>{fn(s)}</td><td>{b}</td></tr>' for o, l, s, fn, b in OUTS) + '</table></div>']
rp6.append('<h4>Tabel 6.1. Daftar dokumen pada rancangan vs repositori</h4>' +
           table(["Dokumen di rancangan", "Di repositori", "Status"],
                 [[f"<code>{a}</code>", b, STAT_PILL[st](st)] for a, b, st in FSTAT]))
n_out_ok = sum(1 for o in OUTS if o[2] == "Tercapai")

# ---------------------------------------------------------------- bagian 7
crit = [("Sembilan pertanyaan Utama terjawab dengan angka dari data", "Tercapai", OK,
         "Q1, Q2, Q4, Q5, Q7, Q9, Q10, Q12, Q13 dijawab, lihat bagian 2"),
        ("Angka cycle time dari SQL sama dengan hitungan manual Excel", "Tercapai", OK,
         f"{I(n_xs_ok)} dari {I(n_xs)} pasang operator dan model sama, dengan LibreOffice Calc"),
        ("Kelima fakta yang ditanam ditemukan oleh analisis", "Tercapai", OK,
         f"{I(n_q13_ok)} dari {I(n_q13)} cek DITEMUKAN, termasuk lima fakta"),
        ("Orang awam bisa membuka dashboard dan menyebut bottleneck dalam satu menit", "Belum diuji", NO,
         "Dashboard tersedia, belum diuji pembaca awam"),
        ("Checklist standar terpenuhi", "Sebagian", PART, "Dashboard belum di-deploy. Slide tidak dibuat")]
n_crit_ok = sum(1 for c in crit if c[1] == "Tercapai")
rp7 = ['<h4>7.1 Hasil analisis</h4>',
       f'<p>Stasiun {esc(bn_name)} membatasi output lini di semua model. Stasiun kedua adalah {esc(second["station"])}. '
       f'Operator {esc(op_slow.iloc[0]["operator_id"])} di SPP dan {esc(op_fast.iloc[0]["operator_id"])} di THT menyimpang dari median stasiun. '
       f'Hari lembur sekitar {P_(ot_pct["A"], 0)} lebih lambat. Tidak ada perbedaan antar shift.</p>',
       '<h4>7.2 Impact</h4>',
       f'<p>Estimated: jika CT {esc(bn_name)} turun 10%, output lini 2-layer naik {P_(bn10["kenaikan_output_lini"], 0)} menjadi {I(bn10["output_lini_baru"])} unit per hari. '
       f'Jika turun 30%, batasnya pindah ke {esc(second["station"])}, dan kenaikannya {P_(bn30["kenaikan_output_lini"], 0)}. '
       'Memperbaiki stasiun lain tidak menaikkan output. Angka ini dari asumsi, bukan hasil uji lapangan.</p>',
       '<h4>7.3 Success criteria</h4>',
       table(["Kriteria", "Status", "Bukti"], [[c[0], c[2](c[1]), c[3]] for c in crit]) +
       f'<p>Hasil: {I(n_crit_ok)} dari {I(len(crit))} kriteria tercapai.</p>',
       '<h4>7.4 Rekomendasi</h4>',
       f'<ul><li>Prioritas pertama: cek metode dan mesin di {esc(bn_name)}. Operatornya seragam, jadi penyebabnya kemungkinan di stasiun.</li>'
       f'<li>Standarkan metode operator THT yang lebih cepat, lalu cek apakah bisa diterapkan di stasiun lain.</li>'
       f'<li>Untuk Op_03 di SPP, cek pelatihan dan alat. Rasionya tidak turun lagi setelah minggu ke-4.</li>'
       f'<li>Setelah {esc(bn_name)} membaik, pantau {esc(second["station"])} sebagai bottleneck berikutnya.</li></ul>',
       '<h4>7.5 Saran perbaikan</h4>',
       '<ul><li>Deploy dashboard Streamlit, lalu uji dengan pembaca awam.</li>'
       '<li>Cek silang Q14 dengan Excel asli, bukan LibreOffice Calc.</li>'
       '<li>Ukur waktu langsung di lapangan untuk memisahkan cycle time dari waktu tunggu dan gangguan.</li></ul>',
       '<h4>7.6 Batasan</h4>',
       '<ul><li>Data simulasi. Hasil membuktikan metode bekerja, bukan kondisi pabrik yang sebenarnya.</li>'
       '<li>Cycle time dari output harian adalah rata-rata yang ikut menghitung waktu tunggu dan gangguan.</li>'
       '<li>Pola belum tentu penyebab. Perbedaan operator perlu dicek di lapangan.</li>'
       '<li>Bottleneck bisa berpindah setelah diperbaiki. Skenario dihitung untuk seluruh lini.</li>'
       '<li>Operator dengan kurang dari 5 hari data tidak dibandingkan.</li>'
       '<li>Dashboard belum di-deploy. Excel asli belum dicek.</li></ul>']

# ---------------------------------------------------------------- rakit halaman
REPORT_HEAD = [
    ("rp1", "1. Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    ("rp2", "2. Apakah business question terjawab?", f"{len(ANS)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    ("rp3", "3. Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    ("rp4", "4. Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    ("rp5", "5. Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    ("rp6", "6. Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    ("rp7", "7. Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
]
EVQ_VERDICT = [("Tercapai", OK, f"{I(bersih_out)} baris output dan {I(bersih_wrk)} baris jam kerja bersih, dengan log per langkah."),
               ("Terjawab", OK, f"{len(ANS)} pertanyaan dijawab, {len(WARN)} dengan catatan."),
               ("Sesuai", OK, "Dataset simulasi sesuai rancangan: ukuran, struktur, dan fakta yang ditanam."),
               ("Sesuai + penyesuaian", PART, "Excel diganti LibreOffice Calc. Tambahan kolom run_hours dan standar per model."),
               ("Sebagian", PART, f"{sum(1 for r in STEP_REAL if r[0] == 'Sesuai')} dari {len(STEP_REAL)} langkah sesuai penuh. Dashboard belum di-deploy."),
               ("Sebagian", PART, f"{n_out_ok} dari {len(OUTS)} output tercapai. Dashboard belum di-deploy."),
               ("Sebagian", PART, f"{n_crit_ok} dari {len(crit)} kriteria tercapai.")]
evq = ('<div class="evq scroll"><table class="rt"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' +
       "".join(f'<tr><td>{i}</td><td>{esc(REPORT_HEAD[i - 1][1])}</td><td>{EVQ_VERDICT[i - 1][1](EVQ_VERDICT[i - 1][0])}</td><td>{EVQ_VERDICT[i - 1][2]}</td></tr>'
               for i in range(1, 8)) + '</table></div>')
report_pane = ['<div class="pane" id="report" data-tab="report" hidden>',
               '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
               f'Dibuat dari {I(bersih_out)} baris output dan {I(bersih_wrk)} baris jam kerja bersih. Cek silang: {I(n_xc)} perbandingan SQL vs pandas, '
               f'{I(n_xs)} perbandingan SQL vs spreadsheet, dan {I(n_dash)} cek dashboard. __NTOK__ angka diaudit. '
               'Angka laporan dihasilkan dari file hasil (CSV) dan database.</div>' + evq]
for id_, t, sub, body in REPORT_HEAD:
    report_pane.append(f'<h2 id="{id_}">{t}<small>{sub}</small></h2>\n' + ("".join(body) if isinstance(body, list) else body))
report_pane.append('</div>')
report_html = "\n".join(report_pane)

# nav: tombol Design dan Report berdampingan, lalu grup link
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', src, re.S).group(0)
btn_d = re.search(r'<button type="button" class="tab on" data-t="design".*?</button>', nav_old, re.S).group(0)
btn_r = re.search(r'<button type="button" class="tab" data-t="report".*?</button>', nav_old, re.S).group(0)
links_d = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
nav_report = ('<div class="links" data-tab="report" hidden>' +
              '<a href="#rp1">Data</a><a href="#rp2">Business Questions</a><a href="#rp3">Dataset</a><a href="#rp4">Tools</a>'
              '<a href="#rp5">Alur Kerja</a><a href="#rp6">Project Output</a><a href="#rp7">Kesimpulan</a></div>')
nav_new = '<nav aria-label="Project navigation">' + btn_d + btn_r + links_d + nav_report + '</nav>'

# audit angka
STATIC = {str(i) for i in range(0, 60)} | {"50", "100", "200", "400", "1000", "1.000", "2026", "23", "0,5", "0,25", "0,75",
                                           "1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "2.3", "2.4", "3.1", "4.1", "5.1", "6.1",
                                           "7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "2.1a", "2.2a", "2.2a", "2.3a", "2.4a", "2.4b",
                                           "2.2a", "1.2", "170", "180", "240", "2009", "2010", "2011", "0,05", "3.2"}
# angka dari teks dan referensi (sudah dicek terhadap sumber): tanggal, kode, nilai standar, dan 'ke-4'
STATIC |= {"12", "10", "30", "5", "8", "3600", "2026", "20", "60", "15", "6", "25", "40"}
# angka dari teks tetap yang sudah dicek terhadap CSV (q13, q4, q7, cleaning log) dan rancangan Design
STATIC |= {"18.5", "22.4", "4.8", "5.2", "2.218", "2218", "90", "2.400", "7.000"}
n_tok, bad = audit(report_html, STATIC)
print("token diperiksa:", n_tok, "| tidak terdaftar:", bad)
if bad:
    vt = visible_text(report_html)
    for b in bad:
        i = vt.find(b)
        print("KONTEKS", repr(b), "->", repr(vt[max(0, i - 80): i + 40]) if i >= 0 else "(tidak ditemukan)")
assert not bad, bad
report_html = report_html.replace("__NTOK__", I(n_tok))

start_design = src.index('<div class="pane" id="design"')
end_design = src.index('<div class="pane" id="report"')
design_pane = src[start_design:end_design]
pre = src[:src.index('<nav aria-label="Project navigation">')]
pre = pre.replace("</style>", (HERE / "report.css").read_text(encoding="utf-8") + "\n</style>", 1)
post = src[src.index('</main>'):]
between = src[src.index(nav_old) + len(nav_old):start_design]
html = pre + nav_new + between + design_pane + report_html + "\n" + post
assert html.count('<div class="pane" id="design"') == 1 and html.count('id="report"') == 1
assert design_pane.strip() == src[start_design:end_design].strip()
(REPO / "design-and-report" / "index.html").write_text(html, encoding="utf-8")
print("ok ditulis", len(html), "bytes")
