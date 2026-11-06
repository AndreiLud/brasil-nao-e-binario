-- Validation: national, UF and abroad totals of our aggregation, in the same long
-- format as the official totals (src/official_totals.py), so they can be compared
-- cell by cell. Used by src/validate.py; supports every question, since all of
-- them start from these totals.

CREATE OR REPLACE TABLE our_totals AS
WITH by_uf AS (
    SELECT year, round, uf AS scope,
           sum(aptos) AS aptos, sum(comparecimento) AS comparecimento, sum(abstencoes) AS abstencoes,
           sum(validos) AS validos, sum(brancos) AS brancos, sum(nulos) AS nulos,
           sum(anulados_apurados_separado) AS anulados_apurados_separado
    FROM mun_turnout
    GROUP BY ALL
),
with_br AS (
    SELECT * FROM by_uf
    UNION ALL
    SELECT year, round, 'BR', sum(aptos), sum(comparecimento), sum(abstencoes), sum(validos), sum(brancos),
           sum(nulos), sum(anulados_apurados_separado)
    FROM by_uf GROUP BY ALL
),
turnout_long AS (
    UNPIVOT with_br ON aptos, comparecimento, abstencoes, validos, brancos, nulos, anulados_apurados_separado
    INTO NAME item VALUE value
),
cand AS (
    SELECT year, round, uf AS scope, 'cand_' || nr_candidato AS item, sum(votes) AS value
    FROM stg_votes GROUP BY ALL
    UNION ALL
    SELECT year, round, 'BR', 'cand_' || nr_candidato, sum(votes)
    FROM stg_votes GROUP BY ALL
)
SELECT year, round, scope, item, CAST(value AS BIGINT) AS value FROM turnout_long
UNION ALL
SELECT year, round, scope, item, CAST(value AS BIGINT) FROM cand;

-- Internal consistency: candidate votes must add up to the valid votes of the
-- turnout table in every municipality-zone (and transit flag).
CREATE OR REPLACE TABLE consistency_zone AS
SELECT d.year, d.round, d.cd_tse, d.zona, d.transit, d.validos,
       coalesce(v.votes, 0) AS candidate_votes, d.validos - coalesce(v.votes, 0) AS diff
FROM stg_detail d
LEFT JOIN (SELECT year, round, cd_tse, zona, transit, sum(votes) AS votes
           FROM stg_votes GROUP BY ALL) v USING (year, round, cd_tse, zona, transit);
