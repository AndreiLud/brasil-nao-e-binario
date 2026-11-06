// Non-map charts. SVG for axes and bars; canvas for the dense scatter.
import { C, NAMES, FULLNAMES, REGION_NAMES, T, regionName, getJSON, results, municipios, row, leader, int, pct, pts, votes, dec, table, segmented, shareScale } from "./core.js";
import { tipNode } from "./mapcore.js";

const svgNS = "http://www.w3.org/2000/svg";
const width = (el) => Math.max(280, el.clientWidth || 320);

// ---------- 1. votes for the local winner vs the local loser ----------
export async function minorityBar() {
  const [res, mun] = await Promise.all([results(2026, 2), municipios()]);
  let lWin = 0, lLose = 0, bWin = 0, bLose = 0;
  for (let i = 0; i < mun.rows.length; i++) {
    const r = row(res, i); if (!r) continue;
    if (r.l > r.b) { lWin += r.l; bLose += r.b; } else if (r.b > r.l) { bWin += r.b; lLose += r.l; } else { lWin += r.l; bWin += r.b; }
  }
  const total = lWin + lLose + bWin + bLose;
  const parts = [
    [T.lWon, lWin, C.l, false], [T.lLost, lLose, C.l, true],
    [T.bLost, bLose, C.b, true], [T.bWon, bWin, C.b, false],
  ];
  const bar = document.getElementById("minority-bar");
  const leg = document.getElementById("minority-legend");
  bar.replaceChildren(); leg.replaceChildren();
  for (const [label, v, color, lost] of parts) {
    const s = document.createElement("span");
    s.style.width = `${(v / total) * 100}%`;
    s.style.background = lost ? `repeating-linear-gradient(135deg, ${color} 0 3px, ${d3.color(color).brighter(1.3)} 3px 6px)` : color;
    s.title = `${label}: ${votes(v)}`;
    bar.appendChild(s);
    const k = document.createElement("span"); k.className = "key";
    const i = document.createElement("i"); i.style.cssText = `width:12px;height:12px;border-radius:3px;display:inline-block;margin-right:6px;vertical-align:-1px;background:${s.style.background}`;
    k.append(i, document.createTextNode(`${label}: ${votes(v)}`));
    leg.appendChild(k);
  }
  bar.setAttribute("aria-label", parts.map(([l, v]) => T.votesOf(l, votes(v))).join("; "));
}

// ---------- 2. national stacked bars over the electorate ----------
export async function nationalBars() {
  const { national } = await getJSON("data/national.json");
  const cats = [
    ["camp_l", (y) => (y === 2014 ? T.dilmaBase : T.campL), C.l, false],
    ["camp_b", (y) => (y === 2014 ? T.aecioBase : T.campB), C.b, false],
    ["others", () => T.others, C.third, true],
    ["blank_null", () => T.blankNull, C.blank, true],
    ["absent", () => T.absent, C.absent, true],
  ];
  const legend = document.getElementById("nat-legend");
  legend.replaceChildren();
  for (const [k, lab, col] of cats) {
    const s = document.createElement("span"); s.className = "key";
    const i = document.createElement("i");
    i.style.background = col;
    s.append(i, document.createTextNode(k === "camp_l" ? T.campLLegend : k === "camp_b" ? T.campBLegend : lab()));
    legend.appendChild(s);
  }
  const host = document.getElementById("natbars");
  host.replaceChildren();
  let prevYear = null;
  for (const n of national) {
    if (prevYear && prevYear !== n.year) { const g = document.createElement("div"); g.className = "gap"; host.appendChild(g); }
    prevYear = n.year;
    const r = document.createElement("div"); r.className = "row" + (n.year === 2014 ? " baseline" : "");
    const lab = document.createElement("div"); lab.className = "row-label";
    const b = document.createElement("b"); b.textContent = String(n.year);
    lab.append(b, document.createTextNode(T.roundShort(n.round)));
    const bar = document.createElement("div"); bar.className = "bar";
    for (const [k, labf, col] of cats) {
      const v = n[k] / n.aptos;
      if (v <= 0) continue;
      const s = document.createElement("div"); s.className = "seg-part" + (k === "absent" ? " absent" : "");
      s.style.width = `${v * 100}%`;
      if (k !== "absent") s.style.background = col;
      // text: white on violet and on the third-candidate grey; ink elsewhere (AA contrast)
      if (k === "camp_b" || k === "blank_null" || k === "absent") s.classList.add("dark-text");
      if (n.year === 2014 && (k === "camp_l" || k === "camp_b")) {   // baseline: lighter fill, same hue
        s.style.background = d3.interpolateLab(col, C.paper)(0.45);
        s.classList.add("dark-text");
      }
      if (v >= 0.1) s.textContent = `${dec(v * 100, 0)}%`;
      s.title = T.ofElectorate(labf(n.year), pct(v), votes(n[k]));
      bar.appendChild(s);
    }
    r.append(lab, bar); host.appendChild(r);
  }
  table(document.getElementById("nat-table"),
    [T.round, T.campL, T.campB, T.othersShort, T.blankNull, T.absent, T.electorate],
    national.map((n) => [T.natRow(n.year, n.round), pct(n.pct_l_aptos), pct(n.pct_b_aptos), pct(n.pct_others_aptos),
      pct(n.pct_blank_null_aptos), pct(n.pct_absent_aptos), int(n.aptos)]));
}

// ---------- 4a. histogram of municipalities ----------
export async function histogram() {
  const stories = await getJSON("data/stories.json");
  const host = document.getElementById("hist");
  const scale = shareScale(false);
  let year = 2026;
  const ctl = document.getElementById("hist-controls");
  ctl.replaceChildren();
  segmented(ctl, T.yearOfRunoff, [[2014, "2014"], [2018, "2018"], [2022, "2022"], [2026, "2026"]], year, (v) => { year = +v; draw(); });
  function draw() {
    const data = stories.hist.filter((d) => d.year === year && d.round === 2);
    const bins = d3.range(0, 100, 5).map((b) => data.find((d) => d.bin_start_pct === b) || { bin_start_pct: b, municipalities: 0 });
    const mino = stories.minority.find((d) => d.year === year && d.round === 2);
    const title = document.getElementById("t-hist");
    if (title) title.textContent = T.histTitle(year, int(mino.n_minority_over_30));
    const W = width(host), H = W < 500 ? 250 : 300, m = { t: 30, r: 8, b: 44, l: 36 };
    const x = d3.scaleLinear().domain([0, 100]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([0, d3.max(bins, (d) => d.municipalities) * 1.08]).nice().range([H - m.b, m.t]);
    const svg = d3.create("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H).attr("role", "presentation");
    svg.append("rect").attr("x", x(30)).attr("width", x(70) - x(30)).attr("y", m.t - 8).attr("height", H - m.b - m.t + 8).attr("fill", C.paper2);
    svg.append("text").attr("class", "anno").attr("x", x(50)).attr("y", m.t - 14).attr("text-anchor", "middle")
      .text(T.histBand(int(mino.n_minority_over_30)));
    const g = svg.append("g").attr("class", "grid");
    y.ticks(4).forEach((t) => g.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(t)).attr("y2", y(t)));
    const ax = svg.append("g").attr("class", "axis");
    y.ticks(4).forEach((t) => ax.append("text").attr("x", m.l - 6).attr("y", y(t) + 4).attr("text-anchor", "end").text(int(t)));
    const bw = x(5) - x(0) - 2;
    const tip = ensureTip(host);
    svg.append("g").selectAll("path").data(bins).join("path")
      .attr("d", (d) => roundedTop(x(d.bin_start_pct) + 1, y(d.municipalities), bw, y(0) - y(d.municipalities), 3))
      .attr("fill", (d) => scale((d.bin_start_pct + 2.5) / 100))
      .attr("stroke", "rgba(30,26,22,0.35)").attr("stroke-width", 1)
      .on("pointermove pointerdown", (ev, d) => {
        const n = NAMES[year];
        showTip(tip, host, ev, tipNode(T.between(n.L, d.bin_start_pct, d.bin_start_pct + 5), [[null, T.municipalities, int(d.municipalities)]],
          `${T.between(n.B, 100 - d.bin_start_pct - 5, 100 - d.bin_start_pct)}.`));
      })
      .on("pointerleave", (e) => { if (e.pointerType !== "touch") tip.classList.remove("on"); });
    const n = NAMES[year];
    const lab = svg.append("g").attr("class", "axis");
    [[0, "0%"], [50, "50%"], [100, "100%"]].forEach(([v, t]) => lab.append("text").attr("x", x(v)).attr("y", H - m.b + 16).attr("text-anchor", v === 0 ? "start" : v === 100 ? "end" : "middle").text(t));
    svg.append("text").attr("x", m.l).attr("y", H - 8).attr("class", "anno").text(`← ${T.more(n.B)}`);
    svg.append("text").attr("x", W - m.r).attr("y", H - 8).attr("text-anchor", "end").attr("class", "anno").text(`${T.more(n.L)} →`);
    if (W >= 440) svg.append("text").attr("x", x(50)).attr("y", H - 8).attr("text-anchor", "middle").attr("class", "anno anno-muted").text(T.shareOf(n.L));
    host.replaceChildren(svg.node(), tip);
    table(document.getElementById("hist-table"), [T.shareOfCap(n.L), T.municipalities], bins.map((d) => [T.pctRange(d.bin_start_pct, d.bin_start_pct + 5), int(d.municipalities)]));
  }
  draw();
  onResize(host, draw);
}

// ---------- 4b. votes by region (absolute) ----------
export async function regions() {
  const stories = await getJSON("data/stories.json");
  const host = document.getElementById("regions");
  const data = stories.region.filter((d) => d.year === 2026 && d.round === 2);
  function draw() {
    const W = width(host), rowH = 52, m = { t: 6, r: 96, b: 6, l: 96 };
    const H = m.t + m.b + data.length * rowH;
    const x = d3.scaleLinear().domain([0, d3.max(data, (d) => Math.max(d.camp_l, d.camp_b))]).range([m.l, W - m.r]);
    const svg = d3.create("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", W).attr("height", H);
    data.forEach((d, i) => {
      const y0 = m.t + i * rowH;
      svg.append("text").attr("x", 0).attr("y", y0 + 24).attr("class", "anno").style("font-weight", 600).text(regionName(d.region_id));
      [["camp_l", C.l, 6], ["camp_b", C.b, 26]].forEach(([k, col, dy]) => {
        const w = Math.max(2, x(d[k]) - m.l);
        svg.append("path").attr("d", roundedRight(m.l, y0 + dy, w, 16, 4)).attr("fill", col);
        svg.append("text").attr("x", m.l + w + 6).attr("y", y0 + dy + 12).attr("class", "anno").text(votes(d[k]));
      });
    });
    host.replaceChildren(svg.node());
  }
  draw(); onResize(host, draw);
  table(document.getElementById("regions-table"), [T.region, T.votesOfL, T.votesOfB, T.wonByL, T.wonByB],
    data.map((d) => [regionName(d.region_id), int(d.camp_l), int(d.camp_b), d.region_id === 9 ? "" : int(d.led_by_l), d.region_id === 9 ? "" : int(d.led_by_b)]));
}

// ---------- 4d. income, size, region ----------
export async function context() {
  const stories = await getJSON("data/stories.json");
  const host = document.getElementById("context");
  const g = stories.context.groups.filter((d) => d.year === 2026);
  const fmtBRL = (v) => `R$\u00a0${dec(v, 2)}`;
  const label = {
    income: (d) => (d.grp === 1 ? T.incomeLow : d.grp === 5 ? T.incomeHigh : T.incomeBand(d.grp)),
    size: (d) => T.sizes[d.grp],
    region: (d) => REGION_NAMES[d.grp],
  };
  const dims = [["income", T.dimIncome], ["size", T.dimSize], ["region", T.dimRegion]];
  const scale = shareScale(false);
  function draw() {
    const W = width(host), rowH = 30, m = { l: W < 500 ? 118 : 150, r: 16 };
    const x = d3.scaleLinear().domain([0, 1]).range([m.l, W - m.r]);
    let y = 0;
    const svg = d3.create("svg").attr("width", W);
    const tip = ensureTip(host);
    for (const [dim, title] of dims) {
      const rows = g.filter((d) => d.dimension === dim).sort((a, b) => a.grp - b.grp);
      svg.append("text").attr("x", 0).attr("y", y + 16).style("font-weight", 650).attr("class", "anno").text(title);
      y += 28;
      svg.append("line").attr("x1", x(0.5)).attr("x2", x(0.5)).attr("y1", y - 6).attr("y2", y + rows.length * rowH).attr("stroke", C.ink).attr("stroke-width", 1).attr("opacity", 0.35);
      rows.forEach((d) => {
        const cy = y + rowH / 2;
        const gg = svg.append("g").style("cursor", "default");
        gg.append("rect").attr("x", 0).attr("y", y).attr("width", W).attr("height", rowH).attr("fill", "transparent");
        gg.append("text").attr("x", 0).attr("y", cy + 4).attr("class", "anno").text(label[dim](d));
        gg.append("line").attr("x1", x(d.p10)).attr("x2", x(d.p90)).attr("y1", cy).attr("y2", cy).attr("stroke", "#a59c90").attr("stroke-width", 3).attr("stroke-linecap", "round");
        gg.append("line").attr("x1", x(d.p25)).attr("x2", x(d.p75)).attr("y1", cy).attr("y2", cy).attr("stroke", scale(d.p50)).attr("stroke-width", 12).attr("stroke-linecap", "round");
        gg.append("circle").attr("cx", x(d.p50)).attr("cy", cy).attr("r", 5).attr("fill", C.ink).attr("stroke", C.paper).attr("stroke-width", 2);
        gg.on("pointermove pointerdown", (ev) => showTip(tip, host, ev, tipNode(label[dim](d), [
          [null, T.municipalities, int(d.municipalities)], [C.l, T.lWonIn, int(d.led_by_l)], [C.b, T.bWonIn, int(d.led_by_b)],
          [null, T.lMedian, pct(d.p50)], [null, T.middleHalf, T.to(pct(d.p25, 0), pct(d.p75, 0))]],
          dim === "income" ? T.incomeRange(fmtBRL(d.income_min), fmtBRL(d.income_max)) : null)))
          .on("pointerleave", (e) => { if (e.pointerType !== "touch") tip.classList.remove("on"); });
        y += rowH;
      });
      y += 18;
    }
    const ax = svg.append("g").attr("class", "axis");
    (W < 500 ? [0, 0.5, 1] : [0, 0.25, 0.5, 0.75, 1]).forEach((t) => ax.append("text").attr("x", x(t)).attr("y", y + 4).attr("text-anchor", t === 0 ? "start" : t === 1 ? "end" : "middle").text(pct(t, 0)));
    svg.append("text").attr("x", x(0.5)).attr("y", y + 22).attr("text-anchor", "middle").attr("class", "anno anno-muted").text(T.lShareValid);
    svg.attr("height", y + 30).attr("viewBox", `0 0 ${W} ${y + 30}`);
    host.replaceChildren(svg.node(), tip);
  }
  draw(); onResize(host, draw);
  table(document.getElementById("context-table"), T.ctxHead,
    dims.flatMap(([dim, title]) => g.filter((d) => d.dimension === dim).sort((a, b) => a.grp - b.grp)
      .map((d) => [`${title}: ${label[dim](d)}`, int(d.municipalities), pct(d.p50), T.to(pct(d.p10, 0), pct(d.p90, 0)), int(d.led_by_l), int(d.led_by_b)])));
}

// ---------- 7a. the turnaround as two balanced bars ----------
export async function bridge() {
  const stories = await getJSON("data/stories.json");
  const n = stories.turnaround2026.national;
  const host = document.getElementById("bridge");
  const top = [[T.thirdR1, n.others_r1, C.third], [T.moreTurnout, n.delta_turnout, C.absent], [T.fewerBlank, -n.delta_blank_null, C.blank]];
  const bottom = [[T.lGain, n.delta_l_votes, C.l], [T.bGain, n.delta_b_votes, C.b]];
  function draw() {
    const W = width(host), barH = 34;
    const total = d3.sum(top, (d) => d[1]);
    const x = d3.scaleLinear().domain([0, total]).range([0, W]);
    const frag = document.createDocumentFragment();
    for (const [title, parts] of [[T.bridgeTop, top], [T.bridgeBottom, bottom]]) {
      const h = document.createElement("p"); h.className = "chart-title"; h.style.fontSize = "0.9rem"; h.style.margin = "0 0 6px"; h.textContent = title;
      const svg = d3.create("svg").attr("width", W).attr("height", barH).attr("viewBox", `0 0 ${W} ${barH}`).attr("aria-hidden", "true");
      let x0 = 0;
      parts.forEach(([lab, v, col], i) => {
        const w = x(v);
        svg.append("rect").attr("x", x0 + (i ? 1 : 0)).attr("y", 0).attr("width", Math.max(1, w - (i ? 2 : 1))).attr("height", barH).attr("rx", 4).attr("fill", col)
          .append("title").text(`${lab}: ${votes(v)}`);
        x0 += w;
      });
      const leg = document.createElement("div"); leg.className = "bridge-legend";
      parts.forEach(([lab, v, col]) => {
        const d = document.createElement("div");
        const i = document.createElement("i"); i.style.background = col;
        const b = document.createElement("b"); b.textContent = votes(v);
        const s = document.createElement("span"); s.textContent = lab;
        d.append(i, b, s); leg.append(d);
      });
      frag.append(h, svg.node(), leg);
    }
    host.replaceChildren(frag);
  }
  draw(); onResize(host, draw);
}

// ---------- 7b. scatter: gains vs third candidates / turnout ----------
export async function scatter() {
  const [r1, r2, mun, stories] = await Promise.all([results(2026, 1), results(2026, 2), municipios(), getJSON("data/stories.json")]);
  const pts_ = [];
  for (let i = 0; i < mun.rows.length; i++) {
    const a = row(r1, i), b = row(r2, i); if (!a || !b) continue;
    pts_.push({ i, name: `${mun.rows[i][1]} (${mun.rows[i][2]})`, aptos: b.aptos,
      gl: b.l / b.aptos - a.l / a.aptos, gb: b.b / b.aptos - a.b / a.aptos,
      others: a.o / a.aptos, turnout: (b.aptos - b.ab) / b.aptos - (a.aptos - a.ab) / a.aptos });
  }
  const host = document.getElementById("scatter");
  const tip = document.getElementById("scatter-tip");
  let xKey = "others";
  const ctl = document.getElementById("scatter-controls");
  ctl.replaceChildren();
  segmented(ctl, T.xAxis, [["others", T.xThird], ["turnout", T.xTurnout]], xKey, (v) => { xKey = v; draw(); });
  const bins = stories.turnaround2026.bins;
  function draw() {
    const W = width(host), narrow = W < 640;
    const panelW = narrow ? W : (W - 24) / 2, panelH = narrow ? 260 : 320;
    const m = { t: 26, r: 10, b: 40, l: 44 };
    const xs = xKey === "others" ? [0, 0.16] : [-0.08, 0.08];
    const x = d3.scaleLinear().domain(xs).range([m.l, panelW - m.r]);
    const y = d3.scaleLinear().domain([-0.06, 0.14]).range([panelH - m.b, m.t]);
    const rs = d3.scaleSqrt().domain([0, 2e6]).range([0.8, 18]);
    const wrap = document.createElement("div");
    wrap.style.display = "grid"; wrap.style.gap = "16px"; wrap.style.gridTemplateColumns = narrow ? "1fr" : "1fr 1fr";
    const panels = [];
    for (const [who, key, col] of [["Lula", "gl", C.l], ["Flávio", "gb", C.b]]) {
      const p = document.createElement("div"); p.style.position = "relative";
      const cv = document.createElement("canvas"); const dpr = Math.min(2, window.devicePixelRatio || 1);
      cv.width = panelW * dpr; cv.height = panelH * dpr; cv.style.width = `${panelW}px`; cv.style.height = `${panelH}px`;
      const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
      ctx.strokeStyle = C.rule; ctx.lineWidth = 1;
      y.ticks(5).forEach((t) => { ctx.beginPath(); ctx.moveTo(m.l, y(t)); ctx.lineTo(panelW - m.r, y(t)); ctx.stroke(); });
      ctx.strokeStyle = C.ink; ctx.globalAlpha = 0.5; ctx.beginPath(); ctx.moveTo(m.l, y(0)); ctx.lineTo(panelW - m.r, y(0)); ctx.stroke(); ctx.globalAlpha = 1;
      const sorted = [...pts_].sort((a, b) => b.aptos - a.aptos);
      ctx.save(); ctx.beginPath(); ctx.rect(m.l, m.t, panelW - m.l - m.r, panelH - m.t - m.b); ctx.clip();
      ctx.fillStyle = col; ctx.globalAlpha = 0.28;
      for (const d of sorted) { ctx.beginPath(); ctx.arc(x(d[xKey]), y(d[key]), rs(d.aptos), 0, Math.PI * 2); ctx.fill(); }
      ctx.restore(); ctx.globalAlpha = 1;
      const out = pts_.filter((d) => d[xKey] < xs[0] || d[xKey] > xs[1] || d[key] < -0.06 || d[key] > 0.14).length;
      // weighted means by fifth of the x variable (from the pipeline)
      // fifths of municipalities (same grouping as the pipeline: by value, ties by IBGE code);
      // x = electorate-weighted mean of the group, y = the pipeline's weighted gain
      const bf = bins.filter((b) => b.factor === (xKey === "others" ? "others_r1_pts" : "turnout_change_pts")).sort((a, b) => a.quintile - b.quintile);
      const ordered = [...pts_].sort((a, b) => a[xKey] - b[xKey] || mun.rows[a.i][0] - mun.rows[b.i][0]);
      const per = ordered.length / 5;
      const gx = bf.map((b, k) => {
        const g = ordered.slice(Math.round(k * per), Math.round((k + 1) * per));
        return d3.sum(g, (d) => d[xKey] * d.aptos) / d3.sum(g, (d) => d.aptos);
      });
      const line = bf.map((b, k) => [x(gx[k]), y(key === "gl" ? b.gain_l_pts_weighted : b.gain_b_pts_weighted)]);
      ctx.strokeStyle = C.ink; ctx.lineWidth = 2; ctx.beginPath();
      line.forEach(([xx, yy], k) => (k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy)));
      ctx.stroke();
      line.forEach(([xx, yy]) => { ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(xx, yy, 4.5, 0, 7); ctx.fill(); ctx.strokeStyle = C.paper2; ctx.lineWidth = 2; ctx.stroke(); });
      const svg = d3.create("svg").attr("width", panelW).attr("height", panelH).style("position", "absolute").style("left", 0).style("top", 0).attr("aria-hidden", "true");
      if (out) svg.append("text").attr("x", panelW - m.r).attr("y", 14).attr("text-anchor", "end").attr("class", "anno anno-muted").text(T.offScale(int(out)));
      svg.append("text").attr("x", m.l).attr("y", 14).attr("class", "anno").style("font-weight", 650).text(T.changeOf(who));
      const ax = svg.append("g").attr("class", "axis");
      y.ticks(5).forEach((t) => ax.append("text").attr("x", m.l - 6).attr("y", y(t) + 4).attr("text-anchor", "end").text(`${t > 0 ? "+" : ""}${dec(t * 100, 0)}`));
      x.ticks(4).forEach((t) => ax.append("text").attr("x", x(t)).attr("y", panelH - m.b + 16).attr("text-anchor", "middle").text(`${xKey === "turnout" && t > 0 ? "+" : ""}${dec(t * 100, 0)}`));
      svg.append("text").attr("x", (m.l + panelW - m.r) / 2).attr("y", panelH - 6).attr("text-anchor", "middle").attr("class", "anno anno-muted")
        .text(xKey === "others" ? T.xLabelThird : T.xLabelTurnout);
      const hl = svg.append("circle").attr("r", 0).attr("fill", "none").attr("stroke", C.ink).attr("stroke-width", 2);
      p.append(cv, svg.node());
      wrap.appendChild(p);
      panels.push({ p, key, hl });
    }
    const qt = d3.quadtree().x((d) => x(d[xKey])).y((d) => y(d.gl)).addAll(pts_);
    const qtb = d3.quadtree().x((d) => x(d[xKey])).y((d) => y(d.gb)).addAll(pts_);
    panels.forEach(({ p, key }, k) => {
      const onMove = (ev) => {
        const r = p.getBoundingClientRect();
        const d = (k === 0 ? qt : qtb).find(ev.clientX - r.left, ev.clientY - r.top, 24);
        if (!d) { tip.classList.remove("on"); panels.forEach((q) => q.hl.attr("r", 0)); return; }
        panels.forEach((q) => q.hl.attr("cx", x(d[xKey])).attr("cy", y(d[q.key])).attr("r", rs(d.aptos) + 3));
        showTip(tip, host.parentElement, ev, tipNode(d.name, [[C.l, T.changeOf("Lula"), pts(d.gl, 1, true)], [C.b, T.changeOf("Flávio"), pts(d.gb, 1, true)],
          [C.third, T.thirdInR1, pct(d.others)], [C.absent, T.turnout, pts(d.turnout, 1, true)]], T.electorateN(int(d.aptos))));
      };
      p.addEventListener("pointermove", onMove);
      p.addEventListener("pointerdown", onMove);
      p.addEventListener("pointerleave", (e) => { if (e.pointerType === "touch") return; tip.classList.remove("on"); panels.forEach((q) => q.hl.attr("r", 0)); });
    });
    const note = document.createElement("p"); note.className = "chart-sub"; note.style.marginTop = "8px";
    note.textContent = T.fifthsNote;
    host.replaceChildren(wrap, note);
  }
  draw(); onResize(host, draw);
  table(document.getElementById("scatter-table"), T.fifthsHead,
    bins.map((b) => [T.fifthRow(b.factor === "others_r1_pts", b.quintile),
      b.factor === "others_r1_pts" ? T.to(pct(b.factor_min), pct(b.factor_max)) : T.to(pts(b.factor_min, 1, true), pts(b.factor_max, 1, true)),
      pts(b.gain_l_pts_weighted, 1, true), pts(b.gain_b_pts_weighted, 1, true)]));
}

// ---------- helpers ----------
export function ensureTip(host) {
  let t = host.querySelector(":scope > .tooltip");
  if (!t) { t = document.createElement("div"); t.className = "tooltip"; t.setAttribute("role", "status"); }
  if (getComputedStyle(host).position === "static") host.style.position = "relative";
  return t;
}
export function showTip(tip, host, ev, node) {
  tip.replaceChildren(node);
  const r = host.getBoundingClientRect();
  const px = ev.clientX - r.left, py = ev.clientY - r.top;
  const tw = tip.offsetWidth || 230, th = tip.offsetHeight || 100;
  let x = px + 14, y = py + 14;
  if (x + tw > r.width) x = Math.max(0, px - tw - 14);
  if (y + th > r.height) y = Math.max(0, py - th - 14);
  tip.style.left = `${x}px`; tip.style.top = `${y}px`; tip.classList.add("on");
}
export function onResize(el, fn) {
  let w = el.clientWidth, t;
  new ResizeObserver(() => { if (Math.abs(el.clientWidth - w) < 2) return; w = el.clientWidth; clearTimeout(t); t = setTimeout(fn, 150); }).observe(el);
}
function roundedTop(x, y, w, h, r) {
  if (h <= 0) return "";
  r = Math.min(r, w / 2, h);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}
function roundedRight(x, y, w, h, r) {
  r = Math.min(r, w, h / 2);
  return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`;
}
export { roundedRight };
