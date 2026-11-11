# O Brasil não é binário

![Mapa de pontos do 2º turno de 2026: um ponto para cada 1.000 votos, violeta para Lula e ocre para Flávio Bolsonaro, misturados pelo país](docs/img/hero.png)

Uma reportagem de dados sobre as eleições presidenciais de 2018, 2022 e 2026, com 2014 como ponto de partida. Os dados são oficiais, do TSE e do IBGE, município por município. O mapa de quem venceu em cada cidade desenha um país partido em dois blocos. Os votos contam outra história: em todo lugar há eleitores dos dois campos, além de quem votou em outro candidato, anulou, votou em branco ou ficou em casa.

* **Site em português:** {{cfg_site_url}}
* **Site em inglês:** {{cfg_site_url}}en/
* **English version of this README:** [README.md](README.md)

O site é bilíngue. As duas versões usam os mesmos dados, gráficos e visual, e um seletor PT/EN no topo de cada página leva de uma à outra.

## Principais achados

Todos os números saem de `docs/data/facts.json`, calculado pelo pipeline. Este README é gerado a partir de um modelo, então nenhum número foi digitado à mão. Os achados são do 2º turno de 2026, salvo indicação.

* **{{e2026r2_local_minority_votes}} de pessoas votaram no candidato que perdeu na própria cidade**, {{e2026r2_local_minority_vote_share}} de todos os votos válidos.
* **O mapa de vencedores esconde um empate.** Lula venceu em {{e2026r2_led_by_l}} municípios e Flávio Bolsonaro em {{e2026r2_led_by_b}}. Dos votos de Lula no Brasil, {{e2026r2_l_share_of_votes_where_b_led}} vieram de municípios onde Flávio venceu; dos de Flávio, {{e2026r2_b_share_of_votes_where_l_led}} vieram de municípios onde Lula venceu.
* **Quem perde numa cidade não some dela.** O lado derrotado teve mais de 30% dos votos em {{e2026r2_n_minority_over_30}} municípios e mais de 10% em {{e2026r2_n_minority_over_10}} dos {{n_mun_2026}}. No município mais lulista, {{e2026r2_most_l_name}}, Flávio teve {{e2026r2_most_l_share_b}}. No mais bolsonarista, {{e2026r2_most_b_name}}, Lula teve {{e2026r2_most_b_share_l}}.
* **Cada lado tem milhões de votos onde perde.** Flávio teve {{e2026r2_reg_ne_camp_b}} de votos no Nordeste, mais do que em {{e2026r2_b_ne_states_n}} unidades da federação de outras regiões somadas. Lula teve {{e2026r2_reg_s_camp_l}} no Sul, mais do que em {{e2026r2_l_s_states_n}} unidades de outras regiões somadas. No Norte, os dois ficaram a {{e2026r2_reg_n_diff_int}} votos de distância.
* **Contra a tese, com o mesmo destaque.** Região e renda se associam fortemente ao voto dos municípios. Lula venceu em {{e2026r2_reg_ne_led_by_l}} dos {{e2026r2_reg_ne_municipalities}} municípios do Nordeste; Flávio, em {{e2026r2_reg_s_led_by_b}} dos {{e2026r2_reg_s_municipalities}} do Sul. A mediana lulista foi {{q7_income1_p50_l}} na faixa de menor renda e {{q7_income5_p50_l}} na de maior renda.
* **2018.** A fatia do candidato que enfrentou o PT no 2º turno (Aécio em 2014, Bolsonaro em 2018) cresceu em {{q4_n_b_grew}} dos {{n_mun_2022}} municípios: {{q4_reg_se_delta_b_share}} no Sudeste, {{q4_reg_s_delta_b_share}} no Sul e {{q4_reg_ne_delta_b_share}} no Nordeste.
* **2022.** Lula teve {{q5_delta_l_votes}} de votos a mais que Haddad no 2º turno. O Sudeste respondeu por {{q5_se_share_of_l_gain}} desse ganho dentro do Brasil.
* **A virada de 2026.** Flávio terminou o 1º turno {{q6_b_lead_r1}} de votos à frente; Lula venceu o 2º por {{q6_l_lead_r2}}. Entre os turnos, Lula somou {{q6_delta_l_votes}} de votos e Flávio, {{q6_delta_b_votes}}. Lula cresceu mais que Flávio em {{q6_n_l_gained_more}} municípios, e Flávio mais que Lula em {{q6_n_b_gained_more}}.

## Perguntas

1. Como o resultado nacional evoluiu de 2018 a 2026, nos dois turnos, incluindo abstenção, brancos e nulos?
2. Como cada município votou em cada eleição e turno?
3. Quão misturado é o voto?
4. Onde e quanto o bolsonarismo cresceu em 2018, em relação ao lado não petista de 2014?
5. Onde o campo lulista recuperou terreno em 2022?
6. Como aconteceu a virada do 2º turno de 2026, e como ela se associa aos votos em terceiros e à mudança de comparecimento?
7. Como o voto se associa a porte, região e renda dos municípios?

Cada pergunta tem um arquivo SQL em `sql/`, de `q1_national.sql` a `q7_context.sql`.

## Campos

* **Campo lulista:** Fernando Haddad (2018) e Lula (2022 e 2026).
* **Campo bolsonarista:** Jair Bolsonaro (2018 e 2022) e Flávio Bolsonaro (2026).
* **2014** (Dilma Rousseff contra Aécio Neves) é só ponto de partida e aparece sempre com o nome dos candidatos.

## Fontes

| Dado | Fonte |
|---|---|
| Votos por candidato, município e zona | [Dados Abertos do TSE](https://dadosabertos.tse.jus.br/), `votacao_candidato_munzona_<ano>.zip` (arquivo `_BR.csv`, presidente) |
| Comparecimento, abstenção, brancos e nulos | TSE, `detalhe_votacao_munzona_<ano>.zip` |
| Códigos TSE e IBGE | TSE, `municipio_tse_ibge.zip`, conferido com o diretório de municípios da Base dos Dados |
| Totais oficiais para conferência | Relatórios de totalização do TSE (2018, 2022 e 2026) e portal de resultados de 2026 |
| Mapa | IBGE, Malha Municipal 2025 |
| Região e UF | API de localidades do IBGE |
| População e renda | IBGE, Censo 2022 (tabelas 4709 e 10295 do Sidra) |

Os endereços exatos, tamanhos, hashes e horários de download ficam em `data/raw/manifest.json` depois de rodar o pipeline.

## Método, em resumo

* Os arquivos do TSE são lidos com DuckDB e somados de zona para município (`sql/00_staging.sql` e `sql/01_model.sql`).
* Em cada município e turno, cinco grupos somam exatamente o eleitorado: campo lulista, campo bolsonarista, outros candidatos, branco ou nulo e quem não votou.
* Os votos no exterior entram nos totais nacionais e ficam fora dos mapas.
* **Conferência:** cada total do Brasil, de cada estado e do exterior, em cada turno, foi comparado com os totais oficiais do TSE. Foram {{validation_cells}} números comparados e {{validation_unexplained}} diferenças sem explicação. Ver `project_docs/quality_log.md`.
* **Mapa:** a malha do IBGE foi projetada (Albers, que mantém as áreas), simplificada sem descolar as fronteiras entre vizinhos e exportada em TopoJSON. No mapa de pontos, cada ponto vale {{dot_votes}} votos e cai em um lugar sorteado dentro do município, com semente fixa.

Detalhes e justificativas: [project_docs/methodology.md](project_docs/methodology.md). Dicionário de dados: [project_docs/data_dictionary.md](project_docs/data_dictionary.md).

## Limites

* Dados por município descrevem lugares, não pessoas. Nenhum número aqui diz como um eleitor votou (falácia ecológica). As associações com renda, porte, terceiros e comparecimento não indicam causa.
* A abstenção inclui cadastros desatualizados, como pessoas que mudaram de cidade ou morreram.
* A comparação com 2014 mede o candidato que enfrentou o PT no 2º turno, não um mesmo movimento político.
* Para 2014 não havia fonte oficial independente acessível. A conferência foi feita contra a votação por seção, que vem da mesma base do TSE.
* Boa Esperança do Norte (MT) foi instalado em 2025, com partes de Sorriso e Nova Ubiratã, e teve sua primeira eleição presidencial em 2026. Os resultados de 2026 desses dois municípios cobrem uma área menor que nas eleições anteriores.

## Como reproduzir

Requisitos: Python 3.12 e cerca de 1 GB livre em disco. Um comando roda tudo e baixa só o que faltar:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py          # baixa, limpa, confere, analisa, exporta e gera os textos
.venv/bin/python -m src.vendor       # opcional: baixa de novo as bibliotecas e fontes fixadas
.venv/bin/python -m playwright install chromium
.venv/bin/python -m src.screenshots og   # opcional: gera de novo as imagens de compartilhamento (PT e EN)
.venv/bin/python -m src.smoke            # teste no navegador dos dois idiomas (erros de JS, controles, busca, link direto)
cd docs && python3 -m http.server 8000   # abra http://localhost:8000 (português) ou /en/ (inglês)
```

Também funciona com `make all`, `make serve` e `make screenshots`. As versões estão fixadas em `requirements.txt`. O DuckDB está fixado na versão 1.5.6 de propósito: os pacotes da 2.0 exigem instruções AVX que algumas máquinas virtuais não têm. Os dados brutos não entram no Git (`data/raw/` é ignorado); `src/download.py` baixa tudo de novo e registra os hashes.

## Site bilíngue

| Peça | Português | Inglês |
|---|---|---|
| Página | `docs/index.html` | `docs/en/index.html` |
| Modelo (todo o texto) | `src/templates/index.html` | `src/templates/index.en.html` |
| Números do texto | texto `pt` de cada chave em `docs/data/facts.json` | texto `en` da mesma chave |
| Rótulos, legendas e tooltips | bloco `pt` de `docs/js/i18n.js` | bloco `en` de `docs/js/i18n.js` |
| Imagem de compartilhamento | `docs/img/og.png` | `docs/img/og-en.png` |

* O JavaScript lê o idioma de `<html lang>` e formata os números de acordo (`46,6 milhões` ou `46.6 million`). A página em inglês declara `data-base="../"` para ler os mesmos arquivos de `docs/data/`.
* Para mudar o texto, edite os dois modelos e rode `.venv/bin/python -m src.render`. O gerador se recusa a escrever as páginas se elas perderem a paridade de estrutura (mesmos ids, passos da rolagem e figuras nos dois idiomas), se aparecer no texto um número que não seja um fato calculado ou se surgir travessão, meia-risca ou hífen como pausa.
* As duas páginas se apontam com links `hreflang`, e cada uma tem sua própria imagem e descrição para compartilhamento.

## Estrutura

```
run_all.py            um comando para o pipeline inteiro
wrangler.jsonc        configuração do Cloudflare Workers (publica docs/)
requirements.txt      dependências Python com versões fixadas
sql/                  um arquivo SQL por pergunta, além de staging, modelo e conferência
src/                  download, correspondência de códigos, checagens, conferência, mapa, exportação, fatos, textos
src/templates/        modelos das páginas (index.html em português, index.en.html em inglês), cartões de
                      compartilhamento, READMEs e metodologia (números vêm do facts.json)
notebooks/            análise exploratória com perguntas e conclusões (executada)
project_docs/         brief, dicionário de dados, registro de qualidade, metodologia
data/raw, interim     fora do Git
data/processed/       tabelas da análise (CSV) e resultados da conferência
docs/                 o site estático: português na raiz, inglês em docs/en/
docs/js/i18n.js       textos dos gráficos e da interface nos dois idiomas
```

## Publicar

O site é a pasta estática `docs/`, publicada como está. `SITE_URL` e `REPO_URL` em `src/config.py` guardam os endereços públicos (os links canônicos e as imagens de compartilhamento precisam de endereço absoluto); se mudar algum deles, rode `.venv/bin/python -m src.render`.

* **Cloudflare Workers:** o `wrangler.jsonc` envia `docs/` como arquivos estáticos (nenhum script roda) e declara os domínios próprios. A Cloudflare cria os registros de DNS e os certificados na publicação. No painel da Cloudflare: **Workers & Pages → Create → Import a repository**, escolha este repositório, mantenha o nome `brasil-nao-e-binario`, deixe o comando de build vazio e use `npx wrangler@4.158.0 deploy` como comando de deploy. Cada push na `main` publica de novo.
* **GitHub Pages:** **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main, pasta /docs → Save.**

## Créditos

Código: licença MIT (ver `LICENSE`). Dados: Tribunal Superior Eleitoral (TSE) e Instituto Brasileiro de Geografia e Estatística (IBGE). Bibliotecas: D3 (ISC), topojson-client (ISC) e Scrollama (MIT). Fontes: Fraunces e Inter (SIL Open Font License). As licenças estão em `docs/vendor` e `docs/fonts`.
