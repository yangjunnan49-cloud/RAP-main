# DPA4提交与推送交接

DPA4受控结构试验完成并停止分块配方：8例/32静态NN，96分数/32距离/28Gram等独立核查通过。分块与普通NN均4正确区分/4弃权、0错误，强基线以上增量0；点到面内点均值仅2/6，不能以击败弱基线晋升。0真实数据/模型/ICP/训练/生产改动，UNRESOLVED/PAUSED和来源/旧停止保持。下一优先既有22生产修改的工程集成审阅，仅计划未执行。用户授权本轮一次聚焦提交与指定分支快进推送，包含此前DPA2/DPA3提交，未提交生产修改保留。

## 可复核产物

build_cases.py生成8固定解析例，inputs/只含点/法线/候选；EVALUATION_ONLY.json单列物理身份，scorer mechanism.py不读取。freeze.json固定所有源码/输入/评价hash，results/保存全部32组NN和选择，INDEPENDENT_CHECKS.json重算96分数等并作身份评价。REPORT_CN.md、SCORES.csv和图记录完整负结果；preflight/synthetic和各supervision记录预算。

先核验ARTIFACT_MANIFEST，可在NumPy环境运行 `python verify_mechanism.py --output /新的绝对路径/check.json` 独立重算现存结果，不追加NN；原结果拒绝覆盖。执行scorer需要SciPy，均不需要原始数据/权重/Open3D/Torch。

## 决策

分块没有普通NN以上可辨识增量，停止此配方，不调参/补例或扩真实试验。可见锚点胜弱点到面不算创新；源可见几何等价时保留歧义。下一既有22生产修改工程基线审阅仅计划，无新训练/真实数据资格。

## 发布与保全

本轮一次提交仅本目录和docs/experiments/DPA4.md，生产修改保留。指定RAP-main origin/chore/autodl-history-20261107快进推送，将包含此前两份已提交DPA2/DPA3历史；不用legacy-origin，不强推，不改RAP-SLAM远端。8入口before/after快照、旧22生产hash和旧seal保全收据在本目录；当前聚合导航仍作为工作区变更保留。提交与远端实际hash完成后存外部版本收据和本地START_HERE，避免自引用第二次提交。
