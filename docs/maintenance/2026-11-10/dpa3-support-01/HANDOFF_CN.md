# DPA3提交交接

DPA3原末态支持代数诊断完成：4对、0新NN/原raw/参考数组读取，32组Gram/谱等独立核对通过。低对6129/7592互惠点对，法线中位夹角约10.06/8.58°，互惠y/z谱比.677–.837，未见该投影单方向近零表现，但不认证物理正确。固定02局部诊断收束，下一策略为结构关联歧义的受控可辨识性与弃权验证；不增加旧ICP迭代或调门控。0模型/训练/生产改动，UNRESOLVED/PAUSED及来源/旧停止保持。一次聚焦RAP-main提交，不推送。

## 输入与复核

inputs/每个NPZ只含9个许可字段；INPUTS.json逐成员接续DPA2已提交数据，不含reference/T1。计算support_algebra.py、监督supervise.py及独立verify_algebra.py均在freeze.json冻结。preflight/synthetic保存10项合成与4类资源负例；real/validation-supervision分别记录真实与核查预算。results/保存4对全部/互惠统计，GRAMS.csv含32组矩阵、谱及特征向量，REPORT_CN.md含结论和局限。

可在NumPy环境中先核验ARTIFACT_MANIFEST，再运行 `python verify_algebra.py --output /新的绝对路径/check.json`，输出拒绝覆盖；计算无需SciPy/Open3D/Torch或原raw，不追加NN。不要在旧results执行run模式，原输出拒绝复用。

## 决策与保全

DPA1–3固定02局部诊断收束，不默认继续局部谱/剖面或同一ICP。低对的数千互惠、法线兼容和非退化y/z投影仍不能证明结构身份/参考物理正确。下一受控结构关联歧义/弃权机制合同DPA4仅草案，先与强几何比，零新增信息即停，不以解析构造绕过来源缺口或准入训练。

旧22生产文件、历史封存和失败保持；当前入口8份先备份后更新，after/提供日期快照。一次聚焦提交仅本目录与docs/experiments/DPA3.md，不混入既有生产修改，不推送；实际hash完成后置外部收据和本地START_HERE，避免自引用二次提交。
