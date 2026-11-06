-- Q3. How mixed is the vote?
--   * distribution of the municipal two-camp share (5-point bins)
--   * municipalities where the side that lost locally still got more than 30% / 40%
--     of the two-camp vote (in a runoff, the two-camp vote equals the valid vote)
--   * absolute votes of each camp in each region and state
--   * the most lulista and the most bolsonarista municipality, and the other side there

CREATE OR REPLACE TABLE q3_hist AS
SELECT year, round,
       least(floor(share_l2 * 20), 19) * 5 AS bin_start_pct,   -- 0, 5, ..., 95
       count(*)                            AS municipalities,
       sum(aptos)                          AS aptos,
       sum(camp_l)                         AS camp_l,
       sum(camp_b)                         AS camp_b
FROM mun_br
GROUP BY ALL
ORDER BY year, round, bin_start_pct;

-- Ties (exactly 50/50 between the camps) have no local loser and are left out here.
CREATE OR REPLACE TABLE q3_minority AS
WITH m AS (
    SELECT *, least(share_l2, 1 - share_l2) AS local_minority_share FROM mun_br WHERE leader2 <> 'tie'
)
SELECT year, round,
       count(*)                                                      AS municipalities,
       count(*) FILTER (WHERE local_minority_share > 0.30)           AS n_minority_over_30,
       count(*) FILTER (WHERE local_minority_share > 0.40)           AS n_minority_over_40,
       count(*) FILTER (WHERE local_minority_share > 0.20)           AS n_minority_over_20,
       count(*) FILTER (WHERE local_minority_share > 0.10)           AS n_minority_over_10,
       count(*) FILTER (WHERE local_minority_share > 0.30) / count(*) AS share_minority_over_30,
       count(*) FILTER (WHERE local_minority_share > 0.40) / count(*) AS share_minority_over_40,
       count(*) FILTER (WHERE local_minority_share > 0.10) / count(*) AS share_minority_over_10,
       sum(aptos) FILTER (WHERE local_minority_share > 0.30) / sum(aptos) AS aptos_share_minority_over_30,
       sum(aptos) FILTER (WHERE local_minority_share > 0.40) / sum(aptos) AS aptos_share_minority_over_40,
       min(local_minority_share)                                     AS min_minority_share,
       min(share_l2)                                                 AS min_share_l2,
       max(share_l2)                                                 AS max_share_l2,
       -- votes of the local minority, summed over all municipalities
       sum(least(camp_l, camp_b))                                    AS local_minority_votes,
       sum(least(camp_l, camp_b)) / sum(camp_l + camp_b)             AS local_minority_vote_share
FROM m
GROUP BY ALL
ORDER BY year, round;

-- Absolute votes by region (abroad shown as its own row).
CREATE OR REPLACE TABLE q3_region AS
SELECT year, round,
       CASE WHEN abroad THEN 'Exterior' ELSE region END AS region,
       CASE WHEN abroad THEN 9 ELSE region_id END       AS region_id,
       count(*) FILTER (WHERE NOT abroad)               AS municipalities,
       sum(aptos) AS aptos, sum(validos) AS validos,
       sum(camp_l) AS camp_l, sum(camp_b) AS camp_b, sum(others) AS others,
       sum(blank_null) AS blank_null, sum(absent) AS absent,
       sum(camp_l) / sum(camp_l + camp_b) AS share_l2,
       count(*) FILTER (WHERE leader = 'L' AND NOT abroad) AS led_by_l,
       count(*) FILTER (WHERE leader = 'B' AND NOT abroad) AS led_by_b,
       count(*) FILTER (WHERE leader = 'O' AND NOT abroad) AS led_by_other,
       sum(camp_l) - sum(camp_b)                           AS lead_l_votes
FROM mun_results
GROUP BY ALL
ORDER BY year, round, region_id;

CREATE OR REPLACE TABLE q3_state AS
SELECT year, round, uf, any_value(region) AS region,
       sum(aptos) AS aptos, sum(validos) AS validos,
       sum(camp_l) AS camp_l, sum(camp_b) AS camp_b, sum(others) AS others,
       sum(camp_l) / sum(camp_l + camp_b) AS share_l2
FROM mun_br
GROUP BY ALL
ORDER BY year, round, uf;

-- Extremes: most lulista and most bolsonarista municipality per election/round,
-- among all municipalities and among those with at least 100,000 voters.
CREATE OR REPLACE TABLE q3_extremes AS
WITH ranked AS (
    SELECT *,
           row_number() OVER (PARTITION BY year, round ORDER BY share_l2 DESC, cd_ibge) AS rank_l,
           row_number() OVER (PARTITION BY year, round ORDER BY share_l2 ASC, cd_ibge)  AS rank_b,
           row_number() OVER (PARTITION BY year, round, aptos >= 100000 ORDER BY share_l2 DESC, cd_ibge) AS rank_l_big,
           row_number() OVER (PARTITION BY year, round, aptos >= 100000 ORDER BY share_l2 ASC, cd_ibge)  AS rank_b_big
    FROM mun_br
),
picked AS (
    SELECT 'most_l' AS kind, * FROM ranked WHERE rank_l = 1
    UNION ALL SELECT 'most_b', * FROM ranked WHERE rank_b = 1
    UNION ALL SELECT 'most_l_100k', * FROM ranked WHERE aptos >= 100000 AND rank_l_big = 1
    UNION ALL SELECT 'most_b_100k', * FROM ranked WHERE aptos >= 100000 AND rank_b_big = 1
)
SELECT year, round, kind, cd_ibge, name, uf, aptos, validos, camp_l, camp_b, others, blank_null, absent,
       share_l2, pct_l_valid, pct_b_valid
FROM picked
ORDER BY year, round, kind;
