-- Q5. Where did the lulista camp regain ground in 2022 (municipal change from 2018 to 2022)?
-- Main measure: change in the lulista share of the runoff valid vote, Haddad 2018 to
-- Lula 2022 (points). Both runoffs had only the two camps, so the valid vote is the
-- two-camp vote.

CREATE OR REPLACE TABLE q5_municipal AS
SELECT a.cd_ibge, a.name, a.uf, a.region, a.region_id, b.population, b.aptos AS aptos_2022,
       a.share_l2                          AS l_share_2018_r2,
       b.share_l2                          AS l_share_2022_r2,
       b.share_l2 - a.share_l2             AS delta_l_r2,
       a.camp_l AS l_votes_2018_r2, b.camp_l AS l_votes_2022_r2, b.camp_l - a.camp_l AS delta_l_votes_r2,
       a.camp_b AS b_votes_2018_r2, b.camp_b AS b_votes_2022_r2, b.camp_b - a.camp_b AS delta_b_votes_r2,
       a.leader2 AS leader_2018_r2, b.leader2 AS leader_2022_r2
FROM mun_br a
JOIN mun_br b ON b.cd_ibge = a.cd_ibge AND b.year = 2022 AND b.round = 2
WHERE a.year = 2018 AND a.round = 2;

CREATE OR REPLACE TABLE q5_summary AS
SELECT count(*)                                         AS municipalities,
       count(*) FILTER (WHERE delta_l_r2 > 0)           AS n_l_grew,
       count(*) FILTER (WHERE delta_l_r2 < 0)           AS n_l_fell,
       count(*) FILTER (WHERE delta_l_r2 >= 0.10)       AS n_l_grew_10pts,
       median(delta_l_r2)                               AS median_delta_l_r2,
       count(*) FILTER (WHERE leader_2018_r2 = 'B' AND leader_2022_r2 = 'L') AS n_flipped_to_l,
       count(*) FILTER (WHERE leader_2018_r2 = 'L' AND leader_2022_r2 = 'B') AS n_flipped_to_b,
       sum(delta_l_votes_r2)                            AS delta_l_votes_r2,
       sum(delta_b_votes_r2)                            AS delta_b_votes_r2
FROM q5_municipal;

CREATE OR REPLACE TABLE q5_region AS
SELECT region_id, region,
       count(*)                                          AS municipalities,
       sum(l_votes_2018_r2) AS l_votes_2018_r2, sum(l_votes_2022_r2) AS l_votes_2022_r2,
       sum(delta_l_votes_r2) AS delta_l_votes_r2, sum(delta_b_votes_r2) AS delta_b_votes_r2,
       sum(l_votes_2022_r2) / (sum(l_votes_2022_r2) + sum(b_votes_2022_r2))
         - sum(l_votes_2018_r2) / (sum(l_votes_2018_r2) + sum(b_votes_2018_r2)) AS delta_l_share_region,
       median(delta_l_r2)                                AS median_delta_l_r2,
       count(*) FILTER (WHERE delta_l_r2 > 0) / count(*) AS share_mun_l_grew,
       count(*) FILTER (WHERE leader_2018_r2 = 'B' AND leader_2022_r2 = 'L') AS n_flipped_to_l
FROM q5_municipal
GROUP BY ALL ORDER BY region_id;

-- Largest increases among municipalities with at least 50,000 voters in 2022.
CREATE OR REPLACE TABLE q5_top AS
SELECT * FROM q5_municipal WHERE aptos_2022 >= 50000 ORDER BY delta_l_r2 DESC LIMIT 15;
