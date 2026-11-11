// Entry point: each chapter loads its data only when the reader gets close to it.
import { C, T, getJSON, results, municipios, row, whenNear, reducedMotion } from "./core.js";
import { peopleSVG } from "./people.js";

const $ = (id) => document.getElementById(id);
const SECTIONS = ["pergunta", "tres-eleicoes", "mapa", "bolha", "em-2018", "em-2022", "em-2026", "sua-cidade", "metodo"];  // chapters, in order
const safe = (fn) => async () => { try { await fn(); } catch (e) { console.error(e); } };

hero();
shareButton();
langSwitch();
restorePosition();

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
  if (!m) {
    if (cityReady) (await cityReady).showAll();   // the city left the address: back to Brazil
    return;
  }
  const api = await loadCity();
  await api.showById(+m[1]);
  $("sua-cidade").scrollIntoView();
}
deepLink().catch(console.error);
window.addEventListener("hashchange", () => deepLink().catch(console.error));

// ---- share: native sheet on touch devices, a small menu elsewhere ----
function shareButton() {
  const btn = $("share-btn"), menu = $("share-menu"), status = $("share-status");
  if (!btn) return;
  const canon = document.querySelector('link[rel="canonical"]');
  const url = canon ? canon.href : location.href.split("#")[0];
  const title = btn.dataset.shareTitle, text = btn.dataset.shareText;
  const enc = encodeURIComponent;
  const links = {
    whatsapp: `https://wa.me/?text=${enc(`${text} ${url}`)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${enc(url)}`,
    x: `https://twitter.com/intent/tweet?text=${enc(text)}&url=${enc(url)}`,
  };
  menu.querySelectorAll("a[data-net]").forEach((a) => { a.href = links[a.dataset.net]; });
  const label = btn.querySelector(".share-label"), original = label.textContent;
  const open = (v) => {
    menu.hidden = !v; btn.setAttribute("aria-expanded", String(v));
    if (v) menu.querySelector(".share-item").focus();
  };
  const touch = window.matchMedia("(pointer: coarse)").matches;
  btn.addEventListener("click", async () => {
    if (touch && navigator.share) {
      try { await navigator.share({ title, text, url }); } catch (e) { /* closed by the reader */ }
      return;
    }
    open(menu.hidden);
  });
  menu.querySelector('[data-net="copy"]').addEventListener("click", async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(url); ok = true; } catch (e) { /* not allowed */ }
    open(false); btn.focus();
    if (ok) {
      label.textContent = T.linkCopied; status.textContent = T.linkCopied;
      setTimeout(() => { label.textContent = original; }, 2200);
    } else {
      status.textContent = `${T.copyFailed} ${url}`;
      window.prompt(T.copyFailed, url);
    }
  });
  menu.querySelectorAll("a[data-net]").forEach((a) => a.addEventListener("click", () => open(false)));
  document.addEventListener("pointerdown", (e) => { if (!menu.hidden && !$("hero-actions").contains(e.target)) open(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { open(false); btn.focus(); } });
}

// ---- language switch: always reachable, keeps the reader at the same point of the story ----

function langSwitch() {
  const nav = document.querySelector(".lang-switch");
  if (!nav) return;
  const link = nav.querySelector("a[hreflang]");
  link.addEventListener("click", (e) => {
    const line = innerHeight * 0.3;
    let cur = null, ratio = 0;
    for (const id of SECTIONS) {
      const el = $(id);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.top <= line) { cur = id; ratio = Math.min(1, Math.max(0, (line - r.top) / r.height)); }
    }
    if (!cur) return;                       // still at the opening: plain link
    e.preventDefault();
    const url = new URL(link.href, location.href);
    url.searchParams.set("s", cur);
    url.searchParams.set("p", ratio.toFixed(4));
    if (/^#cidade-\d{7}$/.test(location.hash)) url.hash = location.hash;
    location.href = url.toString();
  });
  // hide while reading down, show again when the reader scrolls up or reaches the top
  let lastY = scrollY;
  addEventListener("scroll", () => {
    const y = scrollY;
    if (y < 120 || y < lastY - 6) nav.classList.remove("is-hidden");
    else if (y > lastY + 6) nav.classList.add("is-hidden");
    lastY = y;
  }, { passive: true });
}

// Arriving from the other language: go back to the same section and relative position.
function restorePosition() {
  const q = new URLSearchParams(location.search);
  const id = q.get("s");
  if (!id || !SECTIONS.includes(id) || !$(id)) return;
  const p = Math.min(1, Math.max(0, parseFloat(q.get("p")) || 0));
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  let moved = false;
  for (const ev of ["wheel", "touchstart", "keydown", "pointerdown"]) addEventListener(ev, () => { moved = true; }, { once: true, passive: true });
  const go = () => {
    if (moved) return;
    const el = $(id);
    const top = el.getBoundingClientRect().top + scrollY;
    scrollTo({ top: Math.max(0, top + p * el.offsetHeight - innerHeight * 0.3), behavior: "instant" });
  };
  // charts above load lazily and change the page height: re-anchor a few times until the reader takes over
  go();
  for (const t of [200, 600, 1200, 2200, 3500]) setTimeout(go, t);
  const clean = new URL(location.href);
  clean.searchParams.delete("s"); clean.searchParams.delete("p");
  history.replaceState(null, "", clean.pathname + clean.search + clean.hash);
}

async function extremes() {
  const [stories, res, mun] = await Promise.all([getJSON("data/stories.json"), results(2026, 2), municipios()]);
  for (const [kind, id] of [["most_l", "people-most-l"], ["most_b", "people-most-b"]]) {
    const e = stories.extremes.find((d) => d.year === 2026 && d.round === 2 && d.kind === kind);
    const r = row(res, mun._idx.get(e.cd_ibge));
    const { svg } = peopleSVG(r, { size: 180, title: T.extremeTitle(`${e.name} (${e.uf})`), names: { L: "Lula", B: "Flávio" } });
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
