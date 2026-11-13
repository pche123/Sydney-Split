import re, sys, pandas as pd
PAIR = re.compile(r"'([^']+)': '(.*?)'(?=, '[^']+': '|\}$)")
def parse(s): return dict(PAIR.findall(s.strip()))
d = pd.read_csv(sys.argv[1])
d["t"] = d.tags.apply(parse)
bad = (d.t.apply(len) == 0).sum()
print("rows", len(d), "unparsed", bad)
d.to_pickle(sys.argv[2])
