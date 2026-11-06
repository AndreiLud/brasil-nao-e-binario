-- Model: one row per election, round and municipality (plus one row per city abroad),
-- with the two camps, third candidates, blank/null votes and non-attendance.
-- Base table for every question (Q1 to Q7). Requires stg_votes, stg_detail
-- (00_staging.sql) and the reference table `municipalities` (src/crosswalk.py).

-- Camp of each candidate, by ballot number. Mirrors src/config.py CAMPS.
-- 2014 is a baseline only: Dilma (PT) sits on the L side and Aecio (PSDB) on the B side,
-- and both are always labelled by name, never as "lulista" or "bolsonarista".
CREATE OR REPLACE TABLE camps AS
SELECT * FROM (VALUES
    (2014, 13, 'L'), (2014, 45, 'B'),
    (2018, 13, 'L'), (2018, 17, 'B'),
    (2022, 13, 'L'), (2022, 22, 'B'),
    (2026, 13, 'L'), (2026, 22, 'B')
) AS t(year, nr_candidato, camp);

CREATE OR REPLACE TABLE mun_votes AS
WITH cand AS (   -- votes per candidate and municipality (zones summed)
    SELECT v.year, v.round, v.cd_tse, v.nr_candidato, c.camp, sum(v.votes) AS votes
    FROM stg_votes v
    LEFT JOIN camps c USING (year, nr_candidato)
    GROUP BY ALL
)
SELECT
    year, round, cd_tse,
    coalesce(sum(votes) FILTER (WHERE camp = 'L'), 0)      AS camp_l,
    coalesce(sum(votes) FILTER (WHERE camp = 'B'), 0)      AS camp_b,
    coalesce(sum(votes) FILTER (WHERE camp IS NULL), 0)    AS others,
    -- best-placed third candidate (first rounds): votes and ballot number
    coalesce(max(votes) FILTER (WHERE camp IS NULL), 0)    AS top_other,
    arg_max(nr_candidato, votes) FILTER (WHERE camp IS NULL) AS top_other_nr,
    sum(votes)                                             AS nominal_votes
FROM cand
GROUP BY ALL;

-- Zones and the 2014 transit sections are summed into their municipality.
CREATE OR REPLACE TABLE mun_turnout AS
SELECT
    year, round, cd_tse,
    any_value(uf)                     AS uf,
    any_value(nm_municipio_tse)       AS nm_municipio_tse,
    count(*)                          AS n_zone_rows,
    sum(aptos)                        AS aptos,
    sum(comparecimento)               AS comparecimento,
    sum(abstencoes)                   AS abstencoes,
    sum(aptos_secoes_nao_instaladas)  AS aptos_secoes_nao_instaladas,
    sum(validos)                      AS validos,
    sum(brancos)                      AS brancos,
    sum(nulos)                        AS nulos,
    sum(anulados_apurados_separado)   AS anulados_apurados_separado
FROM stg_detail
GROUP BY year, round, cd_tse;

-- Final municipal table. Categories add up to the electorate (aptos):
--   camp_l + camp_b + others + blank_null + absent = aptos
-- blank_null = blank + null + votes annulled and counted separately (746 in 2018, round 1)
-- absent     = aptos - comparecimento (abstention plus voters of sections that were
--              not installed or not counted)
CREATE OR REPLACE TABLE mun_results AS
SELECT
    t.year, t.round, t.cd_tse, t.uf,
    t.uf = 'ZZ'                                         AS abroad,
    m.cd_ibge, coalesce(m.name, t.nm_municipio_tse)     AS name,
    m.region_id, m.region, m.capital, m.population, m.income_pc_median,
    t.aptos, t.comparecimento, t.abstencoes, t.validos, t.brancos, t.nulos,
    t.anulados_apurados_separado,
    coalesce(v.camp_l, 0) AS camp_l, coalesce(v.camp_b, 0) AS camp_b, coalesce(v.others, 0) AS others,
    coalesce(v.top_other, 0) AS top_other, v.top_other_nr,
    t.brancos + t.nulos + t.anulados_apurados_separado AS blank_null,
    t.aptos - t.comparecimento                          AS absent,
    v.camp_l / nullif(v.camp_l + v.camp_b, 0)           AS share_l2,      -- L share of the two camps
    v.camp_l / nullif(t.validos, 0)                     AS pct_l_valid,
    v.camp_b / nullif(t.validos, 0)                     AS pct_b_valid,
    v.others / nullif(t.validos, 0)                     AS pct_others_valid,
    v.camp_l / t.aptos                                  AS pct_l_aptos,
    v.camp_b / t.aptos                                  AS pct_b_aptos,
    v.others / t.aptos                                  AS pct_others_aptos,
    (t.brancos + t.nulos + t.anulados_apurados_separado) / t.aptos AS pct_blank_null_aptos,
    (t.aptos - t.comparecimento) / t.aptos              AS pct_absent_aptos,
    -- leader: who came first in the municipality (a third candidate can lead in a first round)
    CASE WHEN v.camp_l > greatest(v.camp_b, v.top_other) THEN 'L'
         WHEN v.camp_b > greatest(v.camp_l, v.top_other) THEN 'B'
         WHEN v.top_other > greatest(v.camp_l, v.camp_b) THEN 'O'
         ELSE 'tie' END                                 AS leader,
    -- leader2: which of the two camps was ahead of the other (used for changes between elections)
    CASE WHEN v.camp_l > v.camp_b THEN 'L' WHEN v.camp_b > v.camp_l THEN 'B' ELSE 'tie' END AS leader2
FROM mun_turnout t
-- LEFT JOIN: a few polling places abroad have turnout rows but no vote rows (no one
-- voted, or sections not installed); they keep their electorate in the totals.
LEFT JOIN mun_votes v USING (year, round, cd_tse)
LEFT JOIN municipalities m USING (cd_tse);

-- Domestic municipalities only (what the maps show).
CREATE OR REPLACE VIEW mun_br AS SELECT * FROM mun_results WHERE NOT abroad;
