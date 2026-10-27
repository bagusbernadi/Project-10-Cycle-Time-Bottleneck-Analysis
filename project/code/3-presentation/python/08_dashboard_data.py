"""08 - Menyiapkan data kecil untuk dashboard (dibaca app.py tanpa koneksi database).

Output: project/results/3-presentation/dash_output.csv   (satu baris = satu operator, hari, model; dengan CT)
        project/results/3-presentation/dash_stations.csv  (standar per stasiun)
        project/results/3-presentation/dash_kpi.csv       (angka ringkasan untuk cek dashboard)
"""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, RES_PRESENT, SQL_ANALYSIS  # noqa: E402

con = duckdb.connect(str(DB_PATH))
con.execute((SQL_ANALYSIS / "04_views.sql").read_text(encoding="utf-8"))
con.sql("""SELECT date, station, operator_id, model, shift, is_overtime, status,
                   ROUND(ct_s, 2) AS ct_s, ct_std_s, ok_qty, ng_qty, run_hours
            FROM v_output_ct ORDER BY date, station, operator_id, model""").df().to_csv(
    RES_PRESENT / "dash_output.csv", index=False)
con.sql("SELECT station, sequence, ct_std_2layer_s, ct_std_4layer_s, ct_std_8layer_s, n_operator "
        "FROM dim_station ORDER BY sequence").df().to_csv(RES_PRESENT / "dash_stations.csv", index=False)
con.sql("""SELECT (SELECT SUM(ok_qty) FROM daily_output) AS total_ok,
                  (SELECT SUM(ng_qty) FROM daily_output) AS total_ng,
                  (SELECT COUNT(*) FROM dim_operator) AS n_operator,
                  (SELECT COUNT(DISTINCT date) FROM work_hours) AS n_hari""").df().to_csv(
    RES_PRESENT / "dash_kpi.csv", index=False)
con.close()
print("ok")
