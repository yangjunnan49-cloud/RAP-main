# DPA2提交交接

DPA2双锚定交叉诊断完成：4对/16查询、0原raw读取，64项损失独立核算通过。低两对完整/交集支持在双向均随自身锚切换偏好，未建立跨支持一致的末态偏好；高两对均偏末态。优化优先原末态共同几何支持/约束诊断，不据DPA1改参考或校正。无模型/ICP/训练/生产改动；UNRESOLVED/PAUSED、来源未知与旧停止保持。下一DPA3纯代数支持诊断仅草案。用户本轮授权一次聚焦RAP-main提交，不推送；原生产修改保留。

## 可复核材料

本目录inputs/为DPA1保存静态云/法线的精确副本；INPUTS.json记录来源/hash。freeze.json固定实现、父证据和输入。PROTOCOL_CN.md固定假设/预算；preflight.json和synthetic.json固定合成及资源监督结果；results/保存所有16组NN返回与交叉表，INDEPENDENT_CHECKS.json独立重算64项损失/16组距离且衔接DPA1端点。REPORT_CN.md包含全部64读数、支持统计、限制和下一决策。

在保有NumPy/SciPy的环境中，可先按ARTIFACT_MANIFEST核验字节，再将本阶段整个目录复制到新的校验目录，仅在该副本中将INDEPENDENT_CHECKS.json重命名保留，然后执行副本的verify_cross.py；它从保存数组核算，不查询NN。不要删除原件或复用原输出路径。run模式拒绝已存在results，不自动续跑。执行环境为项目Python3.10，NumPy1.26.4；原始数据和Open3D/Torch均不参与DPA2计算。

## 保留状态

旧生产22文件和两仓库未提交工作保留，当前聚合AGENTS/CURRENT_STATE等另在after/留当前快照；它们含此前工程阶段状态，不将它们整包纳入本次生产提交。本轮提交仅本目录与docs/experiments/DPA2.md，新提交不改写旧历史、不推送。提交hash由完成后的外部收据和本地START_HERE记录，避免自引用。

## 下一步

DPA3原末态互惠/法线兼容/y-z投影谱的纯代数诊断仅草案；先合成预检/冻结，不读reference/T1，不新增NN，不把谱满秩认证为正确或安全。不扩大旧ICP/门控，不恢复SSC1/PGC1或训练。
