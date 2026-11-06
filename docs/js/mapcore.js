// Canvas map core: geometry (pre-projected TopoJSON), drawing, hit testing, tooltip placement.
import { getJSON, getBinary, municipios, C } from "./core.js";

let geoPromise = null;
const NEW_MUNICIPALITY = 5101837; // Boa Esperança do Norte (MT), votes from 2026 on

export function loadGeo() {
  if (geoPromise) return geoPromise;
  geoPromise = (async () => {
    const [topo, mun] = await Promise.all([getJSON("data/geo/municipios.topo.json"), municipios()]);
    const obj = topo.objects.municipios;
    const fc = topojson.feature(topo, obj);
    const path = d3.geoPath(d3.geoIdentity());
    const feats = fc.features.map((f) => {
      const p = new Path2D(path(f));
      const [[x0, y0], [x1, y1]] = path.bounds(f);
      return { id: +f.id, row: mun._idx.get(+f.id), path: p, x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
    });
    const ufMesh = new Path2D(path(topojson.mesh(topo, obj, (a, b) => a !== b && Math.floor(a.id / 1e5) !== Math.floor(b.id / 1e5))));
    const outline = new Path2D(path(topojson.mesh(topo, obj, (a, b) => a === b)));
    const [, , width, height] = topo.bbox;
    return { feats, ufMesh, outline, width, height, mun };
  })();
  return geoPromise;
}

export async function loadDots(year, round) {
  const [buf, index] = await Promise.all([getBinary(`data/dots/${year}-${round}.bin`), getJSON("data/dots/index.json")]);
  const n = index.files[`${year}-${round}`].n;
  const x = new Uint16Array(buf, 0, n);
  const y = new Uint16Array(buf, n * 2, n);
  const c = new Uint8Array(buf, n * 4, n);
  return { x, y, c, n, width: index.width, height: index.height };
}

export class CanvasMap {
  constructor(box, { fill, dots = null, hover = null, dark = true }) {
    this.box = box; this.fillC = fill; this.dotsC = dots; this.hoverC = hover; this.dark = dark;
    this.hitCtx = document.createElement("canvas").getContext("2d");
    this.colors = null;
    this.pattern = null;
  }
  async init() {
    this.geo = await loadGeo();
    this.resize();
    let t;
    new ResizeObserver(() => { clearTimeout(t); t = setTimeout(() => { this.resize(); this.redraw && this.redraw(); }, 120); }).observe(this.box);
    return this;
  }
  resize() {
    const w = this.box.clientWidth;
    const h = w * (this.geo.height / this.geo.width);
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.k = w / this.geo.width;
    for (const c of [this.fillC, this.dotsC, this.hoverC]) {
      if (!c) continue;
      c.width = Math.round(w * this.dpr); c.height = Math.round(h * this.dpr);
    }
    this.cssW = w; this.cssH = h;
  }
  hatch() {
    if (this.pattern) return this.pattern;
    const s = document.createElement("canvas"); s.width = s.height = 8;
    const g = s.getContext("2d");
    g.fillStyle = this.dark ? C.stage2 : C.paper2; g.fillRect(0, 0, 8, 8);
    g.strokeStyle = this.dark ? "#6b6672" : "#a59c90"; g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(0, 8); g.lineTo(8, 0); g.moveTo(-2, 2); g.lineTo(2, -2); g.moveTo(6, 10); g.lineTo(10, 6); g.stroke();
    this.pattern = this.fillC.getContext("2d").createPattern(s, "repeat");
    return this.pattern;
  }
  // colors: array aligned with geo.feats (CSS color strings or null = "no data")
  drawFills(colors, { borders = true, seams = true } = {}) {
    this.colors = colors;
    const ctx = this.fillC.getContext("2d");
    const s = this.k * this.dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.fillC.width, this.fillC.height);
    ctx.setTransform(s, 0, 0, s, 0, 0);
    ctx.lineJoin = "round";
    ctx.lineWidth = 0.6 / s; // closes anti-aliasing seams between neighbours
    const feats = this.geo.feats;
    for (let i = 0; i < feats.length; i++) {
      const col = colors[i];
      if (col === null) { ctx.fillStyle = this.hatch(); ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(s, s); ctx.fill(feats[i].path); ctx.restore(); continue; }
      ctx.fillStyle = col; ctx.fill(feats[i].path);
      if (seams) { ctx.strokeStyle = col; ctx.stroke(feats[i].path); }
    }
    if (borders) {
      ctx.strokeStyle = this.dark ? "rgba(23,22,28,0.85)" : "rgba(250,246,239,0.95)";
      ctx.lineWidth = 1.1 / s; ctx.stroke(this.geo.ufMesh);
    }
  }
  // Draws dots [from, to) without clearing (for the incremental reveal); drawDots draws them all.
  drawDots(d, opts = {}) {
    const ctx = this.dotsC.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.dotsC.width, this.dotsC.height);
    this.drawDotsRange(d, 0, d.n, opts);
  }
  drawDotsRange(d, from, to, { lColor = C.lGlow, bColor = C.bGlow } = {}) {
    const ctx = this.dotsC.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const W = this.dotsC.width, H = this.dotsC.height;
    const size = Math.max(1, Math.round(1.15 * this.dpr * Math.min(1.4, Math.max(0.8, this.cssW / 700))));
    const fx = W / 65535, fy = H / 65535;
    // Draw in the file's random order (never one color on top of the other) with a little
    // transparency, so dense places show the real blend of the two colors.
    ctx.globalAlpha = 0.82;
    let last = -1;
    for (let i = from; i < to; i++) {
      const c = d.c[i];
      if (c !== last) { ctx.fillStyle = c === 0 ? lColor : bColor; last = c; }
      ctx.fillRect(d.x[i] * fx, d.y[i] * fy, size, size);
    }
    ctx.globalAlpha = 1;
  }
  clearDots() {
    const ctx = this.dotsC.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, this.dotsC.width, this.dotsC.height);
  }
  // returns feature index under css pixel (px, py), or -1
  hit(px, py) {
    const ux = px / this.k, uy = py / this.k;
    const feats = this.geo.feats;
    for (let i = 0; i < feats.length; i++) {
      const f = feats[i];
      if (ux < f.x0 || ux > f.x1 || uy < f.y0 || uy > f.y1) continue;
      if (this.hitCtx.isPointInPath(f.path, ux, uy)) return i;
    }
    return -1;
  }
  highlight(i) {
    if (!this.hoverC) return;
    const ctx = this.hoverC.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.hoverC.width, this.hoverC.height);
    if (i < 0) return;
    const s = this.k * this.dpr;
    ctx.setTransform(s, 0, 0, s, 0, 0);
    ctx.lineJoin = "round";
    ctx.strokeStyle = this.dark ? "#ffffff" : C.ink; ctx.lineWidth = 2.2 / s;
    ctx.stroke(this.geo.feats[i].path);
    ctx.strokeStyle = this.dark ? C.stage : C.paper; ctx.lineWidth = 0.8 / s;
    ctx.stroke(this.geo.feats[i].path);
  }
  // Pointer + keyboard-free tooltip wiring. render(i) returns a DOM node for the tooltip.
  bindTooltip(target, tip, render) {
    let last = -1;
    this.refreshTip = () => { if (last >= 0 && tip.classList.contains("on")) tip.replaceChildren(render(last)); };
    const move = (ev) => {
      const r = target.getBoundingClientRect();
      const px = ev.clientX - r.left, py = ev.clientY - r.top;
      const i = this.hit(px, py);
      const changed = i !== last;
      if (changed) { this.highlight(i); last = i; }
      if (i < 0) { tip.classList.remove("on"); return; }
      if (changed || !tip.firstChild) tip.replaceChildren(render(i));
      const tw = tip.offsetWidth || 230, th = tip.offsetHeight || 120;
      let x = px + 14, y = py + 14;
      if (x + tw > r.width) x = Math.max(4, px - tw - 14);
      if (y + th > r.height) y = Math.max(4, py - th - 14);
      tip.style.left = `${x}px`; tip.style.top = `${y}px`;
      tip.classList.add("on");
    };
    const hide = () => { tip.classList.remove("on"); this.highlight(-1); last = -1; };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerdown", move);
    // a tap fires pointerleave right after pointerup: keep the tooltip on touch, hide on a tap elsewhere
    target.addEventListener("pointerleave", (e) => { if (e.pointerType !== "touch") hide(); });
    document.addEventListener("pointerdown", (e) => { if (!target.contains(e.target)) hide(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  }
}

export function isNewMunicipality(id, year) { return id === NEW_MUNICIPALITY && year < 2026; }

// Small tooltip builder (textContent only).
export function tipNode(title, rows, note) {
  const d = document.createElement("div");
  const t = document.createElement("div"); t.className = "t-name"; t.textContent = title; d.appendChild(t);
  for (const [color, label, value] of rows) {
    const r = document.createElement("div"); r.className = "t-row";
    const i = document.createElement("i"); i.style.background = color || "transparent";
    const l = document.createElement("span"); l.textContent = label;
    const v = document.createElement("b"); v.textContent = value;
    r.append(i, l, v); d.appendChild(r);
  }
  if (note) { const n = document.createElement("div"); n.className = "t-note"; n.textContent = note; d.appendChild(n); }
  return d;
}
