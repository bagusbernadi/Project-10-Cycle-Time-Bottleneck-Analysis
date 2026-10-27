# Data

- `raw/` berisi data simulasi dari `code/1-data-preparation/python/01_generate_data.py` (seed tetap). Tidak di-commit; dibuat ulang oleh skrip yang sama (hasil identik karena seed tetap).
- `raw/dirty_injection_log.csv` mencatat jumlah data kotor yang disisipkan.
- `ground_truth.md` dan `ground_truth.json` berisi fakta yang sengaja ditanam, dipakai untuk Q13.
- `clean/` berisi hasil cleaning. Tidak di-commit; dibuat ulang oleh `02_clean.py`.

Jalankan ulang dari folder `project/`:

    python code/1-data-preparation/python/01_generate_data.py
    python code/1-data-preparation/python/02_clean.py
