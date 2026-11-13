// Everything that differs between cities lives here. The app itself (app.ts) is city-agnostic.
import type { CityData, Line, HeritageGroup, TimelineLine, TimelineGroup } from "./types";

export interface CityConfig {
  id: string;
  name: string;              // "Sydney"
  place: string;             // "suburb"
  places: string;            // "suburbs"
  placeholder: string;       // search box hint
  refLine: string;           // id of the line other lines are compared with
  refName: string;           // "Latte Line"
  storageKey: string;
  groups: [string, string][];
  herTab: string;
  herKinds: [string, string][];
  tKinds: [string, string, string][];   // id, tab label, list heading
  notes: Record<string, string>;
  tag: Record<string, string>;
  intro: { title: string; items: string[]; refButton: string; placeButton: string };
  creditHtml?: string;                  // shown in the intro and on the map
  asks: string;
  warnBullet: string;
  peakWord: string;
  movedTitle: string;
  movedNote: string;
  chainDefault: [string, string];
  chainOffset: number;                  // metres added to distances in "which store is closer"
  chainDraws: number;
  footer: {
    lines: (d: CityData) => string;
    timelineLines: string;
    timelineGroups: string;
    heritage: string;
    make: string;
  };
  herLabel: (h: HeritageGroup) => string;
  timelineGroupTitle: (g: TimelineGroup) => string;
  timelineGroupNote: (g: TimelineGroup) => string;
  lineExtra?: (l: Line, d: CityData) => string;
  timelineExtra?: (l: TimelineLine) => string;
  heritageExtra?: (h: HeritageGroup) => string;
  heritageClustering?: (h: HeritageGroup) => string | null;
  splitNote?: (l: Line, d: CityData) => string;
  links: { id: string; name: string; href: string }[];
}

const LINKS = [
  { id: "sydney", name: "Sydney", href: "./index.html" },
  { id: "tokyo", name: "Tokyo", href: "./tokyo.html" },
];

const HP = '<a href="https://webservice.recruit.co.jp/" target="_blank" rel="noopener">Powered by ホットペッパー Webサービス</a>';

export const SYDNEY: CityConfig = {
  id: "sydney", name: "Sydney", place: "suburb", places: "suburbs", placeholder: "e.g. Marrickville",
  refLine: "the-latte-line", refName: "Latte Line", storageKey: "ss_intro_seen",
  groups: [["Food", "Food & shops"], ["Night", "After dark"], ["Work", "Work (Census)"], ["Hidden", "Hidden lines (not just rich vs poor)"]],
  herTab: "Heritage",
  herKinds: [["birth", "Birthplace"], ["ancestry", "Ancestry"], ["religion", "Religion"]],
  tKinds: [["lines", "Lines", "Lines through time"], ["birth", "Birthplace", "Born in…"], ["religion", "Religion", "Religion"]],
  notes: {
    birth: "Migrants only: people born overseas. Their Australian-born kids aren't counted.",
    ancestry: "Self-described ancestry (up to two per person). Includes people born in Australia.",
    religion: "Religion as stated on the Census form. The question is optional.",
  },
  tag: {
    lines: "The invisible lines that cut Sydney in two. Pick a line, or look up your suburb.",
    heritage: "Where Sydney's communities live: birthplace, ancestry and religion.",
    overlay: "Put a heritage map under a line. Overlap isn't cause.",
    timeline: "Twenty years of Sydney, Census by Census: 2001 to 2021.",
    make: "Pick any two things and see if they split Sydney. The maths runs live in your browser.",
  },
  intro: {
    title: "Sydney has invisible lines.",
    items: [
      "<b>You've heard of the Latte Line.</b> We used the Census, café and chicken-shop maps, and liquor licences to find it, plus a dozen more.",
      "<b>Each line splits Sydney in two.</b> Orange is one side, blue is the other. Tap or hover over any suburb to see which side it's on.",
      "<b>We check every line against random versions of Sydney that are just as smooth,</b> so you can tell a real line from a gentle pattern or a coincidence.",
    ],
    refButton: "Show me the Latte Line", placeButton: "Find my suburb",
  },
  asks: "The Census doesn't ask about race or ethnicity. It asks where you were born, your ancestry and (optionally) your religion.",
  warnBullet: "Only people born overseas are counted. Their Australian-born kids aren't.",
  peakWord: "peak",
  movedTitle: "Clearly changed side",
  movedNote: "Only changes bigger than normal measurement wobble are listed.",
  chainDefault: ["Red Rooster", "Messina"], chainOffset: 200, chainDraws: 199,
  footer: {
    lines: (d) => `${d.meta.sources}. Covers ${d.meta.areas} Sydney suburbs. Shop and café locations come from OpenStreetMap, which volunteers map, so a few may be missing. A suburb's side describes the area, not the people in it.`,
    timelineLines: "ABS Census 2001–2021 (Time Series Profiles), all years mapped onto today's suburbs. Each year the line splits Sydney's suburbs in half, so it shows who is relatively high or low that year.",
    timelineGroups: "ABS Census 2001–2021 (Time Series Profiles), mapped onto today's suburbs. A place's colour describes the area, not anyone in it.",
    heritage: "ABS 2021 Census: country of birth (G09), year of arrival (G10), ancestry (G08), religion (G14). 300 urban SA2s. A place's colour describes the area, not anyone in it.",
    make: "Calculated live in your browser from the 2021 Census, OpenStreetMap venues (Nov 2026) and NSW liquor licences.",
  },
  herLabel: (h) => (h.kind === "birth" ? `Born in ${h.name}` : h.kind === "ancestry" ? `${h.name} ancestry` : h.name),
  timelineGroupTitle: (g) => (g.kind === "birth" ? `Born in ${g.name}` : g.name),
  timelineGroupNote: (g) => (g.kind === "birth" ? SYDNEY.notes.birth
    : SYDNEY.notes.religion + (g.name === "No religion" ? " From 2016 this also includes secular and other spiritual beliefs." : "")),
  heritageExtra: (h) => (h.kind !== "birth" ? "" : `<div class="box"><h3>What stands out across Sydney</h3><ul class="facts">
    <li>Newer communities cluster more, but only a bit. Vietnam-, Lebanon- and Greece-born communities stay clustered decades on.</li>
    <li>The most clustered (Iraq, Nepal, Afghanistan) include many recent and humanitarian arrivals.</li>
    <li>East and Southeast Asian-born communities share suburbs. So do English- and South African-born.</li>
    <li>New Zealanders are spread most evenly of all.</li></ul></div>`),
  splitNote: (l, d) => (l.id !== "the-hi-vis-line" ? "" : `<div class="box"><h3>Suburbs split down the middle</h3><p style="margin:0">Looking street by street, this line runs right through ${Object.keys(d.split).length} suburbs, including Parramatta, Ultimo, Haymarket and Kogarah.</p><p class="small">Search for a suburb to see if it's one of them.</p></div>`),
  links: LINKS,
};

const FOREIGN = "Foreign residents only: people living in Tokyo with a foreign nationality. Japan's Census doesn't ask about ethnicity, "
  + "ancestry or religion, so Japanese citizens of any background (including naturalised citizens and people with mixed heritage) "
  + "are counted as Japanese and not shown here. Maps show places, not people.";

export const TOKYO: CityConfig = {
  id: "tokyo", name: "Tokyo", place: "neighbourhood", places: "neighbourhoods", placeholder: "e.g. Koenji",
  refLine: "the-hi-vis-line", refName: "Hi-Vis Line", storageKey: "ts_intro_seen",
  groups: [["Work", "Work (Census)"], ["Homes", "People & homes (Census)"], ["Around", "Getting around (Census)"], ["Food", "Food & cafés"],
    ["Chains", "Chain wars"], ["Night", "After dark (HotPepper)"], ["Worship", "Shrines & temples"]],
  herTab: "Foreign residents",
  herKinds: [["foreign", "Foreign residents"]],
  tKinds: [["lines", "Lines", "Lines through time"], ["people", "People", "People"], ["homes", "Homes & work", "Homes & work"]],
  notes: { foreign: FOREIGN },
  tag: {
    lines: "The invisible lines that cut Tokyo in two. Pick a line, or look up your neighbourhood.",
    heritage: "Where Tokyo's foreign residents live. Census data only.",
    overlay: "Put the foreign-residents map under a line. Overlap isn't cause.",
    timeline: "Twenty years of Tokyo, Census by Census: 2000 to 2020.",
    make: "Pick any two things and see if they split Tokyo. The maths runs live in your browser.",
  },
  intro: {
    title: "Tokyo has invisible lines too.",
    items: [
      "<b>Sydney has its Latte Line.</b> We went looking for Tokyo's, using the 2020 Census, OpenStreetMap and HotPepper restaurant listings, and found lines for jobs, ramen, konbini, gyudon, izakaya and more.",
      "<b>Each line splits Tokyo in two.</b> Orange is one side, blue is the other. Tap or hover over any neighbourhood to see which side it's on.",
      "<b>We check every line against random versions of Tokyo that are just as smooth,</b> so you can tell a real line from a gentle pattern or a coincidence.",
    ],
    refButton: "Show me the Hi-Vis Line", placeButton: "Find my neighbourhood",
  },
  creditHtml: `Restaurant listings ${HP}`,
  asks: "Japan's Census asks about age, homes and jobs. It doesn't ask about religion, ancestry or income.",
  warnBullet: "Only foreign nationals are counted. Japanese citizens of any background aren't.",
  peakWord: "highest",
  movedTitle: "Biggest moves",
  movedNote: "Neighbourhoods that changed side with the biggest moves (top 10% of change).",
  chainDefault: ["Iekei ramen", "Hakata tonkotsu ramen"], chainOffset: 50, chainDraws: 99,
  footer: {
    lines: (d) => `${d.meta.sources}. Covers ${d.meta.areas} Tokyo neighbourhoods of about 30,000 people each, built by merging neighbouring 町 within each ward or city. Shops and cafés come from OpenStreetMap, which volunteers map, so some are missing. Restaurant prices and hours come from HotPepper, which lists mostly sit-down places. "Nearby" means within 1 km of a neighbourhood's centre. Neighbourhood names are romanised automatically and may have small mistakes. A neighbourhood's side describes the area, not the people in it.`,
    timelineLines: "Japan Census 2000–2020 (e-Stat small areas), each year shared onto today's neighbourhoods by area. Each year the line splits Tokyo's neighbourhoods in half, so it shows who is relatively high or low that year. The Census changed its job categories in 2010; comparing within each year keeps the job lines fair.",
    timelineGroups: "Japan Census 2000–2020 (e-Stat small areas), mapped onto today's neighbourhoods. A place's colour describes the area, not anyone in it.",
    heritage: "Japan 2020 Census, small-area table 2 (foreign population), e-Stat. Counts of foreign residents only; the small-area table doesn't say which countries people are from. A place's colour describes the area, not anyone in it.",
    make: `Calculated live in your browser from the 2020 Census, OpenStreetMap venues and HotPepper listings (Nov 2026). Restaurant listings ${HP}.`,
  },
  herLabel: (h) => (h.kind === "foreign" ? "Foreign residents" : h.name),
  timelineGroupTitle: (g) => g.name,
  timelineGroupNote: () => "Japan Census, 2000 to 2020. Each year's small areas are shared onto today's neighbourhoods by area.",
  heritageClustering: (h) => (h.kind === "foreign" ? `<li>How clustered: about <b>${Math.round((h.D ?? 0) * 100)}%</b> of foreign residents would have to move house to be spread evenly across Tokyo.</li>` : null),
  lineExtra: (l, d) => (l.id !== "shrines-vs-temples" ? "" : `<div class="box"><h3>Buildings, not beliefs</h3><p style="margin:0">This counts shrines and temples on the map, not what people believe.</p>
    <p class="small">Japan's Census doesn't ask about religion, so there is no data on who is Buddhist, Shinto or Christian in each neighbourhood. Many people visit both a shrine and a temple. Across neighbourhoods, the shrine-vs-temple balance barely relates to how many over-65s live there (rank correlation ${d.meta.worship_age}).</p></div>`),
  timelineExtra: (l) => (l.id !== "grey" ? "" : `<div class="box"><h3>The Grey Flip</h3><p style="margin:0">Where older people live has almost completely reshuffled.</p>
    <p class="small">In 2000 the inner wards were older than Tama. By 2020 it had reversed: new towns built for young families in the 1970s and 80s (Tama, Machida, Hachioji) aged in place, some going from 10% to over 40% aged 65+, while old downtown areas like Kuramae, Torigoe and Toranomon got younger.</p></div>`),
  links: LINKS,
};

export const CITIES: Record<string, CityConfig> = { sydney: SYDNEY, tokyo: TOKYO };
