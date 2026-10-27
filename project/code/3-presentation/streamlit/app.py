"""Dashboard Cycle Time & Bottleneck (Streamlit). Membaca data kecil di project/results/3-presentation/.

Jalankan dari folder project/:  streamlit run code/3-presentation/streamlit/app.py
Kapasitas dihitung ulang dari baris yang sedang difilter, dengan rumus yang sama dengan SQL (docs/kpi_definitions.md).
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PRES = Path(__file__).resolve().parents[3] / "results" / "3-presentation"
MODELS = ["2-layer", "4-layer", "8-layer"]
JAM_NORMAL = 8
MIN_HARI = 5


@st.cache_data
def load():
    out = pd.read_csv(PRES / "dash_output.csv", parse_dates=["date"])
    st_ = pd.read_csv(PRES / "dash_stations.csv")
    return out, st_


out, stations = load()
order = stations["station"].tolist()


def capacity(df):
    """Kapasitas per stasiun (unit per hari) = operator aktif × 8 jam × 3600 ÷ CT median."""
    if df.empty:
        return pd.DataFrame(columns=["station", "n_operator", "ct_median_s", "kapasitas_unit_per_hari"])
    med = df.groupby("station")["ct_s"].median()
    hari = df.groupby(["station", "operator_id"])["date"].nunique().reset_index()
    n = hari[hari["date"] >= MIN_HARI].groupby("station").size()
    t = pd.DataFrame({"n_operator": n, "ct_median_s": med}).dropna().reset_index()
    t["kapasitas_unit_per_hari"] = t["n_operator"] * JAM_NORMAL * 3600 / t["ct_median_s"]
    t["urutan"] = t["station"].map({s: i for i, s in enumerate(order)})
    return t.sort_values("kapasitas_unit_per_hari").reset_index(drop=True)


def output_lini(t):
    """Output lini = kapasitas stasiun terendah. Mengembalikan (nilai, nama stasiun)."""
    if t.empty:
        return float("nan"), "-"
    r = t.iloc[0]
    return r["kapasitas_unit_per_hari"], r["station"]


# ---------- sidebar: filter
with st.sidebar:
    st.header("Filter")
    model = st.selectbox("Model", MODELS, index=0)
    shifts = st.multiselect("Shift", ["A", "B"], default=["A", "B"])
    dmin, dmax = out["date"].min().date(), out["date"].max().date()
    rng = st.date_input("Tanggal", value=(dmin, dmax), min_value=dmin, max_value=dmax)
    d0, d1 = (rng[0], rng[1]) if isinstance(rng, (tuple, list)) and len(rng) == 2 else (dmin, dmax)
    st.caption("Filter model, shift, dan tanggal berlaku di semua halaman, kecuali tabel model di Ringkasan.")
    page = st.radio("Halaman", ["Ringkasan", "Kapasitas Lini", "Cycle Time Operator", "Simulasi Perbaikan"])

base = out[out["shift"].isin(shifts) & out["date"].between(pd.Timestamp(d0), pd.Timestamp(d1))]
sel = base[base["model"] == model]

# ---------- Ringkasan
if page == "Ringkasan":
    st.title("Ringkasan lini PCBA")
    st.caption(f"Data simulasi, {dmin:%d %b %Y} sampai {dmax:%d %b %Y}. Angka kapasitas memakai model "
               f"{model} dan filter yang dipilih.")
    cap = capacity(sel)
    outv, bn = output_lini(cap)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total unit OK", f"{base['ok_qty'].sum():,.0f}")
    c2.metric(f"Bottleneck lini ({model})", bn)
    c3.metric(f"Output lini per hari ({model})", f"{outv:,.0f}" if pd.notna(outv) else "-")

    rows = []
    for m in MODELS:
        t = capacity(base[base["model"] == m])
        v, s = output_lini(t)
        rows.append({"Model": m, "Bottleneck": s, "Output lini per hari (unit)": round(v, 0)})
    st.subheader("Bottleneck dan output lini per model")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("Output lini per hari = kapasitas stasiun terendah. Bukan jumlah unit yang tercatat.")

    daily = base.groupby(["date", "model"], as_index=False)["ok_qty"].sum()
    st.plotly_chart(px.line(daily, x="date", y="ok_qty", color="model", markers=False,
                            labels={"date": "Tanggal", "ok_qty": "Unit OK per hari", "model": "Model"}),
                    width="stretch")

# ---------- Kapasitas Lini
elif page == "Kapasitas Lini":
    st.title("Kapasitas per stasiun")
    st.caption(f"Model {model}. Batang paling kiri adalah bottleneck.")
    cap = capacity(sel)
    if cap.empty:
        st.warning("Tidak ada data untuk filter ini.")
    else:
        bn = cap.iloc[0]["station"]
        cap["bottleneck"] = cap["station"].eq(bn).map({True: "Bottleneck", False: "Lainnya"})
        fig = px.bar(cap.sort_values("kapasitas_unit_per_hari", ascending=True), x="kapasitas_unit_per_hari",
                     y="station", orientation="h", color="bottleneck",
                     color_discrete_map={"Bottleneck": "#F9A825", "Lainnya": "#8AB4F8"},
                     labels={"kapasitas_unit_per_hari": "Kapasitas (unit per hari)", "station": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
        show = cap[["station", "n_operator", "ct_median_s", "kapasitas_unit_per_hari"]].rename(columns={
            "station": "Stasiun", "n_operator": "Operator aktif", "ct_median_s": "CT median (s)",
            "kapasitas_unit_per_hari": "Kapasitas (unit/hari)"}).round(1)
        st.dataframe(show, width="stretch", hide_index=True)
        st.caption("Operator aktif = operator dengan minimal 5 hari data pada filter ini.")

# ---------- Cycle Time Operator
elif page == "Cycle Time Operator":
    st.title("Cycle time per operator")
    stn = st.selectbox("Stasiun", order, index=order.index("Solder Paste Printing"))
    d = sel[sel["station"] == stn]
    if d.empty:
        st.warning("Tidak ada data untuk filter ini.")
    else:
        std = stations.set_index("station").loc[stn, {"2-layer": "ct_std_2layer_s", "4-layer": "ct_std_4layer_s",
                                                       "8-layer": "ct_std_8layer_s"}[model]]
        fig = px.box(d, x="operator_id", y="ct_s", points=False,
                     labels={"operator_id": "Operator", "ct_s": "Cycle time (detik per unit OK)"})
        fig.add_hline(y=std, line_dash="dash", line_color="#D93025", annotation_text=f"standar {std:.0f} s")
        st.plotly_chart(fig, width="stretch")
        med = d.groupby("operator_id").agg(hari=("date", "nunique"), ct_median_s=("ct_s", "median"),
                                           status=("status", "first"))
        st_med = d["ct_s"].median()
        med["deviasi_vs_median_stasiun"] = med["ct_median_s"] / st_med - 1
        med = med.reset_index().rename(columns={"operator_id": "Operator", "hari": "Hari data",
                                                "ct_median_s": "CT median (s)", "status": "Status",
                                                "deviasi_vs_median_stasiun": "Deviasi vs median stasiun"})
        st.dataframe(med.sort_values("Deviasi vs median stasiun", ascending=False).round(3),
                     width="stretch", hide_index=True)
        st.caption(f"Median stasiun ({model}): {st_med:.1f} s. Deviasi di atas ±10% perlu dicek ke lapangan "
                   "sebelum disimpulkan. Operator dengan status 'baru' sedang dalam masa belajar.")

# ---------- Simulasi Perbaikan
else:
    st.title("Simulasi perbaikan cycle time")
    cap = capacity(sel)
    outv, bn = output_lini(cap)
    stn = st.selectbox("Stasiun yang diperbaiki", cap["station"].tolist(),
                       index=cap["station"].tolist().index(bn) if bn in cap["station"].tolist() else 0)
    x = st.slider("Penurunan cycle time stasiun terpilih (%)", 0, 30, 15, step=5)
    new = cap.copy()
    new.loc[new["station"] == stn, "ct_median_s"] *= (1 - x / 100)
    new["kapasitas_unit_per_hari"] = new["n_operator"] * JAM_NORMAL * 3600 / new["ct_median_s"]
    new = new.sort_values("kapasitas_unit_per_hari").reset_index(drop=True)
    outn, bn_new = output_lini(new)
    c1, c2, c3 = st.columns(3)
    c1.metric("Output lini saat ini", f"{outv:,.0f}")
    c2.metric("Output lini setelah perbaikan", f"{outn:,.0f}")
    c3.metric("Kenaikan output", f"{(outn / outv - 1) * 100:+.1f}%")
    st.caption(f"Bottleneck setelah perbaikan: {bn_new}. Output lini hanya naik jika stasiun yang dipercepat "
               "adalah stasiun dengan kapasitas terendah. Hasil ini estimated, bukan hasil uji lapangan.")
    plot = pd.concat([cap.assign(kondisi="Saat ini"), new.assign(kondisi="Setelah")])
    fig = px.bar(plot, x="station", y="kapasitas_unit_per_hari", color="kondisi", barmode="group",
                 labels={"station": "", "kapasitas_unit_per_hari": "Kapasitas (unit/hari)", "kondisi": ""},
                 color_discrete_map={"Saat ini": "#8AB4F8", "Setelah": "#1A73E8"})
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, width="stretch")
