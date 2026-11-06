// Shared helpers: data loading (cached), formatting (pt-BR), colors and labels.

const cache = new Map();
export function getJSON(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(path).then((r) => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.json();
    }));
  }
  return cache.get(path);
}
export function getBinary(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(path).then((r) => {
      if (!r.ok) throw new Error(`${path}: ${r.status}`);
      return r.arrayBuffer();
    }));
  }
  return cache.get(path);
}

export const ELECTIONS = [[2014, 1], [2014, 2], [2018, 1], [2018, 2], [2022, 1], [2022, 2], [2026, 1], [2026, 2]];
export const NAMES = {
  2014: { L: "Dilma", B: "Aécio" },
  2018: { L: "Haddad", B: "Bolsonaro" },
  2022: { L: "Lula", B: "Bolsonaro" },
  2026: { L: "Lula", B: "Flávio" },
};
export const FULLNAMES = {
  2014: { L: "Dilma Rousseff", B: "Aécio Neves" },
  2018: { L: "Fernando Haddad", B: "Jair Bolsonaro" },
  2022: { L: "Lula", B: "Jair Bolsonaro" },
  2026: { L: "Lula", B: "Flávio Bolsonaro" },
};
export const REGION_NAMES = { 1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste" };

// Colors: identical meaning everywhere on the page.
export const C = {
  l: "#6a4c9c", b: "#b8741a", lInk: "#553a85", bInk: "#85520f",
  lGlow: "#a68be6", bGlow: "#cc8f3e",         // marks on the dark stage
  lStage: "#9273d2", bStage: "#c08032",       // fills on the dark stage
  mix: "#e9c3c4",
  third: "#5f748c", blank: "#cfc6b8", absent: "#9a9186", absentLine: "#847c71", thirdStage: "#d0c9be",
  paper: "#faf6ef", paper2: "#f2ece2", ink: "#1e1a16", ink2: "#463f38", muted: "#6b635a", rule: "#ddd4c7",
  stage: "#17161c", stage2: "#221f28", stageInk: "#eee8df", stageMuted: "#a9a298", stageRule: "#36333d",
  neutral: "#d6cfc4",
};

// Proportion scale (share of the L camp among the two camps): the middle is the mixture.
export function shareScale(dark = true) {
  const lo = dark ? C.bStage : C.b, hi = dark ? C.lStage : C.l;
  return d3.scaleLinear().domain([0.15, 0.5, 0.85]).range([lo, C.mix, hi])
    .interpolate(d3.interpolateLab).clamp(true);
}
// Change scale (difference in points, as a fraction): the middle is "no change" (neutral).
export function changeScale(max) {
  return d3.scaleLinear().domain([-max, 0, max]).range([C.b, C.neutral, C.l])
    .interpolate(d3.interpolateLab).clamp(true);
}

// ---- formatting (pt-BR) ----
const MINUS = "−";
const fInt = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
export const int = (n) => fInt.format(Math.round(n)).replace("-", MINUS);
export function dec(x, d = 1) {
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }).format(x).replace("-", MINUS);
}
export const pct = (x, d = 1) => `${dec(x * 100, d)}%`;
export function pts(x, d = 1, signed = false) {
  const v = Math.round(x * 100 * 10 ** d) / 10 ** d + 0;
  const s = signed && v > 0 ? "+" : "";
  return `${s}${dec(v, d)} ${Math.abs(v) < 2 ? "ponto" : "pontos"}`;
}
export function votes(n) {
  const a = Math.abs(n);
  if (a >= 1e6) {
    const v = Math.round(n / 1e5) / 10;
    return `${dec(v, 1)} ${Math.abs(v) < 2 ? "milhão" : "milhões"}`;
  }
  if (a >= 1e4) return `${int(n / 1e3)} mil`;
  return int(n);
}
export function norm(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();
}

export const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ---- data access ----
export async function municipios() {
  const m = await getJSON("data/municipios.json");
  if (!m._idx) {
    m._idx = new Map(m.rows.map((r, i) => [r[0], i]));
  }
  return m;
}
export const results = (y, r) => getJSON(`data/results/${y}-${r}.json`);

// one municipality, one election: counts by category
export function row(res, i) {
  const l = res.l[i];
  if (l === null || l === undefined) return null;
  const o = { l, b: res.b[i], o: res.o[i], bn: res.bn[i], ab: res.ab[i] };
  o.aptos = o.l + o.b + o.o + o.bn + o.ab;
  o.valid = o.l + o.b + o.o;
  o.ot = res.ot ? res.ot[i] : 0;
  o.on = res.on ? res.on[i] : null;
  return o;
}
export function leader(r) {
  if (!r) return null;
  const best = Math.max(r.l, r.b, r.ot || 0);
  const winners = [r.l === best && "L", r.b === best && "B", (r.ot || 0) === best && "O"].filter(Boolean);
  return winners.length === 1 ? winners[0] : "tie";
}

// Inline table for the "table view" twin of each chart.
export function table(container, head, rows) {
  const t = document.createElement("table");
  const thead = t.createTHead().insertRow();
  head.forEach((h) => { const th = document.createElement("th"); th.scope = "col"; th.textContent = h; thead.appendChild(th); });
  const tb = t.createTBody();
  rows.forEach((r) => {
    const tr = tb.insertRow();
    r.forEach((c, i) => {
      if (i === 0) { const th = document.createElement("th"); th.scope = "row"; th.textContent = c; tr.appendChild(th); }
      else tr.insertCell().textContent = c;
    });
  });
  container.replaceChildren(t);
  container.tabIndex = 0;
  container.setAttribute("role", "region");
  const fig = container.closest("figure");
  const title = fig && fig.querySelector(".chart-title");
  container.setAttribute("aria-label", `Tabela: ${title ? title.textContent : head.join(", ")}`);
}

// Segmented control (buttons with aria-pressed).
export function segmented(container, label, options, value, onChange) {
  const wrap = document.createElement("div");
  wrap.style.display = "inline-flex"; wrap.style.alignItems = "center"; wrap.style.gap = "6px 8px"; wrap.style.flexWrap = "wrap";
  const lab = document.createElement("span"); lab.className = "seg-label"; lab.textContent = label; lab.id = `seg-${Math.random().toString(36).slice(2, 8)}`;
  const seg = document.createElement("div"); seg.className = "seg"; seg.setAttribute("role", "group"); seg.setAttribute("aria-labelledby", lab.id);
  const buttons = options.map(([val, text]) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = text; b.dataset.value = val;
    b.setAttribute("aria-pressed", String(val === value));
    b.addEventListener("click", () => { set(val); onChange(val); });
    seg.appendChild(b); return b;
  });
  function set(v) { buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.value === String(v)))); }
  wrap.append(lab, seg); container.appendChild(wrap);
  return { set, buttons };
}

// Run fn once when el gets close to the viewport.
export function whenNear(el, fn, margin = "600px") {
  if (!("IntersectionObserver" in window)) { fn(); return; }
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { io.disconnect(); fn(); }
  }, { rootMargin: margin });
  io.observe(el);
}
