"""Join pre-extracted ABS SA1 SEIFA scores to geometry and publish browser data.
Usage: python scripts/build_derived.py --sa1-shape /path/SA1_2021_AUST_SHP_GDA2020.zip --sa2-shape /path/SA2_2021_AUST_SHP_GDA2020.zip
Run scripts/build_geography.py first if regenerating the spatial mask.
"""
from pathlib import Path
import argparse,json,numpy as np,pandas as pd,geopandas as gpd
from shapely.geometry import Polygon,MultiPolygon
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--sa1-shape',type=Path,required=True);p.add_argument('--sa2-shape',type=Path,required=True);a=p.parse_args()
base=json.loads((ROOT/'data/atlas_geography_base.json').read_text());R=base['regions'];ids={x['id'] for x in R}
sa1_source=ROOT/'data/sa1_seifa_2021_extracted.csv'
if not sa1_source.exists():sa1_source=ROOT/'data/sa1_seifa_2021_extracted.csv.bz2'
sa1=pd.read_csv(sa1_source,dtype={'SA1_CODE21':str});sa1['SA2_CODE21']=sa1.SA1_CODE21.str.slice(0,9);sa1=sa1[sa1.SA2_CODE21.isin(ids)].copy()
shape=gpd.read_file('/vsizip/'+str(a.sa1_shape.resolve()),columns=['SA1_CODE21','AREASQKM21','geometry'],ignore_geometry=True)
sa1=sa1.merge(shape[['SA1_CODE21','AREASQKM21']],on='SA1_CODE21',how='left',validate='one_to_one')
def wstd(v,w):
 mask=np.isfinite(v)&np.isfinite(w)&(w>0)
 if mask.sum()<3:return None
 av=np.average(v[mask],weights=w[mask]);return round(float(np.sqrt(np.average((v[mask]-av)**2,weights=w[mask]))),2)
def wshare(v,w,threshold):
 mask=np.isfinite(v)&np.isfinite(w)&(w>0)
 if not mask.any():return None
 return round(float(np.sum(w[mask]*(v[mask]<threshold))/sum(w[mask])*100),2)
metrics={};cut=float(sa1.IRSAD.quantile(.25))
for sa2,g in sa1.groupby('SA2_CODE21'):
 w=g.pop_sa1.to_numpy(float)
 metrics[sa2]={'pop_from_sa1':int(np.nansum(w)),'mean_sa1_density':round(float(np.nansum(g.pop_sa1)/np.nansum(g.AREASQKM21.replace(0,np.nan))),2),'irsad_dispersion':wstd(g.IRSAD.to_numpy(float),w),'ieo_dispersion':wstd(g.IEO.to_numpy(float),w),'ier_dispersion':wstd(g.IER.to_numpy(float),w),'disadvantaged_pocket_share':wshare(g.IRSAD.to_numpy(float),w,cut),'sa1_count':len(g)}
sa2geom=gpd.read_file('/vsizip/'+str(a.sa2_shape.resolve()),columns=['SA2_CODE21','AREASQKM21','geometry'])
sa2geom=sa2geom[sa2geom.SA2_CODE21.isin(ids)].to_crs('EPSG:7856').set_index('SA2_CODE21')
back=Transformer.from_crs('EPSG:7856','EPSG:4326',always_xy=True);trans=Transformer.from_crs('EPSG:4326','EPSG:7856',always_xy=True)
def rings_polygon(poly):
 result=[]
 for ring in [poly.exterior]+list(poly.interiors):
  xy=list(ring.coords)
  if len(xy)>=4:result.append([[round(x,5),round(y,5)] for x,y in (back.transform(x,y) for x,y in xy)])
 return result
def polys(g):
 if isinstance(g,Polygon):return [rings_polygon(g)]
 if isinstance(g,MultiPolygon):return [rings_polygon(p) for p in g.geoms if p.area>2000]
 return []
cbdx,cbdy=trans.transform(151.2093,-33.8688)
for r in R:
 k=r['id'];g=sa2geom.loc[k].geometry;m=metrics.get(k,{});pop=m.get('pop_from_sa1',r.get('pop'));r['pop']=pop;r['m']=m;r['area_km2']=round(float(sa2geom.loc[k]['AREASQKM21']),3)
 rep=g.representative_point();lng,lat=back.transform(rep.x,rep.y);r['ll']=[round(lng,5),round(lat,5)];r['polys']=polys(g.simplify(75,preserve_topology=True))
 t=r['s'];r['signals']={'irsd':t[0],'irsad':t[1],'ier':t[2],'ieo':t[3],'pop_density':round(float(pop/r['area_km2']),1) if pop and r['area_km2'] else None,'sa1_disparity':m.get('irsad_dispersion'),'education_disparity':m.get('ieo_dispersion'),'resources_disparity':m.get('ier_dispersion'),'pocket_disadvantage':m.get('disadvantaged_pocket_share'),'education_resource_gap':t[3]-t[2],'cbd_distance':round(float(np.hypot(rep.x-cbdx,rep.y-cbdy))/1000,2),'sa1_count':m.get('sa1_count')}
corners=[trans.transform(lon,lat) for lon in [150.69,151.36] for lat in [-34.18,-33.51]]
minx=min(q[0] for q in corners);maxx=max(q[0] for q in corners);miny=min(q[1] for q in corners);maxy=max(q[1] for q in corners)
factor=min((1100-110)/(maxx-minx),(1000-90)/(maxy-miny));OX=(1100-(maxx-minx)*factor)/2;OY=(1000-(maxy-miny)*factor)/2
base['meta']['svg_projection']={'minx':minx,'maxy':maxy,'factor':factor,'ox':OX,'oy':OY}
base['signals']=[
 {'id':'irsad','label':'Socioeconomic advantage','short':'Advantage','group':'ABS indices','detail':'2021 IRSAD; higher = relatively more advantage'},
 {'id':'irsd','label':'Lower disadvantage','short':'Lower disadvantage','group':'ABS indices','detail':'2021 IRSD; higher = less disadvantage'},
 {'id':'ier','label':'Economic resources','short':'Resources','group':'ABS indices','detail':'2021 IER; income and housing aspects'},
 {'id':'ieo','label':'Education & occupation','short':'Education','group':'ABS indices','detail':'2021 IEO; occupations and qualifications'},
 {'id':'pop_density','label':'Population density','short':'Density','group':'Spatial context','detail':'Derived population per SA2 land area'},
 {'id':'cbd_distance','label':'Distance from CBD','short':'CBD distance','group':'Spatial context','detail':'Euclidean CBD distance; geographic baseline, not causal'},
 {'id':'sa1_disparity','label':'Within-area advantage spread','short':'Advantage mix','group':'Local variation','detail':'Population-weighted SA1 IRSAD SD within SA2'},
 {'id':'education_disparity','label':'Within-area education spread','short':'Education mix','group':'Local variation','detail':'Population-weighted SA1 IEO SD within SA2'},
 {'id':'resources_disparity','label':'Within-area resources spread','short':'Resource mix','group':'Local variation','detail':'Population-weighted SA1 IER SD within SA2'},
 {'id':'pocket_disadvantage','label':'Low-advantage population share','short':'Disadvantage pockets','group':'Local variation','detail':'Weighted fraction SA1 population below *study-area SA1* IRSAD first quartile'},
 {'id':'education_resource_gap','label':'Education–resources gap','short':'Degrees vs money','group':'Derived contrasts','detail':'IEO minus IER index scores; not a money amount and not an independent Census measurement'},
]
(ROOT/'src/atlas-data.json').write_text(json.dumps(base,separators=(',',':')))
print('Wrote',len(R),'SA2 areas,',len(sa1),'SA1 rows,',len(base['signals']),'base signals')