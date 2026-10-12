"""Small, inspectable two-way-FE OLS and province-cluster wild-t inference.
This is exploratory inference; it does not certify source comparability.
"""
import numpy as np

def fe_fit(frame, outcome, regressors):
    p=np.asarray(frame['province']); years=np.asarray(frame['year'])
    provinces,gi=np.unique(p,return_inverse=True); periods,ti=np.unique(years,return_inverse=True)
    n=len(frame); G=len(provinces)
    F=np.column_stack([np.eye(G)[gi],np.eye(len(periods))[ti]])
    u,s,_=np.linalg.svd(F,full_matrices=False)
    r=int(np.sum(s>max(F.shape)*np.finfo(float).eps*s[0])); Q=u[:,:r]
    X=np.asarray(frame[regressors],dtype=float); Y=np.asarray(frame[outcome],dtype=float)
    Xm=X-Q@(Q.T@X); Ym=Y-Q@(Q.T@Y)
    k=len(regressors)
    if np.linalg.matrix_rank(Xm)<k:raise ValueError('regressors_not_identified_after_FE')
    inv=np.linalg.inv(Xm.T@Xm); A=inv@Xm.T; beta=A@Ym
    e=Ym-Xm@beta; totalrank=r+k
    if n<=totalrank or G<2:raise ValueError('insufficient_residual_degrees_of_freedom')
    CR1=G/(G-1)*(n-1)/(n-totalrank)
    scores=np.zeros((G,k));np.add.at(scores,gi,Xm*e[:,None])
    cov=CR1*inv@scores.T@scores@inv
    H=Q@Q.T+Xm@A
    # Direct full-dummy least squares must agree with the residualized solution.
    direct=np.linalg.lstsq(np.column_stack([X,F]),Y,rcond=None)[0][:k]
    assert np.allclose(beta,direct,rtol=1e-7,atol=1e-9)
    return dict(beta=beta,cov=cov,e=e,Q=Q,Xm=Xm,A=A,H=H,CR1=CR1,gi=gi,provinces=provinces,n=n,G=G,years=len(periods),rank=totalrank,regressors=regressors,Y=Y,X=X,max_leverage=float(np.max(np.diag(H))))

def wild_t(fit, contrast, B=9999, seed=20261010):
    """Restricted wild-cluster bootstrap p; unrestricted percentile-t interval.
    Rademacher weights shared by every record of a province. Not a WCR test-inverted CI.
    """
    c=np.asarray(contrast,float); beta=fit['beta']; b=float(c@beta)
    se=float(np.sqrt(c@fit['cov']@c)); observed=b/se
    Q=fit['Q']; Xm=fit['Xm']; A=fit['A']; gi=fit['gi']; n=fit['n']; G=fit['G']
    h=c@A
    # Constrained least squares c'beta=0 in the residualized regression.
    inv=np.linalg.inv(Xm.T@Xm)
    restricted=beta-inv@c*(b/(c@inv@c))
    Y=fit['Y']; restricted_e=Y-Q@(Q.T@Y)-Xm@restricted
    C=np.eye(G)[gi].T
    rng=np.random.default_rng(seed); nullts=[]; unts=[]
    for start in range(0,B,500):
        size=min(500,B-start); weights=rng.choice([-1.,1.],size=(G,size))[gi]
        for residual,container in [(restricted_e,nullts),(fit['e'],unts)]:
            v=residual[:,None]*weights
            db=A@v
            es=v-Q@(Q.T@v)-Xm@db
            scores=C@(h[:,None]*es)
            ses=np.sqrt(fit['CR1']*np.sum(scores*scores,axis=0))
            good=ses>1e-12
            container.extend(((c@db)[good]/ses[good]).tolist())
    null=np.asarray(nullts); un=np.asarray(unts)
    lo,hi=np.quantile(un,[.025,.975])
    # Invert the SAME restricted bootstrap test for coherent confidence sets.
    # e(theta)=e(0)+theta*v, so bootstrap scores and numerators are affine in theta.
    direction=-Xm@inv@c/(c@inv@c)
    rng=np.random.default_rng(seed); num0=[];num1=[];va=[];vb=[];vc=[]
    for start in range(0,B,500):
        size=min(500,B-start);weights=rng.choice([-1.,1.],size=(G,size))[gi]
        v0=restricted_e[:,None]*weights;v1=direction[:,None]*weights
        d0=A@v0;d1=A@v1
        e0=v0-Q@(Q.T@v0)-Xm@d0;e1=v1-Q@(Q.T@v1)-Xm@d1
        s0=C@(h[:,None]*e0);s1=C@(h[:,None]*e1)
        num0.extend(c@d0);num1.extend(c@d1)
        va.extend(fit['CR1']*np.sum(s1*s1,axis=0));vb.extend(2*fit['CR1']*np.sum(s0*s1,axis=0));vc.extend(fit['CR1']*np.sum(s0*s0,axis=0))
    num0=np.asarray(num0);num1=np.asarray(num1);va=np.asarray(va);vb=np.asarray(vb);vc=np.asarray(vc)
    def pvalue(theta):
        variance=va*theta*theta+vb*theta+vc;good=variance>1e-24
        ts=(num0[good]+num1[good]*theta)/np.sqrt(variance[good])
        return float((1+np.sum(abs(ts)>=abs((b-theta)/se)))/(len(ts)+1))
    assert abs(pvalue(0)-(1+np.sum(abs(null)>=abs(observed)))/(len(null)+1))<1e-10
    radius=20*se;grid=np.linspace(b-radius,b+radius,2001)
    ps=np.asarray([pvalue(t) for t in grid]);accepted=ps>=.05
    # Record disjoint/unbounded-within-search sets rather than forcing a conventional interval.
    starts=np.flatnonzero(accepted & np.r_[True,~accepted[:-1]])
    ends=np.flatnonzero(accepted & np.r_[~accepted[1:],True])
    bands=[]
    for left,right in zip(starts,ends):
        def boundary(a,z):
            pa=pvalue(a)>=.05
            for _ in range(35):
                mid=(a+z)/2
                if (pvalue(mid)>=.05)==pa:a=mid
                else:z=mid
            return (a+z)/2
        lower=None if left==0 else boundary(grid[left-1],grid[left])
        upper=None if right==len(grid)-1 else boundary(grid[right],grid[right+1])
        bands.append([lower,upper])
    return dict(coefficient=b,cluster_CR1_se=se,wild_restricted_p=pvalue(0),WCR_95_CI_low=bands[0][0],WCR_95_CI_high=bands[-1][1],WCR_95_confidence_bands=str(bands),WCR_search_lower=float(grid[0]),WCR_search_upper=float(grid[-1]),WCR_search_boundary_accepted=bool(accepted[0] or accepted[-1]),WCR_disjoint_bands=len(bands),wild_unrestricted_t_CI_low=float(b-hi*se),wild_unrestricted_t_CI_high=float(b-lo*se),bootstrap_draws=B,valid_null_draws=len(null),valid_interval_draws=len(un),seed=seed)

def point(fit,contrast):
    c=np.asarray(contrast,float)
    return dict(coefficient=float(c@fit['beta']),cluster_CR1_se=float(np.sqrt(c@fit['cov']@c)))
