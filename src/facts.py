"""Every number quoted in the site and the READMEs, computed from the processed tables.

Output: docs/data/facts.json  {key: {value, kind, pt, en, desc}}
Templates reference facts as {{key}}; src/render.py replaces them with the pt or en text,
so no number is typed by hand anywhere.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src import geo


def _sep(s: str, lang: str) -> str:
    # s is formatted with ',' thousands and '.' decimals; negatives use the true minus sign
    s = s.replace("-", "\u2212")
    return s if lang == "en" else s.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt(value, kind: str, lang: str) -> str:
    if kind == "mi" and abs(value) < 1e6:  # small values: thousands or units, never "0,0 milhão"
        kind = "mil" if abs(value) >= 1e4 else "int"
    if kind == "text":
        return str(value)
    if kind == "phrase":
        return value[lang]
    if kind == "list":
        items = list(value)
        conj = " e " if lang == "pt" else " and "
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + conj + items[-1]
    if kind == "int":
        return _sep(f"{int(value):,}", lang)
    if kind == "mi":  # millions, 1 decimal ("1,8 milhão", "2,2 milhões")
        txt = _sep(f"{value / 1e6:,.1f}", lang)
        unit = ("milhão" if abs(round(value / 1e6, 1)) < 2 else "milhões") if lang == "pt" else "million"
        return f"{txt} {unit}"
    if kind == "mil":  # thousands, no decimals: "812 mil" / "812,000"
        return _sep(f"{value / 1e3:,.0f}", lang) + (" mil" if lang == "pt" else ",000")
    if kind == "pct":
        return _sep(f"{value * 100:,.1f}", lang) + "%"
    if kind == "pct0":
        return _sep(f"{value * 100:,.0f}", lang) + "%"
    if kind == "pts":
        v = round(value * 100, 1) + 0.0  # + 0.0 turns -0.0 into 0.0
        unit = (" ponto" if abs(v) < 2 else " pontos") if lang == "pt" else (" point" if abs(v) == 1 else " points")
        return _sep(f"{v:,.1f}", lang) + unit
    if kind == "pts_num":  # number only, for "de 3,7 a 5,1 pontos"
        return _sep(f"{round(value * 100, 1) + 0.0:,.1f}", lang)
    if kind == "pts_signed":
        v = round(value * 100, 1) + 0.0
        unit = (" ponto" if abs(v) < 2 else " pontos") if lang == "pt" else (" point" if abs(v) == 1 else " points")
        return ("+" if v >= 0 else "−") + _sep(f"{abs(v):,.1f}", lang) + unit
    if kind == "r":
        return _sep(f"{value:.2f}", lang)
    if kind == "brl":
        return ("R$\u00a0" if lang == "pt" else "R$") + _sep(f"{value:,.0f}", lang)
    if kind == "brl2":
        return ("R$\u00a0" if lang == "pt" else "R$") + _sep(f"{value:,.2f}", lang)
    if kind == "mi_num":  # the number part of "46,6 milhões"
        return _sep(f"{value / 1e6:,.1f}", lang)
    if kind == "mi_unit":
        return ("milhão" if abs(round(value / 1e6, 1)) < 2 else "milhões") if lang == "pt" else "million"
    raise ValueError(kind)


class Facts:
    def __init__(self):
        self.d = {}

    def add(self, key, value, kind, desc):
        if key in self.d:
            raise KeyError(f"duplicate fact {key}")
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, float):
            # parallel sums in DuckDB differ in the last bits between runs; round so the file is stable
            value = round(value, 10)
        self.d[key] = {"value": value, "kind": kind, "pt": fmt(value, kind, "pt"), "en": fmt(value, kind, "en"),
                       "desc": desc}


UF_NAME = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
           "DF": ("Distrito Federal", "Federal District"), "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
           "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba",
           "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
           "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe",
           "SP": "São Paulo", "TO": "Tocantins"}


def uf_name(uf, lang):
    n = UF_NAME[uf]
    return n if isinstance(n, str) else n[0 if lang == "pt" else 1]


REGION_EN = {"Norte": "North", "Nordeste": "Northeast", "Sudeste": "Southeast", "Sul": "South",
             "Centro-Oeste": "Center-West", "Exterior": "Abroad"}


def both_lists(items_pt, items_en):
    return {"pt": fmt(items_pt, "list", "pt"), "en": fmt(items_en, "list", "en")}


def round_phrase(year, rnd):
    return {"pt": f"{rnd}º turno de {year}", "en": f"{year} first round" if rnd == 1 else f"{year} runoff"}


def r_lab(year, camp):
    return C.CANDIDATE_LABELS[year][camp]


def one(con, sql):
    df = con.sql(sql).df()
    return df.iloc[0] if len(df) else None


def build(con):
    F = Facts()
    q = lambda s: con.sql(s).df()

    F.add("n_mun_2026", int(one(con, "SELECT count(*) n FROM mun_br WHERE year=2026 AND round=2").n), "int",
          "Municipalities in 2026")
    F.add("n_mun_2022", int(one(con, "SELECT count(*) n FROM mun_br WHERE year=2022 AND round=2").n), "int",
          "Municipalities in 2014, 2018 and 2022")
    z = one(con, "SELECT sum(mun_with_zero_l) zl, sum(mun_with_zero_b) zb FROM q2_winners")
    F.add("mun_zero_votes_any_side", int(z.zl + z.zb), "int",
          "Municipality-elections (all 8 election rounds) where one of the two camps got zero votes")

    labels = {(2014, 1): "2014, 1º turno", (2014, 2): "2014, 2º turno"}
    nat = q("SELECT * FROM q1_national")
    win = q("SELECT * FROM q2_winners")
    mino = q("SELECT * FROM q3_minority")
    for r in nat.itertuples():
        p = f"e{r.year}r{r.round}_"
        lab = labels.get((r.year, r.round), f"{r.year} round {r.round}")
        for col, kind in (("aptos", "mi"), ("camp_l", "mi"), ("camp_b", "mi"), ("others", "mi"),
                          ("blank_null", "mi"), ("absent", "mi"), ("comparecimento", "mi")):
            F.add(p + col, int(getattr(r, col)), kind, f"{lab}: {col}")
        for col in ("pct_l_aptos", "pct_b_aptos", "pct_others_aptos", "pct_blank_null_aptos", "pct_absent_aptos",
                    "pct_l_valid", "pct_b_valid", "pct_others_valid", "pct_neither_aptos"):
            F.add(p + col, float(getattr(r, col)), "pct", f"{lab}: {col}")
        F.add(p + "camp_l_int", int(r.camp_l), "int", f"{lab}: votes of the L side (exact)")
        F.add(p + "camp_b_int", int(r.camp_b), "int", f"{lab}: votes of the B side (exact)")
        F.add(p + "margin_votes", abs(int(r.camp_l) - int(r.camp_b)), "mi", f"{lab}: vote margin between the two camps")
        w = win[(win.year == r.year) & (win["round"] == r.round)].iloc[0]
        for col in ("led_by_l", "led_by_b", "led_by_other", "ties"):
            F.add(p + col, int(w[col]), "int", f"{lab}: municipalities where {col} (who came first; "
                  "'other' = a third candidate came first)")
        for col in ("aptos_share_in_l_led", "aptos_share_in_b_led"):
            F.add(p + col, float(w[col]), "pct", f"{lab}: share of the domestic electorate living in municipalities "
                  f"led by {'L' if '_l_' in col else 'B'}")
        F.add(p + "l_share_of_votes_where_b_led", float(w.l_share_of_votes_where_b_led), "pct",
              f"{lab}: share of the L camp's votes cast in Brazil that came from municipalities led by B")
        F.add(p + "b_share_of_votes_where_l_led", float(w.b_share_of_votes_where_l_led), "pct",
              f"{lab}: share of the B camp's votes cast in Brazil that came from municipalities led by L")
        F.add(p + "l_votes_where_b_led", int(w.l_votes_where_b_led), "mi", f"{lab}: L votes in municipalities led by B")
        F.add(p + "b_votes_where_l_led", int(w.b_votes_where_l_led), "mi", f"{lab}: B votes in municipalities led by L")
        m = mino[(mino.year == r.year) & (mino["round"] == r.round)].iloc[0]
        for col in ("n_minority_over_30", "n_minority_over_40", "n_minority_over_20", "n_minority_over_10"):
            F.add(p + col, int(m[col]), "int", f"{lab}: municipalities where the local loser got more than X% of the two-camp vote")
        for col in ("share_minority_over_30", "share_minority_over_40", "share_minority_over_10",
                    "aptos_share_minority_over_30", "aptos_share_minority_over_40", "min_minority_share",
                    "local_minority_vote_share", "min_share_l2", "max_share_l2"):
            F.add(p + col, float(m[col]), "pct", f"{lab}: {col}")
        F.add(p + "local_minority_votes", int(m.local_minority_votes), "mi",
              f"{lab}: votes cast for the side that lost in that municipality")
        F.add(p + "local_minority_votes_num", int(m.local_minority_votes), "mi_num", "same, number part")
        F.add(p + "local_minority_votes_unit", int(m.local_minority_votes), "mi_unit", "same, unit word")

    # Third candidates who came first in a municipality (first rounds)
    ol = q("""SELECT m.year, c.nm_urna, count(*) n FROM q2_municipal m
             JOIN q1_candidates c ON c.year = m.year AND c.round = 1 AND c.nr_candidato = m.top_other_nr
             WHERE m.round = 1 AND m.leader = 'O' GROUP BY ALL ORDER BY m.year, n DESC""")
    for y in C.YEARS:
        g = ol[ol.year == y]
        names = [f"{n.title()}" for n in g.nm_urna]
        F.add(f"e{y}r1_other_leader_names", both_lists(names or ["nenhum"], names or ["none"]), "phrase",
              f"{y} round 1: third candidates who came first somewhere")

    # Across rounds
    best = max([(float(r.pct_l_aptos), r.year, r.round, "L") for r in nat.itertuples()]
               + [(float(r.pct_b_aptos), r.year, r.round, "B") for r in nat.itertuples()])
    F.add("max_pct_aptos_any", best[0], "pct", "largest share of the electorate any candidate got, any round 2014-2026")
    rp = round_phrase(best[1], best[2])
    F.add("max_pct_aptos_any_who", {"pt": f"{r_lab(best[1], best[3])}, {rp['pt']}", "en": f"{r_lab(best[1], best[3])}, {rp['en']}"},
          "phrase", "who and when")
    for camp, col in (("L", "pct_l_aptos"), ("B", "pct_b_aptos")):
        sub = nat[nat.year >= 2018]
        r = sub.loc[sub[col].idxmax()]
        F.add(f"max_pct_aptos_{camp.lower()}", float(r[col]), "pct", f"largest share of the electorate of camp {camp}, 2018-2026")
        rp = round_phrase(int(r.year), int(r["round"]))
        who = C.CANDIDATE_LABELS[int(r.year)][camp]
        F.add(f"max_pct_aptos_{camp.lower()}_who", {"pt": f"{who} no {rp['pt']}", "en": f"{who} in the {rp['en']}"},
              "phrase", "who and when")
    F.add("absent_min", float(nat.pct_absent_aptos.min()), "pct", "lowest share of the electorate that did not vote, any round")
    F.add("absent_max", float(nat.pct_absent_aptos.max()), "pct", "highest share of the electorate that did not vote, any round")
    F.add("e2026r2_two_camp_total", int(nat[(nat.year == 2026) & (nat["round"] == 2)].iloc[0].validos), "mi",
          "2026 runoff: valid votes (= votes of the two candidates)")

    # Regions and states, every runoff
    reg = q("SELECT * FROM q3_region WHERE round = 2")
    for r in reg.itertuples():
        k = {"Norte": "n", "Nordeste": "ne", "Sudeste": "se", "Sul": "s", "Centro-Oeste": "co", "Exterior": "zz"}[r.region]
        p = f"e{r.year}r2_reg_{k}_"
        F.add(p + "camp_l", int(r.camp_l), "mi", f"{r.year} runoff, {r.region}: L votes")
        F.add(p + "camp_b", int(r.camp_b), "mi", f"{r.year} runoff, {r.region}: B votes")
        F.add(p + "share_l2", float(r.share_l2), "pct", f"{r.year} runoff, {r.region}: L share")
        F.add(p + "share_b2", 1 - float(r.share_l2), "pct", f"{r.year} runoff, {r.region}: B share")
        F.add(p + "led_by_l", int(r.led_by_l), "int", f"{r.year} runoff, {r.region}: municipalities led by L")
        F.add(p + "led_by_b", int(r.led_by_b), "int", f"{r.year} runoff, {r.region}: municipalities led by B")
        F.add(p + "municipalities", int(r.municipalities), "int", f"{r.year} runoff, {r.region}: municipalities")
        F.add(p + "two_camp_total", int(r.camp_l + r.camp_b), "mi", f"{r.year} runoff, {r.region}: votes of the two candidates")
        F.add(p + "diff_int", abs(int(r.camp_l) - int(r.camp_b)), "int",
              f"{r.year} runoff, {r.region}: absolute vote difference (leader in key ..._leader)")
        F.add(p + "lead", abs(int(r.camp_l) - int(r.camp_b)), "mi", f"{r.year} runoff, {r.region}: lead of the leader, votes")
        F.add(p + "leader", {"L": r_lab(r.year, "L"), "B": r_lab(r.year, "B")}["L" if r.camp_l > r.camp_b else "B"], "text",
              f"{r.year} runoff, {r.region}: candidate ahead")
    r26 = reg[(reg.year == 2026) & (reg.region != "Exterior")]
    F.add("e2026r2_b_lead_where_b_led_regions", int((r26.camp_b - r26.camp_l)[r26.camp_b > r26.camp_l].sum()), "mi",
          "2026 runoff: Flavio's lead summed over the regions where he was ahead")
    led = [x for x in r26[r26.camp_b > r26.camp_l].sort_values("region_id").region]
    F.add("e2026r2_b_led_regions", both_lists(led, [REGION_EN[x] for x in led]), "phrase",
          "regions where Flavio was ahead")
    # "More votes in region R than in N states of other regions combined", same rule for both camps
    st = q("SELECT * FROM q3_state WHERE year = 2026 AND round = 2")
    reg26 = reg[reg.year == 2026].set_index("region")
    for camp, col, region, key in (("B", "camp_b", "Nordeste", "b_ne"), ("L", "camp_l", "Sul", "l_s")):
        target = int(reg26.loc[region, col])
        others = st[st.region != region].sort_values(col)
        cum, n, names = 0, 0, []
        for s in others.itertuples():
            if cum + getattr(s, col) >= target:
                break
            cum += getattr(s, col)
            n += 1
            names.append(s.uf)
        F.add(f"e2026r2_{key}_states_n", n, "int",
              f"2026 runoff: number of states outside {region} whose {camp} votes, added from the smallest, stay below "
              f"{camp}'s votes in {region}")
        F.add(f"e2026r2_{key}_states_list", both_lists([uf_name(u, "pt") for u in names], [uf_name(u, "en") for u in names]),
              "phrase", "those states (names)")
        F.add(f"e2026r2_{key}_states_sum", cum, "mi", "their combined votes")
    ext = q("SELECT * FROM q3_extremes WHERE round = 2")
    for r in ext.itertuples():
        p = f"e{r.year}r2_{r.kind}_"
        F.add(p + "name", f"{r.name} ({r.uf})", "text", f"{r.year} runoff: {r.kind} municipality")
        F.add(p + "share_l", float(r.share_l2), "pct", f"{r.year} runoff: {r.kind}: L share")
        F.add(p + "share_b", 1 - float(r.share_l2), "pct", f"{r.year} runoff: {r.kind}: B share")
        F.add(p + "votes_l", int(r.camp_l), "int", f"{r.year} runoff: {r.kind}: L votes")
        F.add(p + "votes_b", int(r.camp_b), "int", f"{r.year} runoff: {r.kind}: B votes")
        F.add(p + "aptos", int(r.aptos), "int", f"{r.year} runoff: {r.kind}: electorate")

    # Q4 2018 rise
    s4 = one(con, "SELECT * FROM q4_summary")
    F.add("q4_n_b_grew", int(s4.n_b_grew), "int", "2014->2018 runoff: municipalities where the non-PT side grew")
    F.add("q4_share_b_grew", s4.n_b_grew / s4.municipalities, "pct", "same, share")
    F.add("q4_n_b_fell", int(s4.n_b_fell), "int", "2014->2018: municipalities where it fell")
    F.add("q4_n_flipped_to_b", int(s4.n_flipped_to_b), "int", "2014->2018: municipalities led by PT in 2014 and by Bolsonaro in 2018")
    F.add("q4_n_flipped_to_l", int(s4.n_flipped_to_l), "int", "2014->2018: the opposite")
    natv = q("SELECT year, round, camp_l, camp_b FROM q1_national WHERE round = 2").set_index("year")
    F.add("q4_delta_b_votes", int(natv.loc[2018, "camp_b"] - natv.loc[2014, "camp_b"]), "mi",
          "Bolsonaro 2018 runoff votes minus Aecio 2014 runoff votes, national (abroad included)")
    F.add("q4_delta_l_votes", int(natv.loc[2018, "camp_l"] - natv.loc[2014, "camp_l"]), "mi",
          "Haddad 2018 runoff votes minus Dilma 2014 runoff votes, national (negative = fewer)")
    F.add("q4_delta_l_votes_abs", abs(int(natv.loc[2018, "camp_l"] - natv.loc[2014, "camp_l"])), "mi",
          "absolute value of the previous fact")
    F.add("q4_median_delta_b", float(s4.median_delta_b_r2), "pts", "median municipal change of the non-PT runoff share")
    for r in q("SELECT * FROM q4_region_share").itertuples():
        k = {1: "n", 2: "ne", 3: "se", 4: "s", 5: "co"}[r.region_id]
        F.add(f"q4_reg_{k}_b_share_{r.year}", float(r.b_share_r2), "pct", f"{r.region}: non-PT runoff share in {r.year}")
    for r in q("SELECT * FROM q4_region").itertuples():
        k = {1: "n", 2: "ne", 3: "se", 4: "s", 5: "co"}[r.region_id]
        F.add(f"q4_reg_{k}_share_mun_b_grew", float(r.share_mun_b_grew), "pct", f"{r.region}: share of municipalities where it grew")
        F.add(f"q4_reg_{k}_delta_b_votes", int(r.delta_b_votes_r2), "mi", f"{r.region}: vote change")
        F.add(f"q4_reg_{k}_delta_b_share", float(r.delta_b_share_region), "pts", f"{r.region}: change of the non-PT runoff share")
    t4 = q("SELECT * FROM q4_top LIMIT 1").iloc[0]
    F.add("q4_top_name", f"{t4['name']} ({t4.uf})", "text", "largest growth among municipalities with 50,000+ voters")
    F.add("q4_top_delta", float(t4.delta_b_r2), "pts", "its change")
    F.add("q4_top_b_2014", float(t4.b_share_2014_r2), "pct", "non-PT share there in 2014")
    F.add("q4_top_b_2018", float(t4.b_share_2018_r2), "pct", "Bolsonaro share there in 2018")
    rj_top = int(one(con, "SELECT count(*) n FROM (SELECT * FROM q4_top LIMIT 10) WHERE uf = 'RJ'").n)
    F.add("q4_top10_rj", rj_top, "int", "of the 10 largest increases (50,000+ voters), how many in RJ")
    F.add("q4_top10_rj_phrase", {"pt": "as 10 maiores altas foram todas no estado do Rio de Janeiro" if rj_top == 10
                                 else f"{rj_top} das 10 maiores altas foram no estado do Rio de Janeiro",
                                 "en": "the 10 largest increases were all in Rio de Janeiro state" if rj_top == 10
                                 else f"{rj_top} of the 10 largest increases were in Rio de Janeiro state"}, "phrase",
          "sentence about the 10 largest increases, 2014->2018")

    # Q5 2022 recovery
    s5 = one(con, "SELECT * FROM q5_summary")
    F.add("q5_n_l_grew", int(s5.n_l_grew), "int", "2018->2022 runoff: municipalities where the lulista share grew")
    F.add("q5_share_l_grew", s5.n_l_grew / s5.municipalities, "pct", "same, share")
    F.add("q5_n_l_fell", int(s5.n_l_fell), "int", "2018->2022: municipalities where it fell")
    F.add("q5_n_flipped_to_l", int(s5.n_flipped_to_l), "int", "2018->2022: municipalities led by Bolsonaro in 2018 and by Lula in 2022")
    F.add("q5_n_flipped_to_b", int(s5.n_flipped_to_b), "int", "2018->2022: the opposite")
    F.add("q5_delta_l_votes", int(natv.loc[2022, "camp_l"] - natv.loc[2018, "camp_l"]), "mi",
          "Lula 2022 runoff votes minus Haddad 2018 runoff votes, national (abroad included)")
    F.add("q5_delta_b_votes", int(natv.loc[2022, "camp_b"] - natv.loc[2018, "camp_b"]), "mi",
          "Bolsonaro 2022 runoff minus Bolsonaro 2018 runoff, national (abroad included)")
    for r in q("SELECT * FROM q5_region").itertuples():
        k = {1: "n", 2: "ne", 3: "se", 4: "s", 5: "co"}[r.region_id]
        F.add(f"q5_reg_{k}_delta_l_share", float(r.delta_l_share_region), "pts_signed", f"{r.region}: change of the lulista runoff share")
        F.add(f"q5_reg_{k}_delta_l_share_u", abs(float(r.delta_l_share_region)), "pts", f"{r.region}: same, absolute value")
        F.add(f"q5_reg_{k}_delta_l_votes", int(r.delta_l_votes_r2), "mi", f"{r.region}: change in lulista votes")
        F.add(f"q5_reg_{k}_delta_b_votes", int(r.delta_b_votes_r2), "mi", f"{r.region}: change in Bolsonaro votes (signed)")
        F.add(f"q5_reg_{k}_share_mun_l_grew", float(r.share_mun_l_grew), "pct", f"{r.region}: share of municipalities where it grew")
        F.add(f"q5_reg_{k}_n_flipped_to_l", int(r.n_flipped_to_l), "int", f"{r.region}: municipalities flipped to Lula")
    se = one(con, "SELECT sum(delta_l_votes_r2) FILTER (WHERE region_id = 3) / sum(delta_l_votes_r2) s FROM q5_municipal")
    F.add("q5_se_share_of_l_gain", float(se.s), "pct",
          "share of Lula's 2018->2022 vote gain inside Brazil (abroad excluded) that came from the Southeast")
    t5 = q("SELECT * FROM q5_top LIMIT 1").iloc[0]
    F.add("q5_top_name", f"{t5['name']} ({t5.uf})", "text", "largest lulista growth among 50,000+ voters")
    F.add("q5_top_delta", float(t5.delta_l_r2), "pts", "its change")
    sp_top = int(one(con, "SELECT count(*) n FROM (SELECT * FROM q5_top LIMIT 10) WHERE uf = 'SP'").n)
    F.add("q5_top10_sp", sp_top, "int", "of the 10 largest increases (50,000+ voters), how many in SP")
    F.add("q5_top10_sp_phrase", {"pt": "as 10 maiores altas foram todas no estado de São Paulo" if sp_top == 10
                                 else f"{sp_top} das 10 maiores altas foram no estado de São Paulo",
                                 "en": "the 10 largest increases were all in São Paulo state" if sp_top == 10
                                 else f"{sp_top} of the 10 largest increases were in São Paulo state"}, "phrase",
          "sentence about the 10 largest increases, 2018->2022")

    # Q6 2026 turnaround
    n6 = one(con, "SELECT * FROM q6_national")
    for col, kind in (("delta_l_votes", "mi"), ("delta_b_votes", "mi"), ("others_r1", "mi"), ("delta_turnout", "mi"),
                      ("delta_blank_null", "mi"), ("b_lead_r1", "mi"), ("l_lead_r2", "mi")):
        v = int(getattr(n6, col))
        F.add(f"q6_{col}", abs(v) if col == "delta_blank_null" else v, kind, f"2026 round 1 -> runoff: {col}"
              + (" (absolute value; it fell)" if col == "delta_blank_null" else ""))
    s6 = one(con, "SELECT * FROM q6_summary")
    for col in ("n_l_gained_more", "n_l_gained_votes", "n_b_gained_votes", "n_flipped_to_l", "n_flipped_to_b", "n_turnout_up"):
        F.add(f"q6_{col}", int(getattr(s6, col)), "int", f"2026: municipalities {col}")
    F.add("q6_share_l_gained_more", s6.n_l_gained_more / s6.municipalities, "pct", "share of municipalities where Lula grew more than Flavio")
    F.add("q6_n_turnout_down", int(s6.n_turnout_down), "int", "municipalities where the turnout rate fell")
    F.add("q6_n_b_gained_more", int(s6.n_b_gained_more), "int", "municipalities where Flavio grew more than Lula (points of the electorate)")
    F.add("q6_share_b_gained_more", s6.n_b_gained_more / s6.municipalities, "pct", "same, share")
    idc = one(con, "SELECT max_abs_error FROM q6_identity_check").max_abs_error
    if idc > 1e-9:
        raise AssertionError(f"q6 accounting identity broken: {idc}")
    F.add("q6_median_gain_l", float(s6.median_gain_l_pts), "pts", "median municipal gain of Lula, points of the electorate")
    F.add("q6_median_gain_b", float(s6.median_gain_b_pts), "pts", "median municipal gain of Flavio, points of the electorate")
    flip_b = q("SELECT name, uf FROM q6_municipal WHERE leader_r1 = 'L' AND leader_r2 = 'B'")
    fb = [f"{r['name']} ({r.uf})" for _, r in flip_b.iterrows()]
    F.add("q6_flipped_to_b_names", fb, "list", "municipalities led by Lula in round 1 and by Flavio in the runoff")
    if len(fb) == 1:
        sent = {"pt": f"Em um, {fb[0]}, o caminho foi o inverso.", "en": f"In one, {fb[0]}, it went the other way."}
    else:
        sent = {"pt": f"Em {fmt(len(fb), 'int', 'pt')}, o caminho foi o inverso: {fmt(fb, 'list', 'pt')}.",
                "en": f"In {fmt(len(fb), 'int', 'en')}, it went the other way: {fmt(fb, 'list', 'en')}."}
    F.add("q6_flipped_to_b_sentence", sent, "phrase", "sentence about municipalities that flipped to Flavio")
    for r in q("SELECT * FROM q6_assoc").itertuples():
        F.add(f"q6_r_{r.outcome}_{r.factor}", float(r.r_weighted), "r", f"weighted correlation {r.outcome} x {r.factor}")
    for r in q("SELECT * FROM q6_bins").itertuples():
        if r.quintile in (1, 5):
            F.add(f"q6_bin_{r.factor}_q{r.quintile}_gain_l", float(r.gain_l_pts_weighted), "pts", f"{r.factor} quintile {r.quintile}: Lula gain")
            F.add(f"q6_bin_{r.factor}_q{r.quintile}_gain_b", float(r.gain_b_pts_weighted), "pts", f"{r.factor} quintile {r.quintile}: Flavio gain")
            kind = "pct" if r.factor == "others_r1_pts" else "pts"   # a level vs a change
            F.add(f"q6_bin_{r.factor}_q{r.quintile}_min", float(r.factor_min), kind, f"{r.factor} quintile {r.quintile}: lower bound")
            F.add(f"q6_bin_{r.factor}_q{r.quintile}_max", float(r.factor_max), kind, f"{r.factor} quintile {r.quintile}: upper bound")
    nets = q("SELECT net_gain_l_pts_weighted AS v FROM q6_bins")["v"]
    if not (nets > 0).all():   # the text says Lula gained more in every group
        raise AssertionError("q6: a quintile group where Flavio gained more; rewrite the 2026 text")
    F.add("q6_net_gain_min", float(nets.min()), "pts", "smallest net gain of Lula over Flavio across the ten quintile groups (pts of electorate)")
    F.add("q6_net_gain_min_num", float(nets.min()), "pts_num", "same, number only")
    F.add("q6_net_gain_max", float(nets.max()), "pts", "largest net gain of Lula over Flavio across the ten quintile groups")
    for r in q("SELECT * FROM q6_region").itertuples():
        k = {1: "n", 2: "ne", 3: "se", 4: "s", 5: "co"}[r.region_id]
        F.add(f"q6_reg_{k}_net_swing", int(r.net_swing_to_l), "mi", f"{r.region}: Lula gain minus Flavio gain, votes")
        F.add(f"q6_reg_{k}_delta_l", int(r.delta_l_votes), "mi", f"{r.region}: Lula gain")
        F.add(f"q6_reg_{k}_delta_b", int(r.delta_b_votes), "mi", f"{r.region}: Flavio gain")
    tp = q("SELECT * FROM q6_top_pts LIMIT 1").iloc[0]
    F.add("q6_top_pts_name", f"{tp['name']} ({tp.uf})", "text", "largest Lula gain in points, 50,000+ voters")
    F.add("q6_top_pts_gain", float(tp.gain_l_pts), "pts", "its gain")
    tb = q("SELECT * FROM q6_top_pts_b LIMIT 1").iloc[0]
    F.add("q6_top_pts_b_name", f"{tb['name']} ({tb.uf})", "text", "largest Flavio gain in points, 50,000+ voters")
    F.add("q6_top_pts_b_gain", float(tb.gain_b_pts), "pts", "its gain")
    F.add("q6_top_pts_b_gain_l", float(tb.gain_l_pts), "pts", "Lula's gain in the same municipality")
    go = int(one(con, "SELECT count(*) n FROM (SELECT * FROM q6_top_pts_b LIMIT 10) WHERE uf = 'GO'").n)
    F.add("q6_top10_b_go", go, "int", "of Flavio's 10 largest gains in points (50,000+ voters), how many in Goias")
    tvb = q("SELECT * FROM q6_top_votes_b LIMIT 1").iloc[0]
    F.add("q6_top_votes_b_name", f"{tvb['name']} ({tvb.uf})", "text", "largest Flavio gain in votes")
    F.add("q6_top_votes_b_gain", int(tvb.delta_b_votes), "mi", "its gain in votes")
    tv = q("SELECT * FROM q6_top_votes LIMIT 1").iloc[0]
    F.add("q6_top_votes_name", f"{tv['name']} ({tv.uf})", "text", "largest Lula gain in votes")
    F.add("q6_top_votes_gain", int(tv.delta_l_votes), "mil", "its gain in votes")
    F.add("q6_top_votes_gain_b", int(tv.delta_b_votes), "mil", "Flavio gain in votes there")
    gl, gb = fmt(int(tv.delta_l_votes), "mi", "pt"), fmt(int(tvb.delta_b_votes), "mi", "pt")
    gle, gbe = fmt(int(tv.delta_l_votes), "mi", "en"), fmt(int(tvb.delta_b_votes), "mi", "en")
    if tv.cd_ibge == tvb.cd_ibge:
        city = f"{tv['name']} ({tv.uf})"
        sent = {"pt": f"Em número de votos, o maior ganho dos dois foi no mesmo município, {city}: {gl} para Lula e {gb} para Flávio.",
                "en": f"In absolute votes, both candidates' largest gains came in the same municipality, {city}: {gle} for Lula and {gbe} for Flávio."}
    else:
        sent = {"pt": f"Em número de votos, o maior ganho de Lula foi em {tv['name']} ({tv.uf}) ({gl}), e o de Flávio, em {tvb['name']} ({tvb.uf}) ({gb}).",
                "en": f"In absolute votes, Lula's largest gain came in {tv['name']} ({tv.uf}), with {gle}, and Flávio's in {tvb['name']} ({tvb.uf}), with {gbe}."}
    F.add("q6_top_votes_sentence", sent, "phrase", "sentence about the largest absolute gains of each candidate")

    # Q7 context (2026 runoff)
    g = q("SELECT * FROM q7_groups WHERE year = 2026")
    for r in g.itertuples():
        p = f"q7_{r.dimension}{r.grp}_"
        F.add(p + "p50_l", float(r.p50), "pct", f"2026 runoff, {r.dimension} group {r.grp}: median municipal L share")
        F.add(p + "p50_b", 1 - float(r.p50), "pct", f"2026 runoff, {r.dimension} group {r.grp}: median municipal B share")
        F.add(p + "p10_l", float(r.p10), "pct", f"... 10th percentile of L share")
        F.add(p + "p90_l", float(r.p90), "pct", f"... 90th percentile of L share")
        F.add(p + "led_by_l", int(r.led_by_l), "int", f"... municipalities led by L")
        F.add(p + "led_by_b", int(r.led_by_b), "int", f"... municipalities led by B")
        F.add(p + "municipalities", int(r.municipalities), "int", f"... municipalities")
        F.add(p + "share_l_weighted", float(r.share_l2_weighted), "pct", f"... L share of the group's votes")
        if r.dimension == "income":
            F.add(p + "income_min", float(r.income_min), "brl", "... lowest median income in the group")
            F.add(p + "income_max", float(r.income_max), "brl", "... highest median income in the group")
    a = q("SELECT * FROM q7_assoc").set_index("year")
    F.add("q7_r_income_2026", float(a.loc[2026, "r_share_l2_log_income"]), "r", "2026 runoff: correlation of L share with log median income")
    F.add("q7_r_pop_2026", float(a.loc[2026, "r_share_l2_log_population"]), "r", "2026 runoff: correlation of L share with log population")
    F.add("q7_r_income_within_2026", float(a.loc[2026, "r_income_within_regions"]), "r",
          "same correlation with log income, inside regions (deviations from each region's mean)")
    F.add("q7_r_pop_within_2026", float(a.loc[2026, "r_pop_within_regions"]), "r",
          "same correlation with log population, inside regions")
    cuts = one(con, "SELECT * FROM q7_income_cuts")
    for k in ("p20", "p40", "p60", "p80"):
        F.add(f"q7_income_cut_{k}", float(cuts[k]), "brl2", f"income band cut point ({k} of municipal median income per capita)")
    ir = q("SELECT * FROM q7_income_region")
    F.add("q7_income1_in_ne", int(ir[(ir.income_band == 1) & (ir.region_id == 2)].municipalities.sum()), "int",
          "municipalities of the lowest income band located in the Northeast")
    F.add("q7_income5_in_s", int(ir[(ir.income_band == 5) & (ir.region_id == 4)].municipalities.sum()), "int",
          "municipalities of the highest income band located in the South")

    # Validation
    vs = q("SELECT * FROM read_csv('data/processed/validation_summary.csv')")
    F.add("validation_cells", int(vs.cells.sum()), "int", "cells compared with official totals (all years, rounds and sources)")
    F.add("validation_unexplained", int(vs.unexplained.sum()), "int", "cells with an unexplained difference")
    F.add("dot_votes", geo.DOT_VOTES, "int", "votes per dot in the dot map")

    out = C.SITE_DATA / "facts.json"
    out.write_text(json.dumps(F.d, ensure_ascii=False, indent=1), encoding="utf-8")
    return F.d
