from collect import batch
import sys
sys.stdout.reconfigure(encoding='utf-8')
rows=batch([
 ('province_finance_r21_anhui_2023_xlsx','https://jyt.ah.gov.cn/group3/M00/11/BA/wKg86menG1qAZrN7AADme8oj7LQ95.xlsx'),
 ('province_finance_r21_anhui_2023_cee_xlsx','https://www.cee.edu.cn/n171/n464/n525/c773678/part/773684.xlsx'),
 ('province_finance_r21_guangdong_2022_xlsx','https://edu.gd.gov.cn/attachment/0/539/539530/4324695.xlsx'),
 ('province_finance_r21_guangdong_2022_cee_xlsx','https://www.cee.edu.cn/n171/n464/n525/c773572/part/773598.xlsx'),
 ('province_finance_r21_ningxia_2023_table1_pdf','https://jyt.nx.gov.cn/xwdt/tzgg/202501/P020250124356208784170.pdf'),
 ('province_finance_r21_ningxia_2023_table2_pdf','https://jyt.nx.gov.cn/xwdt/tzgg/202501/P020250124356208922981.pdf'),
 ('province_finance_r21_ningxia_2023_table3_pdf','https://jyt.nx.gov.cn/xwdt/tzgg/202501/P020250124356209013303.pdf'),
 ('province_finance_r21_ningxia_2023_table4_pdf','https://jyt.nx.gov.cn/xwdt/tzgg/202501/P020250124356209092264.pdf'),
 ('province_finance_r21_guizhou_functional_2022_pdf','https://czt.guizhou.gov.cn/zwgk/zdlyxx/czys/202308/P020230816545822790622.pdf'),
], 'province_finance_r21_attachment_sources')
