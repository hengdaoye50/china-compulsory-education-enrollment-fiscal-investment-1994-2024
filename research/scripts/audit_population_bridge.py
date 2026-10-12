"""Official population source coverage audit. No population projection or panel merge."""
import json,hashlib
from decimal import Decimal as D
from parse import ROOT,save_csv

DATA=ROOT/'data'
names=['population_bridge_index_sources','population_bridge_catalog_sources','population_bridge_table_sources','population_bridge_annual_catalog_sources','population_bridge_annual_table_sources','population_bridge_census_year_note_sources']
sources=[]
for name in names:sources+=json.loads((ROOT/(name+'.json')).read_text(encoding='utf-8'))
assert len(sources)==24 and len({s['key'] for s in sources})==24
for s in sources:
 assert s['status']=='downloaded'
 assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256']
lookup={s['key']:s for s in sources}
save_csv(DATA/'population_bridge_source_registry.csv',[{k:v for k,v in s.items() if k!='links'} for s in sources])
# Direct transcription of national row and sampling note, checked against original image headers.
# Numbers are sample counts except 2020 census; never scale by the overall sampling fraction.
values={2017:('2-12','0.824',1145246,192353,822465,130428),2018:('2-12','0.8209',1144648,192963,815039,136645),2019:('2-12','0.780',1091876,183267,771326,137283),2020:('2-16','',1409778724,253383938,965759506,190635280),2021:('2-11','1.058',1494054,261376,1020258,212419),2022:('2-11','1.023',1443996,244887,984232,214877),2023:('2-11','1.051',1482230,242810,1011168,228252)}
coverage=[];checks=[]
for year,(table,rate,total,young,working,old) in values.items():
 s=lookup[f'population_yearbook{year+1}_region_age']
 gap=total-young-working-old
 assert abs(gap)<=1
 checks.append(dict(year=year,table_number=table,check='national broad-age components versus published row total',published_total_minus_components=gap,status='exact_match' if gap==0 else 'original_difference_retained',limit='2018/2021 original rows differ by one; cause not certified; no source correction or population expansion'))
 coverage.append(dict(year=year,volume=year+1,table_number=table,url=s['url'],raw_path=s['path'],sha256=s['sha256'],geography='31 provinces and national aggregate',age_groups='0-14;15-64;65+',count_type='census registered population at reference time' if year==2020 else 'population change survey sample counts',national_sampling_fraction_per_mille=rate,national_row_total=total,national_row_age0_14=young,national_row_age15_64=working,national_row_age65_plus=old,reference_time='2020-11-01 00:00' if year==2020 else 'annual survey; exact reference day not certified in this audit',stage_population_eligible=False,annual_population_count_merge_eligible=False,reason='broad ages do not identify school stages; mixed census/sample counts; no province-specific weights or variances certified',inspection='original image national row and heading visually checked'))
save_csv(DATA/'population_bridge_annual_coverage.csv',coverage)
save_csv(DATA/'population_bridge_transcription_checks.csv',checks)
age=[]
for key,title,geo,ages,eligible,limit in [
 ('population_census2020_region_age','2020 census table 1-5','31 provinces and national','five-year age groups',False,'cannot split 5-9 or 10-14 into province-specific school-age windows'),
 ('population_census2020_single_age','2020 census table 3-1','national only','single completed ages',False,'single time point and national scope; not an annual provincial school-age panel'),
 ('population_census2020_age_composition','2020 census table 3-2','31 provinces and national','0-14;15-64;65+',False,'broad-age composition can be background only; not stage-age population'),
 ('population_yearbook2024_single_age','2023 yearbook table 2-8','national only','five-year age groups',False,'file key inherited as single_age, but original table has five-year groups and sample counts')]:
 s=lookup[key];age.append(dict(title=title,url=s['url'],raw_path=s['path'],sha256=s['sha256'],geography=geo,age_resolution=ages,eligible_for_target_panel=eligible,limit=limit))
save_csv(DATA/'population_bridge_age_resolution.csv',age)
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
audit=dict(official_sources_saved_and_hash_verified=24,annual_province_age_tables_inspected=7,sample_count_tables=6,census_count_tables=1,transcription_cells=28,national_row_arithmetic_exact_matches=sum(r['status']=='exact_match' for r in checks),national_row_original_one_person_differences_retained=sum(r['status']=='original_difference_retained' for r in checks),age_resolution_records=4,eligible_provincial_annual_stage_age_tables_among_inspected=0,population_panel_merged=False,sample_counts_expanded=False,fixed_geography_bridge_completed=False,protected_files_unchanged=True,limit='coverage findings apply to inspected sources only; not proof that no other suitable source exists')
(DATA/'population_bridge_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
