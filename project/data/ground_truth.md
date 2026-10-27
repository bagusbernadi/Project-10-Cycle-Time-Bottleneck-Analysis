# Ground truth: fakta yang sengaja ditanam di data simulasi

Dibuat oleh `project/code/1-data-preparation/python/01_generate_data.py` dengan seed `20260302`.
Angka lengkap ada di `project/data/ground_truth.json`. Dokumen ini hanya ringkasan untuk dibaca manusia.
Analisis tidak membaca file ini; Q13 hanya membandingkan temuan dengan daftar ini.

| # | Fakta | Parameter yang ditanam | Temuan yang diharapkan | Hasil (Q13) |
|---|---|---|---|---|
| 1 | Bottleneck utama | Wave Soldering dengan CT standar tertinggi (245 s untuk 4-layer) | Peringkat 1 di setiap model | DITEMUKAN |
| 2 | Bottleneck kedua | Solder Paste Printing (CT 170–200 s) | Peringkat 2 | DITEMUKAN |
| 3 | Operator lambat | Op_03 di Solder Paste Printing: faktor 1,40 di hari pertama, turun linear ke 1,25 dalam 20 hari kerja | Deviasi terbesar di SPP; CT median ±+25% | DITEMUKAN (deviasi rata-rata +22%) |
| 4 | Operator cepat | Op_22 di THT Insertion: faktor 0,80 | Deviasi terkecil di THT; ±−20% | DITEMUKAN (deviasi rata-rata −18%) |
| 5 | Lembur | CT hari lembur × 1,05 (berlaku untuk seluruh lini) | Rasio CT lembur ÷ normal ±+5% di kedua shift | DITEMUKAN (+4,8% dan +5,2%) |
| 6 | Data kotor | 2–3% baris (lihat tabel di bawah) | Jumlah yang dibuang sama dengan yang disisipkan | DITEMUKAN |

## Data kotor yang disisipkan

| Jenis | Tabel | Jumlah baris yang disisipkan | Aturan cleaning yang menangkap |
|---|---|---|---|
| Jam kerja hilang (output tetap ada) | work_hours | 30 operator-hari (90 baris output) | output tanpa jam kerja |
| Jam kerja lebih dari 12 jam | work_hours | 25 | jam kerja lebih dari 12 jam |
| ok_qty negatif | daily_output | 20 | ok atau ng negatif |
| Baris ganda | daily_output | 40 | baris ganda (semua kolom sama) |
| Operator tidak terdaftar (Op_99) | daily_output | 10 | operator tidak ada di dim_operator |
| Operator tanpa stasiun (Op_41) | dim_operator | 1 operator (5 hari output dan jam kerja) | operator tanpa stasiun |

Jumlah data kotor sekitar 2,3% dari baris output mentah. Angka detail per aturan ada di
`project/results/1-data-preparation/02_cleaning_log.csv`.

## Catatan kejujuran

- Deviasi terukur (Op_03 +22%, Op_22 −18%) lebih kecil dari faktor yang ditanam, karena median
  dihitung dari semua baris operator, termasuk minggu awal dan hari lembur.
- Shift A dan B dibuat sama. Tidak ada fakta shift yang ditanam, jadi Q2 dan Q7 menunjukkan
  tidak ada perbedaan shift.
- Fakta yang tidak ditanam tidak boleh dianggap ditemukan. Hanya lima fakta di atas yang diuji.
