import sys
from collect import batch
sys.stdout.reconfigure(encoding='utf-8')
batch([
 ('yearbook_scope_city_inclusion','https://hudong.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202104/t20210427_528714.html'),
 ('yearbook_scope_primary_definitions','https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202208/t20220804_650737.html'),
 ('yearbook_scope_2020_data_year','https://www.stats.gov.cn/zs/tjwh/tjkw/tjzl/202302/t20230220_1913733.html'),
], 'yearbook_scope_sources')
batch([
 ('yearbook_scope_affiliation_and_funds','https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202307/t20230724_1070556.html'),
 ('yearbook_scope_public_capital','https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202401/t20240112_1099927.html'),
 ('yearbook_scope_city_www','https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202104/t20210427_528714.html'),
], 'yearbook_scope_followup_sources')
