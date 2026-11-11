(()=>{'use strict';
const A=ATLAS,R=A.regions,E=A.edges,N=R.length,baseSignals=A.signals.map(x=>({...x,type:'abs'}));
let signals=[...baseSignals],poiCounts={},osmItems=[],selected=new Set(baseSignals.filter(x=>x.id!=='cbd_distance').map(x=>x.id));
let candidates=[],researchPool=[],current=null,territoryCount=4,activeTab='discover',activeZones=[],activeRaw=[],activeScores=[],currentMajor=[],selectedRegion=-1;
let names={},savedRecipes={},view={z:1,x:0,y:0},osmLoaded=false,trialSeed=20261111;
const $=id=>document.getElementById(id),text=(id,v)=>$(id).textContent=v;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v)),sum=a=>a.reduce((s,x)=>s+x,0);
try{names=JSON.parse(localStorage.getItem('sydney-split-names-v4')||'{}')||{};savedRecipes=JSON.parse(localStorage.getItem('sydney-split-recipes-v4')||'{}')||{}}catch{names={};savedRecipes={}}
function saveStore(){try{localStorage.setItem('sydney-split-names-v4',JSON.stringify(names));localStorage.setItem('sydney-split-recipes-v4',JSON.stringify(savedRecipes))}catch{}}
let toastTimer;function toast(s){text('toast',s);$('toast').classList.remove('hidden');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.add('hidden'),2500)}
let adjacency=Array.from({length:N},()=>[]),polyBBox=[];
for(let e of E){adjacency[e.a].push([e.b,e.len]);adjacency[e.b].push([e.a,e.len])}
for(const r of R){let pts=[];for(const p of r.polys)for(const ring of p)pts.push(...ring);polyBBox.push([Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1])),Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))])}
let normal={},meta={};
function buildSignal(id){const values=R.map(r=>r.signals[id]);let a=values.map((v,i)=>({v,i})).filter(x=>typeof x.v==='number'&&Number.isFinite(x.v)).sort((a,b)=>a.v-b.v),res=Array(N).fill(0);
  if(a.length===0){normal[id]=res;meta[id]={coverage:0,spread:0};return}
  let i=0;while(i<a.length){let j=i+1;while(j<a.length&&a[j].v===a[i].v)j++;let rk=2*((i+j)*.5/a.length)-1;for(let k=i;k<j;k++)res[a[k].i]=rk;i=j}
  normal[id]=res;meta[id]={coverage:a.length/N,spread:new Set(a.map(x=>x.v)).size};
}
for(const s of signals)buildSignal(s.id);
function rng(seed){let x=seed>>>0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296}}
function blend(recipe){let arr=Array(N).fill(0),den=0;for(let [id,w] of recipe){let vec=normal[id];if(!vec)continue;den+=Math.abs(w);for(let i=0;i<N;i++)arr[i]+=w*vec[i]};den=den||1;return arr.map(x=>x/den)}
function smooth(vals,n=2,alpha=.32){let x=vals.slice();for(let t=0;t<n;t++){let y=x.slice();for(let i=0;i<N;i++){let nb=adjacency[i];if(!nb.length)continue;let den=0,s=0;for(let [j,len] of nb){let w=Math.min(2500,len);den+=w;s+=x[j]*w}y[i]=(1-alpha)*x[i]+alpha*(den?s/den:x[i])}x=y}return x}
function grouping(scores,thr=.5){let sorted=[...scores].sort((a,b)=>a-b),border=sorted[Math.floor((N-1)*thr)];let sides=scores.map(s=>s>=border?1:0);
 const lab=Array(N).fill(-1),comps=[],compSide=[];for(let i=0;i<N;i++){if(lab[i]>=0)continue;let id=comps.length,z=sides[i],stack=[i],pop=0,areas=0;lab[i]=id;while(stack.length){let q=stack.pop();pop+=R[q].pop||0;areas++;for(let [j] of adjacency[q])if(lab[j]<0&&sides[j]===z){lab[j]=id;stack.push(j)}}comps.push({pop,areas,side:z});compSide.push(z)}
 let largest=[-1,-1];for(let i=0;i<comps.length;i++){let z=comps[i].side;if(largest[z]<0||comps[i].pop>comps[largest[z]].pop)largest[z]=i}
 let all=[],main=[],mainContrast=0,borderLen=0;for(let t=0;t<E.length;t++){let e=E[t];if(sides[e.a]===sides[e.b])continue;all.push(t);borderLen+=e.len;if((lab[e.a]===largest[0]&&lab[e.b]===largest[1])||(lab[e.a]===largest[1]&&lab[e.b]===largest[0])){main.push(t);mainContrast+=e.len*Math.abs(scores[e.a]-scores[e.b])}}
 let popAll=sum(R.map(r=>r.pop||0)),coverage=largest.reduce((s,i)=>s+(i<0?0:comps[i].pop),0)/(popAll||1),lo=0,hi=0;for(let i=0;i<N;i++)if(sides[i])hi+=R[i].pop||0;else lo+=R[i].pop||0;
 return {sides,lab,largest,main,all,borderLen,mainContrast,coverage,balance:Math.min(lo,hi)/(Math.max(lo,hi)||1),majorLen:sum(main.map(i=>E[i].len))};
}
function scoreCandidate(recipe){let raw=blend(recipe),values=smooth(raw),g=grouping(values);
 const mainShare=g.majorLen/Math.max(1,g.borderLen),jump=g.majorLen?g.mainContrast/g.majorLen:0;
 // Heuristic: coherent two sides, relatively sharp contrast, non-degenerate population division,
 // and restrained boundary length. No inferential significance or validity claim.
 let cross=Math.min(1,jump/.25),complexity=1/(1+g.borderLen/210000),quality=100*(.29*g.coverage+.20*mainShare+.22*cross+.16*g.balance+.13*complexity);
 // Mild penalty for redundant feature bundles and large feature counts.
 let duplicate=0;for(let i=0;i<recipe.length;i++)for(let j=i+1;j<recipe.length;j++){
  const u=normal[recipe[i][0]],v=normal[recipe[j][0]];let cov=0,ua=0,vb=0;for(let t=0;t<N;t++){cov+=u[t]*v[t];ua+=u[t]*u[t];vb+=v[t]*v[t]};let corr=Math.abs(cov/Math.sqrt((ua||1)*(vb||1)));if(corr>.82)duplicate+=(corr-.82)
 }
 quality=quality/(1+.055*duplicate)-Math.max(0,recipe.length-3)*.35;
 return {recipe,score:Math.round(quality*10)/10,...g,raw,values};
}
// CONTIGUITY-CONSTRAINED HIERARCHICAL REGIONALIZATION (Ward-style).
// Only actual SA2 shared borders are visualized. Three isolated graph components arising
// from the exploratory geographic mask are attached by nearest-centroid virtual links,
// used only for computing the hierarchy; they are NOT geographic boundaries.
const REGION_COLORS={
 2:['#ee967d','#5ed3bd'],
 3:['#e98780','#efc47b','#60cdb7'],
 4:['#e88782','#f1b77d','#8dc39a','#719ad3'],
 5:['#e57b83','#eda67c','#ecd38b','#79c7a7','#7498d2'],
 6:['#db7689','#e69e74','#e8cf83','#a4cc8b','#63bfae','#8395d2'],
 7:['#dd7387','#e99873','#f0c17b','#d6d38b','#8acba0','#5fb5c2','#8e90d4']
};
const graphComponents=(()=>{let seen=new Uint8Array(N),out=[];
 for(let i=0;i<N;i++){if(seen[i])continue;let comp=[],stack=[i];seen[i]=1;while(stack.length){let u=stack.pop();comp.push(u);for(const [v] of adjacency[u])if(!seen[v]){seen[v]=1;stack.push(v)}}out.push(comp)}return out.sort((a,b)=>b.length-a.length)})();
const virtualLinks=[];for(const comp of graphComponents.slice(1)){let best=[-1,-1,Infinity];
 for(const i of comp)for(const j of graphComponents[0]){let d=(R[i].cx-R[j].cx)**2+(R[i].cy-R[j].cy)**2;if(d<best[2])best=[i,j,d]}
 if(best[0]>=0)virtualLinks.push({a:best[0],b:best[1],len:0,virtual:true});
}
class MinHeap{constructor(){this.h=[]}push(v){let a=this.h,i=a.length;a.push(v);while(i>0){let p=(i-1)>>1;if(a[p].cost<=v.cost)break;a[i]=a[p];i=p}a[i]=v}
 pop(){let a=this.h;if(!a.length)return null;let ret=a[0],v=a.pop();if(a.length){let i=0;while(i*2+1<a.length){let c=i*2+1;if(c+1<a.length&&a[c+1].cost<a[c].cost)c++;if(v.cost<=a[c].cost)break;a[i]=a[c];i=c}a[i]=v}return ret}}
function hierarchyFor(candidate){if(candidate.hierarchy)return candidate.hierarchy;
 const recipe=candidate.recipe,raw=candidate.raw,values=candidate.values,den=sum(recipe.map(x=>Math.abs(x[1])))||1;
 // Signed composite is primary; constituent signals contribute smaller profile information.
 const vec=R.map((r,i)=>[values[i]*1.8,...recipe.map(([id,w])=>.65*w/den*normal[id][i])]);
 const dims=vec[0].length,weights=R.map(r=>clamp(Math.sqrt((r.pop||12000)/15000),.65,1.55));
 const nodes=vec.map((row,i)=>({id:i,live:true,mean:row.slice(),weight:weights[i],sse:0,members:[i],near:new Map()}));
 for(const e of [...E,...virtualLinks]){const a=nodes[e.a],b=nodes[e.b],l=e.len;
   a.near.set(e.b,(a.near.get(e.b)||0)+l);b.near.set(e.a,(b.near.get(e.a)||0)+l)}
 let totals=Array(dims).fill(0),tw=sum(weights);for(let i=0;i<N;i++)for(let d=0;d<dims;d++)totals[d]+=weights[i]*vec[i][d]/tw;
 let totalVar=0;for(let i=0;i<N;i++)for(let d=0;d<dims;d++)totalVar+=weights[i]*(vec[i][d]-totals[d])**2;
 const heap=new MinHeap();
 function distance(a,b){let sq=0;for(let d=0;d<dims;d++)sq+=(a.mean[d]-b.mean[d])**2;return a.weight*b.weight/(a.weight+b.weight)*sq}
 function enqueue(a,b,len){let ward=distance(nodes[a],nodes[b]);heap.push({a,b,cost:ward/(1+Math.min(4,len/2200)*.09)+(.016/(1+len/1600))+(len===0?.045:0),ward})}
 for(const [i,node] of nodes.entries())for(const [j,l] of node.near)if(j>i)enqueue(i,j,l);
 let live=N,partitions={};
 function snapshot(k){let active=nodes.filter(n=>n.live),sorted=active.slice().sort((a,b)=>{
     let ma=sum(a.members.map(i=>values[i]))/a.members.length,mb=sum(b.members.map(i=>values[i]))/b.members.length;return ma-mb});
   let labels=Array(N).fill(-1);for(let z=0;z<sorted.length;z++)for(const i of sorted[z].members)labels[i]=z;
   let borders=[],boundaryMetres=0,jumps=0;for(let ix=0;ix<E.length;ix++){let e=E[ix];if(labels[e.a]!==labels[e.b]){borders.push(ix);boundaryMetres+=e.len;jumps+=e.len*Math.abs(values[e.a]-values[e.b])}}
   let within=sum(active.map(n=>n.sse)),explained=clamp(1-within/Math.max(1e-9,totalVar),0,1),jump=boundaryMetres?jumps/boundaryMetres:0;
   let popTotal=sum(R.map(r=>r.pop||0))||1;
   let stats=sorted.map((node,z)=>{let pop=sum(node.members.map(i=>R[i].pop||0)),pDen=pop||node.members.length;
     return {id:z+1,pop,n:node.members.length,share:pop/popTotal,mean:sum(node.members.map(i=>values[i]))/node.members.length,
       cx:sum(node.members.map(i=>R[i].cx*(R[i].pop||1)))/sum(node.members.map(i=>R[i].pop||1)),
       cy:sum(node.members.map(i=>R[i].cy*(R[i].pop||1)))/sum(node.members.map(i=>R[i].pop||1))}});
   let entropy= -sum(stats.map(s=>s.share>0?s.share*Math.log(s.share):0))/Math.log(k);
   let simplicity=1/(1+boundaryMetres/(k*63000)),contrast=clamp(jump/.32,0,1);
   let minShare=Math.min(...stats.map(s=>s.share)),popGuard=clamp(minShare/(.12/k),0,1);
   let quality=100*(.34*explained+.25*contrast+.22*entropy+.12*simplicity+.07*popGuard);
   partitions[k]={zones:labels,sides:labels,zoneStats:stats,zoneCount:k,all:borders,main:borders,score:Math.round(quality*10)/10,
       majorLen:boundaryMetres,borderLen:boundaryMetres,coverage:1,balance:entropy,explained,jump,virtualLinkCount:virtualLinks.length};
 }
 while(live>2){let edge=heap.pop();if(!edge)break;let a=nodes[edge.a],b=nodes[edge.b];if(!a?.live||!b?.live||!a.near.has(b.id))continue;
  let weight=a.weight+b.weight,mean=a.mean.map((x,d)=>(x*a.weight+b.mean[d]*b.weight)/weight),id=nodes.length;
  let newnode={id,live:true,mean,weight,sse:a.sse+b.sse+edge.ward,members:a.members.concat(b.members),near:new Map()};
  for(const source of [a,b])for(const [j,len] of source.near){if(j===a.id||j===b.id||!nodes[j].live)continue;newnode.near.set(j,(newnode.near.get(j)||0)+len)}
  a.live=false;b.live=false;for(const [j,len] of newnode.near){nodes[j].near.delete(a.id);nodes[j].near.delete(b.id);nodes[j].near.set(id,len)}
  nodes.push(newnode);for(const [j,len] of newnode.near)enqueue(id,j,len);
  live--;if(live<=7)snapshot(live);
 }
 candidate.hierarchy=partitions;return partitions;
}
function setTerritories(candidate,k=territoryCount){let partition=hierarchyFor(candidate)[k];if(!partition)throw Error('Partition unavailable at '+k+' territories');Object.assign(candidate,partition);return candidate;}
function diversify(a,b){let aa=a.zones,bb=b.zones,na=a.zoneCount,nb=b.zoneCount,m=Array.from({length:na},()=>Array(nb).fill(0)),ma=Array(na).fill(0),mb=Array(nb).fill(0);
 for(let i=0;i<N;i++){m[aa[i]][bb[i]]++;ma[aa[i]]++;mb[bb[i]]++}
 let mi=0,ha=0,hb=0;for(const u of ma){let p=u/N;if(p)ha-=p*Math.log(p)}for(const u of mb){let p=u/N;if(p)hb-=p*Math.log(p)}
 for(let i=0;i<na;i++)for(let j=0;j<nb;j++){let p=m[i][j]/N;if(p&&ma[i]&&mb[j])mi+=p*Math.log(p/((ma[i]/N)*(mb[j]/N)))}
 return ha&&hb?mi/Math.sqrt(ha*hb):0;
}
function rankForTerritories(k=territoryCount){let ranked=researchPool.slice();for(const c of ranked)setTerritories(c,k);ranked.sort((a,b)=>b.score-a.score);
 let chosen=[],counts={},need=Number($('howMany').value),maxSim=$('balance').value==='strict'?.80:.92;
 for(const c of ranked){if(chosen.some(x=>diversify(x,c)>maxSim))continue;
  if((counts[c.recipe.length]||0)>=Math.ceil(need/5)+2)continue;
  chosen.push(c);counts[c.recipe.length]=(counts[c.recipe.length]||0)+1;if(chosen.length>=need)break}
 if(chosen.length<need)for(const c of ranked){if(chosen.includes(c))continue;if(chosen.every(x=>diversify(x,c)<.96)){chosen.push(c);if(chosen.length>=need)break}}
 candidates=chosen;return chosen;
}
function identity(recipe,k=territoryCount){return 'zones'+k+'|'+recipe.map(([id,w])=>id+':'+(w>0?'+':'-')+Math.round(Math.abs(w)*10)/10).sort().join('|')}
function propose(c){let arr=[...c.recipe].sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])),short=id=>(signals.find(s=>s.id===id)||{short:id}).short;
 return arr.slice(0,2).map(x=>short(x[0])).join(' × ')+(territoryCount>2?' territories':' line');}
function candidateName(c){let key=identity(c.recipe);return names[key]||propose(c)}
function similarity(a,b){let match=0;for(let i=0;i<N;i++)if(a.sides[i]===b.sides[i])match++;let sim=match/N;return Math.max(sim,1-sim)}
async function discover(){const opts=[...selected].filter(id=>signals.some(s=>s.id===id)&&meta[id]?.coverage>.92&&meta[id]?.spread>=4);
 let kmin=Number($('minK').value),kmax=Number($('maxK').value),need=Number($('howMany').value);if(opts.length<2){toast('Select at least two populated signals');return}kmax=Math.min(opts.length,kmax);kmin=Math.min(kmin,kmax);
 $('loader').classList.remove('hidden');text('loadTitle','Mining the city’s divides');text('loadMessage','Sampling combinations of 2–'+kmax+' signals and evaluating their geographic structure.');$('loadProgress').style.width='5%';await new Promise(requestAnimationFrame);
 const must=$('mustInclude').value;if(must&&!opts.includes(must)){toast('Select the required signal before discovering');$('loader').classList.add('hidden');return}const random=rng(trialSeed+opts.length*17+osmItems.length+(must?must.length:0)),pool=[],dedup=new Set();
 // At least ~250 trials per supported subset size, with a cap for responsive local processing.
 let ks=[];for(let k=kmin;k<=kmax;k++)ks.push(k);
 const trials=Math.max(900,Math.min(2650,ks.length*335));
 for(let t=0;t<trials;t++){
  let k=ks[t%ks.length],ids=[...opts];for(let j=0;j<k;j++){let p=j+Math.floor(random()*(ids.length-j));[ids[j],ids[p]]=[ids[p],ids[j]]}
  let chosenIds=must?[must,...ids.filter(id=>id!==must).slice(0,k-1)]:ids.slice(0,k);let recipe=chosenIds.sort().map((id,j)=>[id,(id===must?1:(j===0?1:(random()>.38?1:-1)))*(.5+random())]);
  // Avoid trivial composites dominated by a single weight, and keep calculation reproducible.
  let key=recipe.map(([id,w])=>id+Math.sign(w)).join('|');if(dedup.has(key))continue;dedup.add(key);
  let out=scoreCandidate(recipe);if(out.main.length<4||out.majorLen<1700||out.coverage<.69)continue;
  pool.push(out);
  if(t%320===0){$('loadProgress').style.width=(8+84*t/trials)+'%';await new Promise(requestAnimationFrame)}
 }
 pool.sort((a,b)=>b.score-a.score);
 // Include strong binary seeds AND broader candidates so multipart discoveries are not
 // preselected solely by their ability to separate the city into two sides.
 let shortlist=pool.slice(0,190);let remainder=pool.slice(190);
 for(let i=0;i<Math.min(150,remainder.length);i++){let j=Math.floor(random()*remainder.length);shortlist.push(remainder.splice(j,1)[0])}
 researchPool=shortlist;
 for(let i=0;i<researchPool.length;i++){hierarchyFor(researchPool[i]);if(i%60===0){$('loadProgress').style.width=(87+12*i/researchPool.length)+'%';await new Promise(requestAnimationFrame)}}
 rankForTerritories(territoryCount);activeTab='discover';$('loader').classList.add('hidden');$('loadProgress').style.width='100%';renderLeaderboard();
 text('leaderDesc',`Evaluated ${pool.length.toLocaleString()} screening candidates; spatially clustered ${researchPool.length} candidate recipes. Ranked ${territoryCount}-territory partitions, with near-duplicates reduced. Exploratory scores only.`);
 if(candidates.length){applyCandidate(candidates[0],true);toast('Discovered '+candidates.length+' candidate maps with '+territoryCount+' territories')}else toast('No qualifying divisions; change signal selection');
}
function renderSignalList(){let q=$('signalSearch').value.trim().toLowerCase();let list=signals.filter(s=>(s.label+' '+s.short+' '+s.group).toLowerCase().includes(q));$('signalList').innerHTML=list.map(s=>`<label class="signal ${selected.has(s.id)?'checked':''} ${s.type==='poi'?'poi':s.group==='Spatial context'?'geo':s.group==='Local variation'?'variation':''} ${s.type==='poi'&&s.n<8?'weak':''}"><input type="checkbox" data-signal="${esc(s.id)}" ${selected.has(s.id)?'checked':''}><span>${esc(s.label)}</span><small>${s.type==='poi'?s.n+' POIs':s.group==='ABS indices'?'ABS':s.group==='Local variation'?'SA1':'GEOG'}</small><b class="dot"></b></label>`).join('');
 $('signalList').querySelectorAll('[data-signal]').forEach(el=>el.onchange=e=>{let id=el.dataset.signal;if(e.target.checked)selected.add(id);else selected.delete(id);renderSignalList();updateCount()});updateCount();}
function updateCount(){text('signalCount',`${selected.size} selected · ${signals.length} loaded`);const must=$('mustInclude'),old=must.value;must.innerHTML='<option value="">Any signal</option>'+signals.filter(s=>selected.has(s.id)).map(s=>`<option value="${esc(s.id)}">${esc(s.label)}</option>`).join('');must.value=selected.has(old)?old:'';}
function chipList(recipe){return recipe.map(([id,w])=>{let f=signals.find(s=>s.id===id)||{short:id,type:''};return `<span class="chip ${w<0?'neg':''} ${f.type==='poi'?'poi':''}">${w<0?'−':'+'}${esc(f.short)}</span>`}).join('')}
function renderLeaderboard(){const named=activeTab==='named',list=named?Object.entries(savedRecipes).filter(([key])=>key.startsWith('zones'+territoryCount+'|')).map(([key,recipe])=>({key,object:recipe.every(([id])=>normal[id])?setTerritories(scoreCandidate(recipe),Number(key.match(/^zones(\d+)/)?.[1])||2):null})).filter(x=>x.object):candidates.map(c=>({object:c}));
 text('namedCount',Object.keys(savedRecipes).length);$('tabDiscover').classList.toggle('active',!named);$('tabNamed').classList.toggle('active',named);text('leaderTitle',named?'Your named territories':`Top ${candidates.length} · ${territoryCount} territories`);
 $('results').innerHTML=list.map((item,i)=>{let c=item.object;return `<button class="result ${current===c?'active':''}" data-result="${candidates.indexOf(c)}"><div class="result-row"><span class="rank">${named?'★':'#'+String(i+1).padStart(2,'0')}</span><h3>${esc(candidateName(c))}</h3><div class="score">${c.score.toFixed(1)}<small>heuristic</small></div></div><div class="chips">${chipList(c.recipe)}</div><p class="note">${c.recipe.length} signals · ${c.zoneCount} territories · ${Math.round(c.majorLen/1000)} km total borders · ${Math.round(c.explained*100)}% profile variance separated</p></button>`}).join('')||'<div class="rank-foot">No lines in this view yet. Run discovery, select a candidate, then save your own name.</div>';
 $('results').querySelectorAll('[data-result]').forEach((b,i)=>b.onclick=()=>applyCandidate(list[i].object,true));
}
function applyCandidate(c,scroll=false){current=setTerritories(c);selectedRegion=-1;$('placeDetail').classList.add('hidden');drawMap();renderSelected();renderLeaderboard();if(scroll&&innerWidth<960)$('stage').scrollIntoView({behavior:'smooth',block:'start'})}
function poiToSvg(lon,lat){
 const tr=A.meta.svg_projection,rad=Math.PI/180,p=lat*rad,l=lon*rad,l0=153*rad,a=6378137,e2=.00669438002290,ep2=e2/(1-e2),k0=.9996;
 const sin=Math.sin(p),cos=Math.cos(p),T=Math.tan(p)**2,C=ep2*cos*cos,aa=cos*(l-l0),n=a/Math.sqrt(1-e2*sin*sin);
 const M=a*((1-e2/4-3*e2**2/64-5*e2**3/256)*p-(3*e2/8+3*e2**2/32+45*e2**3/1024)*Math.sin(2*p)+(15*e2**2/256+45*e2**3/1024)*Math.sin(4*p)-(35*e2**3/3072)*Math.sin(6*p));
 const east=500000+k0*n*(aa+(1-T+C)*aa**3/6+(5-18*T+T*T+72*C-58*ep2)*aa**5/120);
 const north=10000000+k0*(M+n*Math.tan(p)*(aa*aa/2+(5-T+9*C+4*C*C)*aa**4/24+(61-58*T+T*T+600*C-330*ep2)*aa**6/720));
 return [tr.ox+(east-tr.minx)*tr.factor,tr.oy+(tr.maxy-north)*tr.factor];
}
function renderPOIDots(){if(!current||!osmLoaded){$('poiLayer').innerHTML='';return 0}let relevant=new Set(current.recipe.map(x=>x[0].replace(/^osm_/,'')));let points=osmItems.filter(o=>o.found.some(f=>relevant.has(f)));
 // Cap only the number rendered for speed; model uses *all* matched POIs.
 const step=Math.max(1,Math.ceil(points.length/900));let shown=points.filter((_,i)=>i%step===0);$('poiLayer').innerHTML=shown.map(o=>{let [x,y]=poiToSvg(o.lon,o.lat);return `<circle class="venue-dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.4"/>`}).join('');return shown.length;
}
function renderHierarchyGraph(){if(!current)return;let cuts=hierarchyFor(current),leafOrder=[];
 function descendants(k,z){if(k===7)return [z];let child=new Set();for(let i=0;i<N;i++)if(cuts[k].zones[i]===z)child.add(cuts[k+1].zones[i]);
  return [...child].sort((a,b)=>cuts[k+1].zoneStats[a].mean-cuts[k+1].zoneStats[b].mean).flatMap(c=>descendants(k+1,c));}
 for(let z=0;z<2;z++)leafOrder.push(...descendants(2,z));
 let leafX={};leafOrder.forEach((z,j)=>leafX[z]=30+240*j/Math.max(1,leafOrder.length-1));
 let points={};for(let k=2;k<=7;k++)for(let z=0;z<k;z++){
  let leaves=descendants(k,z),x=sum(leaves.map(l=>leafX[l]*Math.max(1,cuts[7].zoneStats[l].pop)))/sum(leaves.map(l=>Math.max(1,cuts[7].zoneStats[l].pop)));
  points[k+'-'+z]={x,y:16+(k-2)*27};}
 let edges=[];for(let k=2;k<7;k++)for(let z=0;z<k+1;z++){
  let representative=cuts[k+1].zones.findIndex(a=>a===z),parent=cuts[k].zones[representative],a=points[k+'-'+parent],b=points[(k+1)+'-'+z],mid=(a.y+b.y)/2;
  edges.push(`<path d="M${a.x.toFixed(1)} ${a.y} C${a.x.toFixed(1)} ${mid.toFixed(1)} ${b.x.toFixed(1)} ${mid.toFixed(1)} ${b.x.toFixed(1)} ${b.y}" fill="none" stroke="#6a8b91" stroke-width="1.8" opacity=".55"/>`)}
 let nodes=[];for(let k=2;k<=7;k++)for(let z=0;z<k;z++){let p=points[k+'-'+z],color=REGION_COLORS[k][z],active=k===territoryCount;
 nodes.push(`<g data-depth="${k}" style="cursor:pointer"><circle cx="${p.x.toFixed(1)}" cy="${p.y}" r="${active?8:6}" fill="${color}" stroke="${active?'#e5ffa8':'#102d3b'}" stroke-width="${active?2.8:1.2}"/><title>${k} territories · zone ${z+1} · ${(cuts[k].zoneStats[z].share*100).toFixed(1)}% of residents · click to view</title></g>`)}
 $('hierarchyGraph').innerHTML=`<div class="tree-head"><b>THE SAME TREE · SIX LEVELS</b><span>Tap a row to reveal the split</span></div><svg viewBox="0 0 300 165" role="img" aria-label="Nested hierarchy from two to seven regional territories">${edges.join('')}${nodes.join('')}${[2,3,4,5,6,7].map(k=>`<g data-depth="${k}" style="cursor:pointer"><text x="3" y="${20+(k-2)*27}" font-size="11" fill="${k===territoryCount?'#e0f891':'#9db8bf'}" font-weight="800">${k}</text></g>`).join('')}</svg>`;
 $('hierarchyGraph').querySelectorAll('[data-depth]').forEach(n=>n.onclick=()=>{$('territoryCount').value=n.getAttribute('data-depth');$('territoryCount').dispatchEvent(new Event('change'))});
}
function drawMap(){if(!current)return;
 activeRaw=current.raw;activeScores=current.values;activeZones=current.zones;currentMajor=current.main;
 let pal=REGION_COLORS[current.zoneCount],regions=$('regionLayer').children;
 for(let i=0;i<N;i++){regions[i].setAttribute('fill',pal[activeZones[i]]);regions[i].setAttribute('fill-opacity','.87');regions[i].classList.toggle('selected',i===selectedRegion)}
 let markerCount=renderPOIDots();$('minorLayer').innerHTML='';
 $('boundaryLayer').innerHTML=`<path class="boundary" d="${current.all.map(i=>E[i].d).join('')}"/>`;
 $('zoneTagLayer').innerHTML=current.zoneStats.filter(z=>z.n>=2).map(z=>`<g class="zone-badge" transform="translate(${z.cx.toFixed(1)},${z.cy.toFixed(1)})"><circle r="15" fill="#0d2332" stroke="${pal[z.id-1]}" stroke-width="3"/><text text-anchor="middle" dy="4" fill="#fff" font-size="13" font-weight="800">${z.id}</text></g>`).join('');
 const pos=candidates.indexOf(current),name=candidateName(current);
 text('mapKicker',`DISCOVERY ${pos>=0?String(pos+1).padStart(2,'0'):'CUSTOM'} / ${N} SYDNEY SA2s · NESTED LEVEL ${current.zoneCount-1}`);
 text('mapTitle',name);
 text('mapSubtitle',`${current.zoneCount} territories from ${current.recipe.length} signals · ${Math.round(current.explained*100)}% profile variation separated · ${Math.round(current.majorLen/1000)} km total territory borders`);
 text('mapFooterTitle',`${current.zoneCount} nested territories · ${current.score.toFixed(1)}/100 exploratory score`);
 text('mapFooterDesc',`${current.all.length} shared-border segments between coloured regions. ${virtualLinks.length} computational bridge links repair isolated mask pockets (not drawn as borders).${markerCount?' Gold dots: '+markerCount+' mapped OSM venues.':''} No statistical significance implied.`);
 $('legend').innerHTML=current.zoneStats.map(z=>`<span><i style="background:${pal[z.id-1]}"></i>Zone ${z.id} · ${(z.share*100).toFixed(0)}%</span>`).join('');
 text('territorySummary',current.zoneStats.map(z=>`T${z.id}: ${z.n} areas`).join(' · '));renderHierarchyGraph();
}

function renderSelected(){if(!current)return;let key=identity(current.recipe);text('selectedId',candidates.indexOf(current)>=0?`#${candidates.indexOf(current)+1}`:'CUSTOM');text('customTitle',candidateName(current));
 text('customDesc',`${current.recipe.length} signals · ${current.zoneCount} nested territories · ${Math.round(current.majorLen/1000)} km of borders · ${(current.explained*100).toFixed(0)}% profile variation between territories. Name this entire map.`);
 $('lineName').value=names[key]||'';
 $('weightEdit').innerHTML=current.recipe.map(([id,w],k)=>{let f=signals.find(s=>s.id===id);return `<div class="weightrow"><span><b>${esc(f?.short||id)}</b><b id="wv${k}">${w>=0?'+':''}${Math.round(w*100)}%</b></span><input type="range" min="-150" max="150" step="10" value="${Math.round(w*100)}" data-w="${k}"></div>`}).join('');
 $('weightEdit').querySelectorAll('[data-w]').forEach(e=>e.oninput=()=>{let k=Number(e.dataset.w),value=Number(e.value)/100,currentRecipe=current.recipe.map(x=>[...x]);currentRecipe[k][1]=value;current=setTerritories(scoreCandidate(currentRecipe));drawMap();text('wv'+k,(value>=0?'+':'')+Math.round(value*100)+'%');text('customTitle','Custom mix (not re-ranked)')});
}
function showTip(ev,i){let t=$('tooltip'),b=$('stage').getBoundingClientRect(),r=R[i];t.innerHTML=`<b>${esc(r.name)}</b><br><span>Territory ${activeZones[i]+1} of ${current.zoneCount} · ${current.recipe.length} signals</span>`;t.style.left=clamp(ev.clientX-b.left+15,5,b.width-220)+'px';t.style.top=clamp(ev.clientY-b.top+12,5,b.height-75)+'px';t.classList.remove('hidden')}
function showDetail(i){selectedRegion=i;let r=R[i],top=current.recipe.slice().sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,6);$('placeDetail').innerHTML=`<button class="close" id="closeDetail">×</button><h3>${esc(r.name)}</h3><p>Territory ${activeZones[i]+1} of ${current.zoneCount}<br>${(r.pop||0).toLocaleString()} residents in constituent SA1 counts (2021)</p>`+top.map(([id])=>{let f=signals.find(s=>s.id===id),v=r.signals[id];return `<div class="detailrow"><span>${esc(f.short)}</span><b>${typeof v==='number'?v.toFixed(1):'—'}</b></div>`}).join('')+`<p style="font-size:9px">SA2: ${esc(r.id)} · index scores measure places, not individuals.</p>`;$('placeDetail').classList.remove('hidden');$('closeDetail').onclick=()=>{selectedRegion=-1;$('placeDetail').classList.add('hidden');drawMap()};drawMap()}
function initMap(){let g=$('regionLayer');const ns='http://www.w3.org/2000/svg';R.forEach((r,i)=>{let el=document.createElementNS(ns,'path');el.setAttribute('d',r.path);el.setAttribute('class','region');el.setAttribute('fill-rule','evenodd');el.onmousemove=e=>showTip(e,i);el.onmouseleave=()=>$('tooltip').classList.add('hidden');el.onclick=()=>{if(!isDragging)showDetail(i)};g.appendChild(el)});
 $('labelLayer').innerHTML=A.labels.map(l=>`<circle class="city-dot" cx="${l.x}" cy="${l.y}" r="2.5"/><text x="${l.x}" y="${l.y-10}" class="city-label">${esc(l.name)}</text>`).join('');
 function transform(){$('scene').setAttribute('transform',`translate(${view.x} ${view.y}) scale(${view.z})`)}
 function zoom(mult,x=550,y=500){let nz=clamp(view.z*mult,.72,5.5);view.x=x-(x-view.x)*nz/view.z;view.y=y-(y-view.y)*nz/view.z;view.z=nz;transform()}
 $('zoomIn').onclick=()=>zoom(1.32);$('zoomOut').onclick=()=>zoom(1/1.32);$('zoomReset').onclick=()=>{view={z:1,x:0,y:0};transform()};
 let map=$('map'),down=false,px=0,py=0,bx=0,by=0;map.addEventListener('wheel',e=>{e.preventDefault();let b=map.getBoundingClientRect();zoom(e.deltaY>0?.85:1.15,(e.clientX-b.left)/b.width*1100,(e.clientY-b.top)/b.height*1000)},{passive:false});
 map.addEventListener('pointerdown',e=>{if(e.button!==0)return;down=true;isDragging=false;px=e.clientX;py=e.clientY;bx=view.x;by=view.y;map.setPointerCapture(e.pointerId)});map.addEventListener('pointermove',e=>{if(!down)return;let dx=e.clientX-px,dy=e.clientY-py;if(Math.hypot(dx,dy)>4)isDragging=true;if(isDragging){let b=map.getBoundingClientRect();view.x=bx+dx/b.width*1100;view.y=by+dy/b.height*1000;transform();map.classList.add('drag')}});map.addEventListener('pointerup',()=>{down=false;map.classList.remove('drag');setTimeout(()=>{isDragging=false},80)});map.addEventListener('pointercancel',()=>{down=false;isDragging=false;map.classList.remove('drag')});
 $('placeSearch').oninput=()=>{let q=$('placeSearch').value.toLowerCase().trim(),v=R.map((r,i)=>({...r,i})).filter(r=>q.length>=2&&r.name.toLowerCase().includes(q)).slice(0,8);$('placeSuggest').innerHTML=v.map(r=>`<button data-idx="${r.i}">${esc(r.name)}</button>`).join('');$('placeSuggest').classList.toggle('hidden',!v.length);$('placeSuggest').querySelectorAll('button').forEach(b=>b.onclick=()=>{let i=Number(b.dataset.idx),r=R[i];view.z=2.2;view.x=550-2.2*r.cx;view.y=510-2.2*r.cy;transform();showDetail(i);$('placeSearch').value=r.name;$('placeSuggest').classList.add('hidden')})}
}
let isDragging=false;
function download(name,content,mime){let obj=new Blob([content],{type:mime}),url=URL.createObjectURL(obj),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);toast('Saved '+name)}
function exportCurrent(){if(!current)return;let cols=['SA2_CODE21','SA2_NAME21',...current.recipe.map(x=>x[0]),'composite','territory'];let rows=[cols.join(',')];R.forEach((r,i)=>rows.push([r.id,JSON.stringify(r.name),...current.recipe.map(([id])=>r.signals[id]??''),current.values[i].toFixed(4),current.zones[i]+1].join(',')));download('sydney-split-selected-line.csv',rows.join('\n'),'text/csv')}
function exportSVG(){if(!current)return;let s=$('map').cloneNode(true),ns='http://www.w3.org/2000/svg';s.setAttribute('width','1100');s.setAttribute('height','1000');let style=document.createElementNS(ns,'style');style.textContent='.region{stroke:#1d3949;stroke-width:1}.boundary{fill:none;stroke:#e1fca0;stroke-width:3.5}.boundary-soft{fill:none;stroke:#ffe0c0;stroke-width:1.5;opacity:.5}.city-label{fill:#e6f3e7;font:800 11px Arial;stroke:#0a2835;stroke-width:3;paint-order:stroke;text-anchor:middle}.city-dot{fill:#d9f581}.zone-badge{pointer-events:none}.venue-dot{fill:#ffe3a0;stroke:#142934;stroke-width:.8}';s.insertBefore(style,s.firstChild);let b=document.createElementNS(ns,'rect');b.setAttribute('width','1100');b.setAttribute('height','1000');b.setAttribute('fill','#0f2b39');s.insertBefore(b,style.nextSibling);download('sydney-split-'+identity(current.recipe).slice(0,22).replace(/[^a-z0-9]/gi,'-')+'.svg',new XMLSerializer().serializeToString(s),'image/svg+xml')}
function exportLeaderboard(){if(!candidates.length){toast('No discoveries to export');return}const q=s=>JSON.stringify(String(s));let header=['rank','suggested_or_saved_name','exploration_score','signal_count','signals','major_border_km','territories','variance_explained_pct','heuristic_not_p_value'];let rows=[header.join(',')];candidates.forEach((c,i)=>rows.push([i+1,q(candidateName(c)),c.score,c.recipe.length,q(c.recipe.map(([id,w])=>`${id}:${w.toFixed(2)}`).join(';')),Math.round(c.majorLen/1000),c.zoneCount,Math.round(c.explained*100),'true'].join(',')));download('sydney-split-top-lines.csv',rows.join('\n'),'text/csv')}
function exportNames(){const records=Object.entries(savedRecipes).map(([id,recipe])=>({name:names[id]||'Unnamed',recipe,score:recipe.every(([k])=>normal[k])?setTerritories(scoreCandidate(recipe),Number(id.match(/^zones(\d+)/)?.[1])||2).score:null}));download('sydney-split-named-lines.json',JSON.stringify({generatedAt:new Date().toISOString(),dataYear:2021,records},null,2),'application/json')}
// OSM connection and JSON import. Never fabricate missing records. One place with 0 mapped venues is not proof of absence.
const POI=[
 ['red_rooster','Red Rooster',t=>/\bred\s+rooster\b/i.test(t.name||'')],['el_jannah','El Jannah',t=>/el\s*jannah/i.test(t.name||'')],['kfc','KFC',t=>/\bkfc\b/i.test(t.name||'')],['oporto','Oporto',t=>/\boporto\b/i.test(t.name||'')],['mcdonalds','McDonald’s',t=>/mcdonald/i.test(t.name||'')],['hungry_jacks','Hungry Jack’s',t=>/hungry\s+jack/i.test(t.name||'')],
 ['cafes','Cafes',t=>t.amenity==='cafe'],['fast_food','Fast food',t=>t.amenity==='fast_food'],['restaurants','Restaurants',t=>t.amenity==='restaurant'],['pubs','Pubs',t=>t.amenity==='pub'],['bars','Bars',t=>t.amenity==='bar'],['bakeries','Bakeries',t=>t.shop==='bakery'],['supermarkets','Supermarkets',t=>t.shop==='supermarket'],['convenience','Convenience shops',t=>t.shop==='convenience'],['greengrocers','Greengrocers',t=>t.shop==='greengrocer'],['hairdressers','Hairdressers',t=>t.shop==='hairdresser'],['gyms','Gyms & fitness',t=>t.leisure==='fitness_centre'||t.leisure==='sports_centre'],['pilates_yoga','Pilates / yoga',t=>/pilates|yoga/i.test([t.sport,t.name].join(' '))],['libraries','Libraries',t=>t.amenity==='library'],['playgrounds','Playgrounds',t=>t.leisure==='playground'],['childcare','Childcare',t=>t.amenity==='kindergarten'],['ev_charge','EV chargers',t=>t.amenity==='charging_station']
];
const BBOX='(-34.18,150.69,-33.51,151.36)';
const QUERY=`[out:json][timeout:100];(nwr["amenity"~"^(cafe|fast_food|restaurant|pub|bar|library|kindergarten|charging_station)$"]${BBOX};nwr["shop"~"^(bakery|supermarket|convenience|greengrocer|hairdresser)$"]${BBOX};nwr["leisure"~"^(fitness_centre|sports_centre|playground)$"]${BBOX};nwr["name"~"(Red Rooster|El Jannah|KFC|Oporto|McDonald|Hungry Jack|Pilates|Yoga)",i]${BBOX};);out center tags;`;
function insideRing(pt,ring){let x=pt[0],y=pt[1],inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){let a=ring[i],b=ring[j],hit=((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-30)+a[0]);if(hit)inside=!inside}return inside}
function locate(lon,lat){for(let i=0;i<N;i++){let box=polyBBox[i];if(lon<box[0]||lon>box[2]||lat<box[1]||lat>box[3])continue;for(let polygon of R[i].polys){if(!insideRing([lon,lat],polygon[0]))continue;let inHole=false;for(let j=1;j<polygon.length;j++)if(insideRing([lon,lat],polygon[j]))inHole=true;if(!inHole)return i}}return -1}
function consumeOSM(payload){let elements=Array.isArray(payload)?payload:(payload.elements||payload.features||[]);if(!elements.length)throw Error('No OSM features found. Export raw Overpass JSON with tags and coordinates.');
 const grouped=Array.from({length:N},()=>Object.fromEntries(POI.map(x=>[x[0],0]))),seen=new Set();let valid=0,matched=0,footprint=[];
 for(const o of elements){let key=o.type&&o.id?o.type+':'+o.id:JSON.stringify(o.geometry?.coordinates||[])+o.properties?.name;if(seen.has(key))continue;seen.add(key);
  let lat=o.lat??o.center?.lat,lon=o.lon??o.center?.lon,t=o.tags??o.properties??{};
  if(o.type==='Feature'&&o.geometry){let g=o.geometry;let coord=g.type==='Point'?g.coordinates:g.type==='Polygon'?g.coordinates[0]?.[0]:null;if(coord){lon=coord[0];lat=coord[1]}}
  if(!Number.isFinite(lat)||!Number.isFinite(lon))continue;valid++;let region=locate(lon,lat);if(region<0)continue;matched++;let found=[];for(let [id,label,fn] of POI)if(fn(t)){grouped[region][id]++;found.push(id)}if(found.length)footprint.push({lat,lon,region,found,osm:o.type&&o.id?o.type+'/'+o.id:null})
 }
 if(matched<10)throw Error(`Only ${matched} mapped features land within the selected Sydney SA2s. Please check the bounding box and file.`);
 // Remove old cultural signals before replacement, preserve ABS selections.
 signals=signals.filter(s=>s.type!=='poi');for(let r of R)for(let k of Object.keys(r.signals))if(k.startsWith('osm_'))delete r.signals[k];
 let available=0;for(let [id,label] of POI){let n=sum(grouped.map(g=>g[id]));if(n<4)continue;available++;let sid='osm_'+id;signals.push({id:sid,label,short:label,group:'OpenStreetMap POIs',detail:'Current OSM tagged features; spatial smoothing and population adjustment',type:'poi',n});
  for(let i=0;i<N;i++){let nearby=adjacency[i].reduce((a,[j,len])=>a+.18*grouped[j][id]*Math.min(1,len/2500),0),count=grouped[i][id]+nearby;
   R[i].signals[sid]=Math.log1p(count/Math.max(1300,R[i].pop||0)*10000)}buildSignal(sid);
  if(n>=8)selected.add(sid)
 }
 osmLoaded=true;osmItems=footprint;$('osmCredit').innerHTML=' · © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>';text('sourceHead',`✓ ${baseSignals.length} ABS/geographic + ${available} OSM signals`);text('headStatus','ABS 2021 + LIVE / IMPORTED OSM');text('sourceDesc',`${footprint.length.toLocaleString()} OSM records matched the mapped regions; ${available} POI categories. Current venues are not from the 2021 Census period.`);
 text('osmStatus',`${valid.toLocaleString()} coordinate records; ${matched.toLocaleString()} inside mapped areas. POI signals scaled by population with neighbour smoothing.`);
 $('clearOSM').disabled=false;renderSignalList();return {available,matched};
}
async function connectOSM(){text('osmStatus','Requesting real tagged venues from OpenStreetMap (public Overpass service)…');$('loadOSM').disabled=true;
 try{let endpoint='https://overpass-api.de/api/interpreter';let ctl=new AbortController();let timer=setTimeout(()=>ctl.abort(),115000);
 let res=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:'data='+encodeURIComponent(QUERY),signal:ctl.signal});clearTimeout(timer);
 if(!res.ok)throw Error(`Overpass HTTP ${res.status}`);let d=await res.json();let out=consumeOSM(d);toast('Loaded '+out.matched.toLocaleString()+' OSM mapped records');await discover();}
 catch(e){text('osmStatus',`Live data unavailable: ${e.message}. Use “Overpass query” + Import POIs instead. No synthetic fallback was used.`);toast('No OSM data loaded — try import')}
 finally{$('loadOSM').disabled=false}
}
function openImport(){ $('osmFile').click() }
function setup(){const zonePicker=$('territoryCount');zonePicker.value=String(territoryCount);zonePicker.onchange=()=>{territoryCount=Number(zonePicker.value);if(researchPool.length){rankForTerritories(territoryCount);renderLeaderboard();if(current){setTerritories(current);drawMap();renderSelected()}text('leaderDesc',`Now displaying ${territoryCount} nested territories for each candidate. Rankings recalculate at this hierarchy level; geographic mask bridges are internal only.`)}else if(current){setTerritories(current);drawMap();renderSelected()}};for(let s of ['minK','maxK']){$(s).innerHTML=Array.from({length:7},(_,i)=>`<option value="${i+2}" ${s==='minK'&&i===0||s==='maxK'&&i===6?'selected':''}>${i+2} signals</option>`).join('')}
 $('signalSearch').oninput=renderSignalList;for(let [id,mode] of [['selectAll',1],['selectABS',2],['clearSignals',0]])$(id).onclick=()=>{selected=new Set(mode===1?signals.filter(s=>s.type!=='poi'||s.n>=8).map(s=>s.id):mode===2?baseSignals.map(s=>s.id):[]);renderSignalList()};
 $('discoverBtn').onclick=discover;$('exportBoard').onclick=exportLeaderboard;for(let [button,sig] of [['tryLatte','osm_cafes'],['tryRooster','osm_red_rooster'],['tryJannah','osm_el_jannah']])$(button).onclick=()=>{if(!signals.some(s=>s.id===sig)){toast('Load real OpenStreetMap records to explore this line');return}selected.add(sig);renderSignalList();$('mustInclude').value=sig;$('minK').value='2';$('maxK').value='8';discover()};$('tabDiscover').onclick=()=>{activeTab='discover';renderLeaderboard()};$('tabNamed').onclick=()=>{activeTab='named';renderLeaderboard()};$('saveName').onclick=()=>{if(!current)return;let key=identity(current.recipe),v=$('lineName').value.trim();if(!v){delete names[key];delete savedRecipes[key];toast('Removed custom name')}else{names[key]=v;savedRecipes[key]=current.recipe.map(x=>[...x]);toast('Saved “'+v+'” at '+territoryCount+' territories')}saveStore();renderSelected();renderLeaderboard();drawMap()};
 $('loadOSM').onclick=connectOSM;$('importOSM').onclick=openImport;$('osmFile').onchange=async e=>{let f=e.target.files?.[0];if(!f)return;try{let d=JSON.parse(await f.text()),out=consumeOSM(d);toast('Imported '+out.matched+' real OSM records');await discover()}catch(e){text('osmStatus','Import error: '+e.message);toast('Could not import POI JSON')}e.target.value=''};
 $('downloadQuery').onclick=()=>download('sydney-split-overpass.ql',QUERY,'text/plain');$('clearOSM').onclick=()=>{signals=[...baseSignals];for(let r of R)for(let k of Object.keys(r.signals))if(k.startsWith('osm_'))delete r.signals[k];selected=new Set(baseSignals.filter(x=>x.id!=='cbd_distance').map(x=>x.id));osmLoaded=false;osmItems=[];$('osmCredit').innerHTML='';$('clearOSM').disabled=true;text('sourceHead','✓ 11 real ABS & geographic signals');text('headStatus','ABS 2021 · REAL DATA');text('sourceDesc','Four official indexes plus SA1 variation, density and geographic context. Cultural signals become available when you load real OpenStreetMap records.');text('osmStatus','');renderSignalList();discover()};
 $('exportBtn').onclick=exportNames;$('exportCurrent').onclick=exportCurrent;$('exportMap').onclick=exportSVG;$('aboutBtn').onclick=()=>$('modal').classList.remove('hidden');$('modalClose').onclick=()=>$('modal').classList.add('hidden');$('modal').onclick=e=>{if(e.target===$('modal'))$('modal').classList.add('hidden')};
 renderSignalList();initMap();discover();
}
setup();
})();
