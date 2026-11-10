"""Report DPA3 fixed-support statistics without additional geometry queries."""
import csv
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());x=read(R/'results/RESULTS.json');sup=read(R/'real-supervision.json');val=read(R/'validation-supervision.json')
rows=[]
for p in x['pairs']:
 for d in ['forward','reverse']:
  for subset in ['all','mutual']:
   s=p[d][subset]
   for kind in ['unit_gram','huber_gram']:
    g=s[kind]
    rows.append(dict(pair=p['pair'],role=p['role'],event_group=p['event_group'],direction=d,frame=p['gram_frames'][d],subset=subset,weight=kind,count=s['count'],angle_median_deg=s['normal_angle_deg_quantiles'][3],
      Gyy=g['matrix'][0][0],Gyz=g['matrix'][0][1],Gzz=g['matrix'][1][1],lambda_min=g['eigenvalues'][0],lambda_max=g['eigenvalues'][1],ratio=g['lambda_min_over_max'],
      v_min_y=g['eigenvectors_yz_columns'][0][0],v_min_z=g['eigenvectors_yz_columns'][1][0],v_max_y=g['eigenvectors_yz_columns'][0][1],v_max_z=g['eigenvectors_yz_columns'][1][1]))
with (R/'GRAMS.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,3,figsize=(12,4.2),layout='constrained');positions=np.arange(4)
labels=['1825/4400\nlow','1875/4450\nlow','3350/4625\nhigh','3400/4575\nhigh']
for d,offset,color,label in [('forward',-.17,'#176d9c','Forward (target a)'),('reverse',.17,'#d2812b','Reverse (target b)')]:
 axs[0].bar(positions+offset,[p[d]['mutual_fraction']*100 for p in x['pairs']],width=.30,color=color,label=label)
 axs[1].scatter(positions+offset,[p[d]['mutual']['normal_angle_deg_quantiles'][3] for p in x['pairs']],color=color,marker='o',s=45)
 axs[2].scatter(positions+offset,[p[d]['mutual']['unit_gram']['lambda_min_over_max'] for p in x['pairs']],color=color,marker='o',s=45)
for ax in axs:
 ax.set_xticks(positions,labels,fontsize=9);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.axvline(1.5,color='#aaaaaa',lw=.8,ls=':')
axs[0].set(ylabel='Mutual / distance-qualified support (%)',ylim=(0,60),title='Exact reciprocity at T0')
axs[1].set(ylabel='Median absolute normal angle (degrees)',ylim=(0,12),title='Mutual source-target normals')
axs[2].set(ylabel='Local normalized yz Gram: min / max',ylim=(0,1),title='Mutual support, unit weights')
axs[0].legend(fontsize=8,loc='upper left')
fig.suptitle('DPA3: local mutual support and yz projection do not certify physical alignment',fontsize=12)
fig.supxlabel('Four exposed pairs, two events. Each direction uses its own target yz frame; no spectra are pooled.',fontsize=9)
fig.savefig(R/'support_diagnostics.png',dpi=170);fig.savefig(R/'support_diagnostics.svg');plt.close(fig)
# Preserve the exact SVG and add a whitespace-clean derivative for text tooling.
p=R/'support_diagnostics.svg';s=p.read_text();(R/'support_diagnostics.clean.svg').write_text('\n'.join(line.rstrip() for line in s.splitlines())+'\n')
lines=['# DPA3原末态支持诊断与优化决策','','2026-11-10，Asia/Shanghai。用户本轮授权继续决策与执行、更新交接和一次提交。DPA3已完成并关闭；研究 **UNRESOLVED**，论文 **PAUSED**；无新方法/准确率晋升。','',
'## 结论与决策','','低重叠两对在原rap_raw细化末态分别有6129、7592个精确互惠点对，分别占原距离支持的35.2%–36.2%与42.3%–44.3%。互惠源/目标法线中位绝对夹角约10.06°和8.58°。在各自目标坐标的互惠单位权重y/z归一化Gram中，低对λmin约.385–.423、λmin/λmax约.677–.837；这些固定支持统计没有表现为y/z某一个投影方向接近零。高对对应比值约.312–.403，不能把比值更高解释为低对物理信息更强或更正确。','',
'因此，**不把增加同一局部ICP迭代、补单一y/z弱轴或改旧验收阈值作为下一默认优化**。DPA2已显示低事件偏好随对应锚切换，DPA3又说明错误风险可以伴随数千互惠、法线较一致且投影谱非退化的局部对应。仅靠互惠/法线一致/局部谱不能认证结构身份。这与旧SAC1局部满秩仍有别名风险的边界一致，但本轮未重跑旧路线。','',
'下一策略转为**结构关联歧义的受控可辨识性与弃权验证**：先用具有已知物理点身份的受控重复/非重复结构，检验“局部支持丰富但错误别名成立”的反例，以及新增独立结构锚点在可见时是否真的区分候选。完全等价的重复结构必须保留歧义；不能为达到记录1m阈值挑选姿态。下一合同DPA4仅草案，本轮未执行。当前没有足够物理证据选择生产算法改动。','',
'本轮没有证明真实误差来自重复结构、扫描处理或参考；仅排除了在本组固定支持中“近零y/z投影”这一直接数值表现。完整6DoF耦合、对应切换与参考物理精度仍未分离。低两对同一事件02_12_29，高两对同一事件02_22_30，均开发暴露，不作独立统计确认。','',
'## 输入、预算与验证','','仅按ZIP白名单复制原NPY成员：a/b/na/nb/final与f_d0/f_j0/r_d0/r_j0。4个净化NPZ共9,342,732字节，逐成员hash匹配父DPA2已提交数据；未解码/复制reference/initial/T1/d1/j1。计算/核查均只接受9键，不读取原raw，不建树/新NN，不重算法线、不更新姿态，不导入SciPy/Open3D/Torch。','',
f"真实worker墙钟{sup['wall_s']:.3f}秒，峰值RSS约{sup['observed_peak_RSS_bytes']/2**20:.1f}MiB，输出{sup['final_output_bytes']:,}字节；独立核查{val['wall_s']:.3f}秒，约{val['observed_peak_RSS_bytes']/2**20:.1f}MiB。每worker CPU单线程/CUDA不可见，child AS≤2GiB−64MiB、CPU25秒/墙钟30秒、输出≤4MiB，未触发实际预算失败。",
'', '10项合成检查、4类资源监督负例按预期通过，无意外执行失败。独立验证32组Gram矩阵、32组闭式谱/特征向量检验、16组角度分布、16组损失/权重、8组保存距离和8组互惠集合；无额外NN、原raw或禁止数组读取。Gram绝对/相对容差1e-12，acos分位角abs1e-5deg+rel1e-6仅作数值容差。','',
'## 支持数量与几何兼容','','![互惠支持、法线与投影谱](support_diagnostics.png)','','图和下表方向保持分开，forward在目标a坐标，reverse在目标b坐标，不混合特征向量。角度区间只是分布描述，不是新筛选阈值。','','| 配对 | 方向 | 原距离支持 | 精确互惠 | 互惠比例 | 全部/互惠角中位数 | 互惠<15°数量 |','| --- | --- | ---: | ---: | ---: | --- | ---: |']
for p in x['pairs']:
 for d in ['forward','reverse']:
  z=p[d];lines.append(f"| {p['pair']} | {d} | {z['all_count']} | {z['mutual_count']} | {100*z['mutual_fraction']:.2f}% | {z['all']['normal_angle_deg_quantiles'][3]:.3f}° / {z['mutual']['normal_angle_deg_quantiles'][3]:.3f}° | {z['mutual']['normal_angle_bin_counts'][0]} |")
lines+=['','## 全部32组Gram谱','','G按对应数量N归一化，Huber权重不再按权重和归一化。此处仅显示特征值/比例，精确矩阵、特征向量和完整分布见GRAMS.csv及results/RESULTS.json。','','| 配对 | 方向 | 总体 | 权重 | λmin | λmax | 比值 |','| --- | --- | --- | --- | ---: | ---: | ---: |']
for z in rows:lines.append(f"| {z['pair']} | {z['direction']} | {z['subset']} | {z['weight']} | {z['lambda_min']:.8f} | {z['lambda_max']:.8f} | {z['ratio']:.8f} |")
lines+=['','互惠集合前/反点对数量相同，法线分布接近；由于目标坐标/法线不同，两方向矩阵不可直接合并。Huber谱和单位谱在互惠集合上数值接近，但这只说明当前残差下绝大部分权重为1，不证明更改鲁棒核能或不能产生严格覆盖增量。','',
'## 保留边界与提交','','局部统计不认证同物理表面、静态、正确姿态、协方差或可观测性。原扫描0.205°/1.5–60m/.2m/seed311/.6m处理身份保留，不认证来源或处理物理正确。训练真实来源/三划分资格不变，03开发暴露、SSC1/PGC1停止和七份部分准确率未解释读取、official MAC未运行保持。','',
'旧实验及全部封存/失败保留，22生产文件原字节保持。当前8入口先备份再更新；本轮仅一次聚焦RAP-main提交本目录和docs/experiments/DPA3.md，原生产修改保留，未推送。提交后收据置目录外，避免自身hash要求二次提交。','',
'主入口HANDOFF_CN.md；执行合同PROTOCOL_CN.md，冻结freeze.json，白名单来源INPUTS.json，独立核查INDEPENDENT_CHECKS.json，收尾CLOSEOUT_CHECKS.json，提交准备PRECOMMIT_CHECKS.json及ARTIFACT_MANIFEST.json。图保留原SVG，另存只去行尾空格的clean.svg供文本检查；不修改原图或旧科学产物。','']
(R/'REPORT_CN.md').write_text('\n'.join(lines));print('Built DPA3 report, 32-row Gram CSV and figure')
