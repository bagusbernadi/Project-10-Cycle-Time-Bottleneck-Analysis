"""11 - Membuat dan menjalankan notebook analisis (Q1-Q14) dari hasil tahap sebelumnya.

Output: project/results/3-presentation/analysis.ipynb (sudah dieksekusi)
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_PRESENT, ROOT  # noqa: E402

nb = nbformat.v4.new_notebook()
md = lambda t: nbformat.v4.new_markdown_cell(t)  # noqa: E731
code = lambda t: nbformat.v4.new_code_cell(t)  # noqa: E731

nb.cells = [
    md("# Cycle Time & Bottleneck: Lini PCBA (data simulasi)\n"
       "Notebook ini membaca hasil query SQL dan menampilkan jawaban Q1-Q14. Semua angka berasal dari "
       "`project/results/`. Jalankan `01` sampai `10` lebih dulu jika folder hasil kosong."),
    code("import pandas as pd\nimport matplotlib.pyplot as plt\n"
         "R = '../2-analysis/'  # relatif terhadap results/3-presentation\n"
         "pd.set_option('display.float_format', lambda v: f'{v:,.2f}')"),
    md("## Q1 Kapasitas per stasiun\nBottleneck adalah stasiun dengan kapasitas terendah. Output lini = kapasitas itu."),
    code("q1 = pd.read_csv(R + 'q1_capacity.csv')\n"
         "q1[q1['model'] == '2-layer'][['station', 'n_operator_aktif', 'ct_median_s', 'kapasitas_unit_per_hari', 'peringkat_bottleneck']]"),
    md("## Q2 Bottleneck per model dan shift\nBottleneck tidak berpindah antar model. Antar shift juga sama."),
    code("q2 = pd.read_csv(R + 'q2_capacity_shift.csv')\n"
         "q2[q2['peringkat_bottleneck'] <= 2]"),
    md("## Q3 Kestabilan kapasitas harian\nKoefisien variasi (KV) kecil berarti kapasitas stabil dari hari ke hari."),
    code("pd.read_csv(R + 'q3_stability.csv').head(10)"),
    md("## Q4 & Q5 Cycle time per operator dan selisih tercepat\nDeviasi dihitung terhadap median stasiun-model."),
    code("q4 = pd.read_csv(R + 'q4_operator.csv')\n"
         "print('Operator dengan deviasi > ±10%:')\n"
         "q4[q4['deviasi'].abs() > 0.10][['station', 'operator_id', 'model', 'status', 'ct_median_s', 'deviasi']]"),
    code("pd.read_csv(R + 'q5_fastest.csv').head(10)"),
    md("## Q6 Operator baru: Solder Paste Printing (Op_03)\nRasio CT per standar turun di awal, lalu mendatar di sekitar 1,2. "
       "Setelah masa belajar, operator tidak lagi membaik."),
    code("q6 = pd.read_csv(R + 'q6_learning.csv')\n"
         "ax = q6.plot(x='minggu_ke', y='rasio_ct_per_standar', marker='o', legend=False, figsize=(8, 3))\n"
         "ax.axhline(1.0, color='grey', ls='--'); ax.set_ylabel('rasio CT / standar'); ax.set_title('Op_03 per minggu')\n"
         "plt.show()"),
    md("## Q7 Shift dan lembur\nRasio CT per standar di hari lembur sekitar 5% lebih tinggi di kedua shift."),
    code("pd.read_csv(R + 'q7_shift_overtime.csv')"),
    md("## Q8 Rasio CT antar model\nBoard 8-layer memakan waktu sekitar 17–26% lebih lama dari 2-layer."),
    code("pd.read_csv(R + 'q8_model_ratio.csv')"),
    md("## Q9-Q11 Skenario kapasitas\nSemua angka estimated. Bottleneck bisa berpindah setelah diperbaiki."),
    code("sc = pd.read_csv(R + 'capacity_scenarios.csv')\n"
         "sc[['model', 'skenario', 'stasiun', 'output_lini_baru', 'kenaikan_output_lini', 'bottleneck_baru', 'catatan']]"),
    md("## Q12 Kualitas data\nBaris yang dibuang dan dampaknya terhadap angka KPI."),
    code("pd.read_csv('../1-data-preparation/02_cleaning_log.csv')"),
    code("pd.read_csv('../1-data-preparation/02_cleaning_impact.csv')"),
    md("## Q13 Cocokkan dengan fakta yang ditanam\nJika semua baris DITEMUKAN, metode mendeteksi fakta yang sengaja dibuat."),
    code("pd.read_csv(R + 'q13_ground_truth_check.csv')"),
    md("## Q14 Cek silang SQL, pandas, dan Excel"),
    code("pd.read_csv(R + '04_crosscheck_sql_pandas.csv')"),
    code("pd.read_csv(R + '05_crosscheck_spreadsheet.csv')"),
]

out = RES_PRESENT / "analysis.ipynb"
client = NotebookClient(nb, timeout=600, kernel_name="python3",
                        resources={"metadata": {"path": str((ROOT / "results" / "3-presentation").resolve())}})
client.execute()
nbformat.write(nb, out)
errors = [c for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.get("output_type") == "error"]
print("ok", out, "error cells:", len(errors))
