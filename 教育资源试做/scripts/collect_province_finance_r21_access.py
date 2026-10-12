import sys
from collect import batch
sys.stdout.reconfigure(encoding='utf-8')
batch([
 ('province_finance_r21_anhui_2023_original','https://jyt.ah.gov.cn/public/7071/40737502.html'),
 ('province_finance_r21_yearbook_2023_publisher','https://www.zgtjcbs.com/zhuanyetongjinianjian/5676'),
 ('province_finance_r21_yearbook_2024_library_catalog','https://ci.nii.ac.jp/ncid/BD18086103'),
 ('province_finance_r21_xmu_cnki_access','https://library.xmu.edu.cn/info/1069/1080.htm'),
], 'province_finance_r21_access_sources')
