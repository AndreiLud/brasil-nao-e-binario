// "Sua cidade": accessible combobox search + 100-voter profiles for every election.
import { C, NAMES, REGION_NAMES, ELECTIONS, T, results, municipios, row, getJSON, norm, int, pct } from "./core.js";
import { peopleSVG } from "./people.js";

const SPLIT = T.split;

export async function initCity() {
  const mun = await municipios();
  const input = document.getElementById("city-input");
  const list = document.getElementById("city-list");
  const out = document.getElementById("city-out");
  const idx = mun.rows.map((r, i) => ({ i, id: r[0], name: r[1], uf: r[2], key: norm(r[1]), pop: r[4] }));
  let options = [], active = -1;

  function search(q) {
    const k = norm(q);
    if (k.length < 2) return [];
    const starts = [], contains = [];
    for (const m of idx) {
      if (m.key.startsWith(k)) starts.push(m); else if (m.key.includes(k)) contains.push(m);
    }
    const byPop = (a, b) => b.pop - a.pop;
    return [...starts.sort(byPop), ...contains.sort(byPop)].slice(0, 8);
  }
  function renderList() {
    list.replaceChildren();
    options.forEach((m, j) => {
      const li = document.createElement("li");
      li.id = `city-opt-${j}`; li.setAttribute("role", "option"); li.setAttribute("aria-selected", String(j === active));
      const n = document.createElement("span"); n.textContent = m.name;
      const s = document.createElement("small"); s.textContent = m.uf;
      li.append(n, s);
      li.addEventListener("pointerdown", (e) => { e.preventDefault(); choose(m); });
      list.appendChild(li);
    });
    const open = options.length > 0;
    list.hidden = !open; input.setAttribute("aria-expanded", String(open));
    if (active >= 0) {
      input.setAttribute("aria-activedescendant", `city-opt-${active}`);
      const el = document.getElementById(`city-opt-${active}`); if (el) el.scrollIntoView({ block: "nearest" });
    } else input.removeAttribute("aria-activedescendant");
  }
  const status = document.getElementById("city-status");
  const clearBtn = document.createElement("button");
  clearBtn.type = "button"; clearBtn.className = "city-clear"; clearBtn.hidden = true;
  clearBtn.setAttribute("aria-label", T.clearSearch); clearBtn.title = T.clearSearch;
  clearBtn.textContent = "\u00d7";
  input.after(clearBtn);
  const updateClear = () => { clearBtn.hidden = !input.value; };
  input.addEventListener("input", updateClear);
  clearBtn.addEventListener("click", () => { showAll(); input.focus(); });
  // Back to the national view: empty search, no city in the address (so a reload shows Brazil too).
  async function showAll() {
    input.value = ""; options = []; active = -1; renderList(); updateClear();
    await profile(null);
    status.textContent = T.showingAll;
    if (/^#cidade-/.test(location.hash)) {
      try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* ignore */ }
    }
  }
  input.addEventListener("input", () => {
    options = search(input.value); active = options.length ? 0 : -1; renderList();
    const q = input.value.trim();
    if (q.length >= 2 && !options.length) {
      const li = document.createElement("li"); li.setAttribute("role", "option"); li.setAttribute("aria-disabled", "true");
      li.textContent = T.noMatch; list.replaceChildren(li); list.hidden = false;
      status.textContent = T.noMatchFor(q);
    }
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && !options.length && input.value.trim().length >= 2) { options = search(input.value); active = options.length ? 0 : -1; renderList(); e.preventDefault(); }
    else if (e.key === "ArrowDown" && options.length) { active = (active + 1) % options.length; renderList(); e.preventDefault(); }
    else if (e.key === "ArrowUp" && options.length) { active = (active - 1 + options.length) % options.length; renderList(); e.preventDefault(); }
    else if (e.key === "Enter" && active >= 0) { choose(options[active]); e.preventDefault(); }
    else if (e.key === "Escape") { options = []; active = -1; renderList(); }
  });
  input.addEventListener("blur", () => setTimeout(() => { options = []; renderList(); }, 150));

  async function choose(m) {
    input.value = `${m.name} (${m.uf})`;
    options = []; active = -1; renderList(); updateClear();
    await profile(m);
    status.textContent = T.showing(`${m.name} (${m.uf})`);
    try { history.replaceState(null, "", `#cidade-${m.id}`); } catch (e) { /* ignore */ }
  }

  async function profile(m) {
    const all = m ? await Promise.all(ELECTIONS.map(([y, r]) => results(y, r))) : null;
    const frag = document.createDocumentFragment();
    const h = document.createElement("h3"); h.className = "city-name"; h.textContent = m ? m.name : T.allBrazil;
    const meta = document.createElement("p"); meta.className = "city-meta";
    if (m) {
      const r = mun.rows[m.i];
      meta.textContent = T.cityMeta(m.uf, REGION_NAMES[r[3]], int(r[4]));
    } else meta.textContent = T.allMeta;
    frag.append(h, meta);
    if (m) {
      const back = document.createElement("button");
      back.type = "button"; back.className = "city-back"; back.textContent = `\u2190 ${T.backToBrazil}`;
      back.addEventListener("click", () => { showAll(); input.focus(); });
      frag.append(back);
    }
    if (m && SPLIT[m.id]) { const n = document.createElement("p"); n.className = "city-note"; n.textContent = SPLIT[m.id]; frag.append(n); }
    const legend = document.createElement("div"); legend.className = "legend";
    for (const [col, lab, ring] of [[C.l, T.campLLegend], [C.b, T.campBLegend], [C.third, T.others], [C.blank, T.blankNull], [null, T.absent, true]]) {
      const s = document.createElement("span"); s.className = "key";
      const i = document.createElement("i"); if (ring) i.className = "ring"; else i.style.background = col;
      s.append(i, document.createTextNode(lab)); legend.append(s);
    }
    frag.append(legend);
    const grid = document.createElement("div"); grid.className = "city-grid";
    const nat = m ? null : (await getJSON("data/national.json")).national;
    for (const year of [2026, 2022, 2018, 2014]) {
      const box = document.createElement("div"); box.className = "city-year";
      const t = document.createElement("h4");
      t.textContent = T.yearHead(year, NAMES[year].L, NAMES[year].B);
      const rounds = document.createElement("div"); rounds.className = "rounds";
      for (const rnd of [1, 2]) {
        const k = ELECTIONS.findIndex(([y, r]) => y === year && r === rnd);
        let rr;
        if (m) rr = row(all[k], m.i);
        else { const n = nat.find((d) => d.year === year && d.round === rnd); rr = { l: n.camp_l, b: n.camp_b, o: n.others, bn: n.blank_null, ab: n.absent }; }
        const cell = document.createElement("div");
        const lab = document.createElement("div"); lab.className = "round-label"; lab.textContent = T.roundShort(rnd);
        cell.append(lab);
        if (!rr) { const p = document.createElement("p"); p.className = "city-meta"; p.textContent = T.notInstalledDot; cell.append(p); }
        else {
          const { svg, counts } = peopleSVG(rr, { size: 150, title: `${m ? m.name : T.brazil}, ${T.roundOf(year, rnd)}`, names: NAMES[year] });
          const c = document.createElement("div"); c.className = "counts";
          const parts = [[NAMES[year].L, counts.l], [NAMES[year].B, counts.b]];
          if (rnd === 1) parts.push([T.othersShort, counts.o]);
          parts.push([T.blankNullShort, counts.bn], [T.absent, counts.ab]);
          parts.forEach(([n, v]) => { const s = document.createElement("span"); s.textContent = `${n} ${v}`; c.append(s); });
          cell.append(svg, c);
        }
        rounds.append(cell);
      }
      box.append(t, rounds); grid.append(box);
    }
    frag.append(grid);
    out.replaceChildren(frag);
  }

  // deep link #cidade-<ibge>
  async function showById(id) {
    const m = idx.find((x) => x.id === id);
    if (!m) return false;
    input.value = `${m.name} (${m.uf})`; updateClear();
    await profile(m);
    status.textContent = T.showing(`${m.name} (${m.uf})`);
    return true;
  }
  const hash = location.hash.match(/^#cidade-(\d{7})$/);
  if (!(hash && await showById(+hash[1]))) await profile(null);
  return { showById, showAll };
}
