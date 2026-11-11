"""Regenerate the map's SA2 geometry from ABS 2021 SA2 boundaries and the
pre-extracted 2021 SA2 SEIFA CSV in data/. No simulated observations.
Usage: python scripts/build_geography.py --sa2-shape /path/SA2_2021_AUST_SHP_GDA2020.zip
"""
from pathlib import Path
import argparse, json, math
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
P=argparse.ArgumentParser();P.add_argument('--sa2-shape',type=Path,required=True);P.add_argument('--csv',type=Path,default=ROOT/'data/sa2_seifa_2021_selected.csv');args=P.parse_args()
raw=pd.read_csv(args.csv,dtype={'SA2_CODE21':str}).drop_duplicates('SA2_CODE21')
full=gpd.read_file('/vsizip/'+str(args.sa2_shape.resolve()),columns=['SA2_CODE21','SA2_NAME21','GCC_CODE21','geometry'])
full=full[full.GCC_CODE21=='1GSYD'].copy().merge(raw[['SA2_CODE21','IRSD','IRSAD','IER','IEO','population']],on='SA2_CODE21',how='left').to_crs(7856)
forward=Transformer.from_crs('EPSG:4326','EPSG:7856',always_xy=True)
corners=[forward.transform(lon,lat) for lon in [150.69,151.36] for lat in [-34.18,-33.51]]
minx=min(p[0] for p in corners);maxx=max(p[0] for p in corners); miny=min(p[1] for p in corners);maxy=max(p[1] for p in corners)
crop=box(minx,miny,maxx,maxy)
sel=full[full.geometry.intersects(crop)&full[['IRSD','IRSAD','IER','IEO']].notna().all(axis=1)].copy()
sel['geometry']=sel.geometry.intersection(crop)
sel=sel[~sel.geometry.is_empty].copy().reset_index(drop=True)
W,H=1100,1000;factor=min((W-110)/(maxx-minx),(H-90)/(maxy-miny));geoW=(maxx-minx)*factor;geoH=(maxy-miny)*factor;OX=(W-geoW)/2;OY=(H-geoH)/2
def fmt(v):return str(int(round(v,1))) if abs(v-round(v))<.09 else f'{v:.1f}'
def coord(x,y):return fmt(OX+(x-minx)*factor),fmt(OY+(maxy-y)*factor)
def rings_poly(p):
 cmds=[]
 for ring in [p.exterior]+list(p.interiors):
  cc=list(ring.coords)
  if len(cc)<4:continue
  cmds.append('M'+','.join(coord(*cc[0])));cmds.extend('L'+','.join(coord(*pt)) for pt in cc[1:]);cmds.append('Z')
 return ''.join(cmds)
def geo_to_svg(g):
 if g.is_empty:return ''
 if isinstance(g,Polygon):return rings_poly(g)
 if isinstance(g,MultiPolygon):return ''.join(rings_poly(p) for p in g.geoms if p.area>100)
 if isinstance(g,LineString):
  if g.length<50:return ''
  cc=list(g.coords);return 'M'+','.join(coord(*cc[0]))+''.join('L'+','.join(coord(*pt)) for pt in cc[1:])
 if isinstance(g,(MultiLineString,GeometryCollection)):return ''.join(geo_to_svg(q) for q in g.geoms)
 return ''
regions=[]
for i,r in sel.iterrows():
 poly=r.geometry.simplify(55,preserve_topology=True);point=r.geometry.representative_point();px,py=coord(point.x,point.y)
 regions.append({'id':str(r.SA2_CODE21),'name':r.SA2_NAME21,'s':[int(r[c]) for c in ['IRSD','IRSAD','IER','IEO']], 'pop':int(r.population) if pd.notna(r.population) else None,'path':geo_to_svg(poly),'cx':float(px),'cy':float(py)})
inds=sel.sindex.query(sel.geometry,predicate='intersects');edges=[]
for i,j in zip(*inds):
 if i>=j:continue
 line=sel.geometry.iloc[i].boundary.intersection(sel.geometry.iloc[j].boundary);length=line.length
 if length<170:continue
 path=geo_to_svg(line.simplify(30,preserve_topology=True))
 if path:edges.append({'a':int(i),'b':int(j),'len':int(length),'d':path})
lookup=[('PARRAMATTA',['Parramatta - North','Parramatta - South','Parramatta']),('CHATSWOOD',['Chatswood - East','Chatswood']),('BONDI',['Bondi - North','Bondi Beach']),('MANLY',['Manly - Fairlight','Manly']),('BANKSTOWN',['Bankstown - North','Bankstown']),('LIVERPOOL',['Liverpool - East','Liverpool']),('BLACKTOWN',['Blacktown - East','Blacktown']),('PENRITH',['Penrith - North','Penrith']),('HURSTVILLE',['Hurstville']),('SYDNEY CBD',['Sydney - Haymarket - The Rocks']),('NEWTOWN',['Newtown - Camperdown - Darlington','Newtown']),('MOSMAN',['Mosman']),('CRONULLA',['Cronulla - Kurnell - Bundeena','Cronulla'])]
labels=[]
for name,choices in lookup:
 for q in choices:
  matches=sel[sel.SA2_NAME21.str.contains(q,regex=False,case=False)]
  if len(matches):
   pos=matches.iloc[0].geometry.representative_point();px,py=coord(pos.x,pos.y);labels.append({'name':name,'x':float(px),'y':float(py)});break
base={'meta':{'year':2021,'n':len(regions),'edgeN':len(edges),'crs':'EPSG:7856','source':'ABS SEIFA 2021, ASGS 2021 GDA2020','bounds':[150.69,-34.18,151.36,-33.51]},'regions':regions,'edges':edges,'labels':labels}
( ROOT/'data/atlas_geography_base.json').write_text(json.dumps(base,separators=(',',':')))
print('Rebuilt',len(regions),'SA2 and',len(edges),'physical adjacency edges')
