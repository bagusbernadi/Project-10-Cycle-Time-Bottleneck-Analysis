-- 03 - Tabel inti. Constraint menolak data yang salah agar tidak bisa masuk database.
DROP TABLE IF EXISTS daily_output;
DROP TABLE IF EXISTS work_hours;
DROP TABLE IF EXISTS dim_station;
DROP TABLE IF EXISTS dim_operator;

CREATE TABLE dim_station (
    station          VARCHAR PRIMARY KEY,
    sequence         INTEGER NOT NULL CHECK (sequence BETWEEN 1 AND 10),
    ct_std_2layer_s  DOUBLE  NOT NULL CHECK (ct_std_2layer_s > 0),
    ct_std_4layer_s  DOUBLE  NOT NULL CHECK (ct_std_4layer_s > 0),
    ct_std_8layer_s  DOUBLE  NOT NULL CHECK (ct_std_8layer_s > 0),
    n_operator       INTEGER NOT NULL CHECK (n_operator > 0)
);

CREATE TABLE dim_operator (
    operator_id  VARCHAR PRIMARY KEY,
    station      VARCHAR NOT NULL REFERENCES dim_station(station),
    shift        VARCHAR NOT NULL CHECK (shift IN ('A', 'B')),
    start_date   DATE    NOT NULL,
    status       VARCHAR NOT NULL CHECK (status IN ('baru', 'reguler'))
);

CREATE TABLE work_hours (
    date             DATE    NOT NULL,
    operator_id      VARCHAR NOT NULL REFERENCES dim_operator(operator_id),
    effective_hours  DOUBLE  NOT NULL CHECK (effective_hours > 0 AND effective_hours <= 12),
    is_overtime      INTEGER NOT NULL CHECK (is_overtime IN (0, 1)),
    PRIMARY KEY (date, operator_id)
);

CREATE TABLE daily_output (
    date         DATE    NOT NULL,
    shift        VARCHAR NOT NULL CHECK (shift IN ('A', 'B')),
    station      VARCHAR NOT NULL REFERENCES dim_station(station),
    operator_id  VARCHAR NOT NULL REFERENCES dim_operator(operator_id),
    model        VARCHAR NOT NULL CHECK (model IN ('2-layer', '4-layer', '8-layer')),
    run_hours    DOUBLE  NOT NULL CHECK (run_hours > 0),
    ok_qty       INTEGER NOT NULL CHECK (ok_qty >= 0),
    ng_qty       INTEGER NOT NULL CHECK (ng_qty >= 0),
    PRIMARY KEY (date, operator_id, model)
);

INSERT INTO dim_station SELECT * FROM read_csv_auto('{{CLEAN_DIR}}/dim_station.csv');
INSERT INTO dim_operator SELECT operator_id, station, shift, CAST(start_date AS DATE), status
    FROM read_csv_auto('{{CLEAN_DIR}}/dim_operator_clean.csv');
INSERT INTO work_hours SELECT CAST(date AS DATE), operator_id, effective_hours, is_overtime
    FROM read_csv_auto('{{CLEAN_DIR}}/work_hours_clean.csv');
INSERT INTO daily_output SELECT CAST(date AS DATE), shift, station, operator_id, model, run_hours, ok_qty, ng_qty
    FROM read_csv_auto('{{CLEAN_DIR}}/daily_output_clean.csv');
