// The Split app: one codebase for every city. City-specific words live in config.ts.
import type { CityConfig } from "./config";
import type { CityData, Line, HeritageGroup, TimelineLine, TimelineGroup, Brand } from "./types";
import { verdict, rankNormal, splitOf, Graph, quickCheck, chainField, chainTest, minCutSides, lamOf } from "./stats";
import { Viewport } from "./viewport";

const svgNS = "http://www.w3.org/2000/svg";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const $ = (s: string) => document.querySelector(s) as any;
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const RAMP = ["#fbf3dc", "#f6d9a0", "#efb066", "#e0803c", "#c4501f", "#8f2a12"];
const rampIdx = (lq: number) => (lq < 0.5 ? 0 : lq < 1 ? 1 : lq < 2 ? 2 : lq < 4 ? 3 : lq < 8 ? 4 : 5);
const GREY = `<div><i style="background:var(--empty)"></i><span>Not mapped: few people live here</span></div>`;
const isPhone = () => window.matchMedia("(max-width: 760px)").matches;

export function start(DATA: CityData, C: CityConfig) {
  const City = C.name, place = C.place, places = C.places, Places = cap(places);
  const lines = DATA.lines;
  const byId: Record<string, Line> = Object.fromEntries(lines.map((l) => [l.id, l]));
  const ref = byId[C.refLine] || lines[0];
  let current = lines[0], compare: Line | null = null, picked: number | null = null;

  // ---------- static text for this city
  document.title = `${City} / Split`;
  document.querySelectorAll(".cityname").forEach((e) => (e.textContent = City));
  $("#cityswitch").innerHTML = C.links.map((l) => `<a href="${l.href}"${l.id === C.id ? ' aria-current="page"' : ""}>${l.name}</a>`).join("");
  $("#herTab").textContent = C.herTab;
  $("#suburbLabel").textContent = `Your ${place}`;
  $("#suburb").placeholder = C.placeholder;
  $("#map").setAttribute("aria-label", `Map of ${City} coloured by the selected line`);
  $("#introTitle").textContent = C.intro.title;
  $("#introList").innerHTML = C.intro.items.map((t) => `<li>${t}</li>`).join("");
  $("#introLatte").textContent = C.intro.refButton;
  $("#introSuburb").textContent = C.intro.placeButton;
  if (C.creditHtml) {
    $("#introCredit").innerHTML = `${C.creditHtml}. Shown for fun and learning; not affiliated.`; $("#introCredit").hidden = false;
    $("#mapCredit").innerHTML = C.creditHtml; $("#mapCredit").hidden = false;
  }
  $("#yearticks").innerHTML = DATA.timeline.years.map((y) => `<span>${y}</span>`).join("");

  // ---------- modes and lists
  const her = DATA.heritage;
  let mode = "lines", herKind = C.herKinds[0][0], curHer = her.find((h) => h.kind === herKind) || her[0], ovLine = ref;
  const TL = DATA.timeline;
  let tKind = "lines", tLine: TimelineLine = TL.lines[0], tGroup: TimelineGroup = TL.groups[0], tYear = TL.years.length - 1;
  let playing: ReturnType<typeof setInterval> | null = null;
  const Y0 = TL.years[0], Y1 = TL.years[TL.years.length - 1], LAST = TL.years.length - 1;
  const list = $("#list") as HTMLElement;

  function btn(label: string, sub: string, pillHtml: string, onclick: () => void, isCurrent: boolean) {
    const b = document.createElement("button"); b.className = "line-btn";
    b.innerHTML = `<span class="nm"></span>${pillHtml || "<span></span>"}<span class="sub"></span>`;
    b.querySelector(".nm")!.textContent = label; b.querySelector(".sub")!.textContent = sub;
    b.setAttribute("aria-current", String(isCurrent)); b.addEventListener("click", onclick); return b;
  }
  function head(t: string) { const h = document.createElement("h2"); h.textContent = t; list.appendChild(h); }
  function kindsSwitch(kinds: [string, string, ...string[]][], cur: string, set: (k: string) => void) {
    const sw = document.createElement("div"); sw.className = "tabs kinds";
    for (const [k, lab] of kinds) {
      const b = document.createElement("button"); b.textContent = lab; b.setAttribute("aria-selected", String(k === cur));
      b.onclick = () => set(k); sw.appendChild(b);
    }
    list.appendChild(sw);
  }
  function buildList() {
    list.innerHTML = "";
    if (mode === "lines") {
      for (const [g, title] of C.groups) {
        const ls = lines.filter((x) => x.group === g); if (!ls.length) continue;
        head(title);
        for (const l of ls) {
          const [cls, txt] = verdict(l.tier);
          const b = btn(l.name, "Orange: " + l.a, `<span class="pill ${cls}">${txt}</span>`, () => { location.hash = l.id; }, l === current);
          b.dataset.id = l.id; list.appendChild(b);
        }
      }
    } else if (mode === "make") {
      buildMakeControls();
    } else if (mode === "timeline") {
      if (C.tKinds.length > 1) kindsSwitch(C.tKinds, tKind, (k) => { tKind = k; if (k !== "lines") tGroup = TL.groups.find((g) => g.kind === k)!; render(); });
      if (tKind === "lines") {
        head("Lines through time");
        for (const l of TL.lines) list.appendChild(btn(l.name, `${l.same_as_2001[LAST]}% of ${places} on the same side as in ${Y0}`, "", () => { tLine = l; render(); }, l === tLine));
      } else {
        head(C.tKinds.find((k) => k[0] === tKind)![2]);
        for (const g of TL.groups.filter((x) => x.kind === tKind))
          list.appendChild(btn(g.name, `${g.pct[0]}% → ${g.pct[LAST]}% of ${City}`, "", () => { tGroup = g; render(); }, g === tGroup));
      }
    } else {
      if (C.herKinds.length > 1) kindsSwitch(C.herKinds, herKind, (k) => { herKind = k; curHer = her.find((h) => h.kind === k)!; render(); });
      head(mode === "overlay" ? "1. Pick a group" : C.herKinds.find((k) => k[0] === herKind)![1]);
      for (const h of her.filter((x) => x.kind === herKind))
        list.appendChild(btn(h.name, `${h.pct}% of ${City} · ${C.peakWord}: ${h.peaks[0] ? h.peaks[0][0] : "-"}`, "", () => { curHer = h; render(); }, h === curHer));
    }
    syncPicker();
  }

  // On phones the long list becomes a native picker that mirrors whatever the list shows.
  const mpick = $("#mpick") as HTMLElement, msel = $("#mpickSel") as HTMLSelectElement;
  function syncPicker() {
    const items = [...list.querySelectorAll<HTMLElement>("h2, .line-btn")];
    const btns = items.filter((e) => e.classList.contains("line-btn"));
    mpick.hidden = btns.length === 0;
    if (!btns.length) return;
    msel.innerHTML = "";
    let grp: HTMLElement = msel;
    for (const el of items) {
      if (el.tagName === "H2") { grp = document.createElement("optgroup"); (grp as HTMLOptGroupElement).label = el.textContent || ""; msel.appendChild(grp); continue; }
      const o = document.createElement("option"); o.value = String(btns.indexOf(el));
      const pill = el.querySelector(".pill");
      o.textContent = (el.querySelector(".nm")!.textContent || "") + (pill ? ` · ${pill.textContent}` : "");
      if (el.getAttribute("aria-current") === "true") o.selected = true;
      grp.appendChild(o);
    }
    $("#mpickLabel").textContent = mode === "lines" ? "Pick a line" : mode === "timeline" ? "Pick what to follow" : "Pick a group";
  }
  msel.addEventListener("change", () => {
    const b = [...list.querySelectorAll<HTMLElement>(".line-btn")][+msel.value];
    if (b) b.click();
  });

  document.querySelectorAll<HTMLElement>("header > .tabs button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode!)));
  function setMode(m: string) {
    mode = m; picked = null;
    document.querySelectorAll<HTMLElement>("header > .tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.mode === m)));
    $("#tagline").textContent = C.tag[m];
    $(".compare").style.display = m === "heritage" || m === "timeline" || m === "make" ? "none" : "";
    $("#smoothbox").style.display = m === "make" ? "block" : "none";
    if (m !== "make") gDots.innerHTML = "";
    $("#yearbox").style.display = m === "timeline" ? "block" : "none";
    if (m !== "timeline" && playing) { clearInterval(playing); playing = null; $("#play").textContent = "▶ Play"; }
    buildCompareBox(); render();
  }
  const cmp = $("#cmp") as HTMLSelectElement;
  function buildCompareBox() {
    $(".compare label").textContent = mode === "overlay" ? "2. Pick a line to draw on top" : "Compare with another line";
    cmp.innerHTML = mode === "overlay" ? "" : '<option value="">None</option>';
    for (const l of lines) { const o = document.createElement("option"); o.value = l.id; o.textContent = l.name; cmp.appendChild(o); }
    cmp.value = mode === "overlay" ? ovLine.id : compare ? compare.id : "";
  }
  cmp.addEventListener("change", () => {
    if (mode === "overlay") { ovLine = byId[cmp.value]; render(); }
    else { compare = cmp.value ? byId[cmp.value] : null; drawCompare(); }
  });

  // ---------- map
  const map = $("#map") as SVGSVGElement;
  const gAreas = document.createElementNS(svgNS, "g"), gCut = document.createElementNS(svgNS, "g"), gLbl = document.createElementNS(svgNS, "g");
  const gEmpty = document.createElementNS(svgNS, "g"), gDots = document.createElementNS(svgNS, "g");
  map.append(gEmpty, gAreas, gCut, gDots, gLbl);
  for (const e of DATA.empty) {
    const p = document.createElementNS(svgNS, "path"); p.setAttribute("d", e.d); p.setAttribute("class", "empty"); p.dataset.empty = e.name; gEmpty.appendChild(p);
  }
  const areaEls = DATA.areas.map((a, i) => {
    const p = document.createElementNS(svgNS, "path"); p.setAttribute("d", a.d); p.setAttribute("class", "area"); p.dataset.i = String(i);
    gAreas.appendChild(p); return p;
  });
  const haloEl = document.createElementNS(svgNS, "path"); haloEl.setAttribute("class", "halo");
  const cutEl = document.createElementNS(svgNS, "path"); cutEl.setAttribute("class", "cut");
  const cut2El = document.createElementNS(svgNS, "path"); cut2El.setAttribute("class", "cut2");
  gCut.append(haloEl, cutEl, cut2El);
  for (const L of DATA.labels) {
    const a = DATA.areas[L.i], t = document.createElementNS(svgNS, "text");
    t.setAttribute("x", String(a.cx)); t.setAttribute("y", String(a.cy)); t.setAttribute("text-anchor", "middle");
    t.setAttribute("class", "lbl" + ((L.tier || 1) > 1 ? " minor" : "")); t.textContent = L.t; t.dataset.tier = String(L.tier || 1);
    gLbl.appendChild(t);
  }
  const view = new Viewport(map, DATA.w, DATA.h, scaleLabels);
  function scaleLabels() {
    const k = view.vb[2] / DATA.w;                      // keep labels a constant size on screen
    const narrow = map.clientWidth < 520;                 // small screens: fewer names until you zoom in
    const show = narrow ? (k < 0.2 ? 3 : k < 0.38 ? 2 : k < 0.75 ? 1 : 0) : k < 0.3 ? 3 : k < 0.55 ? 2 : 1;
    const px = (k * DATA.w) / Math.max(map.clientWidth, 1);
    let firstTier = 0;
    gLbl.querySelectorAll<SVGTextElement>("text").forEach((t) => {
      const tier = +t.dataset.tier!;
      const keep = tier <= show || (show === 0 && tier === 1 && firstTier++ < 9);   // zoomed out on a phone: the 9 best-known names
      t.style.display = keep ? "" : "none";
      t.style.fontSize = ((tier > 1 ? 10 : 11) * px).toFixed(2) + "px"; t.style.strokeWidth = (3 * px).toFixed(2) + "px";
    });
  }
  $("#zin").onclick = () => view.zoom(1 / 1.4);
  $("#zout").onclick = () => view.zoom(1.4);
  $("#zreset").onclick = () => { view.fit(); view.apply(); };

  // ---------- tooltip (hover with a mouse, tap on a phone)
  const tip = $("#tip") as HTMLElement;
  let tipTimer: ReturnType<typeof setTimeout> | null = null;
  function tipText(target: Element): [string, string] | null {
    const el = target as HTMLElement;
    const emp = el.dataset && el.dataset.empty;
    if (emp) return [emp, "Not mapped: few people live here (parks, industry, airports, bushland or farms)."];
    const iS = el.dataset && el.dataset.i; if (iS === undefined) return null;
    const i = +iS, a = DATA.areas[i];
    if (mode === "make" && MK.side) return [a.name, MK.side[i] ? "Orange side" : "Blue side"];
    if (mode === "timeline") return [a.name, tKind === "lines"
      ? `${TL.years[tYear]}: ${tLine.sides[tYear][i] ? "orange side – " + tLine.a : "blue side – " + tLine.b}`
      : `${TL.years[tYear]}: ${tGroup.lq[tYear][i].toFixed(1)}× the ${City} average`];
    if (mode !== "lines") return [a.name, `${C.herLabel(curHer)}: ${curHer.lq[i].toFixed(1)}× the ${City} average`];
    return [a.name, current.side[i] ? "Orange side: " + current.a : "Blue side: " + current.b];
  }
  function showTip(e: PointerEvent | MouseEvent, sticky: boolean) {
    const t = tipText(e.target as Element);
    if (!t) { tip.style.opacity = "0"; return; }
    tip.innerHTML = "<b></b><br><span></span>"; tip.querySelector("b")!.textContent = t[0]; tip.querySelector("span")!.textContent = t[1];
    const r = map.getBoundingClientRect();
    const w = Math.min(270, r.width * 0.72);
    tip.style.left = Math.max(8, Math.min(e.clientX - r.left + 14, r.width - w - 8)) + "px";
    tip.style.top = Math.max(8, Math.min(e.clientY - r.top + 14, r.height - 70)) + "px";
    tip.style.opacity = "1";
    if (tipTimer) clearTimeout(tipTimer);
    if (sticky) tipTimer = setTimeout(() => (tip.style.opacity = "0"), 3500);
  }
  map.addEventListener("pointermove", (e) => { if (e.pointerType === "mouse" && !view.dragging) showTip(e, false); });
  map.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") tip.style.opacity = "0"; });
  map.addEventListener("click", (e) => {
    if (view.moved) return;
    showTip(e as MouseEvent, true);
    const iS = (e.target as HTMLElement).dataset?.i;
    if (iS !== undefined && mode === "lines") pick(+iS);
  });

  // ---------- render a line
  function agreement(x: Line, y: Line) { let s = 0; x.side.forEach((v, i) => (s += Number(v === y.side[i]))); s /= x.side.length; return Math.max(s, 1 - s); }
  function drawCompare() {
    cut2El.setAttribute("d", compare && compare !== current ? compare.cut : "");
    $("#agree").innerHTML = compare && compare !== current
      ? `<span class="legend-dash"></span>${compare.name} puts ${Math.round(agreement(current, compare) * 100)}% of ${places} on matching sides` : "";
  }
  const WARN = `<div class="warn"><b>Overlap isn't cause.</b> Don't stereotype.
    <details><summary>Why?</summary><ul><li>Maps show places, not people.</li><li>${C.warnBullet}</li>
    <li>Some ${places} were unfairly stigmatised in the past. Don't repeat it.</li></ul></details></div>`;
  const ASKS = `<p class="small">${C.asks}</p>`;
  const legend = () => `<div class="box"><h3>Share vs ${City} average</h3><div class="ramp">${RAMP.map((c) => `<span style="background:${c}"></span>`).join("")}</div>
    <div class="ramp-l"><span>less</span><span>1×</span><span>2×</span><span>4×</span><span>8×+</span></div></div>`;
  const sidesLegend = (a: string, b: string, extra = "") => {
    const el = $("#maplegend") as HTMLElement;
    el.innerHTML = `<div><i style="background:var(--side-a)"></i><span></span></div><div><i style="background:var(--side-b)"></i><span></span></div>
      <div><i style="background:var(--cut);height:3px"></i><span>The line</span></div>${extra}${GREY}`;
    const sp = el.querySelectorAll("span"); sp[0].textContent = a; sp[1].textContent = b;
  };
  function mapLegend() {
    const el = $("#maplegend") as HTMLElement;
    el.classList.toggle("folded", isPhone());
    if (mode === "make") {
      const dots = MK.kind === "chain" && MK.dots
        ? `<div><i style="border-radius:50%;background:var(--side-a);border:1px solid #fff"></i><span class="d1"></span></div><div><i style="border-radius:50%;background:var(--side-b);border:1px solid #fff"></i><span class="d2"></span></div>` : "";
      sidesLegend(MK.aText || "", MK.bText || "", dots);
      if (dots) { el.querySelector(".d1")!.textContent = MK.A + " stores"; el.querySelector(".d2")!.textContent = MK.B + " stores"; }
    } else if (mode === "timeline" && tKind === "lines") {
      sidesLegend(tLine.a, tLine.b, `<div><i style="border:2.6px solid var(--ink);background:none"></i><span>${C.movedTitle}, ${Y0}–${Y1}</span></div>`);
    } else if (mode === "lines") {
      sidesLegend(current.a, current.b);
    } else {
      el.innerHTML = `<div><i style="background:${RAMP[4]}"></i><span>Darker = more than ${City}'s average</span></div>
        <div><i style="background:${RAMP[0]}"></i><span>Lighter = fewer</span></div>
        ${mode === "overlay" ? `<div><i style="background:#111418;height:3px"></i><span>The line you picked</span></div>` : ""}${GREY}`;
    }
  }
  $("#maplegend").addEventListener("click", () => { if (isPhone()) $("#maplegend").classList.toggle("folded"); });

  function render() {
    buildList(); setTimeout(mapLegend, 0);
    if (mode === "make") return renderMake();
    if (mode === "timeline") return renderTimeline();
    if (mode !== "lines") return renderHeritage();
    cutEl.style.display = ""; cutEl.setAttribute("class", "cut"); haloEl.setAttribute("d", "");
    const l = current;
    areaEls.forEach((p, i) => { p.style.fill = ""; p.setAttribute("class", "area " + (l.side[i] ? "a" : "b") + (picked === i ? " picked" : "")); });
    cutEl.setAttribute("d", l.cut);
    drawCompare();
    const [cls, txt] = verdict(l.tier);
    const sureText = l.tier === "line"
      ? `Even next to random versions of ${City} that are just as smooth, this border is unusually clean: only ${Math.max(1, Math.round(l.p * 100))} in 100 drew one this clean, after allowing for how many lines we tried. It still changes gradually across a few kilometres rather than at a hard edge.`
      : l.tier === "gentle"
        ? `The pattern is real: ${City} clearly isn't random here. But a random ${City} that's just as smooth often draws a border this clean, so read it as a gentle slope across the city rather than a sharp line.`
        : `Versions of ${City} with no real pattern often produce a split like this. The map may still tell a story, but the data can't show it yet.`;
    const tech = `Technical: line test p = ${l.p}${l.p_geo != null ? `, any-geography p = ${l.p_geo}` : ""}${l.p_edge != null ? `, edge test p = ${l.p_edge}` : ""}. Random landscapes in real space, simulated from the data, then corrected for the number of lines tried.`;
    const adj = l.adjusted ? `<p class="small">We took out the effect of income and distance from the city first, so this isn't just the usual rich-vs-poor or inner-vs-outer split.</p>` : "";
    const d = $("#detail") as HTMLElement;
    d.innerHTML = `
      <div><h2></h2></div>
      <div class="sides">
        <div class="side"><span class="sw a"></span><div><b class="ta"></b><div class="ex ea"></div></div></div>
        <div class="side"><span class="sw b"></span><div><b class="tb"></b><div class="ex eb"></div></div></div>
      </div>
      <div class="box"><h3>How sure are we?</h3><div class="sure ${cls}"><strong>${txt}</strong></div><p class="small">${sureText}</p><p class="small" style="font-size:11.5px">${tech}</p>${adj}</div>
      <div class="box"><h3>What else changes across it</h3>
        <p class="small" style="margin:0 0 6px">The orange side also has:</p><div class="chips ca"></div>
        <p class="small" style="margin:10px 0 6px">The blue side also has:</p><div class="chips cb"></div></div>
      ${l === ref ? "" : `<div class="box"><h3>Same route as the ${C.refName}?</h3><p style="margin:0"><b>${Math.round(l.latte_agree * 100)}%</b> of ${places} fall on matching sides.</p>
        <p class="small">${l.latte_agree >= 0.75 ? "This line mostly retraces the classic divide." : l.latte_agree >= 0.6 ? "Partly the classic divide, partly its own route." : `This line takes its own route across ${City}.`}</p></div>`}
      ${(DATA.meta.explain || {})[l.id] || ""}
      ${C.lineExtra ? C.lineExtra(l, DATA) : ""}
      ${C.splitNote ? C.splitNote(l, DATA) : ""}
      <div class="box passport" id="passport"></div>
      <footer>${C.footer.lines(DATA)}</footer>`;
    d.querySelector("h2")!.textContent = l.name;
    d.querySelector(".ta")!.textContent = l.a; d.querySelector(".tb")!.textContent = l.b;
    d.querySelector(".ea")!.textContent = "e.g. " + l.ex_a.join(", "); d.querySelector(".eb")!.textContent = "e.g. " + l.ex_b.join(", ");
    l.more.forEach((t) => d.querySelector(".ca")!.appendChild(chip(t, "a")));
    l.less.forEach((t) => d.querySelector(".cb")!.appendChild(chip(t, "b")));
    renderPassport();
  }
  function chip(t: string, c: string) { const s = document.createElement("span"); s.className = "chip " + c; s.textContent = t; return s; }

  function spark(vals: number[], fmt: (v: number) => string) {
    const n = vals.length, w = 300, h = 86, max = Math.max(...vals) * 1.15 || 1, bw = 40, gap = (w - n * bw) / (n - 1);
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-label="Values by Census year">` + vals.map((v, k) => {
      const x = k * (bw + gap), bh = (v / max) * (h - 34), y = h - 16 - bh;
      return `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="3" fill="${k === tYear ? "var(--side-b)" : "var(--rule)"}"></rect>
        <text class="v" x="${x + bw / 2}" y="${y - 4}" text-anchor="middle">${fmt(v)}</text><text x="${x + bw / 2}" y="${h - 2}" text-anchor="middle">${TL.years[k]}</text>`;
    }).join("") + "</svg>";
  }
  function renderTimeline() {
    $("#yearlabel").textContent = TL.years[tYear]; $("#year").value = tYear; $("#year").max = LAST;
    cut2El.setAttribute("d", ""); haloEl.setAttribute("d", ""); $("#agree").innerHTML = "";
    const d = $("#detail") as HTMLElement; const nm = (i: number) => DATA.areas[i].short;
    if (tKind === "lines") {
      const l = tLine, movedSet = new Set([...l.toA, ...l.toB]);
      areaEls.forEach((p, i) => { p.style.fill = ""; p.setAttribute("class", "area " + (l.sides[tYear][i] ? "a" : "b") + (movedSet.has(i) ? " moved" : "")); });
      cutEl.style.display = ""; cutEl.setAttribute("class", "cut"); cutEl.setAttribute("d", l.cuts[tYear]);
      const stable = l.persist_p <= 0.05 ? "Much more stable than chance" : "Not clearly more stable than chance";
      d.innerHTML = `<div><h2></h2><p class="small" style="margin:4px 0 0">Drag the year slider or press Play.</p></div>
        <div class="sides"><div class="side"><span class="sw a"></span><div><b class="ta"></b></div></div><div class="side"><span class="sw b"></span><div><b class="tb"></b></div></div></div>
        <div class="box"><h3>How much has it moved?</h3><p style="margin:0"><b>${l.same_as_2001[tYear]}%</b> of ${places} are on the same side in ${TL.years[tYear]} as in ${Y0}.</p>
          <p class="small">Two unrelated maps of ${City} would still match on about ${l.null_agree}% of ${places}, just because nearby ${places} are alike. ${stable}.</p>
          <p class="small" style="font-size:11.5px">Technical: persistence test, p = ${l.persist_p}</p></div>
        <div class="box"><h3>${C.movedTitle}, ${Y0}–${Y1}</h3>
          <p class="small" style="margin:0 0 4px">${C.movedNote}</p>
          <p style="margin:0 0 6px"><span class="sw a" style="display:inline-block;vertical-align:-2px"></span> Moved to orange: <span class="ma"></span></p>
          <p style="margin:0"><span class="sw b" style="display:inline-block;vertical-align:-2px"></span> Moved to blue: <span class="mb"></span></p></div>
        <div class="box"><h3>Across ${City}: ${l.stat_label}</h3>${spark(l.stat, (v) => v + "%")}</div>
        <footer>${C.footer.timelineLines}</footer>${C.timelineExtra ? C.timelineExtra(l) : ""}`;
      d.querySelector("h2")!.textContent = l.name; d.querySelector(".ta")!.textContent = l.a; d.querySelector(".tb")!.textContent = l.b;
      d.querySelector(".ma")!.textContent = l.toA.length ? l.toA.map(nm).join(", ") : "none";
      d.querySelector(".mb")!.textContent = l.toB.length ? l.toB.map(nm).join(", ") : "none";
    } else {
      const g = tGroup;
      areaEls.forEach((p, i) => { p.setAttribute("class", "area h"); p.style.fill = RAMP[rampIdx(g.lq[tYear][i])]; });
      cutEl.style.display = "none";
      const dD = g.D[LAST] - g.D[0];
      const trend = dD < -0.02 ? `spread out across ${City}` : dD > 0.02 ? `became more concentrated in fewer ${places}` : "stayed about as concentrated";
      d.innerHTML = `<div><h2></h2><p class="note">${C.timelineGroupNote(g)}</p></div>
        <div class="box"><h3>Share of ${City}'s population</h3>${spark(g.pct, (v) => v.toFixed(1) + "%")}</div>
        <div class="box"><h3>Spreading out or clustering?</h3><p style="margin:0">From ${Y0} to ${Y1} this group <b>${trend}</b>.</p>
          <p class="small">In ${TL.years[tYear]}, about ${Math.round(g.D[tYear] * 100)}% would have had to move house for this group to be spread evenly${tYear ? ` (${Y0}: ${Math.round(g.D[0] * 100)}%)` : ""}.</p></div>
        ${legend()}${ASKS}
        <footer>${C.footer.timelineGroups}</footer>`;
      d.querySelector("h2")!.textContent = C.timelineGroupTitle(g);
    }
  }
  $("#year").addEventListener("input", (e: Event) => { tYear = +(e.target as HTMLInputElement).value; render(); });
  $("#play").addEventListener("click", () => {
    if (playing) { clearInterval(playing); playing = null; $("#play").textContent = "▶ Play"; return; }
    if (tYear === LAST) tYear = 0; render(); $("#play").textContent = "❚❚ Pause";
    playing = setInterval(() => {
      if (tYear >= LAST) { clearInterval(playing!); playing = null; $("#play").textContent = "▶ Play"; return; }
      tYear++; render();
    }, 1300);
  });

  // ---------- make your own: live maths in the browser
  const MKD = DATA.make, N = MKD.n, G = new Graph(N, MKD.I, MKD.J, MKD.L);
  const EIG = new Float32Array(Uint8Array.from(atob(MKD.eig), (c) => c.charCodeAt(0)).buffer);   // N x N, row-major
  const SIG = Object.fromEntries(MKD.signals.map((s) => [s.id, s]));
  const has = (id: string) => id in SIG;
  const MK = {
    kind: "line", A: has("share_cafe") ? "share_cafe" : MKD.signals[0].id, B: (has("share_fast_food") ? "share_fast_food" : null) as string | null,
    side: null as boolean[] | null, lam: 0, dots: false, aText: "", bText: "",
  };
  const brand = (n: string) => MKD.brands.find((x) => x.name === n) as Brand;
  function effects(side: boolean[], skip: (string | null)[]) {
    const out: [string, number][] = [];
    for (const s of MKD.signals) {
      if (skip.includes(s.id)) continue;
      const z = rankNormal(s.v); let a = 0, b = 0, na = 0, nb = 0;
      z.forEach((x, i) => (side[i] ? ((a += x), na++) : ((b += x), nb++)));
      out.push([s.more, a / Math.max(na, 1) - b / Math.max(nb, 1)]);
    }
    out.sort((x, y) => y[1] - x[1]);
    return { more: out.slice(0, 5).map((x) => x[0]), less: out.slice(-5).reverse().map((x) => x[0]) };
  }
  function fmtVal(id: string, x: number) {
    if (x == null || isNaN(x)) return "–";
    if (/^median_|^average_/.test(id)) return (Math.round(x * 10) / 10).toLocaleString();
    if (/per_1k$/.test(id)) return x.toFixed(1) + " per 1,000 people";
    if (/price/.test(id)) return "¥" + Math.round(x).toLocaleString();
    return (x * 100).toFixed(1) + "%";
  }
  function sideMean(id: string, side: boolean[], which: boolean) {
    const v = SIG[id].v; let s = 0, n = 0;
    v.forEach((x, i) => { if (x != null && side[i] === which) { s += x; n++; } });
    return n ? s / n : NaN;
  }
  function sel(id: string, label: string, opts: [string, string, string][], value: string, withNone: boolean) {
    const w = document.createElement("div"); w.className = "ctrl";
    w.innerHTML = `<label for="${id}"></label><select id="${id}"></select>`; w.querySelector("label")!.textContent = label;
    const s = w.querySelector("select")!;
    if (withNone) { const o = document.createElement("option"); o.value = ""; o.textContent = "Nothing (just the first thing)"; s.appendChild(o); }
    const groups: Record<string, HTMLOptGroupElement> = {};
    for (const [v, t, g] of opts) {
      if (!groups[g]) { groups[g] = document.createElement("optgroup"); groups[g].label = g; s.appendChild(groups[g]); }
      const o = document.createElement("option"); o.value = v; o.textContent = t; groups[g].appendChild(o);
    }
    s.value = value; return w;
  }
  const resetSmooth = () => { MK.lam = 0; $("#smooth").value = 0; };
  function buildMakeControls() {
    kindsSwitch([["line", "Your line"], ["chain", "Chain vs chain"]], MK.kind, (k) => {
      MK.kind = k; resetSmooth();
      if (k === "chain") { [MK.A, MK.B] = C.chainDefault; } else { MK.A = has("share_cafe") ? "share_cafe" : MKD.signals[0].id; MK.B = has("share_fast_food") ? "share_fast_food" : null; }
      render();
    });
    if (MK.kind === "line") {
      const opts = MKD.signals.map((s) => [s.id, s.label, s.group] as [string, string, string]).sort((x, y) => x[2].localeCompare(y[2]) || x[1].localeCompare(y[1]));
      list.appendChild(sel("mkA", "1. Orange side has more…", opts, MK.A, false));
      list.appendChild(sel("mkB", "2. …compared with (optional)", opts, MK.B || "", true));
    } else {
      const opts = MKD.brands.map((b) => [b.name, `${b.name} (${b.n} stores)`, "Chains"] as [string, string, string]);
      list.appendChild(sel("mkA", "1. Orange: closer to a…", opts, MK.A, false));
      list.appendChild(sel("mkB", "2. Blue: closer to a…", opts, MK.B || "", false));
    }
    const go = document.createElement("div"); go.className = "ctrl";
    go.innerHTML = `<button id="mkSurprise" class="ghost">Surprise me</button>`
      + (MK.kind === "chain" ? `<label class="dotsw"><input type="checkbox" id="mkDots"${MK.dots ? " checked" : ""}> Show the shops on the map</label>` : "");
    list.appendChild(go);
    if (MK.kind === "chain") $("#mkDots").onchange = (e: Event) => { MK.dots = (e.target as HTMLInputElement).checked; render(); };
    $("#mkA").onchange = (e: Event) => { MK.A = (e.target as HTMLSelectElement).value; resetSmooth(); render(); };
    $("#mkB").onchange = (e: Event) => { MK.B = (e.target as HTMLSelectElement).value || null; resetSmooth(); render(); };
    $("#mkSurprise").onclick = () => {
      const pickTwo = (names: string[]) => { const a = names[Math.floor(Math.random() * names.length)]; let b; do { b = names[Math.floor(Math.random() * names.length)]; } while (b === a); return [a, b]; };
      [MK.A, MK.B] = MK.kind === "line" ? pickTwo(MKD.signals.map((s) => s.id)) : pickTwo(MKD.brands.map((b) => b.name));
      resetSmooth(); render();
    };
  }
  function borderPath(side: boolean[]) { let p = ""; for (let e = 0; e < MKD.I.length; e++) if (side[MKD.I[e]] !== side[MKD.J[e]]) p += MKD.ep[e]; return p; }
  function renderMake() {
    const d = $("#detail") as HTMLElement; gDots.innerHTML = ""; cut2El.setAttribute("d", ""); haloEl.setAttribute("d", "");
    let f: number[], title: string, ruleText: string, skip: (string | null)[] = [];
    if (MK.kind === "line") {
      const a = SIG[MK.A], b = MK.B ? SIG[MK.B] : null;
      f = rankNormal(a.v); if (b) { const fb = rankNormal(b.v); f = f.map((x, i) => x - fb[i]); }
      title = b ? `${a.label} vs ${b.label.charAt(0).toLowerCase() + b.label.slice(1)}` : a.label; skip = [MK.A, MK.B];
      MK.aText = cap(b ? `${a.more}, ${b.less}` : a.more); MK.bText = cap(b ? `${b.more}, ${a.less}` : a.less);
      ruleText = b ? `Orange ${places} have ${a.more} and ${b.less} than the ${City} middle.` : `Orange ${places} have ${a.more} than the ${City} middle.`;
      if (/^share_/.test(MK.A) || (b && /^share_/.test(MK.B!))) ruleText += ` (Food and shop counts are compared as a share of all the places to eat in each ${place}.)`;
    } else {
      const bA = brand(MK.A), bB = brand(MK.B!);
      f = chainField(MKD.rep, bA.xy, bB.xy, C.chainOffset); title = `${MK.A} vs ${MK.B}`;
      const art = (x: string) => (/^[AEIOUF]/.test(x) ? "an " : "a ") + x;
      MK.aText = `${cap(art(MK.A))} is closer than ${art(MK.B!)}`; MK.bText = `${cap(art(MK.B!))} is closer than ${art(MK.A)}`;
      ruleText = `Orange ${places} are closer to ${art(MK.A)} than to ${art(MK.B!)}.`;
      if (MK.dots) for (const [b, fill] of [[bA, "var(--side-a)"], [bB, "var(--side-b)"]] as [Brand, string][]) for (const [x, y] of b.vb) {
        const c = document.createElementNS(svgNS, "circle"); c.setAttribute("cx", String(x)); c.setAttribute("cy", String(y)); c.setAttribute("r", "3");
        c.setAttribute("class", "dot"); c.setAttribute("fill", fill); gDots.appendChild(c);
      }
    }
    const raw = splitOf(f), side = MK.lam > 0 ? minCutSides(G, f, MKD.pop, MK.lam) : raw; MK.side = side;
    areaEls.forEach((p, i) => { p.style.fill = ""; p.setAttribute("class", "area " + (side[i] ? "a" : "b")); });
    cutEl.style.display = ""; cutEl.setAttribute("class", "cut"); cutEl.setAttribute("d", borderPath(side));
    const switched = side.filter((s, i) => s !== raw[i]).length;
    $("#smoothinfo").textContent = MK.lam > 0
      ? `${Math.round((switched / N) * 100)}% of ${places} switched; border ${Math.round(G.border(raw))} km → ${Math.round(G.border(side))} km` : "Drag to simplify the border";
    const chainQ = `Do these chains live in different ${City}s?`;
    d.innerHTML = `<div><h2></h2><p class="rule"></p></div>
      <div class="sides"><div class="side"><span class="sw a"></span><div><b class="ta"></b><div class="ex ea"></div></div></div>
        <div class="side"><span class="sw b"></span><div><b class="tb"></b><div class="ex eb"></div></div></div></div>
      <div class="box" id="verdict"><h3>${MK.kind === "chain" ? chainQ : "Is this a real line?"}</h3><p class="small" style="margin:0">Checking against random versions of ${City}…</p></div>
      <div class="box"><h3>What else changes across it</h3><p class="small" style="margin:0 0 6px">The orange side also has:</p><div class="chips ca"></div>
        <p class="small" style="margin:10px 0 6px">The blue side also has:</p><div class="chips cb"></div></div>
      <div class="box"><h3>Same route as the ${C.refName}?</h3><p style="margin:0" id="mklatte"></p></div>
      <footer>${C.footer.make} If you try lots of combinations, about 1 in 20 will pass the check by luck.</footer>`;
    d.querySelector("h2")!.textContent = title; d.querySelector(".rule")!.textContent = ruleText;
    d.querySelector(".ta")!.textContent = MK.aText; d.querySelector(".tb")!.textContent = MK.bText;
    if (MK.kind === "line") {
      const a = SIG[MK.A];
      d.querySelector(".ea")!.textContent = `${a.label}: ${fmtVal(a.id, sideMean(a.id, raw, true))} on average`;
      d.querySelector(".eb")!.textContent = `${a.label}: ${fmtVal(a.id, sideMean(a.id, raw, false))} on average`;
    } else {
      d.querySelector(".ea")!.textContent = `${brand(MK.A).n} ${MK.A} stores on the map`; d.querySelector(".eb")!.textContent = `${brand(MK.B!).n} ${MK.B} stores on the map`;
    }
    const eff = effects(raw, skip);
    eff.more.forEach((x) => d.querySelector(".ca")!.appendChild(chip(x, "a"))); eff.less.forEach((x) => d.querySelector(".cb")!.appendChild(chip(x, "b")));
    let ag = 0; raw.forEach((s, i) => (ag += Number((s ? 1 : 0) === ref.side[i]))); ag /= N; ag = Math.max(ag, 1 - ag);
    $("#mklatte").innerHTML = `<b>${Math.round(ag * 100)}%</b> of ${places} fall on matching sides. ${ag >= 0.75 ? "Mostly the classic divide again." : ag >= 0.6 ? "Partly the classic divide." : `Its own route across ${City}.`}`;
    mapLegend();
    setTimeout(() => {   // run the test after the map paints
      const r = MK.kind === "chain"
        ? chainTest(G, MKD.rep, brand(MK.A).xy, brand(MK.B!).xy, C.chainOffset, C.chainDraws)
        : quickCheck(G, EIG, f);
      const good = r.p <= 0.05, box = $("#verdict"); if (!box) return;
      const msg = MK.kind === "chain"
        ? (good ? `Yes. Shuffle which stores belong to which chain and you rarely get a split this clean. These chains really do favour different parts of ${City}.`
          : "Can't tell. Shuffle the stores between the two chains and you often get a split this clean, so the pattern may just be where shops cluster anyway.")
        : (good ? `Passes the quick check: only ${Math.max(1, Math.round(r.p * 100))} in 100 shuffled ${City}s gave a line this clean. The quick check is generous with smooth maps, so treat this as a pattern worth a closer look rather than a proven line.`
          : `Not even the quick check. Shuffled ${City}s often give a line this clean, so the map may still tell a story, but it can't be shown yet.`);
      const head = good ? (MK.kind === "chain" ? `Different ${City}s` : "Passes the quick check") : (MK.kind === "chain" ? `Same ${City}` : "Could be chance");
      box.innerHTML = `<h3>${MK.kind === "chain" ? chainQ : "Is this a real line?"}</h3><div class="sure ${good ? "good" : "meh"}"><strong>${head}</strong></div>
        <p class="small">${msg}</p><p class="small" style="font-size:11.5px">Technical: line-ness ${r.obs.toFixed(3)}, p = ${r.p.toFixed(3)} (${MK.kind === "chain" ? `label-swap test, ${C.chainDraws} draws` : "quick Moran-rotation check, 199 draws; known to be lenient with smooth maps"})</p>`;
    }, 30);
  }
  $("#smooth").addEventListener("input", (e: Event) => { MK.lam = lamOf(+(e.target as HTMLInputElement).value); if (mode === "make") renderMake(); });

  // ---------- heritage / foreign residents
  function renderHeritage() {
    const h: HeritageGroup = curHer;
    areaEls.forEach((p, i) => { p.setAttribute("class", "area h"); p.style.fill = RAMP[rampIdx(h.lq[i])]; });
    cut2El.setAttribute("d", "");
    if (mode === "overlay") { cutEl.style.display = ""; cutEl.setAttribute("class", "cut onramp"); cutEl.setAttribute("d", ovLine.cut); haloEl.setAttribute("d", ovLine.cut); }
    else { cutEl.style.display = "none"; haloEl.setAttribute("d", ""); }
    $("#agree").innerHTML = "";
    const d = $("#detail") as HTMLElement;
    const BORN = `<p class="note">${C.notes[h.kind] || ""}</p>`;
    const peaks = h.peaks.map((p) => `<li><b>${p[0]}</b>: ${p[1]}% (${p[2]}× average)</li>`).join("");
    const ord = (n: number) => n + (["th", "st", "nd", "rd"][n % 10 < 4 && Math.floor(n / 10) % 10 !== 1 ? n % 10 : 0]);
    const custom = C.heritageClustering ? C.heritageClustering(h) : null;
    const clus = custom ?? (h.D == null ? "" : `<li>How clustered: <b>${h.D_rank === 1 ? "the most" : ord(h.D_rank!) + " most"}</b> of ${h.D_of}. About ${Math.round(h.D * 100)}% would have to move house for this group to be spread evenly across ${City}.</li>`);
    const rec = h.recent == null ? "" : `<li><b>${Math.round(h.recent * 100)}%</b> arrived in Australia in 2011 or later.</li>`;
    if (mode === "heritage") {
      d.innerHTML = `<div><h2></h2>${BORN}</div>
        <div class="box"><h3>Facts</h3><ul class="facts">
          <li><b>${h.pct}%</b> of ${City} (${h.people.toLocaleString()} people)</li>${clus}${rec}
          ${h.shares_with.length ? `<li>Lives in similar places to: ${h.shares_with.join(" and ")}</li>` : ""}</ul></div>
        <div class="box"><h3>Most concentrated in</h3><ul class="facts">${peaks}</ul></div>
        ${legend()}${C.heritageExtra ? C.heritageExtra(h) : ""}${ASKS}
        <footer>${C.footer.heritage}</footer>`;
    } else {
      d.innerHTML = `${WARN}<div><h2></h2>${BORN}</div>
        <div class="box"><h3>On the map</h3><p style="margin:0">Colour: ${C.herLabel(h)}.<br>Black line: <b></b>.</p>
        <p class="small">Orange side of that line: ${ovLine.a}.</p></div>${legend()}
        <footer>Shown side by side only. We don't score heritage against lines on purpose.</footer>`;
      d.querySelector("p b")!.textContent = ovLine.name;
    }
    d.querySelector("h2")!.textContent = mode === "overlay" ? `${C.herLabel(h)} × ${ovLine.name.replace(/^The /, "")}` : C.herLabel(h);
  }

  // ---------- your place's "line passport"
  function renderPassport() {
    const box = $("#passport") as HTMLElement | null; if (!box) return;
    if (picked === null) {
      box.innerHTML = `<h3>Your ${place}'s line passport</h3><p class="small" style="margin:0">Type your ${place} at the top, or tap any area on the map, to see which side of every line it sits on.</p>`;
      return;
    }
    const a = DATA.areas[picked];
    box.innerHTML = `<button class="close" aria-label="Clear ${place}">✕</button><h3>Line passport</h3><p style="margin:0 0 8px"><b></b></p><ul></ul>`;
    box.querySelector("p b")!.textContent = a.name;
    (box.querySelector(".close") as HTMLElement).onclick = () => { picked = null; render(); };
    const ul = box.querySelector("ul")!;
    const sp = DATA.split[picked];
    if (sp) {
      const p = document.createElement("p"); p.className = "small"; p.style.margin = "0 0 8px";
      p.textContent = `Split ${place}: the Hi-Vis Line runs through the middle of it. In one part ${sp[1]}% of workers are professionals; in the other, ${sp[2]}%.`;
      box.insertBefore(p, ul);
    }
    for (const l of lines.filter((x) => x.tier !== "chance")) {
      const li = document.createElement("li"), on = l.side[picked];
      li.innerHTML = `<span class="sw ${on ? "a" : "b"}"></span><span><b></b>: <span></span></span>`;
      li.querySelector("b")!.textContent = l.name.replace(/^The /, "");
      li.querySelector("span span")!.textContent = on ? l.a : l.b;
      ul.appendChild(li);
    }
  }
  function pick(i: number) { picked = i; $("#suburb").value = DATA.areas[i].short; render(); }

  // ---------- place search
  const dl = $("#suburbs") as HTMLDataListElement, nameIdx: Record<string, number> = {};
  DATA.areas.map((a, i) => [a.name, i] as [string, number]).sort().forEach(([n, i]) => {
    const o = document.createElement("option"); o.value = n; dl.appendChild(o); nameIdx[n.toLowerCase()] = i;
  });
  $("#suburb").addEventListener("change", (e: Event) => {
    const q = (e.target as HTMLInputElement).value.trim().toLowerCase(); if (!q) return;
    let i: number | undefined = nameIdx[q];
    if (i === undefined) { const k = Object.keys(nameIdx).find((n) => n.includes(q)); i = k ? nameIdx[k] : undefined; }
    if (i === undefined) return;
    if (mode !== "lines") { location.hash = current.id; }
    pick(i); const a = DATA.areas[i];
    view.focus(a.cx, a.cy, DATA.w / 3.5);
    if (isPhone()) map.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  // ---------- routing
  function route() {
    const h = location.hash.slice(1);
    if (["heritage", "overlay", "timeline", "make"].includes(h)) { setMode(h); return; }
    current = byId[h] || current || lines[0];
    if (mode !== "lines") setMode("lines"); else render();
  }
  window.addEventListener("hashchange", route);
  current = ref;
  view.fit(); view.apply(); setMode("lines"); route();

  // ---------- intro
  const intro = $("#intro") as HTMLElement;
  const openIntro = () => { intro.hidden = false; $("#introLatte").focus(); };
  const closeIntro = () => { intro.hidden = true; try { localStorage.setItem(C.storageKey, "1"); } catch { /* private mode */ } };
  $("#introLatte").onclick = () => { closeIntro(); location.hash = ref.id; route(); };
  $("#introSuburb").onclick = () => { closeIntro(); if (mode !== "lines") { location.hash = ref.id; route(); } $("#suburb").focus(); };
  $("#introPlay").onclick = () => { closeIntro(); location.hash = "make"; };
  $("#introClose").onclick = closeIntro; $("#helpbtn").onclick = openIntro;
  intro.addEventListener("click", (e) => { if (e.target === intro) closeIntro(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !intro.hidden) closeIntro(); });
  let seen = false; try { seen = localStorage.getItem(C.storageKey) === "1"; } catch { /* private mode */ }
  if (!seen && !location.hash) openIntro();
}
