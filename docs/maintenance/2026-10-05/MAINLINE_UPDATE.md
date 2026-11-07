# 主线认知更新：核对完成，联合方向响应未形成独特增益

## Latest continuation: fixed causal local motion screen is negative

The complete58-window test is independently validated. Three-scan RAP median
local translation error0.094945m versus saved dense-map KISS0.018766m; paired
gain versus equal-support three-scan geometry is-0.002817m. Small paired
improvements over two-scan RAP/geometry fail the full frozen conjunction;
nine of18 sequence safety comparisons fail. Stop this exact native local
layout before a trajectory rerun, without budget/seed/initialization rescue.
No original RAP construction or system gain follows. Read
[LMF1 report](local-motion-screen-01/REPORT.md) and
[next design boundary](local-motion-screen-01/NEXT_ROUND_PLAN.md).
All earlier stops and official metrics remain; no training,production/default,
manuscript or Git changes. A distinct construction still needs design/evidence;
none is selected or frozen here.

## Latest continuation: causal local engineering feasibility validated

The owner explicitly restarted the terminated task. Unchanged attempt-02 now
passes the engineering preflight and independent verification: six repeated
local pipelines and two old native flows match byte-exact;18 raw scan inputs,
descriptors and noise reconstruct exactly. This proves executable causal
three-scan motion-source plumbing, not improved local accuracy or trajectory
metrics. Original failure and termination records remain. Read
[LMF0 report](local-motion-feasibility-01/REPORT.md) and its
[next local-accuracy plan](local-motion-feasibility-01/NEXT_ROUND_PLAN.md).
Complete58-window accuracy study is still planned only; no GT result, training,
production/default/manuscript edit or Git synchronization. Earlier response
negative conclusion and all other stops remain unchanged.

本轮完成了数据身份核对，以及一个新的 RAP 机制候选从工程预检到完整信息检验的闭环。结论是：目前没有证据支持修改官方 GT，也没有建立新的 RAP 算法增益。

## 当前问题收敛到哪里

完整可用文件中的帧号、绝对路径、时间序列和标定换算通过核验。265 个扫描、98 个旧端点和190 个局部时序对照独立复现，304万次点距离也通过暴力计算核验。09 的局部 GT/里程计相对运动很接近：平移差中位数约0.108米，旋转差约0.116度。异常仍集中在跨回访对齐，其误差在参考 LiDAR 的 z 分量占比较高；这不是世界竖直方向漂移的证明。缺少原始触发/OXTS记录，物理真值问题仍未定论。官方严格标签、ter/rer/ATE继续保持。

插值路线、联合 GT 机会诊断、外部配准比较已经说明：简单改传播或换回环匹配器没有解决主要指标；理想化 GT 回环也没有消除 ter 回归。把问题继续压成回环质量分数或置信矩阵，需要先证明这种信息有效。

## 这次具体探索了什么

从 RAP 刚性投影前生成的点中提取“方向响应”：同步移除两次访问中的同一空间区域，观察相对位姿六个方向的变化，并加入后期流步骤的变化。它尝试保留联合生成的关联信息。对照分别移除两边点、只看时间变化、各向同性以及等点预算几何条件。

八对工程预检通过，完整200对信息检验也完成独立核验。41对 hard08 上，相对各向同性/几何对照的配对中位增益分别为+0.356835/+0.231504；但相对独立视图/时间对照分别为-0.000334/-0.004908，未达到预设+0.03/+0.02。因此，联合空间机制没有证明自己提供了独特信息。00 正样本相对几何对照还出现-0.112298的退化，越过-0.03安全线。

这条固定路线停止。不能把它称为已校准的不确定性，也不能进入图优化后靠权重调出有利结果。解析反例进一步证明：完全刚性却错了2米的生成，可以给出近零方向响应；“稳定”不等于“正确”。

首版 evaluator 混淆了 F2 分层正样本与 E0 的15米半径，按数量检查停止；已通过显式修订恢复原始75/41样本身份。独立验证器的 GT 旋转对数舍入问题也作了单独修订。原始失败、代码、冻结和响应银行均保留，未更改结果或材料门槛。详见[完整报告](flow-directional-information-01/REPORT.md)。

## 下一步解决方法

转向一个不同的问题：RAP 直接联合生成因果局部多帧的相对运动，是否能在同样扫描数、点预算下优于当前里程计和几何多帧对照。先核实安全加载、尺度/中心/坐标约定，再冻结不按 GT 误差挑选的局部样本；只有局部运动有材料信号，才进入完整轨迹的 ter/ATE 检验。

这改变的是运动来源和物理目标，不能包装成已停止置信路线的调参续篇。普通多帧估计及 RAP 现有联合生成都有先例，三帧输入本身也不构成原创。该方向目前仅有[计划](flow-directional-information-01/NEXT_ROUND_PLAN.md)，没有新冻结、输入银行或推理结果。原始突破要求继续保留，无训练、生产默认、论文或 Git 同步改动。
