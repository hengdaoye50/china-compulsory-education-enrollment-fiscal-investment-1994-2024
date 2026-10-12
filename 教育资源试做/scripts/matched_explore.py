"""Within-province descriptive pairing; no causal identification."""
import csv,json,math,statistics
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=list(csv.DictReader(open(ROOT/'data/education_resource_panel.csv',encoding='utf-8-sig')))
lookup={(r['province'],r['stage'],int(r['year'])):r for r in raw}
observations=[]
for r in raw:
    y=int(r['year'])
    if r['province']=='全国' or y==2013:continue
    prev=lookup[r['province'],r['stage'],y-1]
    d={'province':r['province'],'stage':r['stage'],'year':y}
    for field in ['students','teachers','classes']:
        d[field]=100*(float(r[field])/float(prev[field])-1)
        assert abs(d[field]-float(r[field+'_growth_pct']))<1e-8
        d[field+'_source']=r[field+'_source']
        d[field+'_previous_source']=prev[field+'_source']
    observations.append(d)
def match(tolerance=1,gap=4,end=2024):
    pairs=[]
    for province,stage in sorted({(r['province'],r['stage']) for r in observations}):
        group=[r for r in observations if r['province']==province and r['stage']==stage and r['year']<=end]
        pos=[r for r in group if r['students']>=1]
        neg=[r for r in group if r['students']<=-1]
        @lru_cache(None)
        def solve(i,mask):
            if i==len(pos):return (0,0.,0,())
            best=solve(i+1,mask)
            for j,n in enumerate(neg):
                diff=abs(pos[i]['students']+n['students']);distance=abs(pos[i]['year']-n['year'])
                if mask>>j&1 or diff>tolerance or distance>gap:continue
                rest=solve(i+1,mask|1<<j)
                cand=(rest[0]+1,rest[1]+diff,rest[2]+distance,((i,j),)+rest[3])
                if (-cand[0],cand[1],cand[2],cand[3])<(-best[0],best[1],best[2],best[3]):best=cand
            return best
        for i,j in solve(0,0)[3]:
            p,n=pos[i],neg[j]
            row={'province':province,'stage':stage,'growth_year':p['year'],'shrink_year':n['year'],'magnitude_gap_pp':abs(p['students']+n['students']),'year_gap':abs(p['year']-n['year'])}
            for prefix,d in [('growth',p),('shrink',n)]:
                for field in ['students','teachers','classes']:
                    row[prefix+'_'+field+'_pct']=d[field]
                    row[prefix+'_'+field+'_source']=d[field+'_source']
                    row[prefix+'_'+field+'_previous_source']=d[field+'_previous_source']
            pairs.append(row)
    return pairs
def write(name,rows):
    with open(ROOT/'data'/name,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def summarize(pairs,scenario):
    result=[]
    for stage in ['primary','junior']:
        ps=[p for p in pairs if p['stage']==stage]
        for phase in ['growth','shrink']:
            r={'scenario':scenario,'stage':stage,'phase':'增长' if phase=='growth' else '收缩','n':len(ps),'provinces':len({p['province'] for p in ps})}
            for field in ['students','teachers','classes']:r['median_'+field+'_pct']=statistics.median(p[phase+'_'+field+'_pct'] for p in ps) if ps else None
            r['median_magnitude_gap_pp']=statistics.median(p['magnitude_gap_pp'] for p in ps) if ps else None
            result.append(r)
    return result
pairs=match();write('matched_pairs.csv',pairs)
summaries=summarize(pairs,'主样本：幅度差≤1个百分点、年份差≤4年')
write('matched_phase_summary.csv',summaries)
sensitivity=[]
for tolerance,gap,end in [(0.5,4,2024),(1,3,2024),(2,4,2024),(1,4,2023)]:
    sensitivity+=summarize(match(tolerance,gap,end),f'幅度差≤{tolerance}个百分点、年份差≤{gap}年、截止{end}')
write('matched_sensitivity.csv',sensitivity)
# Check constraints and independently recompute selected growth values from levels.
used=set()
for p in pairs:
    assert p['magnitude_gap_pp']<=1 and p['year_gap']<=4
    for phase in ['growth','shrink']:
        key=(p['province'],p['stage'],p[phase+'_year']);assert key not in used;used.add(key)
        for field in ['students','teachers','classes']:
            a=float(lookup[key][field]);b=float(lookup[key[0],key[1],key[2]-1][field])
            assert abs((a-b)/b*100-p[phase+'_'+field+'_pct'])<1e-8
audit={'pair_count':len(pairs),'unique_observations':len(used),'checks':'No reuse; same province/stage; magnitude/year constraints; selected growth recomputed from raw levels','eligible_observations':sum(abs(r['students'])>=1 for r in observations),'summary':summaries,'sensitivity':sensitivity}
(ROOT/'data/matched_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
