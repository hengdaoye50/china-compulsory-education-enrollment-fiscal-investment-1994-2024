"""Verify received PDFs and preserve scoped, page-located literature evidence.

This audits files and evidence anchors, not the truth of authors' causal claims.
Round 28 public-source audit remains a historical snapshot.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def compact(s):
    return re.sub(r'\s+', '', s)


def main():
    receipt = json.loads((DATA / 'literature_fulltext/receipt.json').read_text(encoding='utf-8'))
    by_id = {r['paper_id']: r for r in receipt}
    meta = {
        'L01': ('40-53', 40, [1, 3, 4, 5, 7, 8, 12, 14], 'three-province conditional forecast; 2026-2050', 'Population model and teacher-need assumptions; not observed policy effects'),
        'L02': ('54-68', 54, [1, 5, 6, 7, 11, 12, 15], '70 studies, 114 effect sizes; publications 1996-2025', 'Correlation-effect synthesis; definitions and moderators vary'),
        'L03': ('107-121', 107, [1, 3, 4, 10, 15], 'anonymous northeast province A; school surveys and fieldwork', 'Selected province and school types; not nationally representative causal identification'),
        'L04': ('229-240', 229, [1, 2, 3, 7, 8, 12], '8 provinces, 16 counties/districts; qualitative fieldwork', 'Stratified purposive cases and institutional interpretation; not probability prevalence estimates'),
    }
    # Evidence statements are analyst paraphrases. Anchors are for locating text only.
    evidence_specs = [
        ('L01', 3, '2026—2050', '以2020年普查为基础预测三个典型省份2026—2050年人口及师资需求', 'conditional forecast', '不能代替31省2017—2023实际调整记录'),
        ('L01', 3, '五四制', '黑龙江部分地区五四学制需要单独处理学段年龄人口', 'model definition', '不把文中最新学制比例追溯套用于本项目各年'),
        ('L01', 4, '毛入学率', '在校生预测使用学龄人口与设定毛入学率，城乡分布另行预测', 'forecast assumption', '实际在校学生不等于同龄常住人口'),
        ('L01', 5, '退休', '教师自然减员与不新增教师的情景属于需求预测条件', 'scenario assumption', '不据情景认定实际退休或招聘政策效果'),
        ('L01', 7, '周课时', '班额、课程课时与教师工作量参与教师需求标准构建', 'normative need model', '不能把研究设定的合理区间作为本项目效率判准'),
        ('L02', 1, '国家财政性教育经费', '该文公共教育支出定义比本项目普通学校一般公共预算范围更宽', 'variable definition', '不能将元分析效应直接赋给本项目财政系列'),
        ('L02', 5, '114', '纳入70项研究、114个效应量；检索截至2025年8月13日', 'review sample', '不是每种人口关系都有70项独立研究'),
        ('L02', 6, '三水平', '三水平模型处理抽样、研究内和研究间变异', 'statistical synthesis', '处理效应依赖不等于统一完成因果识别'),
        ('L02', 7, '0.287', '汇总学龄人口与支出总额正相关、与生均支出负相关', 'pooled correlations', '不能把生均相关方向推广为每省历史因果效应'),
        ('L02', 12, '教育阶段', '教育阶段、区域、年份和统计方法参与效应异质性讨论', 'moderator analysis', '异质性支持交代口径，不证明本项目机制'),
        ('L03', 3, '1688', '匿名东北A省回收1688份学校调查表与12475份问卷，实访35所小规模学校和5所中心校', 'fieldwork sample', '1688所不含0人学校，不能与含0人学校统计混用'),
        ('L03', 4, '固定成本', '调查报告经费不足与资源闲置并存，固定运行成本难以同比缩减', 'local field evidence', '提示备选解释，不据此认证全国财政刚性'),
        ('L03', 10, '转岗', '教师分流涉及调动、转岗及专业适应问题', 'local field evidence', '专任教师总量不能替代学科匹配与安置质量'),
        ('L04', 3, '半结构化访谈', '8省16县区通过分层与目的性抽样及资料可获取性筛选，采用访谈、座谈和观察', 'qualitative design', '有典型性不等于全国代表性，不估计全国障碍比例'),
        ('L04', 7, '有编无钱', '师资供给受来源培养、编制与财政条件共同约束', 'institutional case interpretation', '编制指标不等于实有专任教师'),
        ('L04', 8, '在编', '案例包含在编不在岗、跨部门协同和调配激励等问题', 'institutional case interpretation', '不能把这些机制称为本项目省级数据已验证的原因'),
    ]
    evidence = []
    for i, (ident, page, anchor, statement, kind, limit) in enumerate(evidence_specs, 1):
        pages = json.loads((DATA / f'literature_fulltext/{ident}_columns.json').read_text(encoding='utf-8'))
        ok = compact(anchor) in compact(pages[page - 1])
        evidence.append(dict(evidence_id=f'F{i:02}', paper_id=ident, pdf_page=page,
                             printed_page=meta[ident][1] + page - 1, anchor=anchor,
                             anchor_found=ok, paraphrase=statement, evidence_kind=kind,
                             application_limit=limit, pdf_path=by_id[ident]['path'],
                             sha256=by_id[ident]['sha256']))
    write_csv(DATA / 'literature_fulltext_evidence_ledger.csv', evidence)
    with (DATA / 'literature_cssci_candidate_ledger.csv').open(encoding='utf-8-sig', newline='') as f:
        candidates = list(csv.DictReader(f))
    reviews = []
    for row in candidates:
        ident = row['paper_id']; rec = by_id[ident]
        sha = hashlib.sha256(Path(rec['path']).read_bytes()).hexdigest()
        assert sha == rec['sha256'], ident
        page_range, _, reviewed, sample, limit = meta[ident]
        row.update(pages=page_range, full_text_obtained='True',
                   available_evidence='user-provided full PDF; relevant methods, findings and limits reviewed with page evidence',
                   selection_status='selected for scoped literature dialogue; no claim of exhaustive full-text or replication audit',
                   raw_path=rec['path'], locator='first page bibliography and cited printed/PDF pages; fulltext evidence ledger')
        reviews.append(dict(paper_id=ident, title=row['title'], authors=row['authors'],
                            journal=row['journal'], year=row['year'], issue=row['issue'],
                            pages=page_range, volume='47' if ident == 'L04' else '',
                            source_journal_qualification=row['qualification'],
                            pdf_path=rec['path'], pdf_pages=rec['pdf_pages'], sha256=sha,
                            reviewed_pdf_pages=';'.join(map(str, reviewed)),
                            review_scope='bibliography and selected relevant methods/results/limits; not exhaustive audit',
                            sample_or_period=sample, main_limit=limit))
    write_csv(DATA / 'literature_cssci_candidate_ledger.csv', candidates)
    write_csv(DATA / 'literature_fulltext_review.csv', reviews)
    baseline = json.loads((DATA / 'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
    # Accept the baseline's established serialization; inspect on first run if changed.
    protected = []
    if isinstance(baseline, dict):
        entries = baseline.get('files', baseline)
        if isinstance(entries, dict):
            for rel, value in entries.items():
                target = ROOT / rel
                if target.is_file():
                    expected = value.get('sha256') if isinstance(value, dict) else value
                    actual = hashlib.sha256(target.read_bytes()).hexdigest()
                    protected.append(dict(path=rel, unchanged=actual == expected, sha256=actual))
    audit = dict(date='2026-10-08', round=29, received_pdf_count=len(receipt),
                 selected_scoped_paper_count=len(reviews), evidence_count=len(evidence),
                 anchor_checks_passed=sum(r['anchor_found'] for r in evidence),
                 originals_sha256_verified=True, reviewed_entire_text=False,
                 source_journal_floor='CSSCI source journals 2025-2026, excluding extension; round28 verification retained',
                 individual_cssci_database_inclusion_checked=False,
                 protected_files=protected,
                 note='Bibliographic and selected passage audit; not method replication or causal certification')
    (DATA / 'literature_fulltext_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False))
    assert all(r['anchor_found'] for r in evidence), 'Evidence anchor requires review'
    assert len(protected) == 4 and all(r['unchanged'] for r in protected), 'Protected baseline requires review'


if __name__ == '__main__':
    main()
