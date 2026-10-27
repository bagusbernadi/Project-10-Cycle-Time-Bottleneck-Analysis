# Definisi KPI

Semua rumus dihitung di SQL (`project/code/2-analysis/sql/04_views.sql`) dan diulang di pandas untuk cek silang (Q14).

| KPI | Rumus | Satuan | Catatan |
|---|---|---|---|
| Cycle time baris (CT) | jam efektif baris × 3600 ÷ unit OK | detik per unit OK | hanya baris dengan unit OK > 0 |
| Cycle time median stasiun-model | median CT semua baris stasiun dan model | detik | dasar peringkat bottleneck |
| Operator aktif | operator dengan minimal 5 hari data pada stasiun dan model | orang | operator di bawah 5 hari tidak dibandingkan |
| Kapasitas stasiun (standar) | operator aktif × 8 jam × 3600 ÷ CT median stasiun-model | unit per hari | 8 jam = jam normal, bukan jam lembur |
| Output lini per hari | kapasitas stasiun terendah pada model yang sama | unit per hari | stasiun terendah = bottleneck |
| Deviasi operator | CT median operator ÷ CT median stasiun − 1 | persen | positif = lebih lambat |
| Outlier baris (IQR) | CT di luar Q1 − 1,5 IQR atau Q3 + 1,5 IQR, per stasiun dan model | jumlah hari | dipakai untuk tanda, bukan untuk membuang data |
| Rasio CT per standar | CT ÷ CT standar model | rasio | 1,00 = sesuai standar |
| CT harmonik (efektif) | n ÷ Σ(1 ÷ CT operator) | detik | dipakai untuk skenario operator (Q10) |
| Kenaikan kapasitas | CT lama ÷ CT baru − 1 | persen | estimated |
| Kenaikan output lini | output baru ÷ output lama − 1 | persen | estimated; bottleneck bisa berpindah |

## Batasan rumus

- CT dari output harian adalah rata-rata. Waktu tunggu, ganti model, dan gangguan mesin ikut terhitung.
- Dua basis kapasitas dipakai: standar (median, untuk peringkat) dan efektif (harmonik, untuk skenario operator).
  Keduanya tidak dicampur dalam satu perbandingan kenaikan.
