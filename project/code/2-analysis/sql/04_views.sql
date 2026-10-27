-- 04 - View KPI. Rumus mengikuti docs/kpi_definitions.md.
-- CT (detik per unit OK) = jam efektif per baris × 3600 ÷ unit OK. Hanya baris dengan ok_qty > 0.
-- Kapasitas stasiun (unit per hari) = jumlah operator aktif × 8 jam normal × 3600 ÷ CT median stasiun-model.

CREATE OR REPLACE VIEW v_output_ct AS
SELECT o.date, o.station, o.operator_id, o.model, o.shift,
       w.is_overtime, d.status,
       o.run_hours, o.ok_qty, o.ng_qty,
       o.run_hours * 3600.0 / o.ok_qty AS ct_s,
       CASE o.model WHEN '2-layer' THEN s.ct_std_2layer_s
                    WHEN '4-layer' THEN s.ct_std_4layer_s
                    ELSE s.ct_std_8layer_s END AS ct_std_s
FROM daily_output o
JOIN work_hours   w ON w.date = o.date AND w.operator_id = o.operator_id
JOIN dim_operator d ON d.operator_id = o.operator_id
JOIN dim_station  s ON s.station = o.station
WHERE o.ok_qty > 0;

-- CT per operator, stasiun, dan model (dengan IQR untuk deteksi outlier di level operator)
CREATE OR REPLACE VIEW v_operator_ct AS
SELECT station, operator_id, model,
       COUNT(DISTINCT date)            AS n_hari,
       MAX(status)                     AS status,
       MAX(ct_std_s)                   AS ct_std_s,
       median(ct_s)                    AS ct_median_s,
       quantile_cont(ct_s, 0.25)       AS ct_q1_s,
       quantile_cont(ct_s, 0.75)       AS ct_q3_s,
       quantile_cont(ct_s, 0.75) - quantile_cont(ct_s, 0.25) AS ct_iqr_s
FROM v_output_ct
GROUP BY station, operator_id, model;

-- CT median per stasiun dan model, dan kapasitas (hanya operator dengan >= 5 hari data)
CREATE OR REPLACE VIEW v_station_capacity AS
WITH st AS (
    SELECT station, model, median(ct_s) AS ct_median_s, MAX(ct_std_s) AS ct_std_s
    FROM v_output_ct GROUP BY station, model
),
op AS (
    SELECT station, model, COUNT(*) AS n_operator_aktif
    FROM v_operator_ct WHERE n_hari >= 5 GROUP BY station, model
)
SELECT st.station, st.model, dim.sequence,
       st.ct_std_s, st.ct_median_s,
       op.n_operator_aktif,
       op.n_operator_aktif * 8 * 3600.0 / st.ct_median_s AS kapasitas_unit_per_hari
FROM st
JOIN op ON op.station = st.station AND op.model = st.model
JOIN dim_station dim ON dim.station = st.station;

-- Output lini per model = kapasitas stasiun terendah (bottleneck)
CREATE OR REPLACE VIEW v_line_output AS
SELECT model,
       arg_min(station, kapasitas_unit_per_hari)   AS bottleneck,
       MIN(kapasitas_unit_per_hari)                AS output_lini_per_hari
FROM v_station_capacity
GROUP BY model;
