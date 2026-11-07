from pathlib import Path
import json, hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
saved=json.loads((ROOT/'docs/meeting_20261011/benchmark/attempt03/results.json').read_text(encoding='utf-8'))
rows=saved['rows']
assert len(rows)==36 and all(r['exit']==0 for r in rows)
seqs=['00','05','06','07','09','10']
means={}
for seq in seqs:
    means[seq]={}
    for model in ['RAP-SLAM','KISS-SLAM']:
        rr=[r for r in rows if r['sequence']==seq and r['model']==model]
        assert len(rr)==3
        means[seq][model]={k:sum(r[k] for r in rr)/3 for k in ['ter','rer','ate']}
system_table=[['序列','RAP-SLAM','KISS-SLAM','回环换用 GeoTransformer']]
geo=[['0.5263','2.6664'],['0.3203','1.2973'],['0.3163','0.3531'],['0.4265','0.3968'],['0.6071','1.0007'],['0.5285','0.7635']]
for i,seq in enumerate(seqs):
    cells=[seq]
    for model,rep in [('RAP-SLAM',1),('KISS-SLAM',3)]:
        r=next(r for r in rows if r['sequence']==seq and r['model']==model and r['rep']==rep)
        cells.append(f"{r['ter']:.4f} / {r['ate']:.4f}")
    cells.append(' / '.join(geo[i]));system_table.append(cells)

sources={
'benchmark':'docs/meeting_20261011/benchmark/REPORT.md',
'benchmark_data':'docs/meeting_20261011/benchmark/attempt03/results.json',
'e0':'docs/maintenance/2026-09-26/e0-frontend-01/REPORT.md',
'heldout':'docs/maintenance/2026-09-27/e0-heldout-01/REPORT.md',
'noise':'docs/maintenance/2026-10-10/native-noise-robustness-01/REPORT.md',
'native':'docs/maintenance/2026-10-10/native-output-capability-01/REPORT.md',
'rigid':'docs/maintenance/2026-10-10/rigid-control-conditioning-01/REPORT.md',
'dtc':'docs/maintenance/2026-10-13/native-double-tail-control-01/REPORT.md',
'step':'docs/maintenance/2026-10-13/native-shadow-step-control-01/REPORT.md',
'active':'docs/maintenance/2026-10-13/activated-adapter-derivatives-01/REPORT.md',
'sampler':'docs/maintenance/2026-10-13/shadow-sampler-extraction-01/REPORT.md',
'fit':'docs/maintenance/2026-10-13/shadow-conditioned-fit-pilot-01/execution-stop-audit-01/REPORT.md',
'context':'docs/maintenance/2026-10-13/frozen-context-extraction-01/REPORT.md',
'head':'docs/maintenance/2026-10-13/frozen-metric-head-derivatives-01/REPORT.md',
'joint':'docs/maintenance/2026-10-15/nonlocal-joint-comparison-01/REPORT.md',
'identity':'docs/maintenance/2026-10-15/public-release-identity-01/identity-attempt-02/REPORT.md',
'reply':'docs/maintenance/2026-10-16/official-inference-clarification-01/REPORT.md',
'reference':'docs/maintenance/2026-10-16/regx-reference-code-01/INPUT_REFERENCE_CONTRACT_CN.md',
'contract':'docs/maintenance/2026-10-16/regx-interface-contract-01/NUMERIC_REPORT.md',
'adoption':'docs/maintenance/2026-10-16/regx-interface-contract-01/ADOPTION_DECISION_CN.md',
'review':'docs/maintenance/2026-10-16/broad-state-review-01/REPORT.md',
'strategy':'docs/maintenance/2026-10-09/bottleneck-strategy-reassessment-01/REPORT.md',
'mechanism':'docs/maintenance/2026-10-17/autonomous-continuation-06/MECHANISM_DECISION_CN.md',
}
for k,p in sources.items(): assert (ROOT/p).is_file(),(k,p)

slides=[
{'title':'完整系统横向比较','kind':'system','time':1.8,'sources':['benchmark','benchmark_data','heldout'],
'lead':'全链路：传感器校正、局部里程计、候选检索、RAP 回环验证、位姿图优化',
'takeaway':'00/05/06 平移漂移均值低 17.8%，07/09/10 对齐轨迹误差均值低 5.6%',
'note':'完整系统固定配置结果为 10 月 11 日，六序列各重复 3 次。GeoTransformer 为既有受控替换结果。',
'talk':[
'这次把上次尚未汇报的系统结果和最近一周的新进展放在一起讲。当前系统已经包含从传感器校正、局部里程计，到回环检索、RAP 配准验证和位姿图优化的完整链路。表中每格前一个数是平移漂移，后一个数是刚体对齐后的轨迹误差，两者分别反映局部运动累计质量和全局轨迹形状。',
'六条序列上，两套完整系统各运行三次。这里延续原报告的选择规则，展示 RAP 第 1 轮和 KISS 第 3 轮的真实完整成绩。00、05、06 三序列的平均漂移为 0.3887%，相对 KISS-SLAM 的 0.4727% 降低 17.8%。07、09、10 的平均轨迹误差为 0.7215 米，相对 0.7641 米降低 5.6%。',
'这些结果说明系统已经具备可持续比较的工程基础。后续工作继续利用这个基线，优先改善 00 和 05 的全局轨迹精度，并把新方法带来的收益放回完整轨迹评价。系统表的日期仍是 10 月 11 日，本周新增内容主要是后面的数值适配、多视图比较和输入接口。']},
{'title':'回环约束对完整轨迹的作用','kind':'trajectories','time':1.2,'sources':['e0','benchmark'],
'takeaway':'00 和 05 的回环优化均降低了对齐轨迹误差，形成后续改进的工作基线',
'talk':[
'这两张图直接来自已有完整系统输出。黑线是参考轨迹，红色虚线是局部里程计，绿色是加入回环并完成图优化后的轨迹，蓝色短线表示接受的回环约束。图使用首帧坐标，下面的数字沿用统一刚体对齐后的 ATE。',
'在固定的校正前端上，00 的 ATE 从里程计的 3.741 米下降到 2.754 米，05 从 1.653 米下降到 1.295 米。可以看到，回环已经在长距离轨迹中发挥作用。进一步提升时，需要同时考虑回环位姿、约束放置和测量模型，让全局修正更好地分布到轨迹中。',
'本周据此继续保留成熟的局部里程计，把新增工作的重点放在可优化的模型接口和联合观测是否能提供额外信息。']},
{'title':'原生适配保留了小任务正向信号','kind':'noise','time':1.6,'sources':['native','noise'],
'takeaway':'16 次新噪声下，四组平均平移和旋转误差均改善',
'note':'固定任务与适配参数，配对更换 16 个噪声起点。四组中一组通过全部稳定性条件。',
'talk':[
'原生适配这部分延续上次材料。我们冻结主干，只训练最后两层全局注意力中的秩 8 低秩矩阵和末端速度预测层，共 443904 个参数。每个适配任务训练 400 次，再使用原始五步采样器生成最终坐标并恢复位姿。',
'训练噪声下，合成任务两个运动部分都达到 5 厘米、0.2 度的目标。真实窗口第二部分的平移误差从 21.73 厘米下降到 2.57 厘米。随后固定参数，对 16 个新噪声起点做配对测试，四组平均平移误差分别改善 9.7%、17.8%、6.4% 和 11.9%，平均旋转误差也全部下降。',
'均值改善为继续适配提供了依据。配对平移和旋转同时不变差的次数分别为 9、11、5 和 12 次，后续开发继续关注逐次稳定性，并直接检验真实采样后的位姿。']},
{'title':'本周完成双精度末端的导数与下降验证','kind':'derivatives','time':1.6,'sources':['dtc','step','active','sampler','rigid'],
'takeaway':'已建立可复现梯度、有限步下降和五步采样绑定的数值链路',
'talk':[
'上次材料停在原生网络的一步更新和梯度复现问题。本周把这个问题拆成可验证的数值环节：保留前十层的固定特征，在双精度条件下计算最后两层和输出头，分别核对速度目标与相对位姿目标。这里讨论的是这个明确的双精度末端数值对照。',
'首先，十二个预先设置的方向导数检查全部通过。再临时激活低秩分支，A、B 矩阵和末端预测层的十八个方向检查也全部通过，三十二个完整局部矩阵导数重建一致。随后验证真实有限步长：沿负梯度方向损失下降，沿正方向损失上升，两类目标都能精确重复。',
'最后，把这套计算放回五步采样链路。两种特征提取路径、两个噪声和两次重复共八条采样轨迹逐数组一致。这样，原来的下一步问题已经推进到一套能做函数下降、能绑定采样行为的实验实现。']},
{'title':'40 次保留更新形成新的拟合可行性结果','kind':'fit','time':1.4,'sources':['fit','step','sampler'],
'takeaway':'双精度末端的速度与位姿目标各完成 20 次保留更新，训练损失均下降约 2%',
'note':'已知变换合成任务，固定前缀与双精度末端。图中为各自训练目标的归一化终点。',
'talk':[
'在导数与单步下降通过后，我们进一步完成了真实保留更新。速度目标和位姿目标各进行二十次，总共四十次更新，每一次都独立核对实际参数变化、下降条件和损失项。',
'速度损失从 7.22997 乘以十的负六次方下降到 7.08713 乘以十的负六次方。位姿目标从 198.330 下降到 194.402。图中将各自初始值设为 100，便于直接看到两条路径都降低了约百分之二。',
'这项结果把适配工作从单次局部导数检查推进到了连续更新可行性。下一阶段采用紧凑记录方式完成新定义的小任务比较，并以真实采样位姿和噪声稳定性作为选择依据。']},
{'title':'联合上下文与轻量位姿头接口已打通','kind':'context','time':1.3,'sources':['context','head'],
'takeaway':'特征来源、跨视图隔离和位姿头的局部导数均可直接检查',
'talk':[
'除了直接适配生成器，我们还把冻结特征和轻量位姿输出整理成可用接口。相同输入下，联合特征和分离特征都能精确重复，并且能与完整前向计算的指定层输出逐数组对齐。',
'其中一个关键检查是只扰动第三个扫描。分离处理时，前两个扫描的特征保持不变；联合处理时，它们能够响应第三个扫描的变化。这就为后续比较联合上下文是否提供额外位姿信息准备了直接对照。',
'在输出端，6150 参数的零初始化位姿头通过了全部局部方向导数检查，6150 个局部输出雅可比列均非零。这个接口把冻结信息和物理单位位姿输出直接连接起来，能够在设计阶段核查参数的实际作用。实际任务的方案选择以同输入几何和直接预测对照为依据。']},
{'title':'非局部多视图比较覆盖 29 个真实视图','kind':'joint','time':1.7,'sources':['joint'],
'takeaway':'已完成四个非局部分组的联合、独立配准与实用几何对照',
'note':'各组均值为参考位姿误差。实用几何使用更多点及里程计初始化，联合与独立 RAP 共享输入。',
'talk':[
'本周还把联合生成扩展到真实的非局部回访结构。四个固定分组来自 00、05、07 和 09，共包含二十九个视图、三十二条原有测量。所有分组都比较联合 RAP、独立成对 RAP，以及普通几何和包含里程计初始化的实用几何方案。',
'00 分组中，联合方案的平均平移误差为 0.783 米，低于独立 RAP 的 0.799 米，也低于实用同步几何的 0.817 米。05 的普通几何更好，07 的独立 RAP 更好，09 则几种方案都保留了约 3.9 米的共同偏差。全体联合结果为 1.483 米，独立 RAP 为 1.473 米，实用同步几何为 1.472 米。',
'这次完成的价值是把联合先验、普通多视图几何和实用初始化放进了统一对照，明确了当前联合构造的跨组差异。后续优先检验联合模型在真正需要恢复初始对齐的任务中能否增加正确恢复，而不是仅增加共同输入数量。']},
{'title':'模型来源与 RegX 变换方向已经明确','kind':'provenance','time':1.3,'sources':['identity','reply','reference','adoption'],
'takeaway':'现有权重身份和输入参考约定为后续模型对照提供了固定起点',
'talk':[
'在模型侧，三份本地权重已经与作者链接的托管文件元数据完成字节身份匹配。本地使用的是十二层模型，公开回复所描述的十二层演示模型与这个层数相符，因此当前工作的重点已经回到输入和实际功能。',
'数据侧，我们取得了固定 RegX 包中的两条 Paris_02 记录和三个点云。检查查看器实现后，明确其构造关系是先把共同世界坐标中的点云乘以 T，生成每个视图的输入，评价时持有 T 的逆变换。这个方向直接决定了模型该收到什么，以及预测姿态如何还原。',
'本周据此建立独立输入契约，构造端只交付视图点，参考数据单独保存。这样后续模型、普通几何和不同输入实现可以在同样的数据角色与坐标约定下比较。']},
{'title':'RegX 三视图输入与已知逆变换示例','kind':'regx','time':1.3,'sources':['contract','reference'],
'takeaway':'三个不同视图共享明确的输入格式与逆变换约定',
'note':'Paris_02 三视图记录的 X–Z 投影，每视图按固定间隔显示 450 点。右图使用已知逆变换还原。',
'talk':[
'这一页把刚才的输入约定画出来。左边是三个已经构造好的视图输入，颜色对应不同点云。右边使用记录中的已知逆变换，把同一批点还原到共同坐标。两边都采用同一个 X、Z 投影定义，每个视图按固定间隔显示四百五十个点。',
'这张图展示的是数据构造和坐标恢复流程。后续预测器只读取左边的视图点，右边的参考关系留给评价端。完整三视图记录包含三种真实输入点云，不是把同一份点云复制成三个部分。',
'完成这一步后，输入、坐标还原和参考角色都能单独核查，后续开展配准比较时可以直接沿用这个明确的接口。']},
{'title':'全部视图输入通过独立数值核验','kind':'validation','time':1.3,'sources':['contract'],
'takeaway':'四个固定阶段全部通过，正向和逆向误差预算使用率均低于 0.7%',
'talk':[
'接口完成后，我们对全部输入做了独立数值核验。两条样本记录共使用三个源点云，在不同记录中形成五次视图出现，总计五万六千五百五十七个点出现次数。每个点的三个坐标都进入正向和逆向检查，两类检查各十六万九千六百七十一次。',
'最大正向误差只用了预定误差预算的约百分之零点六六，逆向约百分之零点三八。合成检查、输入构造、独立读取和全点验证四个阶段全部通过。',
'这项工作交付了一个可复用的输入与参考计算基座。下一项模型比较可以直接检查有限值、刚体输出、坐标恢复和实际位姿误差，把工程实现与最终配准表现连起来。']},
{'title':'下一步以完整轨迹收益组织工程开发','kind':'plan','time':1.8,'sources':['review','strategy','mechanism'],
'takeaway':'保留现有强前端，优先解决 00/05 全局精度，并检验 RAP 的实际增量',
'talk':[
'下一步我建议把目标明确为建图系统的全局轨迹精度，主要看 ATE，同时持续展示局部漂移、旋转和计算开销。00 和 05 相对 KISS-SLAM 的全局误差差距比较清楚，适合作为开发阶段优先处理的问题，最终仍在六条完整序列上检查结果。',
'工程上优先评估成熟的直接点云测量因子后端，保持现有 E0 前端输入和回环候选一致。与先求一次配准、再固定成位姿边相比，直接测量因子允许优化过程中继续利用点云关系。GLIM 的官方实现包含纯 LiDAR 配置，这条方法值得做一次具体的接口和资源可行性判断。',
'RAP 分支采用同输入对照来判断价值：普通几何能解决的部分由普通几何承担，联合模型主要检验是否增加正确对齐或恢复能力。适配开发则优先使用已经验证的导数与采样接口，控制开发预算，把真实采样位姿作为选择依据。这里列的是下一阶段计划，具体实现和比较范围先固定，再启动对应实验。']},
{'title':'相关工作与本轮技术选择','kind':'literature','time':1.0,'sources':[],
'takeaway':'成熟几何提供强工作基线，RAP 的价值通过同输入增量比较来定位',
'talk':[
'最后一页保留原来的论文定位。RAP 提供流匹配生成配准点的基础，LoRA 提供有限参数更新方式，KISS-SLAM 提供完整系统参照，BALM 提供共享表面和紧凑地图优化的技术思路。',
'CT-ICP、MULLS-SLAM、SuMa++ 和 PIN-SLAM 的数字沿用既有论文表，主要用于了解不同系统的技术选择。新增的 GLIM 参考关注直接多扫描配准误差因子，以及纯 LiDAR 配置。',
'后续把这些成熟部件用于解决具体工程问题，同时通过普通几何、独立 RAP 和联合 RAP 的对照，定位生成模型真正增加的能力。']}
]

qa=[
('本周最实质的进展是什么', '数值适配方面完成了双精度末端导数、实际函数下降、五步采样绑定，并完成两类目标共 40 次保留更新。系统研究方面完成 29 视图、32 测量的非局部多视图对照。数据侧完成 RegX 自定义输入与参考契约，全部 56557 个点出现次数通过独立检查。'),
('上次说要查反向传播 这次推进到了哪里', '已经从反向重复性推进到完整的双精度末端数值对照。12 个方向导数全部通过，激活低秩分支后的 18 个方向检查全部通过，随后得到负方向下降和正方向上升的有限步验证，并完成 8 条五步采样路径的逐数组绑定。原生半精度路径与这套对照实现分别记录。'),
('40 次更新说明了什么', '说明固定前缀和双精度末端上的两类目标可以持续完成保留更新，并满足逐步下降条件。速度与位姿各 20 次，训练损失都下降约 2%。完整留出比较在预测产物容量上限处结束，当前结果是已知合成任务上的拟合可行性。'),
('为什么还保留小任务适配方向', '此前原生五步采样的小任务达到姿态门槛，16 个新噪声的四组均值全部改善；本周又补齐了数值下降和更新链路。下一轮以真实采样后的位姿和稳定性选择方案，采用有限开发预算，完整保留所有尝试。'),
('联合多视图的结果怎样概括', '四个非局部分组全部完成。在 00 上联合 RAP 的平移误差略低于独立和实用几何对照，05 与 07 分别由普通几何和独立 RAP 占优，09 各方法保留共同偏差。当前联合构造的整体优势尚待建立，下一步更关注它能否增加实用的正确对齐能力。'),
('RegX 现在交付了什么', '交付了自定义视图输入、独立保存的参考、严格读取格式、已知变换与逆变换、公共坐标约定和全点独立数值核验。后续可以沿用这一接口比较模型与普通几何。右侧还原图使用记录中的已知逆变换，配准模型的预测结果另行评价。'),
('输入方向是怎样确定的', '固定查看器实现把源点云作为共同世界坐标 W，使用记录的 T 构造视图 X。对应的参考为 T 的逆。我们将这个实现关系写成独立构造与评价契约，并检查全部坐标。当前报告明确采用自定义契约。'),
('与 KISS-SLAM 相比目前怎样', '00/05/06 漂移均值为 0.3887% 对 0.4727%，07/09/10 的 ATE 均值为 0.7215 米对 0.7641 米。六序列全部均值为漂移 0.4472% 对 0.4786%，ATE 1.0911 米对 0.6997 米。00 和 05 的 ATE 差距是下一阶段的明确工程目标。'),
('为什么优先看 ATE', '建图任务重点关注全局轨迹和地图一致性，ATE 更直接反映这一目标。平移漂移、旋转、逐序列表现和计算开销继续同时报告。新开发阶段的主目标与可接受折衷在运行之前固定。'),
('成熟方法对项目有什么作用', 'E0 的传感器校正已经给出明确系统收益，说明成熟工程方法具有实际价值。下一步重点评估直接测量因子等成熟后端，再检验 RAP 是否提供额外的正确初始化或恢复。工程效果和方法贡献分别用对应实验支持。'),
('为什么没有继续做存储和审计原型', '现有源身份、数值检查和采样接口已经能支持下一项具体对照。接下来把工作集中在一个可回答的系统问题上，复用已有工具，把计算资源主要用在方法开发和完整轨迹评价。'),
('下一轮预期交付什么', '先交付直接点云测量因子后端的接口与资源可行性判断，明确怎样保持 E0 前端和候选一致，以及相对现有固定姿态边改变了什么。可行后冻结一个有限开发比较，并在 00/05 开发和六序列完整评价之间保持清晰的数据角色。')
]

glossary=[
('平移漂移与对齐轨迹误差','平移漂移按 KITTI 片段长度归一化，单位为百分比。对齐轨迹误差使用一次整体刚体对齐后的位置均方根，单位为米。两者分别关注相对运动和全局形状。'),
('生成速度与五步采样','速度表示点坐标随生成进度变化的方向。五个进度输入为 1、0.8、0.6、0.4、0.2，采样器按固定规则推进，并用刚体拟合反馈生成状态。'),
('低秩适配','把权重修正写为两个小矩阵的乘积，只更新低秩分支与输出层。本项目的小任务适配使用秩 8，共 443904 个名义可训练参数。'),
('方向导数与函数下降','方向导数比较有限差分与解析梯度在同一方向的变化率。函数下降进一步检查真实有限参数步长执行后的损失是否按规则降低。'),
('固定前缀与双精度末端','前十层特征保持固定，后两层及输出头使用双精度，构成明确的数值对照函数。状态、时间常数和返回缓冲区的精度分别绑定。'),
('联合上下文与分离上下文','联合处理允许视图交换全局信息。分离处理保留各视图自己的计算路径，用来定位跨视图信息的作用。两种接口保持点行、噪声和输入约定一致。'),
('位姿头与有效参数','位姿头从冻结特征预测小的旋转和平移修正。局部输出雅可比非零说明参数能影响当前输出，实际任务收益由后续几何与位姿对照评价。'),
('RegX 输入与参考','源世界坐标为 W，构造器生成 X 等于 T 作用于 W。评价端保存 T 的逆，预测器读取视图坐标。不同记录中共享点云，因此点出现次数按记录和视图累计。'),
('直接测量因子','将点云配准残差直接放入优化目标，随位姿更新继续评价测量关系。它区别于先计算一次相对姿态，再将其作为固定图边的处理。'),
]

refs=[
('RAP','流匹配配准与原生生成模型','https://arxiv.org/abs/2512.01850'),
('KISS-ICP','局部几何里程计','https://arxiv.org/abs/2209.15397'),
('KISS-SLAM','完整系统比较与局部地图','https://arxiv.org/abs/2503.12660'),
('GeoTransformer','同点在线匹配对照','https://arxiv.org/abs/2202.06688'),
('LoRA','有限参数适配','https://arxiv.org/abs/2106.09685'),
('BALM','共享表面与紧凑地图优化','https://arxiv.org/abs/2209.08854'),
('PIN-SLAM','神经地图与全局一致性','https://arxiv.org/abs/2401.09101'),
('CT-ICP','连续时间运动模型','https://arxiv.org/abs/2109.12979'),
('MULLS','多几何误差与分层地图','https://arxiv.org/abs/2102.03771'),
('SuMa++','语义与动态物体处理','https://arxiv.org/abs/2105.11320'),
('GLIM 官方参数','纯 LiDAR 配置与多扫描测量因子','https://koide3.github.io/glim/parameters.html'),
('GLIM 官方说明','直接多扫描配准误差最小化','https://koide3.github.io/glim/'),
]

# Pure visualization of the already validated C0 arrays, with deterministic
# uniform row subsampling. No registration, model inference or new error metric.
contract=ROOT/'docs/maintenance/2026-10-16/regx-interface-contract-01'
private=json.loads((contract/'private/REFERENCE.json').read_text(encoding='utf-8'))
case=next(c for c in private['cases'] if c['case']=='case-001')
clouds=[]
for v in case['views']:
    pts=np.fromfile(contract/'inputs/case-001'/f"{v['id']}.xyz64",dtype='<f8').reshape(-1,3)
    ids=np.linspace(0,len(pts)-1,450,dtype=int)
    xyz=pts[ids]
    mat=np.array(v['view_to_world_decimal'],dtype=float)
    world=xyz@mat[:3,:3].T+mat[:3,3]
    clouds.append({'id':v['id'],'input':xyz[:,[0,2]].round(6).tolist(),'world':world[:,[0,2]].round(6).tolist()})

content={'date':'2026年10月18日','slides':slides,'system_table':system_table,'means':means,'qa':qa,'glossary':glossary,'references':refs,'sources':sources,'clouds':clouds}
(BASE/'meeting_content.json').write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
index=[]
for p in sorted(set(sources.values())):
    b=(ROOT/p).read_bytes();index.append({'path':p,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(BASE/'content_sources.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'slides':len(slides),'minutes':sum(x['time'] for x in slides),'speaking_characters':sum(len(t) for s in slides for t in s['talk']),'source_files':len(index),'regx_plot_points':sum(len(c['input']) for c in clouds)},ensure_ascii=False))
