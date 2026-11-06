-- Q6. How did the 2026 runoff turnaround happen? In which municipalities did Lula gain the
-- most between the first round (2026-10-04) and the runoff (2026-10-25), and how is that
-- associated with the third-candidate vote in the first round and with the change in
-- turnout between rounds?
-- All measures are in points of each municipality's electorate (aptos), so the four
-- components (each camp, third candidates, blank/null, absent) add up to 100 in both rounds.
-- Associations are municipal-level (ecological): they do not say how any person voted.

CREATE OR REPLACE TABLE q6_municipal AS
SELECT r1.cd_ibge, r1.name, r1.uf, r1.region, r1.region_id, r1.population,
       r2.aptos                                   AS aptos,
       r1.camp_l AS l_r1, r2.camp_l AS l_r2, r2.camp_l - r1.camp_l AS delta_l_votes,
       r1.camp_b AS b_r1, r2.camp_b AS b_r2, r2.camp_b - r1.camp_b AS delta_b_votes,
       r1.others AS others_r1,
       r1.blank_null AS blank_null_r1, r2.blank_null AS blank_null_r2,
       r1.comparecimento AS turnout_r1, r2.comparecimento AS turnout_r2,
       r2.pct_l_aptos - r1.pct_l_aptos            AS gain_l_pts,
       r2.pct_b_aptos - r1.pct_b_aptos            AS gain_b_pts,
       r1.pct_others_aptos                        AS others_r1_pts,
       r2.comparecimento / r2.aptos - r1.comparecimento / r1.aptos AS turnout_change_pts,
       r2.pct_blank_null_aptos - r1.pct_blank_null_aptos           AS blank_null_change_pts,
       r1.share_l2 AS share_l2_r1, r2.share_l2 AS share_l2_r2,
       -- which camp was ahead of the other (in round 1 a third candidate never led in 2026,
       -- see q2_winners; leader2 ignores third candidates by construction)
       r1.leader2 AS leader_r1, r2.leader2 AS leader_r2
FROM mun_br r1
JOIN mun_br r2 ON r2.cd_ibge = r1.cd_ibge AND r2.year = 2026 AND r2.round = 2
WHERE r1.year = 2026 AND r1.round = 1;

-- National arithmetic of the turnaround (abroad included), in votes.
CREATE OR REPLACE TABLE q6_national AS
SELECT sum(r2.camp_l) - sum(r1.camp_l)            AS delta_l_votes,
       sum(r2.camp_b) - sum(r1.camp_b)            AS delta_b_votes,
       sum(r1.others)                             AS others_r1,
       sum(r2.comparecimento) - sum(r1.comparecimento) AS delta_turnout,
       sum(r2.blank_null) - sum(r1.blank_null)    AS delta_blank_null,
       sum(r1.camp_b) - sum(r1.camp_l)            AS b_lead_r1,
       sum(r2.camp_l) - sum(r2.camp_b)            AS l_lead_r2
FROM mun_results r1
JOIN mun_results r2 ON r2.cd_tse = r1.cd_tse AND r2.year = 2026 AND r2.round = 2
WHERE r1.year = 2026 AND r1.round = 1;

-- Weighted (by electorate) Pearson correlations across municipalities.
CREATE OR REPLACE MACRO wcorr(x, y, w) AS
    (sum(w * x * y) / sum(w) - (sum(w * x) / sum(w)) * (sum(w * y) / sum(w)))
    / sqrt((sum(w * x * x) / sum(w) - power(sum(w * x) / sum(w), 2))
         * (sum(w * y * y) / sum(w) - power(sum(w * y) / sum(w), 2)));

CREATE OR REPLACE TABLE q6_assoc AS
SELECT 'gain_l_pts' AS outcome, 'others_r1_pts' AS factor,
       wcorr(gain_l_pts, others_r1_pts, aptos) AS r_weighted, corr(gain_l_pts, others_r1_pts) AS r_unweighted
FROM q6_municipal
UNION ALL SELECT 'gain_l_pts', 'turnout_change_pts', wcorr(gain_l_pts, turnout_change_pts, aptos),
       corr(gain_l_pts, turnout_change_pts) FROM q6_municipal
UNION ALL SELECT 'gain_b_pts', 'others_r1_pts', wcorr(gain_b_pts, others_r1_pts, aptos),
       corr(gain_b_pts, others_r1_pts) FROM q6_municipal
UNION ALL SELECT 'gain_b_pts', 'turnout_change_pts', wcorr(gain_b_pts, turnout_change_pts, aptos),
       corr(gain_b_pts, turnout_change_pts) FROM q6_municipal
UNION ALL SELECT 'gain_l_pts', 'blank_null_change_pts', wcorr(gain_l_pts, blank_null_change_pts, aptos),
       corr(gain_l_pts, blank_null_change_pts) FROM q6_municipal;

-- Lula's gain by fifths of the third-candidate vote and of the turnout change.
CREATE OR REPLACE TABLE q6_bins AS
WITH b AS (
    SELECT *, ntile(5) OVER (ORDER BY others_r1_pts, cd_ibge) AS q_others,
              ntile(5) OVER (ORDER BY turnout_change_pts, cd_ibge) AS q_turnout
    FROM q6_municipal
)
SELECT 'others_r1_pts' AS factor, q_others AS quintile, count(*) AS municipalities,
       min(others_r1_pts) AS factor_min, max(others_r1_pts) AS factor_max,
       sum(delta_l_votes) / sum(aptos) AS gain_l_pts_weighted,
       sum(delta_b_votes) / sum(aptos) AS gain_b_pts_weighted,
       (sum(delta_l_votes) - sum(delta_b_votes)) / sum(aptos) AS net_gain_l_pts_weighted,
       median(gain_l_pts) AS gain_l_pts_median, median(gain_b_pts) AS gain_b_pts_median
FROM b GROUP BY q_others
UNION ALL
SELECT 'turnout_change_pts', q_turnout, count(*), min(turnout_change_pts), max(turnout_change_pts),
       sum(delta_l_votes) / sum(aptos), sum(delta_b_votes) / sum(aptos),
       (sum(delta_l_votes) - sum(delta_b_votes)) / sum(aptos),
       median(gain_l_pts), median(gain_b_pts)
FROM b GROUP BY q_turnout
ORDER BY factor, quintile;

CREATE OR REPLACE TABLE q6_region AS
SELECT region_id, region,
       sum(delta_l_votes) AS delta_l_votes, sum(delta_b_votes) AS delta_b_votes,
       sum(delta_l_votes) - sum(delta_b_votes) AS net_swing_to_l,
       sum(others_r1) AS others_r1,
       sum(turnout_r2) - sum(turnout_r1) AS delta_turnout,
       count(*) FILTER (WHERE gain_l_pts > gain_b_pts) AS n_mun_l_gained_more,
       count(*) AS municipalities,
       count(*) FILTER (WHERE leader_r1 = 'B' AND leader_r2 = 'L') AS n_flipped_to_l
FROM q6_municipal
GROUP BY ALL ORDER BY region_id;

CREATE OR REPLACE TABLE q6_summary AS
SELECT count(*)                                                AS municipalities,
       count(*) FILTER (WHERE gain_l_pts > gain_b_pts)         AS n_l_gained_more,
       count(*) FILTER (WHERE delta_l_votes > 0)               AS n_l_gained_votes,
       count(*) FILTER (WHERE delta_b_votes > 0)               AS n_b_gained_votes,
       count(*) FILTER (WHERE leader_r1 = 'B' AND leader_r2 = 'L') AS n_flipped_to_l,
       count(*) FILTER (WHERE leader_r1 = 'L' AND leader_r2 = 'B') AS n_flipped_to_b,
       count(*) FILTER (WHERE turnout_change_pts > 0)          AS n_turnout_up,
       count(*) FILTER (WHERE turnout_change_pts < 0)          AS n_turnout_down,
       count(*) FILTER (WHERE gain_b_pts > gain_l_pts)         AS n_b_gained_more,
       median(gain_l_pts) AS median_gain_l_pts, median(gain_b_pts) AS median_gain_b_pts
FROM q6_municipal;

-- Largest gains for Lula: in points of the electorate (municipalities with >= 50,000
-- voters) and in absolute votes.
CREATE OR REPLACE TABLE q6_top_pts AS
SELECT * FROM q6_municipal WHERE aptos >= 50000 ORDER BY gain_l_pts DESC LIMIT 15;
CREATE OR REPLACE TABLE q6_top_votes AS
SELECT * FROM q6_municipal ORDER BY delta_l_votes DESC LIMIT 15;
-- Same lists for Flavio, so both camps get the same treatment.
CREATE OR REPLACE TABLE q6_top_pts_b AS
SELECT * FROM q6_municipal WHERE aptos >= 50000 ORDER BY gain_b_pts DESC LIMIT 15;
CREATE OR REPLACE TABLE q6_top_votes_b AS
SELECT * FROM q6_municipal ORDER BY delta_b_votes DESC LIMIT 15;
-- In points of the electorate, round 1 -> runoff, by construction:
--   gain_l + gain_b = others_r1 + turnout_change - blank_null_change
-- so both gains are mechanically larger where third candidates or turnout gains were larger.
CREATE OR REPLACE TABLE q6_identity_check AS
SELECT max(abs((gain_l_pts + gain_b_pts) - (others_r1_pts + turnout_change_pts - blank_null_change_pts))) AS max_abs_error
FROM q6_municipal;
