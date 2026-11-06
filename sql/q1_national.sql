-- Q1. How did the national result evolve from 2014 (baseline) and 2018 to 2026, in both
-- rounds, including abstention, blank and null votes?
-- National totals include votes cast abroad. Percentages are over the electorate
-- (aptos) and over valid votes.

CREATE OR REPLACE TABLE q1_national AS
SELECT
    year, round,
    sum(aptos)            AS aptos,
    sum(comparecimento)   AS comparecimento,
    sum(absent)           AS absent,
    sum(validos)          AS validos,
    sum(brancos)          AS brancos,
    sum(nulos)            AS nulos,
    sum(blank_null)       AS blank_null,
    sum(camp_l)           AS camp_l,
    sum(camp_b)           AS camp_b,
    sum(others)           AS others,
    sum(camp_l) / sum(aptos)       AS pct_l_aptos,
    sum(camp_b) / sum(aptos)       AS pct_b_aptos,
    sum(others) / sum(aptos)       AS pct_others_aptos,
    sum(blank_null) / sum(aptos)   AS pct_blank_null_aptos,
    sum(absent) / sum(aptos)       AS pct_absent_aptos,
    sum(camp_l) / sum(validos)     AS pct_l_valid,
    sum(camp_b) / sum(validos)     AS pct_b_valid,
    sum(others) / sum(validos)     AS pct_others_valid,
    -- people who did not choose either camp: absent + blank/null + third candidates
    (sum(absent) + sum(blank_null) + sum(others)) / sum(aptos) AS pct_neither_aptos,
    sum(camp_l) FILTER (WHERE abroad) AS camp_l_abroad,
    sum(camp_b) FILTER (WHERE abroad) AS camp_b_abroad,
    sum(aptos) FILTER (WHERE abroad)  AS aptos_abroad
FROM mun_results
GROUP BY year, round
ORDER BY year, round;

-- Every candidate, nationally (first rounds list the third candidates).
CREATE OR REPLACE TABLE q1_candidates AS
SELECT v.year, v.round, v.nr_candidato, any_value(v.nm_urna) AS nm_urna, any_value(v.partido) AS partido,
       c.camp, sum(v.votes) AS votes,
       sum(v.votes) / any_value(n.validos) AS pct_valid
FROM stg_votes v
LEFT JOIN camps c USING (year, nr_candidato)
JOIN q1_national n USING (year, round)
GROUP BY v.year, v.round, v.nr_candidato, c.camp
ORDER BY v.year, v.round, votes DESC;
