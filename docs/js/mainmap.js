// The scrollytelling map: winner -> proportion -> dots, then free exploration.
import { C, NAMES, FULLNAMES, T, results, row, leader, shareScale, segmented, int, pct, votes, reducedMotion, getJSON } from "./core.js";
import { CanvasMap, loadDots, isNewMunicipality, tipNode } from "./mapcore.js";

const MODES = [["winner", T.modes.winner], ["share", T.modes.share], ["dots", T.modes.dots]];
const STEP_STATE = [
  { year: 2026, round: 2, mode: "winner" },
  { year: 2026, round: 2, mode: "winner" },
  { year: 2026, round: 2, mode: "share" },
  { year: 2026, round: 2, mode: "dots" },
  { year: 2026, round: 2, mode: "dots" },
  null, // free exploration: keep whatever the reader chose
  null,
];

export async function initMainMap() {
  const box = document.getElementById("mainmap");
  const fill = document.getElementById("map-fill");
  const dotsC = document.getElementById("map-dots");
  const hover = document.getElementById("map-hover");
  const tip = document.getElementById("map-tip");
  const legend = document.getElementById("map-legend");
  const caption = document.getElementById("map-caption");
  const controls = document.getElementById("map-controls");
  const map = await new CanvasMap(box, { fill, dots: dotsC, hover, dark: true }).init();
  const feats = map.geo.feats;
  const scale = shareScale(true);
  const index = await getJSON("data/dots/index.json");

  const state = { year: 2026, round: 2, mode: "winner" };
  let current = null;        // colors currently drawn
  let anim = null;
  let res = null;
  let dots = null, dotsKey = null, dotsRaf = null, seq = 0;

  function colorFor(r, mode) {
    if (!r) return null;
    if (mode === "winner") {
      const w = leader(r);
      return w === "L" ? C.lStage : w === "B" ? C.bStage : w === "O" ? C.thirdStage : C.mix;
    }
    if (mode === "share") return scale(r.l / (r.l + r.b));
    return C.stage2; // dots: quiet base
  }

  function targetColors() {
    return feats.map((f) => {
      if (isNewMunicipality(f.id, state.year)) return null;
      return colorFor(row(res, f.row), state.mode);
    });
  }

  function paint(target) {
    if (anim) cancelAnimationFrame(anim);
    if (!current || reducedMotion()) { current = target; map.drawFills(target, { seams: state.mode !== "dots" }); return; }
    const from = current;
    const interp = target.map((t, i) => (t && from[i] ? d3.interpolateRgb(from[i], t) : null));
    const t0 = performance.now(), dur = 650;
    const frame = (now) => {
      const k = d3.easeCubicInOut(Math.min(1, (now - t0) / dur));
      const cols = interp.map((f, i) => (f ? f(k) : target[i]));
      map.drawFills(cols, { seams: state.mode !== "dots" });
      if (k < 1) anim = requestAnimationFrame(frame); else { current = target; anim = null; }
    };
    anim = requestAnimationFrame(frame);
  }

  async function showDots(my) {
    const key = `${state.year}-${state.round}`;
    const d = await loadDots(state.year, state.round);
    if (my !== seq || state.mode !== "dots") return;   // a newer request won
    if (dotsRaf) cancelAnimationFrame(dotsRaf);
    dots = d; dotsKey = key;
    dotsC.style.opacity = 1;
    if (reducedMotion()) { map.drawDots(d); return; }
    map.clearDots();
    const t0 = performance.now(), dur = 900;
    let drawn = 0;
    const frame = (now) => {
      if (my !== seq) return;
      const k = Math.min(1, (now - t0) / dur);
      const upto = Math.floor(d.n * d3.easeQuadOut(k));
      map.drawDotsRange(d, drawn, upto); drawn = upto;   // only the new dots each frame
      dotsRaf = k < 1 ? requestAnimationFrame(frame) : null;
    };
    dotsRaf = requestAnimationFrame(frame);
  }

  async function update() {
    const my = ++seq;
    const r = await results(state.year, state.round);
    if (my !== seq) return;                 // a newer click or step already took over
    res = r;
    paint(targetColors());
    if (map.refreshTip) map.refreshTip();
    if (state.mode === "dots") showDots(my); else { if (dotsRaf) cancelAnimationFrame(dotsRaf); dotsC.style.opacity = 0; }
    renderLegend();
    renderCaption();
    ctl.year.set(state.year); ctl.round.set(state.round); ctl.mode.set(state.mode);
  }
  map.redraw = () => { if (current) map.drawFills(current, { seams: state.mode !== "dots" }); if (state.mode === "dots" && dots) map.drawDots(dots); };

  function key(color, label, ring = false) {
    const s = document.createElement("span"); s.className = "key";
    const i = document.createElement("i"); i.style.background = color; if (ring) i.className = "ring";
    s.append(i, document.createTextNode(label)); return s;
  }
  function renderLegend() {
    const n = NAMES[state.year];
    const wrap = document.createElement("div");
    if (state.mode === "winner") {
      const l = document.createElement("div"); l.className = "legend";
      l.append(key(C.lStage, T.won(n.L)), key(C.bStage, T.won(n.B)));
      if (state.round === 1 && (state.year === 2014 || state.year === 2018)) l.append(key(C.thirdStage, T.otherWon));
      if (state.year < 2026) l.append(key("repeating-linear-gradient(135deg,#6b6672 0 2px,#221f28 2px 5px)", T.notInstalled));
      wrap.append(l);
    } else if (state.mode === "share") {
      const g = document.createElement("div"); g.className = "grad";
      g.style.background = `linear-gradient(90deg, ${d3.range(0, 1.001, 0.1).map((t) => scale(0.15 + t * 0.7)).join(",")})`;
      const labels = document.createElement("div"); labels.className = "grad-labels";
      for (const t of [T.orMore(n.B), T.half, T.orMore(n.L)]) { const s = document.createElement("span"); s.textContent = t; labels.append(s); }
      const sub = document.createElement("p"); sub.className = "chart-sub"; sub.style.margin = "6px 0 0"; sub.style.fontSize = "0.78rem";
      sub.textContent = T.shareSub;
      wrap.append(g, labels, sub);
    } else {
      const l = document.createElement("div"); l.className = "legend";
      const f = index.files[`${state.year}-${state.round}`];
      l.append(key(C.lGlow, `${n.L}`), key(C.bGlow, `${n.B}`));
      const s = document.createElement("span"); s.textContent = T.perDot(int(index.votes_per_dot)); s.style.color = C.stageMuted;
      l.append(s);
      wrap.append(l);
      if (f) wrap.dataset.n = f.n;
    }
    legend.replaceChildren(wrap);
  }
  function renderCaption() {
    const n = FULLNAMES[state.year];
    const text = T.caption(state.year, state.round, n.L, n.B);
    if (caption.textContent !== text) caption.textContent = text;
  }

  // controls (live inside the sticky panel)
  const ctl = {};
  ctl.year = segmented(controls, T.year, [[2014, "2014"], [2018, "2018"], [2022, "2022"], [2026, "2026"]], state.year, (v) => { state.year = +v; update(); });
  ctl.round = segmented(controls, T.round, [[1, T.roundBtn(1)], [2, T.roundBtn(2)]], state.round, (v) => { state.round = +v; update(); });
  ctl.mode = segmented(controls, T.map, MODES, state.mode, (v) => { state.mode = v; update(); });

  // tooltip
  map.bindTooltip(box, tip, (i) => {
    const f = feats[i];
    const m = map.geo.mun.rows[f.row];
    const title = `${m[1]} (${m[2]})`;
    if (isNewMunicipality(f.id, state.year)) {
      return tipNode(title, [], T.tipNew);
    }
    const r = row(res, f.row);
    if (!r) return tipNode(title, [], T.tipNone);
    const n = NAMES[state.year];
    const rows = [[C.lStage, n.L, `${pct(r.l / r.valid)} · ${int(r.l)}`], [C.bStage, n.B, `${pct(r.b / r.valid)} · ${int(r.b)}`]];
    if (state.round === 1) rows.push([C.third, T.others, `${pct(r.o / r.valid)} · ${int(r.o)}`]);
    rows.push([C.blank, T.blankNull, int(r.bn)], [C.absent, T.absent, int(r.ab)]);
    return tipNode(title, rows, T.tipNote(state.year, state.round));
  });

  await update();
  loadDots(2026, 2).catch(() => {});   // prefetch the layer used by the scrollytelling

  // scrollytelling
  if (window.scrollama) {
    const scroller = scrollama();
    // the cards (not the tall step boxes) trigger the changes, so the map switches when its text arrives
    scroller.setup({ step: "#scrolly .step .card", offset: 0.65 }).onStepEnter(({ index: i }) => {
      const s = STEP_STATE[i];
      if (!s) return;
      if (s.year !== state.year || s.round !== state.round || s.mode !== state.mode) {
        Object.assign(state, s); update();
      }
    });
    window.addEventListener("resize", () => scroller.resize());
  }
  return { map, state };
}
