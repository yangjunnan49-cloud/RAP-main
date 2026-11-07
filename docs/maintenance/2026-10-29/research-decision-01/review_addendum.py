"""Resolve a numerical-boundary review and expose all secondary-bin failures."""
import datetime,hashlib,json
from pathlib import Path
workspace=Path(__file__).resolve().parents[2];root=workspace/'outputs/feature_geometry_20261029';out=workspace/'outputs/研究决策_2026-10-29'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
inputs=[]
for stage in ('predict','evaluate','aliasing'):
    filename='PREDICTIONS.json' if stage=='predict' else 'ROWS.json';p=root/stage/filename;e=next(z for z in read(root/stage/'SEAL.json')['files'] if z['path']==filename)
    assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];inputs.append(dict(path=str(p),bytes=e['bytes'],sha256=e['sha256']))
ps={r['key']:r for r in read(inputs[0]['path'])};es=read(inputs[1]['path']);aliases=read(inputs[2]['path']);pairs=[]
for r in aliases:
    for z in r['arms']['J']['incompatible_accepted_pairs']:pairs.append(z)
assert len(pairs)==87 and all(z['translation_separation_m']>2.000001 for z in pairs)
severe=[]
for e in es:
    z=e['arms']['J']
    if z['accepted'] and (e['stratum']=='confuser' or not z['R5_t2']):
        p=ps[e['key']]['arms']['J'];severe.append(dict(key=e['key'],stratum=e['stratum'],historical_category=e['historical_N_category'],selected=p['name'],overlap_1m=p['symmetric_overlap_1m'],mean_NN_m=p['symmetric_mean_distance'],clipped_squared_NN=p['score'],rotation_error_deg=z['rotation_error_deg'],translation_error_m=z['translation_error_m'],primary_correct_candidate_available=e['J_correct_pool'],R_rotation_deg=e['arms']['R']['rotation_error_deg'],R_translation_m=e['arms']['R']['translation_error_m']))
assert len(severe)==2
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs=inputs,source_sha256=sha(__file__),J_incompatible_pose_pairs=87,minimum_translation_separation_m=min(z['translation_separation_m'] for z in pairs),all_reported_J_ambiguities_certified_by_translation_alone=True,secondary_wrong_accepts=severe,tracked_git_observation=dict(main_HEAD='4055d929c594b0033aafc6eed339c910369eef55',SLAM_HEAD='6d3f2d22cedfe1f807deb11fd8796b9f5bf17cd6',main_tracked_dirty_paths=['.gitignore','AGENTS.md'],SLAM_tracked_dirty_path_count=9,HEADs_and_path_sets_match_prior_observation=True,untracked_remote_and_entire_worktree_content_not_audited=True),visual_review=dict(comparison=True,bottleneck=True,all5_case_PNGs=True,case_XZ_metric_aspect_preserved=True),no_new_prediction_or_gate=True)
save(out/'REVIEW_ADDENDUM.json',v)
text='''# 收尾审阅补记

本补记为已封存结果的只读审阅，原报告、主要判定、图和封存均未修改。

J中4个歧义配对共87组不兼容的已接受候选，全部仅靠平移距离已超过2.000001米，最小为'''+f"{v['minimum_translation_separation_m']:.6f}"+'''米。因此，这四个实际案例的“无法同时落入1米平移球”可直接由欧氏三角不等式确认，不依赖参考旋转的有限精度、SO(3)投影或临界10度数值解释。原标量距离审计仍保留；没有添加拒绝规则。

全部超过原先声明的次要5度/2米范围的J接受错误恰好为以下两例，完整披露而非挑选最差个例：

|ID|选中候选|1米重叠比例|平均最近邻米|R误差度|t误差米|
|---|---|---:|---:|---:|---:|
'''
for z in severe:text+=f"|{z['key']}|{z['selected']}|{z['overlap_1m']:.4f}|{z['mean_NN_m']:.6f}|{z['rotation_error_deg']:.6f}|{z['translation_error_m']:.6f}|\n"
text+='''
两例都是真实回环配对，均能通过当前重叠≥0.7且平均最近邻≤2.5米条件；这说明必须评价具体位姿错误，不能只用回环/非回环分类判定测量安全。第一例的原RAP输出旋转误差约0.95度、平移约1.84米，属于原次要范围但不属于主要范围；选中几何结果却接近180度/33米。第二例的RAP输出也超过2米。它们没有被统一归因为同一种物理原因，不据此调阈值或建立新选择器。

最后只读Git观察中，RAP-main和RAP-SLAM的HEAD及已跟踪脏路径集合与此前观察一致（2条/9条）；AGENTS内容按本轮授权追加。没有审计远端、未跟踪文件或对所有已有脏文件做历史字节比较，因此不把“路径集合一致”扩展成所有外部状态绝对不变。

已查看总览、瓶颈和全部5张案例PNG。案例保留完整点支持、共同范围和实际XY/XZ米制比例；XZ较扁且保留空白，不能从这种显示比例推断高度方向没有误差。全部候选/误差矩阵和SVG仍可复核。WSL在数值任务收尾时已恢复Stopped，没有为本补记再次启动。

该补记不改变下一轮建议：先核实更强普通求解器的可执行条件和观测/参考适用性，再决定验证机制；当前不训练、不提升默认。额度事实另见ACCOUNT_STATUS.json。
'''
(out/'收尾审阅补记.md').write_text(text,encoding='utf-8')
save(out/'REVIEW_ADDENDUM_SEAL.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in (out/'REVIEW_ADDENDUM.json',out/'收尾审阅补记.md',Path(__file__))]))
print('Read-only closure addendum COMPLETE')
