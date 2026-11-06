"""Build and execute notebooks/01_exploratory_analysis.ipynb.

The notebook reads only data/processed (outputs of the SQL questions) and
docs/data/facts.json. Its takeaway cells are rendered from facts, so the numbers in
the prose are the numbers the pipeline computed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src.render import load_facts, render_text

NB = C.ROOT / "notebooks" / "01_exploratory_analysis.ipynb"

SETUP = """\
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
P = ROOT / "data" / "processed"
facts = json.loads((ROOT / "docs" / "data" / "facts.json").read_text(encoding="utf-8"))
L, B, MIX, GREY = "#6A4C9C", "#B8741A", "#E9C3C4", "#9A9186"
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "font.size": 10})
pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
"""

CELLS = [
    ("md", """# Brazil is not binary: exploratory analysis

Presidential elections 2018, 2022 and 2026 (2014 as a baseline), municipality level.
Data: TSE open data (votes and turnout by municipality and zone), IBGE (mesh, population, income).
Every table read here is produced by `python run_all.py` (one SQL file per question in `sql/`).

**Camps.** Lulista = Haddad 2018, Lula 2022 and 2026. Bolsonarista = Jair Bolsonaro 2018 and 2022,
Flávio Bolsonaro 2026. In 2014 the runoff was Dilma (PT) against Aécio (PSDB); it is used only as a
baseline and labelled by name.

**Caveat.** Municipal data describe places, not people. Associations between municipal measures
do not tell how any individual voted (ecological fallacy)."""),
    ("code", SETUP),
    ("md", "## Q1. National results, including people who chose neither camp"),
    ("code", """\
nat = pd.read_csv(P / "q1_national.csv")
cols = ["pct_l_aptos", "pct_b_aptos", "pct_others_aptos", "pct_blank_null_aptos", "pct_absent_aptos"]
labels = ["Lulista (2014: Dilma)", "Bolsonarista (2014: Aécio)", "Third candidates", "Blank or null", "Did not vote"]
colors = [L, B, "#677B91", "#CFC6B8", GREY]
fig, ax = plt.subplots(figsize=(8, 3.6))
y = [f"{r.year} r{r['round']}" for _, r in nat.iterrows()]
left = [0] * len(nat)
for c, lab, col in zip(cols, labels, colors):
    ax.barh(y, nat[c] * 100, left=left, color=col, label=lab)
    left = [l + v * 100 for l, v in zip(left, nat[c])]
ax.invert_yaxis(); ax.set_xlabel("% of the electorate"); ax.legend(ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2))
ax.set_title("Each round, as a share of everyone who could vote")
plt.show()
nat[["year", "round", "aptos", "camp_l", "camp_b", "others", "blank_null", "absent", "pct_l_valid", "pct_b_valid", "pct_neither_aptos"]]"""),
    ("md", """**Takeaways**

* 2026 runoff: Lula {{e2026r2_pct_l_valid}} and Flávio Bolsonaro {{e2026r2_pct_b_valid}} of valid votes.
* {{e2026r2_pct_neither_aptos}} of the electorate did not vote for either candidate in the 2026 runoff:
  {{e2026r2_pct_absent_aptos}} did not turn out and {{e2026r2_pct_blank_null_aptos}} voted blank or null. Abstention also
  includes registered voters who moved or died, so it is not all a choice.
* 2026 first round: Flávio {{e2026r1_pct_b_valid}}, Lula {{e2026r1_pct_l_valid}}, and {{e2026r1_others}} votes for third candidates."""),
    ("md", "## Q2. Municipal results: who led where"),
    ("code", """\
win = pd.read_csv(P / "q2_winners.csv")
win[["year", "round", "led_by_l", "led_by_b", "ties", "aptos_share_in_l_led", "l_votes_where_b_led", "b_votes_where_l_led"]]"""),
    ("md", """**Takeaways**

* 2026 runoff: Lula led in {{e2026r2_led_by_l}} municipalities and Flávio in {{e2026r2_led_by_b}}.
  The electorate living in municipalities led by each is almost exactly split ({{e2026r2_aptos_share_in_l_led}} and {{e2026r2_aptos_share_in_b_led}}).
* {{e2026r2_l_votes_where_b_led}} Lula votes came from municipalities where Flávio led, and {{e2026r2_b_votes_where_l_led}}
  Flávio votes from municipalities where Lula led.
* In {{e2026r2_n_minority_over_10}} of {{n_mun_2026}} municipalities the side that lost locally still got more than 10%.
* First rounds: a third candidate came first in {{e2014r1_led_by_other}} municipalities in 2014 (Marina Silva) and
  {{e2018r1_led_by_other}} in 2018 (Ciro Gomes); in 2022 and 2026, in {{e2026r1_led_by_other}}."""),
    ("md", "## Q3. How mixed is the vote?"),
    ("code", """\
h = pd.read_csv(P / "q3_hist.csv")
fig, axes = plt.subplots(1, 4, figsize=(12, 2.8), sharey=True)
for ax, yr in zip(axes, [2014, 2018, 2022, 2026]):
    d = h[(h.year == yr) & (h["round"] == 2)]
    ax.bar(d.bin_start_pct + 2.5, d.municipalities, width=4.6,
           color=[L if b >= 50 else B for b in d.bin_start_pct])
    ax.set_title(f"{yr} runoff"); ax.set_xlabel("lulista share of the two camps (%)")
axes[0].set_ylabel("municipalities")
plt.tight_layout(); plt.show()
mino = pd.read_csv(P / "q3_minority.csv")
mino[["year", "round", "n_minority_over_30", "share_minority_over_30", "n_minority_over_40", "aptos_share_minority_over_30", "local_minority_votes", "local_minority_vote_share", "min_minority_share"]]"""),
    ("code", """\
reg = pd.read_csv(P / "q3_region.csv")
reg[(reg.year == 2026) & (reg["round"] == 2)][["region", "municipalities", "camp_l", "camp_b", "share_l2", "led_by_l", "led_by_b"]]"""),
    ("code", """\
pd.read_csv(P / "q3_extremes.csv").query("round == 2")[["year", "kind", "name", "uf", "aptos", "camp_l", "camp_b", "share_l2"]]"""),
    ("md", """**Takeaways**

* 2026 runoff: {{e2026r2_local_minority_votes}} people ({{e2026r2_local_minority_vote_share}} of valid votes) voted for the
  candidate who lost in their own municipality.
* In {{e2026r2_n_minority_over_30}} municipalities ({{e2026r2_share_minority_over_30}}) the local loser still got more than 30%;
  in {{e2026r2_n_minority_over_40}} ({{e2026r2_share_minority_over_40}}), more than 40%.
* Even the most one-sided places are mixed: in {{e2026r2_most_l_name}} Flávio got {{e2026r2_most_l_share_b}};
  in {{e2026r2_most_b_name}} Lula got {{e2026r2_most_b_share_l}}.
* Flávio got {{e2026r2_reg_ne_camp_b}} votes in the Northeast, more than in {{e2026r2_b_ne_states_n}} states of other regions
  combined. Lula got {{e2026r2_reg_s_camp_l}} in the South, more than in {{e2026r2_l_s_states_n}} states of other regions combined.
* In the North the two were {{e2026r2_reg_n_diff_int}} votes apart.
* Against the thesis, regions are not mirror images: in the Northeast Lula led {{e2026r2_reg_ne_led_by_l}} of
  {{e2026r2_reg_ne_municipalities}} municipalities; in the South Flávio led {{e2026r2_reg_s_led_by_b}} of {{e2026r2_reg_s_municipalities}},
  and in the Center-West {{e2026r2_reg_co_led_by_b}} of {{e2026r2_reg_co_municipalities}}.
* Lula's lead in the Northeast was {{e2026r2_reg_ne_lead}} votes; Flávio's leads in {{e2026r2_b_led_regions}} added up to
  {{e2026r2_b_lead_where_b_led_regions}}."""),
    ("md", "## Q4. 2018: growth of the bolsonarista camp over the non-PT side of 2014"),
    ("code", """\
q4 = pd.read_csv(P / "q4_municipal.csv")
fig, ax = plt.subplots(figsize=(7, 3))
ax.hist(q4.delta_b_r2 * 100, bins=60, color=B)
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("change in the non-PT runoff share, 2014 to 2018 (points)"); ax.set_ylabel("municipalities")
plt.show()
display(pd.read_csv(P / "q4_region_share.csv"))
pd.read_csv(P / "q4_top.csv")[["name", "uf", "aptos_2018", "b_share_2014_r2", "b_share_2018_r2", "delta_b_r2"]].head(10)"""),
    ("md", """**Takeaways**

* The non-PT runoff share grew in {{q4_n_b_grew}} municipalities ({{q4_share_b_grew}}); {{q4_n_flipped_to_b}} municipalities that
  Dilma led in 2014 were led by Bolsonaro in 2018.
* The non-PT runoff share rose by {{q4_reg_n_delta_b_share}} in the North, {{q4_reg_se_delta_b_share}} in the Southeast,
  {{q4_reg_s_delta_b_share}} in the South and {{q4_reg_co_delta_b_share}} in the Center-West, and by {{q4_reg_ne_delta_b_share}} in the Northeast.
  Different candidates (Aécio, then Bolsonaro): this measures the side opposed to the PT, not one movement.
* Nationally, Bolsonaro had {{q4_delta_b_votes}} more runoff votes than Aécio; Haddad had {{q4_delta_l_votes}} relative to Dilma.
* Of the ten largest increases among municipalities with 50,000+ voters, {{q4_top10_rj}} were in Rio de Janeiro state;
  the largest was {{q4_top_name}}, {{q4_top_delta}}."""),
    ("md", "## Q5. 2022: where the lulista camp regained ground"),
    ("code", """\
q5 = pd.read_csv(P / "q5_municipal.csv")
fig, ax = plt.subplots(figsize=(7, 3))
ax.hist(q5.delta_l_r2 * 100, bins=60, color=L)
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("change in the lulista runoff share, 2018 to 2022 (points)"); ax.set_ylabel("municipalities")
plt.show()
display(pd.read_csv(P / "q5_region.csv")[["region", "delta_l_share_region", "delta_l_votes_r2", "delta_b_votes_r2", "share_mun_l_grew", "n_flipped_to_l"]])
pd.read_csv(P / "q5_top.csv")[["name", "uf", "aptos_2022", "l_share_2018_r2", "l_share_2022_r2", "delta_l_r2"]].head(10)"""),
    ("md", """**Takeaways**

* The lulista runoff share grew in {{q5_n_l_grew}} municipalities ({{q5_share_l_grew}}); {{q5_n_flipped_to_l}} flipped to Lula and {{q5_n_flipped_to_b}} to Bolsonaro.
* Lula had {{q5_delta_l_votes}} more runoff votes than Haddad; Bolsonaro had {{q5_delta_b_votes}} more than in 2018.
* The recovery was mostly in the Southeast ({{q5_reg_se_delta_l_share}}), which accounts for {{q5_se_share_of_l_gain}} of Lula's vote gain;
  the Northeast barely moved ({{q5_reg_ne_delta_l_share}})."""),
    ("md", "## Q6. 2026: the runoff turnaround"),
    ("code", """\
q6 = pd.read_csv(P / "q6_municipal.csv")
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, x, lab in ((axes[0], "others_r1_pts", "third-candidate vote in round 1 (% of electorate)"),
                   (axes[1], "turnout_change_pts", "turnout change, round 1 to runoff (points)")):
    ax.scatter(q6[x] * 100, q6.gain_l_pts * 100, s=q6.aptos / 20000, alpha=0.35, color=L, lw=0)
    ax.set_xlabel(lab)
axes[0].set_ylabel("Lula gain (points of the electorate)")
plt.tight_layout(); plt.show()
display(pd.read_csv(P / "q6_assoc.csv"))
display(pd.read_csv(P / "q6_bins.csv"))
pd.read_csv(P / "q6_national.csv")"""),
    ("md", """**Takeaways**

* Flávio led the first round by {{q6_b_lead_r1}} votes; Lula won the runoff by {{q6_l_lead_r2}}.
* Between rounds Lula gained {{q6_delta_l_votes}} votes and Flávio {{q6_delta_b_votes}}. Third candidates had {{q6_others_r1}} votes in
  round 1, turnout rose by {{q6_delta_turnout}} and blank or null votes fell by {{q6_delta_blank_null}}.
* Lula grew more than Flávio (in points of the electorate) in {{q6_n_l_gained_more}} of {{n_mun_2026}} municipalities, Flávio more than Lula
  in {{q6_n_b_gained_more}}; {{q6_n_flipped_to_l}} flipped to Lula and {{q6_n_flipped_to_b}} to Flávio ({{q6_flipped_to_b_names}}).
* Largest gains among municipalities with 50,000+ voters: Lula in {{q6_top_pts_name}} ({{q6_top_pts_gain}}), Flávio in
  {{q6_top_pts_b_name}} ({{q6_top_pts_b_gain}}).
* Where third candidates had more votes in round 1, both candidates grew more in the runoff; where turnout rose more, too.
  Part of this is arithmetic: in points of the electorate, the two gains add up to the third-candidate vote plus the turnout
  change minus the change in blank/null votes. Lula's net advantage grew by a similar amount everywhere, from {{q6_net_gain_min}}
  to {{q6_net_gain_max}} across groups of municipalities. Municipal data do not show who switched votes."""),
    ("md", "## Q7. Size, region and income: overlapping distributions"),
    ("code", """\
g = pd.read_csv(P / "q7_groups.csv").query("year == 2026")
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), sharey=True)
for ax, dim, title in zip(axes, ["income", "size", "region"], ["Income band (1 = lowest)", "Size class (1 = smallest)", "Region (1 = N ... 5 = CO)"]):
    d = g[g.dimension == dim]
    ax.vlines(d.grp, d.p10 * 100, d.p90 * 100, color=GREY, lw=6, alpha=0.5)
    ax.vlines(d.grp, d.p25 * 100, d.p75 * 100, color=MIX, lw=6)
    ax.scatter(d.grp, d.p50 * 100, color="k", zorder=3, s=12)
    ax.axhline(50, color="k", lw=0.6); ax.set_title(title)
axes[0].set_ylabel("lulista share, 2026 runoff (%)\\nbars: 10-90 and 25-75 percentiles")
plt.tight_layout(); plt.show()
display(g[["dimension", "grp", "municipalities", "p10", "p50", "p90", "led_by_l", "led_by_b"]])
pd.read_csv(P / "q7_assoc.csv")"""),
    ("md", """**Takeaways**

* Income goes together with the municipal vote (r = {{q7_r_income_2026}} with log median income in 2026), and with region:
  {{q7_income1_in_ne}} of the {{q7_income1_municipalities}} lowest-income municipalities are in the Northeast and {{q7_income5_in_s}} of the
  {{q7_income5_municipalities}} highest-income ones in the South. Inside regions the association remains (r = {{q7_r_income_within_2026}}).
* At the extremes the distributions barely overlap: this is evidence against a 'no pattern' reading and is shown as such.
  There are exceptions on both sides: Flávio led {{q7_income1_led_by_b}} municipalities of the lowest band, Lula {{q7_income5_led_by_l}} of the highest.
* These are places, not people: richer municipalities also have poorer voters, and the reverse.
* Size: almost no association nationally (r = {{q7_r_pop_2026}}), slightly negative inside regions (r = {{q7_r_pop_within_2026}})."""),
]


def build():
    facts = load_facts()
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    for kind, src in CELLS:
        if kind == "md":
            nb.cells.append(nbformat.v4.new_markdown_cell(render_text(src, "en", facts)))
        else:
            nb.cells.append(nbformat.v4.new_code_cell(src))
    return nb


def run():
    nb = build()
    NotebookClient(nb, timeout=300, kernel_name="python3",
                   resources={"metadata": {"path": str(NB.parent)}}).execute()
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, NB)
    print(f"  wrote {NB.relative_to(C.ROOT)}")


if __name__ == "__main__":
    run()
