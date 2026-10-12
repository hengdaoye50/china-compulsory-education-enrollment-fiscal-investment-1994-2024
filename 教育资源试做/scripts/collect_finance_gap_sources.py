from collect import batch
jobs=[
('finance_gap_weihai_2022','https://www.weihai.gov.cn/art/2023/10/24/art_80943_4087670.html'),
('finance_gap_weihai_2023','https://www.weihai.gov.cn/art/2024/6/4/art_80943_4573889.html'),
('finance_gap_jiangyin_2024','https://www.jiangyin.gov.cn/uploadfiles/202508/21/2025082110590444127646.pdf'),
('finance_gap_nbs_system_2025','https://www.stats.gov.cn/fw/bmdcxmsp/bmzd/202506/t20250604_1960023.html'),
('finance_gap_nbs_approval_directory','https://www.stats.gov.cn/fw/bmdcxmsp/bmdcxmml/202302/t20230215_1907008.html'),
('finance_gap_suzhou_reporting_2023','https://www.suzhou.gov.cn/szsrmzf/bmwj/202302/2cec361eab264f8ea6befd568b0a6547.shtml'),
('finance_gap_moe_quick_2023','https://hudong.moe.gov.cn/jyb_xwfb/gzdt_gzdt/s5987/202407/t20240722_1142296.html')]
batch(jobs,'finance_gap_sources')
