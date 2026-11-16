# Findings in plain words

What we know after testing 29 cities. A **real line** splits a city more cleanly than random versions of that city that are just as smooth. A **gentle pattern** is real geography, but a slope rather than a line. **Could be chance** means the data can't tell. Descriptions are about areas, not the people in them. Older, longer notes are in the git history; where they disagree with this page, this page is right.

How sure each result is: see "Confirmatory or exploratory?" in [HYPOTHESES.md](HYPOTHESES.md).

## The test works, and the usual one doesn't

- The standard method (Moran spectral randomisation) calls lines on 26–66% of maps that have none, and on 99% of Chicago-shaped gradients. Ours, as every verdict uses it, called 5 lines in 72 empty Chicago maps (6.9%, close to the 5% it should).
- Our quick version runs a little hot (up to 10%) because one map can't reveal how broad the city's biggest gradients are. The double-check fixes this.
- The cost of being careful is power. A real step of 2 standard deviations across a border is found about one time in ten; one of 3 standard deviations, 17–54% of the time. "Gentle" means "no step big enough to see", not "no step".

## What's out there

- **Few lines are real.** 4% of lines in the first 18 cities, 7% in the 11 held-out ones.
- **They're slopes, not cliffs.** 94–98% of lines have no sharp stretch at all.
- **Lines rarely travel.** Four lines that looked general in Australia, Japan and England (Factory, Laptop vs Hard Hat, Degree, Bicycle) failed in the US, New Zealand and Singapore.
- **The Latte Line travels.** Cafés and fast food sort apart in all 29 cities, and the line is real pooled over the held-out cities (p = 0.02, with the pooling checked against maps that have no line). Across all 27 cities it survives taking out how well OpenStreetMap is filled in and how dense each area is (p = 0.005); in the held-out cities alone that leaves it borderline (p = 0.09), and in San Francisco it is mostly a mapping-and-density pattern. We found this by pooling every line, not as a written prediction, so the European cities are its real test.
- **US cities split by shopping:** Starbucks vs Dunkin' (New York), Whole Foods vs Walmart (Los Angeles).
- **Money is a slope.** Rent forms a line in none of 14 cities. It follows the class divide (Hi-Vis or Degree) in all 12 Australian and US cities, and renting and car ownership in New Zealand.
- **No hidden grammar.** Neighbouring areas' four-letter "words" (work, inner city, age, nightlife) go together beyond chance in only 1 of 26 cities once the broad gradients the lines share are kept in the comparison.
- **Countries have their own lines.** The Factory Line is real across Australia although no single city (Melbourne, Brisbane, Perth, Adelaide) shows it alone, and across England. Bicycle (Australia), Degree (England) and Latte (US) lean the same way but don't pass. Found, not yet confirmed.
- **Pooling needs checking too.** Even with no line anywhere, our p-values lean slightly low, and adding up 11 cities turns that lean into 14% false alarms. Every pooled result here is checked against pools of maps with no line.
- **Area size doesn't change the story.** Rebuilding four US cities from census tracts changed 3 of 56 verdicts.

## The Latte Line on trial (Sydney)

| Claim | Verdict |
|---|---|
| The 2021 lockdown's councils of concern were its fast-food side | **Holds** (p = 0.004; 0.02 after allowing for the six claims tested). Where the rules fell, not whether they were fair. |
| There are Latte Lines in other cities | **Holds** (see above) |
| Melbourne's divide is weaker | **Holds** (2 real lines in Sydney, none in Melbourne) |
| It runs north-east vs south-west through Parramatta | Likely (p = 0.03; 0.08 corrected) |
| School results depend on the side | Likely, for degrees (p = 0.01; 0.07 corrected) |
| It's a figure of speech, not coffee data | The data has one anyway, but it's a slope |
| The Red Rooster Line | Half true (p = 0.03 alone, 0.16 corrected) |
| Haves vs have-nots | Money falls the same way, as a slope that follows jobs more than coffee |
| $1m homes above the line | Mostly (70% and 79%, not "almost always") |
| It's breaking down | Consistent: El Jannah vs Starbucks could be chance |
| It's hardening | **No**, up to 2021: the jobs line was a real line in every census from 2001, equally sharp |
| Heat and tree cover; "ethnic west" | Not tested (no data; and we never test heritage against a line) |

## Sydney and Tokyo

- **Sydney:** two real lines, Hi-Vis (logistics, driving and labouring jobs vs professionals) and Factory. 93% of suburbs stayed on the same side of the Hi-Vis Line from 2001 to 2021.
- **Tokyo:** no line passes. Its divides ride one very broad gradient from the bay-side wards to the Tama hills, so short borders are what its scale predicts.

## What's next

- Ten European cities (Paris, Lyon, Marseille, Berlin, Munich, Hamburg, Rome, Milan, Madrid, Barcelona) against 20 predictions already on record, including whether Berlin's lines still follow the Wall.
- The 2026 Australian Census, to test "hardening" properly.
