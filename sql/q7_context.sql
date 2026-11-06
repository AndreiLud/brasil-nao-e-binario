-- Q7. How is the municipal vote associated with municipality size, region and income
-- (IBGE)? The point is the overlap of the distributions, not a stereotype: for each
-- group we report the spread of municipal results, not only the average.
-- Uses every runoff (2014 baseline, 2018, 2022, 2026). Size = Censo 2022 population
-- (2025 estimate for the one municipality created after the census). Income = Censo 2022
-- median household income per capita, grouped in five bands cut at the 20th, 40th, 60th and
-- 80th percentiles of the 5,570 municipalities with census income. Many municipalities share
-- the same median (395 sit exactly at R$ 1,212, the 2022 minimum wage), so ties are kept in
-- the same band (value <= cut point) and band sizes are close to, not exactly, one fifth.
-- The bands are the same for every election.

CREATE OR REPLACE TABLE q7_income_cuts AS
SELECT quantile_disc(income_pc_median, 0.2) AS p20, quantile_disc(income_pc_median, 0.4) AS p40,
       quantile_disc(income_pc_median, 0.6) AS p60, quantile_disc(income_pc_median, 0.8) AS p80
FROM municipalities WHERE income_pc_median IS NOT NULL;

CREATE OR REPLACE MACRO income_band(x) AS (
    SELECT CASE WHEN x IS NULL THEN NULL WHEN x <= p20 THEN 1 WHEN x <= p40 THEN 2
                WHEN x <= p60 THEN 3 WHEN x <= p80 THEN 4 ELSE 5 END
    FROM q7_income_cuts
);

CREATE OR REPLACE TABLE q7_groups AS
WITH base AS (
    SELECT m.*,
           CASE WHEN population <= 10000 THEN 1 WHEN population <= 50000 THEN 2
                WHEN population <= 200000 THEN 3 WHEN population <= 1000000 THEN 4 ELSE 5 END AS size_class,
           income_band(income_pc_median) AS income_q
    FROM mun_br m
    WHERE round = 2
),
long AS (
    SELECT year, 'size' AS dimension, size_class AS grp, * EXCLUDE (year) FROM base
    UNION ALL SELECT year, 'region', region_id, * EXCLUDE (year) FROM base
    UNION ALL SELECT year, 'income', income_q, * EXCLUDE (year) FROM base WHERE income_q IS NOT NULL
)
SELECT year, dimension, grp,
       count(*)                                        AS municipalities,
       sum(aptos)                                      AS aptos,
       sum(camp_l) / sum(camp_l + camp_b)              AS share_l2_weighted,
       quantile_cont(share_l2, 0.10)                   AS p10,
       quantile_cont(share_l2, 0.25)                   AS p25,
       median(share_l2)                                AS p50,
       quantile_cont(share_l2, 0.75)                   AS p75,
       quantile_cont(share_l2, 0.90)                   AS p90,
       min(share_l2) AS min_share_l2, max(share_l2) AS max_share_l2,
       count(*) FILTER (WHERE leader = 'L')            AS led_by_l,
       count(*) FILTER (WHERE leader = 'B')            AS led_by_b,
       min(income_pc_median) AS income_min, max(income_pc_median) AS income_max,
       min(population) AS pop_min, max(population) AS pop_max
FROM long
GROUP BY ALL
ORDER BY year, dimension, grp;

-- Histograms (5-point bins) of the municipal two-camp share inside each group, to draw
-- the overlapping distributions.
CREATE OR REPLACE TABLE q7_hist AS
WITH base AS (
    SELECT m.*,
           CASE WHEN population <= 10000 THEN 1 WHEN population <= 50000 THEN 2
                WHEN population <= 200000 THEN 3 WHEN population <= 1000000 THEN 4 ELSE 5 END AS size_class,
           income_band(income_pc_median) AS income_q
    FROM mun_br m WHERE round = 2
)
SELECT year, 'size' AS dimension, size_class AS grp, least(floor(share_l2 * 20), 19) * 5 AS bin_start_pct,
       count(*) AS municipalities FROM base GROUP BY ALL
UNION ALL
SELECT year, 'region', region_id, least(floor(share_l2 * 20), 19) * 5, count(*) FROM base GROUP BY ALL
UNION ALL
SELECT year, 'income', income_q, least(floor(share_l2 * 20), 19) * 5, count(*) FROM base
WHERE income_q IS NOT NULL GROUP BY ALL
ORDER BY 1, 2, 3, 4;

CREATE OR REPLACE TABLE q7_assoc AS
WITH d AS (
    SELECT year, region_id, share_l2, ln(income_pc_median) AS li, ln(population) AS lp
    FROM mun_br WHERE round = 2 AND income_pc_median IS NOT NULL
),
-- deviations from each region's mean, to measure the association inside regions
w AS (
    SELECT year, share_l2 - avg(share_l2) OVER (PARTITION BY year, region_id) AS s,
           li - avg(li) OVER (PARTITION BY year, region_id) AS li,
           lp - avg(lp) OVER (PARTITION BY year, region_id) AS lp
    FROM d
)
SELECT d.year,
       corr(share_l2, li) AS r_share_l2_log_income,
       corr(share_l2, lp) AS r_share_l2_log_population,
       any_value(wi.r_income_within) AS r_income_within_regions,
       any_value(wi.r_pop_within) AS r_pop_within_regions
FROM d
JOIN (SELECT year, corr(s, li) AS r_income_within, corr(s, lp) AS r_pop_within FROM w GROUP BY year) wi USING (year)
GROUP BY d.year ORDER BY d.year;

-- Where each income band sits: municipalities per band and region (fixed across years).
CREATE OR REPLACE TABLE q7_income_region AS
SELECT income_band(income_pc_median) AS income_band, region_id, any_value(region) AS region, count(*) AS municipalities
FROM municipalities WHERE income_pc_median IS NOT NULL
GROUP BY ALL ORDER BY ALL;
