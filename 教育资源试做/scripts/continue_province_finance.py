"""Collect next provincial notices; render Fujian for field-level visual audit."""
from collect import ROOT, batch
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
import sys
sys.stdout.reconfigure(encoding='utf-8')

jobs = [
 ('province_finance_next_sichuan_2023', 'https://edu.sc.gov.cn/scedu/c100495/2024/12/24/86ba46d710d546c18384838df095af05.shtml'),
 ('province_finance_next_sichuan_2023_cee', 'https://www.cee.edu.cn/n171/n464/n525/c773296/content.html'),
 ('province_finance_next_shandong_2023', 'https://edu.shandong.gov.cn/art/2024/12/19/art_107114_10335894.html?xxgkhide=1'),
 ('province_finance_next_shandong_2023_cee', 'https://www.cee.edu.cn/n171/n464/n525/c775550/content.html'),
 ('province_finance_next_hubei_2023', 'https://jyt.hubei.gov.cn/zfxxgk/fdzdgknr_GK2020/tjxx_GK2020/202412/t20241226_5475533.shtml'),
 ('province_finance_next_hubei_2023_cee', 'https://www.cee.edu.cn/n171/n464/n525/c773255/content.html'),
 ('province_finance_next_hunan_2022', 'https://jyt.hunan.gov.cn/jyt/sjyt/xxgk/tzgg/202312/t20231225_32609079.html'),
]
if __name__ == '__main__':
 rows = batch(jobs, 'province_finance_next_sources')
 for r in rows:
  for a in r.get('links', []):
   if any(x in a['url'].lower() for x in ['.xlsx','.xls','.pdf','.doc']):
    print(r['key'], a)
 out = ROOT/'.tmp/fujian_2023_visual'; out.mkdir(parents=True, exist_ok=True)
 doc = pdfium.PdfDocument(ROOT/'raw/province_finance_fujian_2023_pdf.pdf')
 print('Fujian PDF pages:',len(doc))
 for start in range(0,len(doc),8):
  sheet=Image.new('RGB',(1600,1120),'white'); draw=ImageDraw.Draw(sheet)
  for i in range(start,min(start+8,len(doc))):
   im=doc[i].render(scale=1.1).to_pil(); im.thumbnail((390,520))
   x=(i-start)%4*400; y=(i-start)//4*560
   sheet.paste(im,(x,y+25)); draw.text((x+8,y+4),f'PDF physical page {i+1}',fill='black')
  sheet.save(out/f'contact_{start+1:02}.png')
 doc.close()
