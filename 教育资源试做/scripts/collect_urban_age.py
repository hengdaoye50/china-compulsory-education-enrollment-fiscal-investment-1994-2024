from collect import batch
jobs=[]
for y,tail in [(2015,'jytjsj_2015/2015_qg/201610/t20161019_285580.html'),(2016,'jytjsj_2016/2016_qg/201708/t20170823_311719.html'),(2017,'jytjsj_2017/qg/201808/t20180808_344716.html')]:
    jobs.append((f'urban_national_{y}_primary_age','https://hudong.moe.gov.cn/jyb_sjzl/moe_560/'+tail))
batch(jobs,'urban_age_sources')
