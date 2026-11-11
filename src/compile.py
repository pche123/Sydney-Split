"""Build standalone index.html from HTML template, inline source and JSON."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
t=(root/'src/index.template.html').read_text(encoding='utf-8')
app=(root/'src/app.js').read_text(encoding='utf-8')
data=(root/'src/atlas-data.json').read_text(encoding='utf-8')
json.loads(data)
assert t.count('__ATLAS_DATA__')==1 and t.count('__APP_JS__')==1, 'missing template markers'
t=t.replace('__ATLAS_DATA__',data).replace('__APP_JS__',app)
(root/'index.html').write_text(t,encoding='utf-8')
print('Wrote index.html,',len(t),'characters')
