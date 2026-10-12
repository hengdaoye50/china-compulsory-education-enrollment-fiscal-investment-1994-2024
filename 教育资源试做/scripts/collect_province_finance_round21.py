"""Round 21 public source collection. Keep functional accounts separate."""
from collect import batch
import sys
sys.stdout.reconfigure(encoding='utf-8')
rows=batch([
 ('province_finance_r21_anhui_2023_cee','https://www.cee.edu.cn/n171/n464/n525/c773678/content.html'),
 ('province_finance_r21_guangdong_2022','https://edu.gd.gov.cn/gkmlpt/content/4/4324/post_4324695.html'),
 ('province_finance_r21_guangdong_2022_cee','https://www.cee.edu.cn/n171/n464/n525/c773572/content.html'),
 ('province_finance_r21_ningxia_2023','https://jyt.nx.gov.cn/xwdt/tzgg/202501/t20250124_4805525.html'),
 ('province_finance_r21_guizhou_functional_2023_pdf','https://czt.guizhou.gov.cn/zwgk/zdlyxx/czys/202408/P020240821359121088999.pdf'),
], 'province_finance_r21_sources')
for r in rows:
 for a in r.get('links',[]):
  if any(x in a['url'].lower() for x in ['.xlsx','.xls','.pdf','.doc']):print(r['key'],a)
