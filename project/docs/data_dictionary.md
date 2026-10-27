# Kamus data

Empat tabel di `cycletime.duckdb`. Sumber: CSV simulasi di `project/data/raw/` (dibersihkan ke `project/data/clean/`).

## daily_output (satu baris = satu operator, satu hari, satu model)

| Kolom | Tipe | Arti | Satuan |
|---|---|---|---|
| date | DATE | tanggal kerja | tanggal |
| shift | VARCHAR | shift operator (A atau B) | - |
| station | VARCHAR | stasiun tempat operator bekerja | - |
| operator_id | VARCHAR | ID operator | - |
| model | VARCHAR | 2-layer, 4-layer, atau 8-layer | - |
| run_hours | DOUBLE | jam kerja yang dialokasikan ke model itu pada hari itu | jam |
| ok_qty | INTEGER | unit OK | unit |
| ng_qty | INTEGER | unit NG | unit |

Kunci: (date, operator_id, model). `run_hours` per operator-hari dijumlahkan sama dengan jam efektif.

## work_hours (satu baris = satu operator, satu hari)

| Kolom | Tipe | Arti | Satuan |
|---|---|---|---|
| date | DATE | tanggal kerja | tanggal |
| operator_id | VARCHAR | ID operator | - |
| effective_hours | DOUBLE | jam kerja efektif, di luar istirahat (8 normal, 10 lembur) | jam |
| is_overtime | INTEGER | 1 jika hari lembur | 0/1 |

Kunci: (date, operator_id).

## dim_station (satu baris = satu stasiun)

| Kolom | Tipe | Arti | Satuan |
|---|---|---|---|
| station | VARCHAR | nama stasiun | - |
| sequence | INTEGER | urutan di lini (1–10) | - |
| ct_std_2layer_s | DOUBLE | standar CT untuk 2-layer | detik per unit OK |
| ct_std_4layer_s | DOUBLE | standar CT untuk 4-layer | detik per unit OK |
| ct_std_8layer_s | DOUBLE | standar CT untuk 8-layer | detik per unit OK |
| n_operator | INTEGER | jumlah operator yang ditetapkan | orang |

## dim_operator (satu baris = satu operator)

| Kolom | Tipe | Arti | Satuan |
|---|---|---|---|
| operator_id | VARCHAR | ID operator | - |
| station | VARCHAR | stasiun tetap | - |
| shift | VARCHAR | A atau B | - |
| start_date | DATE | tanggal mulai bekerja | tanggal |
| status | VARCHAR | baru (kurang dari sekitar 4 minggu) atau reguler | - |

## Relasi

daily_output.(date, operator_id) → work_hours.(date, operator_id)
daily_output.operator_id → dim_operator.operator_id
daily_output.station → dim_station.station
