-- Q2. How did each municipality vote in each election and round?
-- One row per election, round and municipality (abroad excluded: it has no polygon).
-- Also counts how many municipalities each side led, and how many voters live in them,
-- which is what the "winner by city" map shows. In first rounds a third candidate can come
-- first in a municipality ('O'); those are counted apart, never assigned to a camp.

CREATE OR REPLACE TABLE q2_municipal AS
SELECT year, round, cd_ibge, cd_tse, name, uf, region, population,
       aptos, comparecimento, validos, camp_l, camp_b, others, blank_null, absent,
       top_other, top_other_nr,
       share_l2, pct_l_valid, pct_b_valid, pct_others_valid,
       pct_l_aptos, pct_b_aptos, pct_others_aptos, pct_blank_null_aptos, pct_absent_aptos, leader, leader2
FROM mun_br
ORDER BY year, round, cd_ibge;

CREATE OR REPLACE TABLE q2_winners AS
SELECT year, round,
       count(*)                                           AS municipalities,
       count(*) FILTER (WHERE leader = 'L')               AS led_by_l,
       count(*) FILTER (WHERE leader = 'B')               AS led_by_b,
       count(*) FILTER (WHERE leader = 'O')               AS led_by_other,
       count(*) FILTER (WHERE leader = 'tie')             AS ties,
       sum(aptos) FILTER (WHERE leader = 'L') / sum(aptos) AS aptos_share_in_l_led,
       sum(aptos) FILTER (WHERE leader = 'B') / sum(aptos) AS aptos_share_in_b_led,
       sum(aptos) FILTER (WHERE leader = 'O') / sum(aptos) AS aptos_share_in_other_led,
       -- votes of each side cast where the other side led locally
       sum(camp_l) FILTER (WHERE leader = 'B')            AS l_votes_where_b_led,
       sum(camp_b) FILTER (WHERE leader = 'L')            AS b_votes_where_l_led,
       sum(camp_l) FILTER (WHERE leader = 'B') / sum(camp_l) AS l_share_of_votes_where_b_led,
       sum(camp_b) FILTER (WHERE leader = 'L') / sum(camp_b) AS b_share_of_votes_where_l_led,
       count(*) FILTER (WHERE camp_l = 0)                 AS mun_with_zero_l,
       count(*) FILTER (WHERE camp_b = 0)                 AS mun_with_zero_b
FROM mun_br
GROUP BY year, round
ORDER BY year, round;
