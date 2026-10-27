"""09 - Cek dashboard vs hasil SQL (Q13 untuk dashboard). Menjalankan app.py dengan Streamlit AppTest.

Output: project/results/3-presentation/09_dashboard_check.csv
"""
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_ANALYSIS, RES_PRESENT  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "streamlit" / "app.py"
q1 = pd.read_csv(RES_ANALYSIS / "q1_capacity.csv")
q1_2l = q1[q1["model"] == "2-layer"].sort_values("kapasitas_unit_per_hari").reset_index(drop=True)
kpi = pd.read_csv(RES_PRESENT / "dash_kpi.csv").iloc[0]
rows = []


def metric(at, prefix):
    return next(m.value for m in at.metric if m.label.startswith(prefix))


at = AppTest.from_file(str(APP), default_timeout=120).run()
assert not at.exception, at.exception
ok_dash = float(str(metric(at, "Total unit OK")).replace(",", ""))
rows.append({"cek": "total unit OK (dashboard vs SQL)", "dashboard": ok_dash, "sql": float(kpi["total_ok"]),
             "status": "PASS" if abs(ok_dash - kpi["total_ok"]) < 0.5 else "FAIL"})
bn_dash = metric(at, "Bottleneck lini")
bn_sql = q1_2l.iloc[0]["station"]
rows.append({"cek": "bottleneck 2-layer (dashboard vs SQL)", "dashboard": bn_dash, "sql": bn_sql,
             "status": "PASS" if bn_dash == bn_sql else "FAIL"})
out_dash = float(str(metric(at, "Output lini per hari")).replace(",", ""))
out_sql = round(q1_2l.iloc[0]["kapasitas_unit_per_hari"])
rows.append({"cek": "output lini 2-layer per hari (dashboard vs SQL)", "dashboard": out_dash, "sql": out_sql,
             "status": "PASS" if abs(out_dash - out_sql) <= 1 else "FAIL"})

# Simulasi: memperbaiki stasiun non-bottleneck tidak menaikkan output; memperbaiki bottleneck menaikkan
at.sidebar.radio[0].set_value("Simulasi Perbaikan").run()
stn_box = at.selectbox[0]
second = q1_2l.iloc[1]["station"]
stn_box.set_value(second).run()
inc_non = float(metric(at, "Kenaikan output").replace("%", "").replace("+", ""))
rows.append({"cek": "perbaiki stasiun kedua (non-bottleneck) 15%: kenaikan output", "dashboard": inc_non,
             "sql": 0.0, "status": "PASS" if abs(inc_non) < 0.05 else "FAIL"})
stn_box.set_value(bn_sql).run()
inc_bn = float(metric(at, "Kenaikan output").replace("%", "").replace("+", ""))
rows.append({"cek": "perbaiki bottleneck 15%: kenaikan output > 0", "dashboard": inc_bn,
             "sql": "> 0", "status": "PASS" if inc_bn > 0 else "FAIL"})
assert not at.exception, at.exception

# Halaman lain tidak error
for page in ["Kapasitas Lini", "Cycle Time Operator", "Ringkasan"]:
    at.sidebar.radio[0].set_value(page).run()
    rows.append({"cek": f"halaman {page} tampil tanpa error", "dashboard": "ok", "sql": "ok",
                 "status": "PASS" if not at.exception else "FAIL"})

out = pd.DataFrame(rows)
out.to_csv(RES_PRESENT / "09_dashboard_check.csv", index=False)
print(out.to_string(index=False))
