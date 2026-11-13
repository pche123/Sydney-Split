// Shape of the per-city data file written by the pipeline (app/data/<city>.json).

export interface Area { name: string; short: string; d: string; cx: number; cy: number }

export interface Line {
  id: string; name: string; group: string;
  a: string; b: string;                  // words for the orange (a) and blue (b) sides
  p: number; tier: "line" | "gentle" | "chance";
  p_geo?: number | null; p_edge?: number | null; p_old?: number;
  side: number[]; cut: string;
  more: string[]; less: string[]; ex_a: string[]; ex_b: string[];
  latte_agree: number; adjusted?: boolean;
}

export interface HeritageGroup {
  id: string; kind: string; name: string; pct: number; people: number;
  lq: number[]; peaks: [string, number, number][];
  D?: number | null; D_rank?: number; D_of?: number; recent?: number | null; shares_with: string[];
}

export interface TimelineLine {
  id: string; name: string; a: string; b: string;
  sides: number[][]; cuts: string[]; same_as_2001: number[];
  toA: number[]; toB: number[]; persist_p: number; null_agree: number;
  stat: number[]; stat_label: string;
}

export interface TimelineGroup { kind: string; name: string; pct: number[]; lq: number[][]; D: number[] }

export interface Signal { id: string; label: string; more: string; less: string; group: string; v: (number | null)[] }
export interface Brand { name: string; n: number; xy: [number, number][]; vb: [number, number][] }

export interface MakeData {
  n: number; I: number[]; J: number[]; L: number[]; eig: string; pop: number[]; ep: string[];
  rep: [number, number][]; signals: Signal[]; brands: Brand[];
}

export interface CityData {
  w: number; h: number;
  areas: Area[]; empty: { name: string; d: string }[];
  lines: Line[]; labels: { i: number; t: string; tier?: number }[];
  meta: { sources: string; areas: number; explain?: Record<string, string>; worship_age?: number; [k: string]: unknown };
  split: Record<string, [string, number, number]>;
  heritage: HeritageGroup[];
  timeline: { years: string[]; lines: TimelineLine[]; groups: TimelineGroup[] };
  make: MakeData;
}
