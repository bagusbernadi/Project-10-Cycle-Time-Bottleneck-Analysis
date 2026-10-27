"""04 - Menjalankan query analisis (sql/05_analysis.sql) dan menyimpan setiap blok ke CSV.

Output: project/results/2-analysis/<nama_blok>.csv
"""
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import DB_PATH, RES_ANALYSIS, SQL_ANALYSIS  # noqa: E402

con = duckdb.connect(str(DB_PATH), read_only=False)
con.execute((SQL_ANALYSIS / "04_views.sql").read_text(encoding="utf-8"))

text = (SQL_ANALYSIS / "05_analysis.sql").read_text(encoding="utf-8")
blocks = re.split(r"^-- name: ", text, flags=re.M)[1:]
for b in blocks:
    name, sql = b.split("\n", 1)
    df = con.sql(sql.strip().rstrip(";")).df()
    df.to_csv(RES_ANALYSIS / f"{name.strip()}.csv", index=False)
    print(f"{name.strip():20s} {len(df):5d} baris")
con.close()
