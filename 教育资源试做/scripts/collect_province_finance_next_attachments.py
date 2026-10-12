from collect import ROOT, batch
import json, sys
from urllib.parse import quote, urlsplit, urlunsplit
sys.stdout.reconfigure(encoding='utf-8')
def encoded(url):
 p=urlsplit(url)
 return urlunsplit((p.scheme,p.netloc,quote(p.path,safe='/%'),p.query,p.fragment))
jobs=[
 ('province_finance_next_sichuan_2023_xlsx', encoded('https://edu.sc.gov.cn/scedu/c100495/2024/12/24/86ba46d710d546c18384838df095af05/files/2023年全省教育经费执行情况统计表-2024.12.23.xlsx')),
 ('province_finance_next_sichuan_2023_cee_xlsx','https://www.cee.edu.cn/n171/n464/n525/c773296/part/773302.xlsx'),
 ('province_finance_next_hubei_2023_xlsx','https://jyt.hubei.gov.cn/zfxxgk/fdzdgknr_GK2020/tjxx_GK2020/202412/P020241226335741972813.xlsx'),
 ('province_finance_next_hubei_2023_cee_xlsx','https://www.cee.edu.cn/n171/n464/n525/c773255/part/773261.xlsx'),
 ('province_finance_next_shandong_2023_attachment','http://edu.shandong.gov.cn/module/download/downfile.jsp?classid=0&filename=5469dddcc5714edc9bc17a676a59e6ff.doc'),
 ('province_finance_next_hunan_2023','https://jyt.hunan.gov.cn/jyt/sjyt/xxgk/tzgg/202412/t20241226_1152042.html'),
 ('province_finance_next_hunan_2022_http','http://jyt.hunan.gov.cn/jyt/sjyt/xxgk/tzgg/202312/t20231225_32609079.html'),
 ('province_finance_next_cee_index','https://www.cee.edu.cn/n171/n464/n525/index.html'),
]
rows=batch(jobs,'province_finance_next_attachment_sources')
for r in rows:
 for a in r.get('links',[]):
  if any(x in a['url'].lower() for x in ['.xls','.pdf','.doc']) or a['label'] in ['湖南','山东','安徽','广东']:
   print(r['key'],a)
