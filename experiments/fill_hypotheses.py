"""Write the scored results into the Phase 1 column of HYPOTHESES.md.

    python experiments/fill_hypotheses.py results/phase1/hypotheses.csv

Each cell becomes: symbol, the figure behind it, and the p-value where a test applies.
✓ held · ✗ failed · ◐ partly held · – not testable with this phase's data.
"""
import os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); MD = os.path.join(HERE, "..", "HYPOTHESES.md")
SYM = {"held": "✓", "failed": "✗", "partly": "◐", "not testable": "–"}
d = pd.read_csv(sys.argv[1]).set_index("id")

def fmt_p(p):
    if pd.isna(p): return ""
    return " (p < 0.001)" if p < 0.001 else f" (p = {p:.3f})"

out = []
for line in open(MD, encoding="utf-8").read().split("\n"):
    m = re.match(r"\| \*{0,2}(\d+)\*{0,2} \|", line)
    if m and int(m.group(1)) in d.index:
        r = d.loc[int(m.group(1))]
        cells = line.split("|")                       # ['', ' # ', ' hyp ', ' holds if ', ' phase0 ', ' phase1 ', '']
        cell = f"{SYM[r.verdict]} {r.figure}{fmt_p(r.p)}".replace("|", "/")
        cells[-2] = f" {cell} "
        line = "|".join(cells)
    out.append(line)
open(MD, "w", encoding="utf-8").write("\n".join(out))
print(d.verdict.value_counts().to_string())
