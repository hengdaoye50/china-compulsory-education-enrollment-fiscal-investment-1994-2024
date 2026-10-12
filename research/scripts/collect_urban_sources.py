import json
from collect import ROOT,batch
jobs=[]
for y,tail in [(2014,'jytjsj_2014/2014_qg/201509/t20150902_205017.html'),(2015,'jytjsj_2015/2015_qg/201610/t20161019_285583.html'),(2016,'jytjsj_2016/2016_qg/201708/t20170823_311720.html'),(2017,'jytjsj_2017/qg/201808/t20180808_344718.html')]:
    jobs.append((f'urban_national_{y}_primary_course','https://hudong.moe.gov.cn/jyb_sjzl/moe_560/'+tail))
jobs.extend([('urban_national_2013_directory','https://hudong.moe.gov.cn/jyb_sjzl/moe_560/s8492/s8493/'),('urban_definition_education','https://hudong.moe.gov.cn/srcsite/A16/s3342/201203/W020220704498224866735.pdf')])
batch(jobs,'urban_sources')
