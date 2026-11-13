// Pure maths used by the app. No DOM here, so it can be unit-tested.

export type Tier = "line" | "gentle" | "chance";

/** Label and colour class for an audited verdict. */
export function verdict(tier: Tier): [string, string] {
  return tier === "line" ? ["good", "Real line"] : tier === "gentle" ? ["gentle", "Real pattern, gentle"] : ["meh", "Could be chance"];
}

/** Inverse normal CDF (Acklam's approximation, |error| < 1.2e-9). */
export function invNorm(p: number): number {
  const a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924];
  const b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857];
  const c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878];
  const d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742];
  const pl = 0.02425;
  if (p < pl) { const q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
  if (p > 1 - pl) { const q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
  const q = p - 0.5, r = q * q;
  return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
}

/** Rank-normal transform: ties get their average rank, missing values the median. */
export function rankNormal(vals: (number | null)[]): number[] {
  const ok = vals.filter((v): v is number => v != null).sort((x, y) => x - y);
  const med = ok.length ? ok[Math.floor(ok.length / 2)] : 0;
  const v = vals.map((x) => (x == null ? med : x));
  const idx = v.map((_, i) => i).sort((i, j) => v[i] - v[j]);
  const rank = new Array<number>(v.length);
  for (let k = 0; k < idx.length;) {
    let m = k;
    while (m + 1 < idx.length && v[idx[m + 1]] === v[idx[k]]) m++;
    const r = (k + m) / 2 + 1;
    for (let q = k; q <= m; q++) rank[idx[q]] = r;
    k = m + 1;
  }
  return rank.map((r) => invNorm((r - 0.5) / v.length));
}

export function median(f: number[]): number {
  const s = [...f].sort((x, y) => x - y);
  return (s[(s.length - 1) >> 1] + s[s.length >> 1]) / 2;
}

/** Median split: true = orange side (above the middle). */
export function splitOf(f: number[]): boolean[] {
  const m = median(f);
  return f.map((x) => x > m);
}

/** Areas and their shared borders (I[e], J[e] share L[e] km of border). */
export class Graph {
  readonly total: number;
  constructor(readonly n: number, readonly I: number[], readonly J: number[], readonly L: number[]) {
    this.total = L.reduce((s, x) => s + x, 0);
  }
  /** Border length between the two sides. */
  border(side: boolean[]): number {
    let c = 0;
    for (let e = 0; e < this.I.length; e++) if (side[this.I[e]] !== side[this.J[e]]) c += this.L[e];
    return c;
  }
  /** Border length relative to a random split (about 1); lower = cleaner line. */
  cleanness(side: boolean[]): number { return this.border(side) / (0.5 * this.total); }
}

/** Small seeded random generator, so live results are repeatable. */
export class Rng {
  constructor(private seed: number) {}
  next(): number { this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff; return this.seed / 0x7fffffff; }
  gauss(): number {
    let u = 0, v = 0;
    while (!u) u = this.next();
    while (!v) v = this.next();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}

/** Random orthogonal m x m matrix (Gram-Schmidt on a Gaussian matrix). */
export function randOrth(m: number, rng: Rng): number[][] {
  const Q: number[][] = [];
  for (let i = 0; i < m; i++) {
    let v = Array.from({ length: m }, () => rng.gauss());
    for (const q of Q) { const d = v.reduce((s, x, k) => s + x * q[k], 0); v = v.map((x, k) => x - d * q[k]); }
    const nrm = Math.hypot(...v);
    Q.push(v.map((x) => x / nrm));
  }
  return Q;
}

/**
 * Quick in-browser check: Moran-band rotation (MSR). Known to be lenient with smooth maps
 * (see FINDINGS.md); the app labels it a "quick check" and uses the audited test for its own lines.
 * eig is the N x N eigenvector matrix, row-major.
 */
export function quickCheck(g: Graph, eig: Float32Array, f: number[], draws = 199): { obs: number; p: number } {
  const N = g.n;
  const mu = f.reduce((s, x) => s + x, 0) / N;
  const sd = Math.sqrt(f.reduce((s, x) => s + (x - mu) ** 2, 0) / N) || 1;
  const z = f.map((x) => (x - mu) / sd), c = new Float64Array(N);
  for (let k = 0; k < N; k++) { let s = 0; for (let i = 0; i < N; i++) s += eig[i * N + k] * z[i]; c[k] = s; }
  const obs = g.cleanness(splitOf(f));
  const rng = new Rng(777);
  let hits = 0;
  for (let t = 0; t < draws; t++) {
    const cr = new Float64Array(N);
    for (let x0 = 0; x0 < N; x0 += 12) {
      const x1 = Math.min(x0 + 12, N), m = x1 - x0, Q = randOrth(m, rng);
      for (let i = 0; i < m; i++) { let s = 0; for (let j = 0; j < m; j++) s += Q[i][j] * c[x0 + j]; cr[x0 + i] = s; }
    }
    const h = new Array<number>(N);
    for (let i = 0; i < N; i++) { let s = 0; for (let k = 0; k < N; k++) s += eig[i * N + k] * cr[k]; h[i] = s; }
    if (g.cleanness(splitOf(h)) <= obs) hits++;
  }
  return { obs, p: (hits + 1) / (draws + 1) };
}

/** log(distance to nearest B + off) - log(distance to nearest A + off); > 0 means an A store is closer. */
export function chainField(rep: [number, number][], A: [number, number][], B: [number, number][], off: number): number[] {
  const nearest = (xy: [number, number][]) => rep.map(([x, y]) => {
    let m = Infinity;
    for (const [a, b] of xy) { const d = (a - x) ** 2 + (b - y) ** 2; if (d < m) m = d; }
    return Math.sqrt(m);
  });
  const dA = nearest(A), dB = nearest(B);
  return dA.map((a, i) => Math.log(dB[i] + off) - Math.log(a + off));
}

/** Label-swap test for chain vs chain: shuffle which stores belong to which chain. */
export function chainTest(g: Graph, rep: [number, number][], A: [number, number][], B: [number, number][], off: number, draws = 199) {
  const obs = g.cleanness(splitOf(chainField(rep, A, B, off)));
  const pool = [...A, ...B], rng = new Rng(999);
  let hits = 0;
  for (let t = 0; t < draws; t++) {
    const p = [...pool];
    for (let i = p.length - 1; i > 0; i--) { const j = Math.floor(rng.next() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; }
    if (g.cleanness(splitOf(chainField(rep, p.slice(0, A.length), p.slice(A.length), off))) <= obs) hits++;
  }
  return { obs, p: (hits + 1) / (draws + 1) };
}

/**
 * Smooth the line by minimum cut (Potts model): each area pays sqrt(pop) * |f - median| to sit on
 * the "wrong" side, and every km of border costs lam. Solved exactly with Dinic's max-flow.
 */
export function minCutSides(g: Graph, f: number[], pop: number[], lam: number): boolean[] {
  const N = g.n, m = median(f), S = N, T = N + 1;
  const head = new Int32Array(N + 2).fill(-1), to: number[] = [], cap: number[] = [], nxt: number[] = [];
  const add = (u: number, v: number, c1: number, c2: number) => {
    to.push(v); cap.push(c1); nxt.push(head[u]); head[u] = to.length - 1;
    to.push(u); cap.push(c2); nxt.push(head[v]); head[v] = to.length - 1;
  };
  for (let i = 0; i < N; i++) {
    const w = Math.sqrt(Math.max(pop[i], 1)) * Math.abs(f[i] - m);
    if (f[i] > m) add(S, i, w, 0); else add(i, T, w, 0);
  }
  for (let e = 0; e < g.I.length; e++) add(g.I[e], g.J[e], lam * g.L[e], lam * g.L[e]);
  const level = new Int32Array(N + 2), it = new Int32Array(N + 2);
  const bfs = () => {
    level.fill(-1); level[S] = 0; const q = [S];
    for (let h = 0; h < q.length; h++) {
      const u = q[h];
      for (let e = head[u]; e !== -1; e = nxt[e]) if (cap[e] > 1e-9 && level[to[e]] < 0) { level[to[e]] = level[u] + 1; q.push(to[e]); }
    }
    return level[T] >= 0;
  };
  const dfs = (u: number, fl: number): number => {
    if (u === T) return fl;
    for (; it[u] !== -1; it[u] = nxt[it[u]]) {
      const e = it[u], v = to[e];
      if (cap[e] > 1e-9 && level[v] === level[u] + 1) {
        const d = dfs(v, Math.min(fl, cap[e]));
        if (d > 0) { cap[e] -= d; cap[e ^ 1] += d; return d; }
      }
    }
    return 0;
  };
  while (bfs()) { for (let i = 0; i < N + 2; i++) it[i] = head[i]; while (dfs(S, Infinity) > 0); }
  bfs();
  return Array.from({ length: N }, (_, i) => level[i] >= 0);
}

/** Slider position -> smoothing strength. */
export const lamOf = (v: number) => (v === 0 ? 0 : 2 * Math.pow(1.45, v));
