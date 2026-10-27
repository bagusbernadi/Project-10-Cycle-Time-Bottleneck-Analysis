"""10 - One-sheet infografik (PNG dan PDF) dari tabel hasil analisis.

Output: project/results/3-presentation/infographic.png dan infographic.pdf
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import RES_ANALYSIS, RES_PRESENT  # noqa: E402

q1 = pd.read_csv(RES_ANALYSIS / "q1_capacity.csv")
q4 = pd.read_csv(RES_ANALYSIS / "q4_operator.csv")
sc = pd.read_csv(RES_ANALYSIS / "capacity_scenarios.csv")
kpi = pd.read_csv(RES_PRESENT / "dash_kpi.csv").iloc[0]
cap2 = q1[q1["model"] == "2-layer"].sort_values("kapasitas_unit_per_hari")
bn = cap2.iloc[0]
s2 = cap2.iloc[1]
base = float(bn["kapasitas_unit_per_hari"])
bn_name = bn["station"]
q4_wave = q4[(q4["station"] == bn_name) & (q4["model"] == "2-layer")]
spp = q4[(q4["station"] == s2["station"]) & (q4["model"] == "2-layer")].sort_values("deviasi")
tht = q4[(q4["station"] == "THT Insertion") & (q4["model"] == "2-layer")].sort_values("deviasi")

BLUE, GREY, RED, AMBER = "#1A73E8", "#5F6368", "#D93025", "#F9A825"
fig = plt.figure(figsize=(16, 11), facecolor="white")
fig.suptitle("Cycle Time & Bottleneck: Lini PCBA (data simulasi)", fontsize=22, fontweight="bold", y=0.975)

# KPI
rev = [(f"{kpi['total_ok'] / 1e3:,.0f} rb", "Unit OK (60 hari)"),
       (f"{kpi['total_ok'] / (kpi['total_ok'] + kpi['total_ng']) * 100:.1f}%", "Rendemen OK"),
       (bn_name.split(" (")[0], "Bottleneck lini"),
       (f"{base:,.0f}", "Output lini per hari (2-layer)")]
for i, (v, lab) in enumerate(rev):
    ax = fig.add_axes([0.04 + i * 0.24, 0.84, 0.21, 0.09])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#F1F3F4", edgecolor="#DADCE0"))
    ax.text(0.5, 0.62, v, ha="center", va="center", fontsize=22 if len(v) < 12 else 17,
            fontweight="bold", color=BLUE if i != 2 else RED)
    ax.text(0.5, 0.25, lab, ha="center", va="center", fontsize=12, color=GREY)

# Kapasitas per stasiun
ax = fig.add_axes([0.10, 0.45, 0.36, 0.32])
colors = [AMBER if s == bn_name else ("#8AB4F8" if s == s2["station"] else "#BDC1C6") for s in cap2["station"]]
short = cap2["station"].str.replace(r" \(.*\)", "", regex=True)
ax.barh(short, cap2["kapasitas_unit_per_hari"], color=colors)
for y, v in enumerate(cap2["kapasitas_unit_per_hari"]):
    ax.text(v + 8, y, f"{v:,.0f}", va="center", fontsize=9)
ax.set_title("Kapasitas per stasiun, 2-layer (unit/hari)", loc="left", fontsize=14)
ax.tick_params(labelsize=9)
ax.spines[["top", "right"]].set_visible(False)

# Operator menyimpang
ax = fig.add_axes([0.58, 0.45, 0.37, 0.32])
ops = pd.concat([spp.assign(st="SPP"), tht.assign(st="THT")])
lab = ops["operator_id"] + " (" + ops["st"] + ")"
cols = [RED if d > 0.10 else ("#34A853" if d < -0.10 else "#BDC1C6") for d in ops["deviasi"]]
ax.barh(lab, ops["deviasi"] * 100, color=cols)
ax.axvline(0, color=GREY, lw=1)
ax.axvline(10, color=GREY, lw=0.8, ls="--")
ax.axvline(-10, color=GREY, lw=0.8, ls="--")
ax.set_title("Deviasi CT operator vs median stasiun (%, 2-layer)", loc="left", fontsize=14)
ax.tick_params(labelsize=9)
ax.spines[["top", "right"]].set_visible(False)

# Skenario bottleneck
ax = fig.add_axes([0.10, 0.07, 0.36, 0.27])
sb = sc[(sc["model"] == "2-layer") & (sc["skenario"].str.startswith("bottleneck CT turun"))]
ax.bar(["−10%", "−20%", "−30%"], sb["output_lini_baru"], color=BLUE)
for i, v in enumerate(sb["output_lini_baru"]):
    ax.text(i, v + 6, f"{v:,.0f}\n({sb['kenaikan_output_lini'].iloc[i] * 100:+.0f}%)", ha="center", fontsize=10)
ax.axhline(base, color=GREY, ls="--", lw=1)
ax.set_ylim(0, max(sb["output_lini_baru"]) * 1.25)
ax.set_title("Output lini jika CT Wave Soldering turun (estimated)", loc="left", fontsize=14)
ax.set_ylabel("unit per hari")
ax.spines[["top", "right"]].set_visible(False)

# Pesan
ax = fig.add_axes([0.58, 0.07, 0.37, 0.27])
ax.axis("off")
msgs = [
    f"{bn_name} membatasi output lini. Perbaikan di stasiun lain tidak menaikkan output.",
    f"Solder Paste Printing adalah bottleneck kedua. Setelah Wave turun 30%, batasnya berpindah ke sana.",
    f"Satu operator SPP (Op_03) ±{(spp.loc[spp['operator_id'] == 'Op_03', 'deviasi'].iloc[0]) * 100:.0f}% di atas median: "
    "cek pelatihan atau metode kerja.",
    "Satu operator THT (Op_22) ±20% lebih cepat: metodenya layak distandarkan.",
    "Angka skenario adalah estimasi dari data simulasi, bukan hasil uji lapangan.",
]
ax.text(0, 1.02, "Temuan utama", fontsize=15, fontweight="bold", va="top")
for i, m in enumerate(msgs):
    ax.text(0, 0.88 - i * 0.18, "• " + m, fontsize=11, va="top", wrap=True)

fig.text(0.04, 0.012, "Sumber: data simulasi (seed tetap), 10 stasiun, 3 model, 40 operator, 60 hari kerja. "
         "Cycle time = jam efektif × 3600 ÷ unit OK.", fontsize=10, color=GREY)
out = RES_PRESENT / "infographic"
fig.savefig(out.with_suffix(".png"), dpi=150)
fig.savefig(out.with_suffix(".pdf"))
print("ok", out.with_suffix(".png"))
