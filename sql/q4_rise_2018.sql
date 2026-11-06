-- Q4. Where and how much did the bolsonarista camp grow in 2018, compared with the
-- non-PT side of 2014 (Aecio, PSDB, the runoff opponent of the PT)?
-- 2014 is a baseline, not a "bolsonarista" election: the comparison measures how much
-- the side opposed to the PT grew from one runoff to the next, municipality by municipality.
-- Main measure: share of the non-PT side in the runoff valid vote (points).

CREATE OR REPLACE TABLE q4_municipal AS
SELECT a.cd_ibge, a.name, a.uf, a.region, a.region_id, b.population, b.aptos AS aptos_2018,
       1 - a.share_l2                     AS b_share_2014_r2,
       1 - b.share_l2                     AS b_share_2018_r2,
       (a.share_l2 - b.share_l2)          AS delta_b_r2,          -- growth of the non-PT side, runoff
       a.camp_b                           AS b_votes_2014_r2,
       a.camp_l                           AS l_votes_2014_r2,
       b.camp_l                           AS l_votes_2018_r2,
       b.camp_b                           AS b_votes_2018_r2,
       b.camp_b - a.camp_b                AS delta_b_votes_r2,
       a1.pct_b_valid                     AS b_valid_2014_r1,
       b1.pct_b_valid                     AS b_valid_2018_r1,
       b1.pct_b_valid - a1.pct_b_valid    AS delta_b_valid_r1,
       a.leader2 AS leader_2014_r2, b.leader2 AS leader_2018_r2
FROM mun_br a
JOIN mun_br b  ON b.cd_ibge = a.cd_ibge AND b.year = 2018 AND b.round = 2
JOIN mun_br a1 ON a1.cd_ibge = a.cd_ibge AND a1.year = 2014 AND a1.round = 1
JOIN mun_br b1 ON b1.cd_ibge = a.cd_ibge AND b1.year = 2018 AND b1.round = 1
WHERE a.year = 2014 AND a.round = 2;

CREATE OR REPLACE TABLE q4_summary AS
SELECT count(*)                                         AS municipalities,
       count(*) FILTER (WHERE delta_b_r2 > 0)           AS n_b_grew,
       count(*) FILTER (WHERE delta_b_r2 < 0)           AS n_b_fell,
       count(*) FILTER (WHERE delta_b_r2 >= 0.20)       AS n_b_grew_20pts,
       median(delta_b_r2)                               AS median_delta_b_r2,
       count(*) FILTER (WHERE leader_2014_r2 = 'L' AND leader_2018_r2 = 'B') AS n_flipped_to_b,
       count(*) FILTER (WHERE leader_2014_r2 = 'B' AND leader_2018_r2 = 'L') AS n_flipped_to_l,
       sum(delta_b_votes_r2)                            AS delta_b_votes_r2
FROM q4_municipal;

CREATE OR REPLACE TABLE q4_region AS
SELECT region_id, region,
       count(*)                                          AS municipalities,
       sum(b_votes_2014_r2)                              AS b_votes_2014_r2,
       sum(b_votes_2018_r2)                              AS b_votes_2018_r2,
       sum(b_votes_2018_r2) - sum(b_votes_2014_r2)       AS delta_b_votes_r2,
       median(delta_b_r2)                                AS median_delta_b_r2,
       count(*) FILTER (WHERE delta_b_r2 > 0) / count(*) AS share_mun_b_grew,
       sum(b_votes_2018_r2) / (sum(b_votes_2018_r2) + sum(l_votes_2018_r2))
         - sum(b_votes_2014_r2) / (sum(b_votes_2014_r2) + sum(l_votes_2014_r2)) AS delta_b_share_region
FROM q4_municipal
GROUP BY ALL ORDER BY region_id;

-- Regional runoff shares of the non-PT side (weighted by votes, from the model).
CREATE OR REPLACE TABLE q4_region_share AS
SELECT year, region_id, any_value(region) AS region, sum(camp_b) / sum(camp_l + camp_b) AS b_share_r2
FROM mun_br WHERE round = 2 AND year IN (2014, 2018)
GROUP BY ALL ORDER BY region_id, year;

-- Largest increases among municipalities with at least 50,000 voters in 2018.
CREATE OR REPLACE TABLE q4_top AS
SELECT * FROM q4_municipal WHERE aptos_2018 >= 50000 ORDER BY delta_b_r2 DESC LIMIT 15;
