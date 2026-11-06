// Change maps (light background): which side gained between two elections, by municipality,
// plus a small bar chart by region.
import { C, NAMES, REGION_NAMES, results, municipios, row, getJSON, changeScale, pts, pct, int, table } from "./core.js";
import { CanvasMap, isNewMunicipality, tipNode } from "./mapcore.js";
import { onResize, roundedRight } from "./charts.js";

const CONFIG = {
  2018: { a: [2014, 2], b: [2018, 2], max: 0.25, measure: "share" },
  2022: { a: [2018, 2], b: [2022, 2], max: 0.15, measure: "share" },
  2026: { a: [2026, 1], b: [2026, 2], max: 0.12, measure: "net" },
};

function value(cfg, ra, rb) {
  if (!ra || !rb) return null;
  if (cfg.measure === "share") return rb.l / (rb.l + rb.b) - ra.l / (ra.l + ra.b);   // + = L side gained
  return (rb.l / rb.aptos - ra.l / ra.aptos) - (rb.b / rb.aptos - ra.b / ra.aptos);  // Lula gain minus Flávio gain
}

export async function changeMap(key) {
  const cfg = CONFIG[key];
  const box = document.getElementById(`map-${key}`);
  const canvas = document.createElement("canvas");
  const hover = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true"); hover.setAttribute("aria-hidden", "true");
  box.prepend(canvas, hover);
  const tip = box.querySelector(".tooltip");
  const [ra, rb, mun] = await Promise.all([results(...cfg.a), results(...cfg.b), municipios()]);
  const map = await new CanvasMap(box, { fill: canvas, hover, dark: false }).init();
  const scale = changeScale(cfg.max);
  const vals = map.geo.feats.map((f) => (isNewMunicipality(f.id, cfg.a[0]) ? null : value(cfg, row(ra, f.row), row(rb, f.row))));
  const colors = vals.map((v) => (v === null ? null : scale(v)));
  map.redraw = () => map.drawFills(colors);
  map.redraw();
  const na = NAMES[cfg.a[0]], nb = NAMES[cfg.b[0]];
  map.bindTooltip(box, tip, (i) => {
    const f = map.geo.feats[i], m = mun.rows[f.row];
    const a = row(ra, f.row), b = row(rb, f.row);
    if (!a) return tipNode(`${m[1]} (${m[2]})`, [], "Município instalado em 2025: sem resultado presidencial anterior para comparar.");
    if (cfg.measure === "share") {
      return tipNode(`${m[1]} (${m[2]})`, [
        [C.l, `${na.L} ${cfg.a[0]}`, pct(a.l / (a.l + a.b))], [C.l, `${nb.L} ${cfg.b[0]}`, pct(b.l / (b.l + b.b))],
        [C.b, `${na.B} ${cfg.a[0]}`, pct(a.b / (a.l + a.b))], [C.b, `${nb.B} ${cfg.b[0]}`, pct(b.b / (b.l + b.b))]],
        "Fatias nos votos válidos do 2º turno.");
    }
    return tipNode(`${m[1]} (${m[2]})`, [
      [C.l, "Variação de Lula", pts(b.l / b.aptos - a.l / a.aptos, 1, true)], [C.b, "Variação de Flávio", pts(b.b / b.aptos - a.b / a.aptos, 1, true)]],
      "Em pontos do eleitorado, do 1º para o 2º turno.");
  });
  // legend
  const lg = document.getElementById(`legend-${key}`);
  const grad = document.createElement("div"); grad.style.width = "100%";
  const g = document.createElement("div"); g.className = "grad";
  g.style.background = `linear-gradient(90deg, ${d3.range(-1, 1.001, 0.1).map((t) => scale(t * cfg.max)).join(",")})`;
  const labels = document.createElement("div"); labels.className = "grad-labels";
  const left = cfg.measure === "share" ? (key === "2018" ? "Aécio/Bolsonaro cresceu" : `${nb.B} cresceu`) : "Flávio cresceu mais";
  const right = cfg.measure === "share" ? (key === "2018" ? "Dilma/Haddad cresceu" : `${nb.L} cresceu`) : "Lula cresceu mais";
  for (const t of [left, "sem mudança", right]) { const s = document.createElement("span"); s.textContent = t; labels.append(s); }
  labels.lastChild.style.textAlign = "right"; labels.children[1].style.textAlign = "center";
  const sc = document.createElement("p"); sc.className = "chart-foot"; sc.style.margin = "2px 0 0";
  sc.textContent = `Cores mais fortes: ${int(cfg.max * 100)} pontos ou mais.`;
  grad.append(g, labels, sc);
  const hatch = document.createElement("span"); hatch.className = "key";
  if (cfg.a[0] < 2026) {
    const i = document.createElement("i"); i.style.background = "repeating-linear-gradient(135deg,#a59c90 0 2px,#f2ece2 2px 5px)";
    hatch.append(i, document.createTextNode("Sem comparação (município instalado em 2025)"));
  }
  lg.replaceChildren(grad, hatch);
  if (key !== "2026") regionBars(key);
  else {
    const stories = await getJSON("data/stories.json");
    table(document.getElementById("table-2026"), ["Região", "Lula cresceu (votos)", "Flávio cresceu (votos)", "Diferença", "Municípios onde Lula cresceu mais"],
      stories.turnaround2026.region.map((d) => [d.region, int(d.delta_l_votes), int(d.delta_b_votes), int(d.net_swing_to_l), `${int(d.n_mun_l_gained_more)} de ${int(d.municipalities)}`]));
  }
}

async function regionBars(key) {
  const stories = await getJSON("data/stories.json");
  const host = document.getElementById(`bars-${key}`);
  const data = key === "2018"
    ? stories.rise2018.region.map((d) => ({ region: d.region, v: -d.delta_b_share_region, label: d.delta_b_share_region }))
    : stories.recovery2022.region.map((d) => ({ region: d.region, v: d.delta_l_share_region, label: d.delta_l_share_region }));
  const title = "Por região";
  function draw() {
    const W = Math.max(260, host.clientWidth || 300), rowH = 34, m = { t: 30, r: 92, l: 104 };
    const H = m.t + data.length * rowH + 10;
    const max = d3.max(data, (d) => Math.abs(d.v));
    const x = d3.scaleLinear().domain([0, max]).range([0, W - m.l - m.r]);
    const svg = d3.create("svg").attr("width", W).attr("height", H).attr("viewBox", `0 0 ${W} ${H}`);
    svg.append("text").attr("x", 0).attr("y", 14).attr("class", "anno").style("font-weight", 650).text(title);
    data.forEach((d, i) => {
      const y = m.t + i * rowH;
      svg.append("text").attr("x", 0).attr("y", y + 15).attr("class", "anno").text(d.region);
      const w = Math.max(2, x(Math.abs(d.v)));
      svg.append("path").attr("d", roundedRight(m.l, y + 4, w, 16, 4)).attr("fill", d.v >= 0 ? C.l : C.b);
      svg.append("text").attr("x", m.l + w + 6).attr("y", y + 16).attr("class", "anno").text(pts(d.label, 1, true));
    });
    host.replaceChildren(svg.node());
  }
  draw(); onResize(host, draw);
  table(document.getElementById(`table-${key}`), ["Região", key === "2018" ? "Variação da fatia de Aécio (2014) para Bolsonaro (2018)" : "Variação da fatia de Haddad (2018) para Lula (2022)"],
    data.map((d) => [d.region, pts(d.label, 1, true)]));
}
