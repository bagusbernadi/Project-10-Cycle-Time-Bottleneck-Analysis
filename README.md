[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 10: Cycle Time & Bottleneck Analysis

**Status: Design (rancangan).**

**Tujuan:** Membangun analisis dan dashboard cycle time per stasiun dan per operator di lini PCBA, untuk menemukan stasiun yang membatasi output lini dan operator yang menyimpang dari standar, sehingga perbaikan metode dan penambahan kapasitas dapat difokuskan pada titik yang benar-benar menaikkan output.

| | |
|---|---|
| Kategori | Manufaktur (PCBA) |
| Tingkat | Mudah |
| Data | Simulasi: output harian per operator dan jam kerja efektif (10 stasiun, 3 model) |
| Tools | DuckDB + SQL, Python (pandas, NumPy), Excel (opsional), Streamlit + Plotly |

## 1. Problem
Stasiun mana yang menjadi bottleneck output lini, operator mana yang menyimpang dari standar cycle time di stasiun yang sama, dan berapa kenaikan output jika bottleneck diperbaiki?

## 2. Data
Data simulasi buatan sendiri yang meniru struktur file kerja (output harian dan jam kerja di file terpisah), dibuat oleh `scripts/generate_data.py` (seed tetap). Perkiraan ±7.000 baris output harian dan ±2.400 baris jam kerja (10 stasiun, 3 model, 2 shift, ±40 operator, ±60 hari kerja). Bottleneck, operator lambat dan cepat, efek lembur, dan 2–3% data kotor sengaja ditanam sebagai ground truth.

## 3. Analysis
Rencana: cycle time per operator, median per stasiun, outlier IQR, kapasitas per stasiun, output lini, skenario perbaikan bottleneck, dan pencocokan dengan ground truth. Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- Cycle time dari output harian adalah rata-rata yang ikut menghitung waktu tunggu dan gangguan.
- Pola belum tentu penyebab; perbedaan operator perlu dicek di lapangan.
- Bottleneck bisa berpindah setelah satu stasiun diperbaiki.

## Struktur repository (rencana)
```
docs/            # definisi KPI, kamus data
scripts/         # generator data simulasi, cleaning, pemuat data
data/            # data simulasi dan ground truth
sql/             # query cycle time, kapasitas, output lini
notebooks/       # analisis
dashboard/       # aplikasi Streamlit
index.html       # halaman rancangan (GitHub Pages)
README.md
```
