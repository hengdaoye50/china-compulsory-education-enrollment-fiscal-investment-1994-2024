"""Round 30: province CR1 inference for existing two-way FE timing models.

Reconstruct inputs from saved levels; preserve all old estimates and charts.
No scipy/statsmodels dependency: t tails integrate the NIST density after a
bounded angular transform. Independent full-dummy and within covariance checks.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PROTECTED = json.loads((DATA / 'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
QUAD = {n: np.polynomial.legendre.leggauss(n) for n in [64, 128]}


def read(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save(name, rows):
    with (DATA / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def t_pvalue(t, df, order=64):
    # t = sqrt(df)*tan(theta), yielding cos(theta) ** (df-1).
    lo, hi = math.atan(abs(float(t)) / math.sqrt(df)), math.pi / 2
    z, w = QUAD[order]
    theta = lo + (z + 1) * (hi - lo) / 2
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(math.pi)
    return min(1., max(0., c * (hi - lo) * float(w @ np.cos(theta) ** (df - 1))))


def t_critical(df):
    lo, hi = 0., 10.
    for _ in range(65):
        mid = (lo + hi) / 2
        if t_pvalue(mid, df) > .05: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def holm(rows, field, target):
    order = sorted(range(len(rows)), key=lambda i: rows[i][field])
    previous = 0.
    for j, i in enumerate(order):
        previous = min(1., max(previous, (len(rows) - j) * rows[i][field]))
        rows[i][target] = previous


def covariance(x, residuals, groups, factor):
    bread = np.linalg.inv(x.T @ x)
    scores = np.asarray([x[groups == g].T @ residuals[groups == g] for g in np.unique(groups)])
    return factor * bread @ (scores.T @ scores) @ bread


def within(a, n_provinces, n_years):
    shape = (n_provinces, n_years) + a.shape[1:]
    v = a.reshape(shape)
    return (v - v.mean(axis=1, keepdims=True) - v.mean(axis=0, keepdims=True) + v.mean(axis=(0, 1), keepdims=True)).reshape(a.shape)


def main():
    numerical_checks = []
    for df in [1, 2, 30]:
        for t in [0., .5, 2., 5., 20.]:
            p = t_pvalue(t, df)
            delta = abs(p - t_pvalue(t, df, 128))
            assert delta < 1e-12
            if df == 1: assert abs(p - (1 - 2 * math.atan(t) / math.pi)) < 1e-12
            if df == 2: assert abs(p - (1 - t / math.sqrt(t * t + 2))) < 1e-12
            numerical_checks.append(dict(df=df, t=t, p=p, quadrature_difference=delta))
    assert abs(t_critical(30) - 2.042272456301238) < 1e-10
    # Holm check includes ties, monotonicity and clipping.
    sample = [{'p': p} for p in [.01, .01, .04, .8]]
    holm(sample, 'p', 'adjusted')
    assert np.allclose([r['adjusted'] for r in sample], [.04, .04, .08, .8])
    raw = read('education_resource_panel.csv')
    levels = {(r['stage'], r['province'], int(r['year'])): r for r in raw}
    assert len(raw) == len(levels) == 768
    provinces = sorted({r['province'] for r in raw if r['province'] != '全国'})
    assert len(provinces) == 31
    specs = read('resource_timing_models.csv')
    coefficients, contrasts, joints, checks, covariance_rows = [], [], [], [], []
    for model in specs:
        stage, resource, scenario = (model[k] for k in ['stage', 'resource', 'scenario'])
        years = list(range(int(model['first_year']), int(model['last_year']) + 1))
        values, targets, group_ids = [], [], []
        for g, province in enumerate(provinces):
            for year in years:
                now, prev, earlier = [levels[stage, province, year - d] for d in [0, 1, 2]]
                values.append([100 * math.log(float(now['students']) / float(prev['students'])),
                               100 * math.log(float(prev['students']) / float(earlier['students']))])
                targets.append(100 * math.log(float(now[resource]) / float(prev[resource])))
                group_ids.append(g)
        x, y, groups = np.array(values), np.array(targets), np.array(group_ids)
        g_count, t_count, n = len(provinces), len(years), len(y)
        time_ids = np.tile(np.arange(t_count), g_count)
        # Intercept, slopes, omitted-category province and year dummies.
        full_x = np.column_stack([np.ones(n), x, np.eye(g_count)[groups, 1:], np.eye(t_count)[time_ids, 1:]])
        beta, _, rank, _ = np.linalg.lstsq(full_x, y, rcond=None)
        assert rank == full_x.shape[1] == g_count + t_count + 1
        full_e = y - full_x @ beta
        wx, wy = within(x, g_count, t_count), within(y, g_count, t_count)
        wb = np.linalg.lstsq(wx, wy, rcond=None)[0]; we = wy - wx @ wb
        factor = g_count / (g_count - 1) * (n - 1) / (n - rank)
        full_cov = covariance(full_x, full_e, groups, factor)[1:3, 1:3]
        cov = covariance(wx, we, groups, factor)
        b = beta[1:3]
        old = np.array([float(model['current_student_coef']), float(model['previous_student_coef'])])
        b_delta = max(float(np.max(abs(b - wb))), float(np.max(abs(b - old))))
        v_delta = float(np.max(abs(cov - full_cov)))
        assert b_delta < 1e-10 and v_delta < 1e-10
        assert np.max(abs(full_e - we)) < 1e-10
        assert np.linalg.eigvalsh(cov).min() > 0
        within_r2 = 1 - float(we @ we / (wy @ wy))
        assert abs(within_r2 - float(model['within_r_squared'])) < 1e-10
        common = dict(stage=stage, resource=resource, scenario=scenario, n=n, provinces=g_count,
                      first_year=years[0], last_year=years[-1], full_design_rank=int(rank),
                      cluster_df=g_count - 1, cr1_factor=factor, within_r_squared=within_r2)
        critical = t_critical(g_count - 1)
        for i, name in enumerate(['current_students', 'previous_students']):
            se = math.sqrt(float(cov[i, i])); t = float(b[i]) / se
            p = t_pvalue(t, g_count - 1)
            assert abs(p - t_pvalue(t, g_count - 1, 128)) < 1e-12
            coefficients.append({**common, 'term': name, 'coefficient': float(b[i]), 'cluster_se': se,
                                 't_stat': t, 'p_two_sided': p, 'ci95_low': float(b[i]) - critical * se,
                                 'ci95_high': float(b[i]) + critical * se, 'p_holm_main8': ''})
        c = np.array([-1., 1.]); difference = float(c @ b); se = math.sqrt(float(c @ cov @ c))
        contrasts.append({**common, 'contrast': 'previous_minus_current', 'difference': difference,
                          'cluster_se': se, 't_stat': difference / se,
                          'p_two_sided': t_pvalue(difference / se, g_count - 1),
                          'ci95_low': difference - critical * se, 'ci95_high': difference + critical * se,
                          'p_holm_main4': ''})
        f = float(b @ np.linalg.solve(cov, b)) / 2
        # F(2, df) has this exact survival function.
        p_f = ((g_count - 1) / ((g_count - 1) + 2 * f)) ** ((g_count - 1) / 2)
        joints.append({**common, 'null': 'current=previous=0', 'f_stat': f, 'numerator_df': 2,
                       'p_joint_f': p_f, 'p_holm_main4': ''})
        covariance_rows.append({**common, 'cov_current_current': float(cov[0, 0]),
                                'cov_current_previous': float(cov[0, 1]), 'cov_previous_previous': float(cov[1, 1])})
        checks.append({**common, 'max_coef_difference': b_delta, 'max_covariance_difference': v_delta,
                       'max_residual_difference': float(np.max(abs(full_e - we))), 'passed': True})
    main_coefs = [r for r in coefficients if r['scenario'] == 'main_2015_2024']
    main_contrasts = [r for r in contrasts if r['scenario'] == 'main_2015_2024']
    main_joints = [r for r in joints if r['scenario'] == 'main_2015_2024']
    assert len(main_coefs) == 8 and len(main_contrasts) == len(main_joints) == 4
    holm(main_coefs, 'p_two_sided', 'p_holm_main8')
    holm(main_contrasts, 'p_two_sided', 'p_holm_main4')
    holm(main_joints, 'p_joint_f', 'p_holm_main4')
    protected_checks = []
    for rel, sha in PROTECTED.items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == sha
        protected_checks.append(dict(path=rel, sha256=actual, unchanged=True))
    assert len(protected_checks) == 4
    save('resource_timing_cluster_coefficients.csv', coefficients)
    save('resource_timing_cluster_contrasts.csv', contrasts)
    save('resource_timing_cluster_joint_tests.csv', joints)
    save('resource_timing_cluster_covariances.csv', covariance_rows)
    save('resource_timing_cluster_checks.csv', checks)
    audit = dict(date='2026-10-08', round=30, model_count=len(specs), coefficient_rows=len(coefficients),
                 contrast_rows=len(contrasts), joint_test_rows=len(joints),
                 covariance='province CR1; full dummy rank used in finite sample correction',
                 reference_distribution='two-sided Student t(G-1); joint Wald F(2,G-1), approximate cluster inference',
                 main_families='8 slope nulls; separately 4 lag-current contrasts and 4 joint tests; Holm per family',
                 sensitivity='all 3 existing sensitivity windows shown; no selected specification promotion',
                 exploratory=True, preregistered=False, within_cluster_dependence_allowed=True,
                 cross_province_independence_assumed=True, causal_identification=False,
                 numerical_distribution_checks=numerical_checks, numerical_t30_critical=t_critical(30),
                 max_coefficient_difference=max(r['max_coef_difference'] for r in checks),
                 max_covariance_difference=max(r['max_covariance_difference'] for r in checks),
                 protected_files=protected_checks,
                 input_hashes={n: hashlib.sha256((DATA / n).read_bytes()).hexdigest() for n in ['education_resource_panel.csv', 'resource_timing_models.csv']},
                 method_sources=['https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html',
                                 'https://www.statsmodels.org/v0.14.0/_modules/statsmodels/regression/linear_model.html',
                                 'https://www.itl.nist.gov/div898/handbook/eda/section3/eda3664.htm'])
    (DATA / 'resource_timing_cluster_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'models': len(specs), 'checks': 'passed', 'main_coefficients': main_coefs,
                      'main_contrasts': main_contrasts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
