import { describe, it, expect } from "vitest";
import { verdict, invNorm, rankNormal, median, splitOf, Graph, minCutSides, chainField } from "../src/stats";

// A 4 x 4 grid of square areas, each border 1 km long.
function grid(k = 4) {
  const I: number[] = [], J: number[] = [], L: number[] = [];
  for (let r = 0; r < k; r++) for (let c = 0; c < k; c++) {
    const i = r * k + c;
    if (c + 1 < k) { I.push(i); J.push(i + 1); L.push(1); }
    if (r + 1 < k) { I.push(i); J.push(i + k); L.push(1); }
  }
  return new Graph(k * k, I, J, L);
}

describe("verdict", () => {
  it("maps the three audited tiers", () => {
    expect(verdict("line")[1]).toBe("Real line");
    expect(verdict("gentle")[1]).toBe("Real pattern, gentle");
    expect(verdict("chance")[1]).toBe("Could be chance");
  });
});

describe("rank-normal", () => {
  it("inverts the normal CDF", () => {
    expect(invNorm(0.5)).toBeCloseTo(0, 8);
    expect(invNorm(0.975)).toBeCloseTo(1.959964, 5);
  });
  it("gives ties the same score and fills missing values with the median", () => {
    const z = rankNormal([1, 2, 2, null, 5]);
    expect(z[1]).toBeCloseTo(z[2], 12);
    expect(z[0]).toBeLessThan(z[1]);
    expect(z[4]).toBeGreaterThan(z[2]);
  });
});

describe("border statistic", () => {
  it("a straight split of a grid has the shortest border", () => {
    const g = grid();
    const left = Array.from({ length: 16 }, (_, i) => i % 4 < 2);
    const checker = Array.from({ length: 16 }, (_, i) => ((i % 4) + Math.floor(i / 4)) % 2 === 0);
    expect(g.border(left)).toBe(4);
    expect(g.border(checker)).toBe(24);
    expect(g.cleanness(left)).toBeLessThan(g.cleanness(checker));
  });
  it("median split puts half the areas on each side", () => {
    const f = Array.from({ length: 16 }, (_, i) => i);
    expect(median(f)).toBe(7.5);
    expect(splitOf(f).filter(Boolean).length).toBe(8);
  });
});

describe("min-cut smoothing", () => {
  it("with no smoothing it reproduces the median split", () => {
    const g = grid(), f = Array.from({ length: 16 }, (_, i) => (i % 4) + 0.01 * i);
    expect(minCutSides(g, f, new Array(16).fill(1), 0)).toEqual(splitOf(f));
  });
  it("strong smoothing never makes the border longer", () => {
    const g = grid(), f = Array.from({ length: 16 }, (_, i) => Math.sin(i * 1.7));
    const raw = splitOf(f), smooth = minCutSides(g, f, new Array(16).fill(1), 5);
    expect(g.border(smooth)).toBeLessThanOrEqual(g.border(raw));
  });
});

describe("chain field", () => {
  it("is positive where chain A is closer", () => {
    const f = chainField([[0, 0], [10, 0]], [[0, 1]], [[10, 1]], 0.5);
    expect(f[0]).toBeGreaterThan(0);
    expect(f[1]).toBeLessThan(0);
  });
});
