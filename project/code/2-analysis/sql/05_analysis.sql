-- 05 - Query analisis Q1-Q8. Setiap blok bernama -- name: X disimpan ke results/2-analysis/X.csv.

-- name: q1_capacity
SELECT model, sequence, station, n_operator_aktif, ROUND(ct_std_s, 1) AS ct_std_s,
       ROUND(ct_median_s, 1) AS ct_median_s, ROUND(kapasitas_unit_per_hari, 1) AS kapasitas_unit_per_hari,
       RANK() OVER (PARTITION BY model ORDER BY kapasitas_unit_per_hari) AS peringkat_bottleneck
FROM v_station_capacity
ORDER BY model, peringkat_bottleneck, station;

-- name: q2_capacity_shift
WITH st AS (
    SELECT station, model, shift, median(ct_s) AS ct_median_s, COUNT(DISTINCT operator_id) AS n_op
    FROM v_output_ct GROUP BY station, model, shift
)
SELECT model, shift, station, n_op, ROUND(ct_median_s, 1) AS ct_median_s,
       ROUND(n_op * 8 * 3600.0 / ct_median_s, 1) AS kapasitas_unit_per_hari,
       RANK() OVER (PARTITION BY model, shift ORDER BY n_op * 8 * 3600.0 / ct_median_s) AS peringkat_bottleneck
FROM st
ORDER BY model, shift, peringkat_bottleneck, station;

-- name: q3_stability
WITH d AS (
    SELECT station, model, date, median(ct_s) AS ct_d, COUNT(DISTINCT operator_id) AS n_op
    FROM v_output_ct GROUP BY station, model, date
), c AS (
    SELECT station, model, n_op * 8 * 3600.0 / ct_d AS cap FROM d
)
SELECT station, model, COUNT(*) AS hari, ROUND(AVG(cap), 1) AS rata_rata_kapasitas,
       ROUND(STDDEV_SAMP(cap), 1) AS simpang_baku, ROUND(STDDEV_SAMP(cap) / AVG(cap), 3) AS koef_variasi
FROM c GROUP BY station, model
ORDER BY model, koef_variasi DESC, station;

-- name: q4_operator
WITH bounds AS (
    SELECT station, model, quantile_cont(ct_s, 0.25) AS q1, quantile_cont(ct_s, 0.75) AS q3, median(ct_s) AS med
    FROM v_output_ct GROUP BY station, model
), flag AS (
    SELECT v.station, v.operator_id, v.model,
           (v.ct_s < b.q1 - 1.5 * (b.q3 - b.q1) OR v.ct_s > b.q3 + 1.5 * (b.q3 - b.q1)) AS outlier
    FROM v_output_ct v JOIN bounds b USING (station, model)
)
SELECT o.station, o.operator_id, o.model, o.status, o.n_hari,
       ROUND(o.ct_median_s, 1) AS ct_median_s, ROUND(o.ct_q1_s, 1) AS ct_q1_s, ROUND(o.ct_q3_s, 1) AS ct_q3_s,
       ROUND(b.med, 1) AS ct_median_stasiun,
       ROUND(o.ct_median_s / b.med - 1, 4) AS deviasi,
       (SELECT SUM(CAST(f.outlier AS INT)) FROM flag f
         WHERE f.operator_id = o.operator_id AND f.station = o.station AND f.model = o.model) AS n_outlier_hari
FROM v_operator_ct o JOIN bounds b USING (station, model)
ORDER BY o.station, o.model, deviasi DESC, o.operator_id;

-- name: q5_fastest
WITH st AS (
    SELECT station, model, median(ct_s) AS med FROM v_output_ct GROUP BY station, model
), mn AS (
    SELECT station, model, MIN(ct_median_s) AS ct_tercepat
    FROM v_operator_ct WHERE n_hari >= 5 GROUP BY station, model
)
SELECT mn.station, mn.model, ROUND(st.med, 1) AS ct_median_stasiun, ROUND(mn.ct_tercepat, 1) AS ct_tercepat,
       ROUND(mn.ct_tercepat / st.med, 3) AS rasio_tercepat_per_median
FROM mn JOIN st USING (station, model)
ORDER BY model, rasio_tercepat_per_median, mn.station;

-- name: q6_learning
SELECT o.operator_id, o.station, CAST(FLOOR(DATE_DIFF('day', d.start_date, o.date) / 7) AS INT) + 1 AS minggu_ke,
       COUNT(*) AS baris, ROUND(median(o.ct_s / o.ct_std_s), 3) AS rasio_ct_per_standar
FROM v_output_ct o JOIN dim_operator d USING (operator_id)
WHERE d.status = 'baru'
GROUP BY o.operator_id, o.station, minggu_ke
ORDER BY minggu_ke;

-- name: q7_shift_overtime
SELECT shift, CASE WHEN is_overtime = 1 THEN 'lembur (10 jam)' ELSE 'normal (8 jam)' END AS kondisi,
       COUNT(*) AS baris, ROUND(median(ct_s / ct_std_s), 3) AS rasio_ct_per_standar
FROM v_output_ct
GROUP BY shift, is_overtime
ORDER BY shift, is_overtime;

-- name: q8_model_ratio
WITH m AS (
    SELECT station, model, median(ct_s) AS med FROM v_output_ct GROUP BY station, model
)
SELECT t8.station, ROUND(t8.med, 1) AS ct_8layer_s, ROUND(t2.med, 1) AS ct_2layer_s,
       ROUND(t8.med / t2.med, 3) AS rasio_8_per_2, ROUND(t4.med / t2.med, 3) AS rasio_4_per_2
FROM m t8 JOIN m t2 ON t2.station = t8.station AND t2.model = '2-layer' AND t8.model = '8-layer'
JOIN m t4 ON t4.station = t8.station AND t4.model = '4-layer'
ORDER BY rasio_8_per_2 DESC, t8.station;

-- name: q_operator_rows
SELECT o.date, o.station, o.operator_id, o.model, o.run_hours, o.ok_qty, o.ng_qty,
       ROUND(o.ct_s, 2) AS ct_s, w.effective_hours, w.is_overtime
FROM v_output_ct o JOIN work_hours w USING (date, operator_id)
ORDER BY o.date, o.operator_id, o.model;

-- name: q14_agg
-- CT agregat (jam × 3600 ÷ unit OK, dijumlahkan dulu) per operator, stasiun, dan model: dipakai untuk cek silang Excel
SELECT station, operator_id, model,
       COUNT(*) AS baris,
       ROUND(SUM(run_hours), 2) AS total_jam,
       SUM(ok_qty) AS total_ok,
       ROUND(SUM(run_hours) * 3600.0 / SUM(ok_qty), 2) AS ct_agregat_s
FROM v_output_ct
GROUP BY station, operator_id, model
ORDER BY station, operator_id, model;
