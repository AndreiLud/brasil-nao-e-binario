// "If your city had 100 voters": a 10 x 10 grid of small figures.
import { C } from "./core.js";

const svgNS = "http://www.w3.org/2000/svg";

// Largest-remainder rounding so the five groups add up to exactly 100.
export function hundred(r) {
  const parts = [["l", r.l], ["b", r.b], ["o", r.o], ["bn", r.bn], ["ab", r.ab]];
  const total = parts.reduce((s, p) => s + p[1], 0);
  const raw = parts.map(([k, v]) => [k, (v / total) * 100]);
  const out = Object.fromEntries(raw.map(([k, v]) => [k, Math.floor(v)]));
  let left = 100 - Object.values(out).reduce((s, v) => s + v, 0);
  raw.map(([k, v]) => [k, v - Math.floor(v)]).sort((a, b) => b[1] - a[1]).forEach(([k]) => { if (left > 0) { out[k] += 1; left -= 1; } });
  return out;
}

const FILL = { l: C.l, b: C.b, o: C.third, bn: C.blank, ab: "none" };

export function peopleSVG(r, { size = 180, title = "", names = { L: "o campo lulista", B: "o campo bolsonarista" } } = {}) {
  const h = hundred(r);
  const cell = 18, W = cell * 10, H = cell * 10 + 4;
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("width", size); svg.setAttribute("height", (size * H) / W);
  svg.setAttribute("role", "img");
  const parts = [[h.l, `votaram em ${names.L}`], [h.b, `em ${names.B}`], [h.o, "em outros candidatos"],
    [h.bn, "votaram em branco ou anularam"], [h.ab, "não foram votar"]].filter(([n]) => n > 0).map(([n, t]) => `${n} ${t}`);
  const said = parts.length > 1 ? `${parts.slice(0, -1).join(", ")} e ${parts[parts.length - 1]}` : parts[0];
  svg.setAttribute("aria-label", `${title}${title ? ". " : ""}De cada 100 eleitores, ${said}.`);
  let k = 0;
  for (const key of ["l", "b", "o", "bn", "ab"]) {
    for (let j = 0; j < h[key]; j++, k++) {
      const x = (k % 10) * cell + cell / 2, y = Math.floor(k / 10) * cell;
      const g = document.createElementNS(svgNS, "g");
      const head = document.createElementNS(svgNS, "circle");
      head.setAttribute("cx", x); head.setAttribute("cy", y + 5); head.setAttribute("r", 3.3);
      const body = document.createElementNS(svgNS, "path");
      body.setAttribute("d", `M${x - 5.5},${y + 17} v-4.2 a5.5,5 0 0 1 11,0 v4.2 z`);
      for (const el of [head, body]) {
        if (key === "ab") { el.setAttribute("fill", "none"); el.setAttribute("stroke", C.absentLine); el.setAttribute("stroke-width", 1.6); }
        else {
          el.setAttribute("fill", FILL[key]);
          if (key === "bn") { el.setAttribute("stroke", "#8f877c"); el.setAttribute("stroke-width", 0.9); }
        }
        g.appendChild(el);
      }
      svg.appendChild(g);
    }
  }
  return { svg, counts: h };
}
