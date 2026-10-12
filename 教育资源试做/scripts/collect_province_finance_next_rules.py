from collect import batch
import sys
sys.stdout.reconfigure(encoding='utf-8')
rows=batch([
 ('province_finance_next_hunan_2023_http','http://jyt.hunan.gov.cn/jyt/sjyt/xxgk/tzgg/202412/t20241226_1152042.html'),
 ('province_finance_next_hunan_2022_attachment','https://cms.jyt.hunan.gov.cn/zcms/contentcore/resource/download?ID=118281'),
 ('province_finance_next_hunan_reporting_2023_pdf','https://www.hnswxy.com/uploads/soft/240517/29-24051G51211.pdf'),
 ('province_finance_next_moe_standards_2023','https://www.moe.gov.cn/srcsite/A05/s7499/202310/t20231013_1085389.html'),
], 'province_finance_next_rule_sources')
for r in rows:
 for a in r.get('links',[]):
  if 'download?' in a['url'] or any(x in a['url'].lower() for x in ['.xls','.pdf','.doc']):print(r['key'],a)
