-- Staging: load the raw TSE presidential files (2014, 2018, 2022, 2026) into typed tables.
-- Answers no question directly; every question reads from these tables.
-- Raw files are Latin-1, ';'-separated, with quoted fields. Everything is read as
-- text first so municipality codes keep their leading zeros, then cast explicitly.

CREATE OR REPLACE TABLE raw_votes AS
SELECT *
FROM read_csv('data/raw/tse/votacao_candidato_munzona_*_BR.csv',
              delim = ';', quote = '"', header = true, encoding = 'latin-1',
              all_varchar = true, union_by_name = true, filename = true);

CREATE OR REPLACE TABLE raw_detail AS
SELECT *
FROM read_csv('data/raw/tse/detalhe_votacao_munzona_*_BR.csv',
              delim = ';', quote = '"', header = true, encoding = 'latin-1',
              all_varchar = true, union_by_name = true, filename = true);

-- One row per year, round, municipality, zone, transit flag and candidate.
CREATE OR REPLACE TABLE stg_votes AS
SELECT
    CAST(ANO_ELEICAO AS INTEGER)            AS year,
    CAST(NR_TURNO AS INTEGER)               AS round,
    CAST(CD_ELEICAO AS INTEGER)             AS cd_eleicao,
    CAST(CD_CARGO AS INTEGER)               AS cd_cargo,
    SG_UF                                   AS uf,
    lpad(CD_MUNICIPIO, 5, '0')              AS cd_tse,
    NM_MUNICIPIO                            AS nm_municipio_tse,
    CAST(NR_ZONA AS INTEGER)                AS zona,
    ST_VOTO_EM_TRANSITO                     AS transit,
    CAST(NR_CANDIDATO AS INTEGER)           AS nr_candidato,
    NM_URNA_CANDIDATO                       AS nm_urna,
    SG_PARTIDO                              AS partido,
    CAST(QT_VOTOS_NOMINAIS AS BIGINT)       AS votes,
    -- Only published from 2018 on; NULL in 2014.
    CAST(QT_VOTOS_NOMINAIS_VALIDOS AS BIGINT) AS votes_valid_col,
    NM_TIPO_DESTINACAO_VOTOS                AS destination
FROM raw_votes;

-- One row per year, round, municipality, zone and transit flag.
CREATE OR REPLACE TABLE stg_detail AS
SELECT
    CAST(ANO_ELEICAO AS INTEGER)                      AS year,
    CAST(NR_TURNO AS INTEGER)                         AS round,
    CAST(CD_ELEICAO AS INTEGER)                       AS cd_eleicao,
    CAST(CD_CARGO AS INTEGER)                         AS cd_cargo,
    SG_UF                                             AS uf,
    lpad(CD_MUNICIPIO, 5, '0')                        AS cd_tse,
    NM_MUNICIPIO                                      AS nm_municipio_tse,
    CAST(NR_ZONA AS INTEGER)                          AS zona,
    ST_VOTO_EM_TRANSITO                               AS transit,
    CAST(QT_APTOS AS BIGINT)                          AS aptos,
    CAST(QT_COMPARECIMENTO AS BIGINT)                 AS comparecimento,
    CAST(QT_ABSTENCOES AS BIGINT)                     AS abstencoes,
    CAST(QT_ELEITORES_SECOES_NAO_INSTALADAS AS BIGINT) AS aptos_secoes_nao_instaladas,
    CAST(QT_VOTOS AS BIGINT)                          AS votos_total,
    CAST(QT_TOTAL_VOTOS_VALIDOS AS BIGINT)            AS validos,
    CAST(QT_VOTOS_NOMINAIS_VALIDOS AS BIGINT)         AS nominais_validos,
    CAST(QT_VOTOS_BRANCOS AS BIGINT)                  AS brancos,
    CAST(QT_TOTAL_VOTOS_NULOS AS BIGINT)              AS nulos,           -- includes technical nulls
    CAST(QT_VOTOS_NULOS AS BIGINT)                    AS nulos_urna,
    CAST(QT_VOTOS_NULOS_TECNICOS AS BIGINT)           AS nulos_tecnicos,
    CAST(QT_TOTAL_VOTOS_ANULADOS AS BIGINT)           AS anulados,
    CAST(QT_TOTAL_VOTOS_ANUL_SUBJUD AS BIGINT)        AS anulados_subjudice,
    CAST(QT_VOTOS_ANULADOS_APU_SEP AS BIGINT)         AS anulados_apurados_separado
FROM raw_detail;
