"""03 - Memuat 4 tabel bersih ke DuckDB dan menguji constraint dengan satu baris salah.

Output: project/cycletime.duckdb (tidak di-commit, dibuat ulang)
        project/results/1-data-preparation/03_table_counts.csv
        project/results/1-data-preparation/03_constraint_test.csv
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import CLEAN_DIR, DB_PATH, RAW_DIR, RES_PREP, SQL_PREP  # noqa: E402

sql = (SQL_PREP / "03_build_tables.sql").read_text(encoding="utf-8")
sql = sql.replace("{{CLEAN_DIR}}", CLEAN_DIR.as_posix())
# dim_station berasal dari raw (standar tidak perlu dibersihkan)
sql = sql.replace(f"{CLEAN_DIR.as_posix()}/dim_station.csv", f"{RAW_DIR.as_posix()}/dim_station.csv")

if DB_PATH.exists():
    DB_PATH.unlink()
con = duckdb.connect(str(DB_PATH))
con.execute(sql)

counts = [{"tabel": t, "baris": con.sql(f"SELECT COUNT(*) FROM {t}").fetchall()[0][0]}
          for t in ["dim_station", "dim_operator", "work_hours", "daily_output"]]
pd.DataFrame(counts).to_csv(RES_PREP / "03_table_counts.csv", index=False)

# Uji: baris salah harus ditolak
tests = {
    "ok_qty negatif": "INSERT INTO daily_output VALUES ('2026-03-02','A','Packing','Op_05','2-layer',1.0,-5,0)",
    "jam kerja 13": "INSERT INTO work_hours VALUES ('2026-03-02','Op_05',13.0,0)",
    "operator tidak terdaftar": "INSERT INTO daily_output VALUES ('2026-03-02','A','Packing','Op_99','2-layer',1.0,5,0)",
}
rows = []
for name, stmt in tests.items():
    try:
        con.execute(stmt)
        result = "DITERIMA (gagal)"
    except duckdb.Error:
        result = "DITOLAK (sesuai)"
    rows.append({"uji": name, "hasil": result})
pd.DataFrame(rows).to_csv(RES_PREP / "03_constraint_test.csv", index=False)
con.close()
print(pd.DataFrame(counts).to_string(index=False))
print(pd.DataFrame(rows).to_string(index=False))
