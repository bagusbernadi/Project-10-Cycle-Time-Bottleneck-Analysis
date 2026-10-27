[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 10: Cycle Time & Bottleneck Analysis

**Status: Selesai di branch `project-10-build` (belum digabung ke `main`).** Dashboard belum di-deploy. Excel asli belum dicek.

**Tujuan:** Menemukan stasiun yang membatasi output lini PCBA, operator yang menyimpang dari standar cycle time, dan estimasi kenaikan output jika bottleneck diperbaiki.

| | |
|---|---|
| Kategori | Manufaktur (PCBA) |
| Tingkat | Mudah |
| Data | Simulasi: output harian per operator dan jam kerja efektif (10 stasiun, 3 model, 40 operator, 60 hari kerja) |
| Tools | Python (pandas, NumPy), DuckDB + SQL, LibreOffice Calc (cek silang), Streamlit + Plotly |

## 1. Problem
Stasiun mana yang menjadi bottleneck output lini, operator mana yang menyimpang dari standar cycle time di stasiun yang sama, dan berapa kenaikan output jika bottleneck diperbaiki?

## 2. Data
Data simulasi buatan sendiri yang meniru struktur file kerja (output harian dan jam kerja di file terpisah). Dibuat oleh `project/code/1-data-preparation/python/01_generate_data.py` dengan seed tetap.

| Tabel | Baris mentah | Baris bersih |
|---|---|---|
| daily_output (satu operator, satu hari, satu model) | 7.054 | 6.814 |
| work_hours (satu operator, satu hari) | 2.308 | 2.278 |

Data kotor (sekitar 2,3% baris mentah) disisipkan dengan sengaja: jam kerja hilang, jam kerja lebih dari 12, unit OK negatif, baris ganda, operator tidak terdaftar, dan operator tanpa stasiun. Semua tertangkap oleh aturan cleaning dan tercatat di `project/results/1-data-preparation/02_cleaning_log.csv`.

## 3. Analysis
Cycle time (CT) = jam efektif × 3600 ÷ unit OK. Kapasitas stasiun = jumlah operator aktif × 8 jam × 3600 ÷ CT median. Output lini = kapasitas stasiun terendah. Definisi lengkap ada di `project/docs/kpi_definitions.md`.

Temuan utama:
- **Bottleneck lini: Wave Soldering.** Peringkat 1 di ketiga model dan kedua shift. Kapasitas 2-layer 484 unit per hari. Stasiun kedua: Solder Paste Printing (667).
- **Bottleneck tidak berpindah** antar model dan shift. Shift A dan B hampir sama.
- **Operator menyimpang:** Op_03 di Solder Paste Printing rata-rata 22% lebih lambat dari median stasiun, dan masih begitu setelah 12 minggu. Op_22 di THT Insertion 18% lebih cepat.
- **Operator di Wave Soldering seragam:** operator tercepat hanya sekitar 3% di bawah median. Masalahnya ada di stasiun, bukan di orang.
- **Hari lembur** sekitar 5% lebih lambat dari hari normal, di kedua shift.
- **Board 8-layer** memakan waktu 17% sampai 26% lebih lama dari 2-layer per stasiun.

## 4. Recommendation
1. Prioritas pertama: cek metode dan mesin di Wave Soldering. Karena operatornya seragam, penyebabnya kemungkinan ada di stasiun.
2. Standarkan metode operator THT Insertion yang lebih cepat (Op_22), lalu cek apakah bisa diterapkan di stasiun lain.
3. Untuk Op_03 di Solder Paste Printing, cek pelatihan dan alat. Rasionya tidak turun lagi setelah minggu ke-4.
4. Setelah Wave Soldering membaik, pantau Solder Paste Printing sebagai bottleneck berikutnya.

## 5. Impact
Semua angka berikut **estimated** dari data simulasi, bukan hasil uji lapangan.

| Skenario (2-layer) | Output lini per hari | Kenaikan |
|---|---|---|
| Saat ini | 484 | - |
| CT Wave Soldering turun 10% | 537 | +11% |
| CT Wave Soldering turun 20% | 604 | +25% |
| CT Wave Soldering turun 30% | 667 (bottleneck pindah ke Solder Paste Printing) | +38% |
| CT stasiun kedua turun 30% | 484 | 0% |
| Operator Wave mencapai tercepat | 499 | +3% |

Angka lengkap untuk tiga model ada di `project/results/2-analysis/capacity_scenarios.csv`.

## 6. Validasi
- Cek fakta yang ditanam (Q13): 10 dari 10 cek DITEMUKAN. Daftar fakta ada di `project/data/ground_truth.md`.
- Cek silang SQL vs pandas: PASS (120 operator, 30 kapasitas, 4 rasio).
- Cek silang SQL vs LibreOffice Calc (SUMIFS): 14 dari 14 PASS. Excel asli belum dicek.
- Cek dashboard vs SQL: 8 dari 8 PASS.

## Batasan yang sudah diketahui
- Data simulasi. Hasil membuktikan metode bekerja, bukan kondisi pabrik yang sebenarnya.
- Cycle time dari output harian adalah rata-rata yang ikut menghitung waktu tunggu, ganti model, dan gangguan.
- Pola belum tentu penyebab. Perbedaan operator perlu dicek di lapangan.
- Bottleneck bisa berpindah setelah diperbaiki. Skenario dihitung untuk seluruh lini.
- Operator dengan kurang dari 5 hari data tidak dibandingkan.
- Deviasi terukur (22% dan 18%) lebih kecil dari faktor yang ditanam (25% dan 20%), karena median ikut minggu awal dan hari lembur.

## Menjalankan ulang
Dari folder `project/`, dengan Python 3.11 atau lebih baru:

    pip install -r requirements.txt
    python code/1-data-preparation/python/01_generate_data.py
    python code/1-data-preparation/python/02_clean.py
    python code/1-data-preparation/python/03_load_db.py
    python code/2-analysis/python/04_crosscheck_pandas.py
    python code/2-analysis/python/05_run_analysis.py
    python code/2-analysis/python/06_excel_crosscheck.py
    python code/2-analysis/python/07_scenarios.py
    python code/3-presentation/python/08_dashboard_data.py
    python code/3-presentation/python/09_dashboard_check.py
    python code/3-presentation/python/10_infographic.py
    python code/3-presentation/python/11_build_notebook.py

Dashboard:

    streamlit run code/3-presentation/streamlit/app.py

Halaman rancangan dan report: buka `index.html` (GitHub Pages) atau jalankan `python design-and-report/src/build_report.py`.

## Struktur repositori
```
project/
  code/
    1-data-preparation/   # generator, cleaning, pemuat database (python dan sql)
    2-analysis/           # view dan query analisis, cek silang, skenario
    3-presentation/       # data dashboard, Streamlit, infografik, notebook
    common.py             # path dan konstanta
  data/                   # data simulasi (raw), ground truth
  docs/                   # definisi KPI, kamus data, keputusan cleaning
  results/                # hasil per tahap (1-data-preparation, 2-analysis, 3-presentation)
design-and-report/        # halaman rancangan dan report (src/build_report.py)
index.html                # redirect ke design-and-report/
README.md
```
