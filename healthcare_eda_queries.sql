-- =============================================================================
--  HEALTHCARE WAITING LIST — SQL ANALYSIS
--  Ireland HSE National Waiting List Data  |  2018 – 2021
--  Portfolio Project  |  Senior Data Analyst
-- =============================================================================
--  DATABASE: MySQL / PostgreSQL compatible (minor syntax differences noted)
--  Dialect:  Standard SQL  (ANSI-compliant where possible)
-- =============================================================================


-- =============================================================================
-- SECTION 1: SCHEMA DEFINITION — DATA MODEL
-- =============================================================================

-- ── Dimension Table: dim_specialty ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_specialty (
    specialty_name   VARCHAR(100)  NOT NULL,
    specialty_group  VARCHAR(60)   NOT NULL DEFAULT 'Other',
    CONSTRAINT pk_specialty PRIMARY KEY (specialty_name)
);

-- ── Fact Table: fact_inpatient ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_inpatient (
    id               INT           NOT NULL AUTO_INCREMENT,
    archive_date     DATE          NOT NULL,
    specialty_hipe   INT,
    specialty_name   VARCHAR(100)  NOT NULL,
    case_type        VARCHAR(30),           -- 'Inpatient' | 'Day Case'
    adult_child      VARCHAR(10),           -- 'Adult' | 'Child'
    age_profile      VARCHAR(10),           -- '0-15' | '16-64' | '65+'
    time_bands       VARCHAR(20),           -- '0-3 Months' … '18+ Months'
    total            INT           NOT NULL,
    year             INT           NOT NULL,
    CONSTRAINT pk_inpatient    PRIMARY KEY (id),
    CONSTRAINT fk_ip_specialty FOREIGN KEY (specialty_name)
        REFERENCES dim_specialty(specialty_name)
);

-- ── Fact Table: fact_outpatient ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_outpatient (
    id               INT           NOT NULL AUTO_INCREMENT,
    archive_date     DATE          NOT NULL,
    specialty_hipe   INT,
    specialty_name   VARCHAR(100)  NOT NULL,
    adult_child      VARCHAR(10),
    age_profile      VARCHAR(10),
    time_bands       VARCHAR(20),
    total            INT           NOT NULL,
    year             INT           NOT NULL,
    CONSTRAINT pk_outpatient   PRIMARY KEY (id),
    CONSTRAINT fk_op_specialty FOREIGN KEY (specialty_name)
        REFERENCES dim_specialty(specialty_name)
);

-- ── Combined View: vw_waiting_list ─────────────────────────────────────────
CREATE OR REPLACE VIEW vw_waiting_list AS
    SELECT
        archive_date,
        specialty_name,
        adult_child,
        age_profile,
        time_bands,
        total,
        year,
        'Inpatient'  AS patient_type
    FROM fact_inpatient
    UNION ALL
    SELECT
        archive_date,
        specialty_name,
        adult_child,
        age_profile,
        time_bands,
        total,
        year,
        'Outpatient' AS patient_type
    FROM fact_outpatient;

-- ── Enriched View: vw_waiting_list_full ────────────────────────────────────
-- Joins the combined fact view with the specialty dimension
CREATE OR REPLACE VIEW vw_waiting_list_full AS
    SELECT
        w.*,
        COALESCE(s.specialty_group, 'Other') AS specialty_group
    FROM  vw_waiting_list  w
    LEFT JOIN dim_specialty s
           ON w.specialty_name = s.specialty_name;

-- =============================================================================
-- NOTE ON JOIN STRATEGY:
--   LEFT JOIN is used to preserve all records even if a specialty_name
--   in the fact tables has no matching entry in dim_specialty.
--   Unmatched records receive specialty_group = 'Other'.
--   This is consistent with the Python pipeline (fillna('Other')).
-- =============================================================================


-- =============================================================================
-- SECTION 2: BUSINESS QUESTION 1
--   How has the total waiting list changed year-on-year,
--   and what is the COVID-19 impact?
-- =============================================================================

-- Q1a: Annual totals by patient type
SELECT
    year,
    patient_type,
    SUM(total)                                       AS total_patients,
    COUNT(*)                                         AS record_count
FROM vw_waiting_list_full
GROUP BY year, patient_type
ORDER BY year, patient_type;

-- Q1b: Year-over-year percentage change
WITH annual AS (
    SELECT
        year,
        patient_type,
        SUM(total) AS total_patients
    FROM vw_waiting_list_full
    GROUP BY year, patient_type
)
SELECT
    curr.year,
    curr.patient_type,
    curr.total_patients                                             AS current_year,
    prev.total_patients                                             AS prior_year,
    curr.total_patients - prev.total_patients                       AS absolute_change,
    ROUND(
        (curr.total_patients - prev.total_patients)
        * 100.0 / prev.total_patients,
    1)                                                              AS pct_change
FROM  annual curr
LEFT JOIN annual prev
       ON curr.patient_type = prev.patient_type
      AND curr.year         = prev.year + 1
WHERE prev.year IS NOT NULL
ORDER BY curr.patient_type, curr.year;

-- Q1c: Monthly trend with 3-month rolling average
-- (MySQL 8+ / PostgreSQL)
WITH monthly AS (
    SELECT
        DATE_FORMAT(archive_date, '%Y-%m') AS year_month,
        archive_date,
        patient_type,
        SUM(total)                         AS monthly_total
    FROM vw_waiting_list_full
    GROUP BY year_month, patient_type
)
SELECT
    year_month,
    patient_type,
    monthly_total,
    ROUND(AVG(monthly_total) OVER (
        PARTITION BY patient_type
        ORDER BY year_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 0)                                  AS rolling_3mo_avg,
    SUM(monthly_total) OVER (
        PARTITION BY patient_type
        ORDER BY year_month
    )                                      AS cumulative_total
FROM monthly
ORDER BY year_month, patient_type;


-- =============================================================================
-- SECTION 3: BUSINESS QUESTION 2
--   Which specialties carry the highest waiting list burden,
--   and where are the long-wait concentrations?
-- =============================================================================

-- Q2a: Top 15 specialties — total volume + long-wait rate
SELECT
    specialty_name,
    specialty_group,
    SUM(total)                                                       AS total_patients,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)  AS long_wait_count,
    ROUND(
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
        * 100.0 / SUM(total),
    2)                                                               AS long_wait_pct,
    RANK() OVER (ORDER BY SUM(total) DESC)                          AS volume_rank,
    RANK() OVER (
        ORDER BY
            SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
            * 100.0 / SUM(total) DESC
    )                                                                AS risk_rank
FROM vw_waiting_list_full
GROUP BY specialty_name, specialty_group
ORDER BY volume_rank
LIMIT 15;

-- Q2b: Specialty group risk matrix
SELECT
    specialty_group,
    SUM(total)                                                       AS total_patients,
    ROUND(SUM(total) * 100.0 / SUM(SUM(total)) OVER (), 2)         AS share_of_total_pct,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)  AS long_wait_patients,
    ROUND(
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
        * 100.0 / SUM(total),
    2)                                                               AS long_wait_rate_pct,
    CASE
        WHEN SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
             * 100.0 / SUM(total) >= 7  THEN 'HIGH'
        WHEN SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
             * 100.0 / SUM(total) >= 4  THEN 'MEDIUM'
        ELSE 'LOW'
    END                                                              AS risk_level
FROM vw_waiting_list_full
GROUP BY specialty_group
ORDER BY long_wait_rate_pct DESC;

-- Q2c: Specialty annual trend — which grew during COVID?
SELECT
    specialty_name,
    specialty_group,
    SUM(CASE WHEN year = 2018 THEN total ELSE 0 END) AS total_2018,
    SUM(CASE WHEN year = 2019 THEN total ELSE 0 END) AS total_2019,
    SUM(CASE WHEN year = 2020 THEN total ELSE 0 END) AS total_2020,
    ROUND(
        (SUM(CASE WHEN year = 2020 THEN total ELSE 0 END)
         - SUM(CASE WHEN year = 2019 THEN total ELSE 0 END))
        * 100.0
        / NULLIF(SUM(CASE WHEN year = 2019 THEN total ELSE 0 END), 0),
    1)                                               AS covid_yoy_pct
FROM vw_waiting_list_full
GROUP BY specialty_name, specialty_group
HAVING SUM(CASE WHEN year = 2019 THEN total ELSE 0 END) > 0
ORDER BY covid_yoy_pct DESC
LIMIT 20;


-- =============================================================================
-- SECTION 4: BUSINESS QUESTION 3
--   How does waiting time distribution differ across
--   age groups and adult vs child patients?
-- =============================================================================

-- Q3a: Age group × time band cross-analysis
SELECT
    age_profile,
    time_bands,
    SUM(total)                                               AS total_patients,
    ROUND(
        SUM(total) * 100.0
        / SUM(SUM(total)) OVER (PARTITION BY age_profile),
    2)                                                       AS pct_within_age_group
FROM vw_waiting_list_full
WHERE age_profile IS NOT NULL
GROUP BY age_profile, time_bands
ORDER BY
    age_profile,
    CASE time_bands
        WHEN '0-3 Months'   THEN 1
        WHEN '3-6 Months'   THEN 2
        WHEN '6-9 Months'   THEN 3
        WHEN '9-12 Months'  THEN 4
        WHEN '12-15 Months' THEN 5
        WHEN '15-18 Months' THEN 6
        WHEN '18+ Months'   THEN 7
        ELSE 8
    END;

-- Q3b: Adult vs Child — long-wait comparison by year
SELECT
    year,
    adult_child,
    SUM(total)                                                       AS total_patients,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)  AS long_wait_count,
    ROUND(
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
        * 100.0 / SUM(total),
    2)                                                               AS long_wait_pct
FROM vw_waiting_list_full
WHERE adult_child IS NOT NULL
GROUP BY year, adult_child
ORDER BY year, adult_child;

-- Q3c: 65+ elderly growth analysis
SELECT
    year,
    patient_type,
    SUM(CASE WHEN age_profile = '65+' THEN total ELSE 0 END)   AS elderly_patients,
    SUM(total)                                                   AS all_patients,
    ROUND(
        SUM(CASE WHEN age_profile = '65+' THEN total ELSE 0 END)
        * 100.0 / SUM(total),
    2)                                                           AS elderly_share_pct
FROM vw_waiting_list_full
WHERE age_profile IS NOT NULL
GROUP BY year, patient_type
ORDER BY year, patient_type;


-- =============================================================================
-- SECTION 5: BUSINESS QUESTION 4
--   What does the waiting duration profile reveal about
--   system performance — and where is the 18+ month crisis worst?
-- =============================================================================

-- Q4a: Time band distribution — full profile
SELECT
    patient_type,
    time_bands,
    SUM(total)                                               AS total_patients,
    ROUND(
        SUM(total) * 100.0
        / SUM(SUM(total)) OVER (PARTITION BY patient_type),
    2)                                                       AS pct_of_type
FROM vw_waiting_list_full
GROUP BY patient_type, time_bands
ORDER BY
    patient_type,
    CASE time_bands
        WHEN '0-3 Months'   THEN 1  WHEN '3-6 Months'   THEN 2
        WHEN '6-9 Months'   THEN 3  WHEN '9-12 Months'  THEN 4
        WHEN '12-15 Months' THEN 5  WHEN '15-18 Months' THEN 6
        WHEN '18+ Months'   THEN 7  ELSE 8
    END;

-- Q4b: 18+ month waiters by specialty and year
SELECT
    specialty_name,
    specialty_group,
    year,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END) AS long_wait_total,
    SUM(total)                                                      AS all_patients,
    ROUND(
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
        * 100.0 / NULLIF(SUM(total), 0),
    2)                                                              AS long_wait_pct,
    LAG(SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END))
        OVER (PARTITION BY specialty_name ORDER BY year)           AS prev_year_long_wait,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
    - LAG(SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END))
        OVER (PARTITION BY specialty_name ORDER BY year)           AS yoy_change
FROM vw_waiting_list_full
GROUP BY specialty_name, specialty_group, year
ORDER BY year, long_wait_total DESC;

-- Q4c: Case type comparison — Day Case vs Inpatient wait profiles
SELECT
    case_type,
    time_bands,
    SUM(total)                                               AS total_patients,
    ROUND(
        SUM(total) * 100.0
        / SUM(SUM(total)) OVER (PARTITION BY case_type),
    2)                                                       AS pct_within_case_type
FROM fact_inpatient fi
LEFT JOIN dim_specialty ds ON fi.specialty_name = ds.specialty_name
WHERE case_type IS NOT NULL
GROUP BY case_type, time_bands
ORDER BY
    case_type,
    CASE time_bands
        WHEN '0-3 Months'   THEN 1  WHEN '3-6 Months'   THEN 2
        WHEN '6-9 Months'   THEN 3  WHEN '9-12 Months'  THEN 4
        WHEN '12-15 Months' THEN 5  WHEN '15-18 Months' THEN 6
        WHEN '18+ Months'   THEN 7  ELSE 8
    END;


-- =============================================================================
-- SECTION 6: BUSINESS QUESTION 5
--   Descriptive statistics — SQL computed
-- =============================================================================

-- Q5: Statistical summary per specialty
-- (Median approximation via percentile_cont — PostgreSQL syntax)
SELECT
    specialty_name,
    patient_type,
    COUNT(*)                                  AS record_count,
    SUM(total)                                AS sum_total,
    ROUND(AVG(total), 2)                      AS mean_total,
    ROUND(STDDEV(total), 2)                   AS std_dev,
    MIN(total)                                AS min_total,
    MAX(total)                                AS max_total,
    MAX(total) - MIN(total)                   AS range_total,
    ROUND(STDDEV(total) / AVG(total) * 100, 1) AS coeff_variation_pct,
    -- Percentile approximation (PostgreSQL)
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total) AS q1,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total) AS median_total,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total) AS q3,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total) AS p95
FROM vw_waiting_list_full
GROUP BY specialty_name, patient_type
ORDER BY sum_total DESC
LIMIT 20;

-- Q5b: Overall descriptive stats (MySQL compatible median approximation)
WITH ranked AS (
    SELECT
        total,
        patient_type,
        ROW_NUMBER() OVER (PARTITION BY patient_type ORDER BY total)  AS rn,
        COUNT(*) OVER (PARTITION BY patient_type)                     AS cnt
    FROM vw_waiting_list_full
)
SELECT
    patient_type,
    COUNT(*)                   AS n,
    SUM(total)                 AS sum_total,
    ROUND(AVG(total), 2)       AS mean_total,
    AVG(CASE WHEN rn IN (FLOOR((cnt+1)/2), CEIL((cnt+1)/2))
             THEN total END)   AS median_approx,
    ROUND(STDDEV(total), 2)    AS std_dev,
    MIN(total)                 AS min_val,
    MAX(total)                 AS max_val
FROM ranked
GROUP BY patient_type;


-- =============================================================================
-- SECTION 7: ADVANCED ANALYTICS — WINDOW FUNCTIONS
-- =============================================================================

-- Q6a: Running total — monthly cumulative backlog
SELECT
    DATE_FORMAT(archive_date, '%Y-%m')         AS year_month,
    patient_type,
    SUM(total)                                 AS monthly_total,
    SUM(SUM(total)) OVER (
        PARTITION BY patient_type
        ORDER BY DATE_FORMAT(archive_date, '%Y-%m')
    )                                          AS cumulative_total,
    AVG(SUM(total)) OVER (
        PARTITION BY patient_type
        ORDER BY DATE_FORMAT(archive_date, '%Y-%m')
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    )                                          AS rolling_3mo_avg
FROM vw_waiting_list_full
GROUP BY year_month, patient_type
ORDER BY year_month, patient_type;

-- Q6b: Specialty ranking within group each year
SELECT
    year,
    specialty_group,
    specialty_name,
    SUM(total)                                                AS total_patients,
    RANK() OVER (
        PARTITION BY year, specialty_group
        ORDER BY SUM(total) DESC
    )                                                         AS rank_within_group,
    ROUND(
        SUM(total) * 100.0
        / SUM(SUM(total)) OVER (PARTITION BY year, specialty_group),
    1)                                                        AS share_within_group_pct
FROM vw_waiting_list_full
GROUP BY year, specialty_group, specialty_name
ORDER BY year, specialty_group, rank_within_group;

-- Q6c: COVID shock detection — flag months with >10% MoM change
WITH monthly_totals AS (
    SELECT
        DATE_FORMAT(archive_date, '%Y-%m') AS year_month,
        SUM(total)                         AS monthly_total
    FROM vw_waiting_list_full
    GROUP BY year_month
),
with_change AS (
    SELECT
        year_month,
        monthly_total,
        LAG(monthly_total) OVER (ORDER BY year_month)    AS prev_month,
        ROUND(
            (monthly_total - LAG(monthly_total) OVER (ORDER BY year_month))
            * 100.0
            / LAG(monthly_total) OVER (ORDER BY year_month),
        1)                                               AS mom_pct_change
    FROM monthly_totals
)
SELECT
    year_month,
    monthly_total,
    prev_month,
    mom_pct_change,
    CASE
        WHEN ABS(mom_pct_change) > 10 THEN '⚠ SPIKE'
        WHEN ABS(mom_pct_change) > 5  THEN '! ELEVATED'
        ELSE 'normal'
    END                                                  AS change_flag
FROM with_change
WHERE mom_pct_change IS NOT NULL
ORDER BY year_month;

-- Q6d: Long-wait acceleration index — which specialties worsened fastest?
WITH lw_annual AS (
    SELECT
        specialty_name,
        year,
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
            * 100.0 / NULLIF(SUM(total), 0)   AS lw_rate
    FROM vw_waiting_list_full
    GROUP BY specialty_name, year
)
SELECT
    a.specialty_name,
    a.lw_rate                                   AS rate_2020,
    b.lw_rate                                   AS rate_2018,
    ROUND(a.lw_rate - b.lw_rate, 2)             AS acceleration,
    CASE
        WHEN a.lw_rate - b.lw_rate > 5 THEN 'WORSENING FAST'
        WHEN a.lw_rate - b.lw_rate > 2 THEN 'WORSENING'
        WHEN a.lw_rate - b.lw_rate < -2 THEN 'IMPROVING'
        ELSE 'STABLE'
    END                                         AS trend_flag
FROM       lw_annual a
INNER JOIN lw_annual b
        ON a.specialty_name = b.specialty_name
       AND a.year = 2020
       AND b.year = 2018
ORDER BY acceleration DESC
LIMIT 20;


-- =============================================================================
-- SECTION 8: BUSINESS RECOMMENDATIONS QUERIES
--   Queries that directly support each recommendation
-- =============================================================================

-- REC 1: Quantify the 18+ month crisis
SELECT
    'TOTAL 18+ MONTH WAITERS'           AS metric,
    SUM(total)                          AS value
FROM vw_waiting_list_full
WHERE time_bands = '18+ Months'
UNION ALL
SELECT
    '% OF ALL PATIENTS',
    ROUND(
        (SELECT SUM(total) FROM vw_waiting_list_full WHERE time_bands = '18+ Months')
        * 100.0 / (SELECT SUM(total) FROM vw_waiting_list_full),
    1);

-- REC 2: Top 5 specialties needing surge capacity (highest long-wait rate)
SELECT
    specialty_name,
    specialty_group,
    SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)  AS long_waiters,
    ROUND(
        SUM(CASE WHEN time_bands = '18+ Months' THEN total ELSE 0 END)
        * 100.0 / SUM(total),
    1)                                                               AS long_wait_pct
FROM vw_waiting_list_full
GROUP BY specialty_name, specialty_group
HAVING SUM(total) > 10000
ORDER BY long_wait_pct DESC
LIMIT 5;

-- REC 3: Outpatient efficiency impact — 5% improvement scenario
SELECT
    'Current Outpatient Total'                AS scenario,
    SUM(total)                                AS patients
FROM vw_waiting_list_full
WHERE patient_type = 'Outpatient'
UNION ALL
SELECT
    '5% Efficiency Gain Would Clear',
    ROUND(SUM(total) * 0.05, 0)
FROM vw_waiting_list_full
WHERE patient_type = 'Outpatient';

-- REC 4: Paediatric long waits
SELECT
    year,
    SUM(CASE WHEN adult_child='Child' AND time_bands='18+ Months'
             THEN total ELSE 0 END)          AS child_long_waiters,
    SUM(CASE WHEN adult_child='Child'
             THEN total ELSE 0 END)          AS child_total,
    ROUND(
        SUM(CASE WHEN adult_child='Child' AND time_bands='18+ Months' THEN total ELSE 0 END)
        * 100.0
        / NULLIF(SUM(CASE WHEN adult_child='Child' THEN total ELSE 0 END), 0),
    2)                                       AS child_long_wait_pct
FROM vw_waiting_list_full
WHERE adult_child IS NOT NULL
GROUP BY year
ORDER BY year;

-- =============================================================================
-- END OF SQL ANALYSIS FILE
-- =============================================================================
