"""Post-chart additional check, explicitly adaptive and not a new primary test."""
import os,sys
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'research/data/支出细项与补助拓展_20261011'
sys.path.insert(0,str(ROOT/'research/.tmp/figure_deps'))
import pandas as pd
from exploratory_panel_stats import fe_fit,point
from infer_resource_timing import t_critical
def main():
    # Record motivation before fitting the extra checks, after viewing the composition graph.
    (OUT/'追加敏感性方案.md').write_text('2026年10月11日。在查看构成图后，发现2017—2018年个人内部份额发生明显变化，追加剔除这两年、2008—2016年和2019—2023年分段拟合。仍估计DGW对学生与自身实际收入，省份年份效应、省级CR1。用于观察关系是否仅依赖构成转换；不增加确认性假设、不跨模型显著性比较，也不将后期较宽区间当作机制改变。',encoding='utf8')
    result=[]
    for s in ['primary','junior']:
        d=pd.read_csv(OUT/f'{s}_component_model_input.csv')
        for name,mask in [('without_2017_18',~d.year.isin([2017,2018])),('period_2008_2016',d.year<=2016),('period_2019_2023',d.year>=2019)]:
            f=fe_fit(d[mask],'DGW',['dS','dR_real']);crit=t_critical(f['G']-1)
            for k,r in enumerate(['dS','dR_real']):
                z=point(f,[int(k==0),int(k==1)]);result.append(dict(stage=s,specification=name,outcome='DGW',regressor=r,n=f['n'],provinces=f['G'],coefficient=z['coefficient'],cluster_CR1_se=z['cluster_CR1_se'],low=z['coefficient']-crit*z['cluster_CR1_se'],high=z['coefficient']+crit*z['cluster_CR1_se'],post_chart_adaptive=True))
    df=pd.DataFrame(result);df.to_csv(OUT/'additional_regime_sensitivity.csv',index=False,encoding='utf-8-sig');print(df.to_string(index=False))
    os.environ['MPLCONFIGDIR']=str(ROOT/'research/.tmp/mpl_deepening')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');plt.rcParams.update({'font.family':font.get_name(),'font.size':10,'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    co=pd.read_csv(OUT/'all_coefficients.csv');full=co[(co.specification=='components')&(co.outcome=='DGW')&(co.regressor=='dS')].copy();full['specification']='full_2008_2023';draw=pd.concat([full,df[(df.regressor=='dS')&df.specification.str.startswith('period_')]]);draw.to_csv(OUT/'period_contrast_plot_data.csv',index=False,encoding='utf-8-sig')
    fig,axs=plt.subplots(1,2,figsize=(9,4.3),sharex=True)
    for i,s in enumerate(['primary','junior']):
        ax=axs[i]
        for k,(spec,label) in enumerate([('full_2008_2023','全窗口 2008—2023'),('period_2008_2016','前期 2008—2016'),('period_2019_2023','后期 2019—2023')]):
            r=draw[(draw.stage==s)&(draw.specification==spec)].iloc[0];ax.errorbar(r.coefficient,2-k,xerr=[[r.coefficient-r.low],[r.high-r.coefficient]],fmt='o',color='#7E0C6E' if k==0 else '#B68A3A',capsize=4)
        ax.set_yticks([2,1,0],['2008—2023\n全窗口（472条）','2008—2016\n前期（258条）','2019—2023\n后期（153条）']);ax.set_ylim(-.45,2.5);ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E5E5E5');ax.spines[['top','right']].set_visible(False);ax.set_title('小学' if i==0 else '初中');ax.set_xlabel('商品服务减工资福利：学生响应差')
    fig.subplots_adjust(left=.19,right=.98,top=.9,bottom=.18,wspace=.95)
    folder=ROOT/'research/figures/支出细项与补助图组_20261011'
    for ext in ['png','svg','pdf']:fig.savefig(folder/f'图F7_时期分段响应.{ext}',dpi=600,facecolor='white')
    plt.close(fig)
if __name__=='__main__':main()
