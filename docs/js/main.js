// Entry point: each chapter loads its data only when the reader gets close to it.
import { C, getJSON, results, municipios, row, whenNear, reducedMotion } from "./core.js";
import { peopleSVG } from "./people.js";

const $ = (id) => document.getElementById(id);
const safe = (fn) => async () => { try { await fn(); } catch (e) { console.error(e); } };

hero();

whenNear($("pergunta"), safe(async () => { const m = await import("./charts.js"); await m.minorityBar(); }));
whenNear($("tres-eleicoes"), safe(async () => { const m = await import("./charts.js"); await m.nationalBars(); }));
whenNear($("mapa"), safe(async () => { const m = await import("./mainmap.js"); await m.initMainMap(); }), "1200px");
whenNear($("bolha"), safe(async () => {
  const m = await import("./charts.js");
  await Promise.all([m.histogram(), m.regions(), m.context(), extremes()]);
}));
for (const key of ["2018", "2022", "2026"]) {
  whenNear($(`map-${key}`), safe(async () => { const m = await import("./changemaps.js"); await m.changeMap(key); }));
}
whenNear($("bridge"), safe(async () => { const m = await import("./charts.js"); await Promise.all([m.bridge(), m.scatter()]); }));
let cityReady = null;
const loadCity = () => (cityReady ??= import("./city.js").then((m) => m.initCity()));
whenNear($("sua-cidade"), safe(loadCity));
// deep link: #cidade-<IBGE code> opens the city view directly
async function deepLink() {
  const m = location.hash.match(/^#cidade-(\d{7})$/);
  if (!m) return;
  const api = await loadCity();
  await api.showById(+m[1]);
  $("sua-cidade").scrollIntoView();
}
deepLink().catch(console.error);
window.addEventListener("hashchange", () => deepLink().catch(console.error));

async function extremes() {
  const [stories, res, mun] = await Promise.all([getJSON("data/stories.json"), results(2026, 2), municipios()]);
  for (const [kind, id] of [["most_l", "people-most-l"], ["most_b", "people-most-b"]]) {
    const e = stories.extremes.find((d) => d.year === 2026 && d.round === 2 && d.kind === kind);
    const r = row(res, mun._idx.get(e.cd_ibge));
    const { svg } = peopleSVG(r, { size: 180, title: `${e.name} (${e.uf}), 2º turno de 2026`, names: { L: "Lula", B: "Flávio" } });
    $(id).replaceChildren(svg);
  }
}

// Decorative opening: two colors drifting into each other. Static if the reader prefers less motion.
function hero() {
  const cv = $("hero-canvas");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  let W, H, dots = [], raf = null, visible = true;
  let seed = 20261025;
  const rand = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
  function setup() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round(Math.min(2600, (W * H) / 420));
    seed = 20261025;
    dots = d3.range(n).map(() => {
      const x = rand() * W, y = rand() * H;
      // soft patches of each color that blend into each other (no left/right meaning)
      const p = 0.5 + 0.32 * Math.sin((x / W) * 5.1 + 1.3) * Math.cos((y / H) * 4.3 - 0.7) + (rand() - 0.5) * 0.45;
      return { x, y, c: rand() < p ? 1 : 0, r: 1 + rand() * 2.2, vx: (rand() - 0.5) * 0.14, vy: (rand() - 0.5) * 0.14 };
    });
  }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const d of dots) {
      ctx.fillStyle = d.c ? C.bGlow : C.lGlow;
      ctx.globalAlpha = 0.7;
      ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, 7); ctx.fill();
    }
    ctx.globalAlpha = 1;
    const g = ctx.createLinearGradient(0, H * 0.35, 0, H);
    g.addColorStop(0, "rgba(23,22,28,0)"); g.addColorStop(1, "rgba(23,22,28,0.92)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  function tick() {
    for (const d of dots) {
      d.x += d.vx; d.y += d.vy;
      if (d.x < 0) d.x += W; if (d.x > W) d.x -= W; if (d.y < 0) d.y += H; if (d.y > H) d.y -= H;
    }
    draw();
    raf = visible ? requestAnimationFrame(tick) : null;
  }
  setup(); draw();
  if (!reducedMotion()) {
    new IntersectionObserver((e) => { visible = e[0].isIntersecting; if (visible && !raf) raf = requestAnimationFrame(tick); }).observe(cv);
  }
  let t; window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { setup(); draw(); }, 200); });
}
