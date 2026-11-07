# 源码审计：2026-11-07

审计基线：服务器提交 RAP-main `dd94d6f292ef446ed04771476cbec90e374a3266`，RAP-SLAM `27e297c29a1765b6aa3fd640b682913dbe57be8a`。分析对象是本轮下载的 `work/audit_snapshot` 源码，不对远端修改。未读取 PGC1 部分准确率，未运行训练、GPU、旧科学实验或权重推理。

本次找到四个可独立复现的代码缺陷，以及一个已知但尚未落实到日常入口的权重加载加固项。它们不意味着已封存科学结果自动失效；训练问题主要影响待建设的完整训练路径，路径问题影响未来的标准评估命令。

## 1. [P1] 动态batch的长度与实际迭代不一致，DDP各rank可能步数不同

定位：`RAP-main/rectified_point_flow/data/datamodule.py:99`、`:128`、`:145`。

`__iter__`先按`seed+epoch`打乱全体索引，再按rank切片；`_compute_num_batches`却对未打乱索引按rank切片。`__len__`得出的“共同批次数”因此不是实际各rank批次数的上界。补齐逻辑只对过少的rank重复尾批，并不截短多出的rank；当估计低于实际时，不能保证各rank同步。

已用AST只提取原始`DynamicBatchSampler`类，并以标准库桩替代类型和dist接口，未改其方法。输入点数`[2000,4000,8000,2000]`、容量10000、seed0、shuffle=True、world_size2：

| drop_last | 两个rank报告的len | 实际迭代步数rank0/rank1 |
|---|---|---|
| False | 1 / 1 | 2 / 1 |
| True | 0 / 0 | 1 / 0 |

单个样本均不超过容量，所以不是“超大样本”特例。若该采样器直接驱动DDP，同步反向可能缺少相应rank，或上层根据错误len提前截断。这里只实际验证采样器计划；没有声称已观测到Lightning/DDP挂起，Lightning如何重建/包装自定义batch_sampler还需未来训练入口验收。

修复方向：用相同epoch排列形成一次确定的各rank batch计划，由该计划同时提供`__iter__`与`__len__`；明确补齐/丢弃策略及空rank处理。最少需覆盖异质点数、跨epoch、空rank与1/2rank计划一致性，再做真实双进程有界工程验收。

复现：`work/source_audit_repro.py`、`work/source_audit_repro.json`。

## 2. [P2] 按epoch重新抽样被内部重新设seed覆盖，始终训练同一子集

定位：`RAP-main/rectified_point_flow/data/datamodule.py:241`、`:245`。

`RandomSampledDataset.set_epoch(epoch)`先`random.seed(seed+epoch)`，随即调用`_update_indices()`；后者又执行`random.seed(seed)`，导致epoch信息丢失。对20条样本、num_samples5、seed42，epoch0到3都得到`[3,0,8,7,16]`。即便未来正确接上epoch hook，仍不会每epoch换子集。它还会更改进程全局Python RNG状态。

影响：配置中“每epoch随机抽若干样本”实际变成固定子集，多训练epoch不能带来预期的数据覆盖；不应以名义数据集大小解释训练曝光量。现有受维护训练入口尚未完成，未据此否定已有独立影子adapter实验。

修复方向：保留`epoch`字段，用局部`random.Random(seed+epoch)`生成子集，避免两次seed和全局RNG副作用；在真正会被训练框架执行的hook中更新，并把成员列表/epoch纳入恢复状态。A4已指出DataModule epoch hook可能未执行，本次发现是在hook执行以后依然存在的第二层缺陷。

复现：同上，标准库AST抽取原类。

## 3. [P2] 标准evaluate命令允许分离输入输出，但评估器路径记录会抛异常

定位：`RAP-SLAM/scripts/eval_external_trajectory.py:60`、`:103`；接口来源`RAP-main/rap_runtime/launch.py:148`、`:158`。

启动器允许任意显式`--poses-dir`和全新的输出路径，路径预检只检查输入存在；评估器却用`pose_file.resolve().relative_to(out_path.parent.resolve())`生成记录。输入轨迹若不在输出父目录树中（正常的数据/运行目录分离布局），会在指标算完后的记录阶段抛`ValueError`，结果无法保存。

已构造标准库路径夹具：输入在`input/trajectories/`，数据在`input/dataset/`，输出在`sibling runs/my-evaluation`。原launcher的`plan(... --check)`返回errors=[]；执行评估器的原始relative_to表达式必报“is not in the subpath”。这个复现只做路径合同，不读取点云或计算轨迹指标。

修复方向：记录绝对输入路径，或用`os.path.relpath`允许`..`，不要要求输入必须位于输出父目录；保存时记录清楚路径基准。添加一个输入、输出在兄弟目录的有效路径回归检查即可，无需新模型/轨迹实验。

复现：`work/evaluation_path_repro.py`、`work/evaluation_path_repro.json`。

## 4. [P2] 验证loader默认丢掉最后一个batch，完整满额batch也会丢失

定位：`RAP-main/rectified_point_flow/data/datamodule.py:122`、`:603`。

`val_dataloader`未显式传drop_last，继承默认True。采样器只要是末batch就不追加，连刚好达到max_points的末batch也丢；原docstring说的是丢“总点数不足”的最后批，代码行为更强。单rank、点数`[5000,5000]`、容量10000、shuffle=False，实际yield零批、len0。较大验证集也会遗漏固定尾部。

影响：未来验证指标与数据清单的分母不一致；小型训练/恢复验收可能根本没有验证数据。测试loader显式drop_last=False，因此不据此断言现有sample/test推理漏样本。

修复方向：验证loader显式`drop_last=False`并记录实际样本ID覆盖；训练loader另定义动态batch的drop语义，保留完整满额末批。它与第1项共享采样器，但根因和修复点不同。

## 5. [P2] 日常推理入口对checkpoint key缺失/多余仅日志告知

定位：`RAP-main/rectified_point_flow/utils/checkpoint.py:19`、`:59`；调用点`RAP-SLAM/rap_slam/rap_backend.py:102`、`RAP-main/sample.py:58`。

loader默认`strict=False`；日常调用没有覆盖，也没有把`missing_keys/unexpected_keys`提升为失败。换错同形部分权重或加载不完整state_dict时，缺失参数可能保留初始化值，命令仍继续。当前启动器只检查checkpoint文件存在。

必须保留的范围区别：本次迁移GPU probe另外严格核验了当前两个权重的state_dict，不能据此声称当前已验收权重已坏，或封存结果都用了随机参数。本项是持续入口缺少同等保证，属于此前A4已识别的缺口加固，而不是新发现当前结果失效。

修复方向：正式推理默认strict=True；确有迁移需求时用显式允许列表，同时保存加载差异与权重hash。训练warm-start可有不同合同，但不能与完整resume混用。可信旧checkpoint的完整反序列化和新的安全state_dict读取也应分开处理，避免盲改历史接口。

## 额外的架构观察（不列为代码缺陷）

- `loop_closure.py:55`合并候选时先放全部proximity，再放Scan Context，最后截全局max_candidates（默认12）。proximity已满额时，`--loop-method both`并不会给SC保留名额。这是代码明确写出的政策，不是隐藏异常；研究比较应公开候选策略、预算单位与实际来源覆盖，不能把模型未收到的回环算作模型失败。
- `run_pipeline.py:129`先读入全部扫描，再离线运行里程计和全局候选检索。当前基线不是实时流式SLAM，现有完整运行内存/时延不能直接解读为实时指标。
- `sample.py:23`全局启用TF32，而RAPBackend通过`rap_precision`作用域控制IEEE float32几何；两条入口不是已证数值等价的同一路径。已知五步/十步、采样与特征条件也要按实际配置区分，不建议为“统一”直接改冻结数值。

## 审计证据与边界

复现只使用AST中原类方法与标准库类型/随机数/路径操作，没有导入torch、numpy、Lightning，也没有改动远端或执行旧研究。父代理本轮19项现有runtime/environment测试通过；它们没有覆盖这里的数据采样和分离目录评估场景，因此两者不矛盾。

源文件SHA256：

|文件|SHA256|
|---|---|
|RAP-main/rectified_point_flow/data/datamodule.py|c5a3d69f75e61692968aed363d7e288bb1df7fa4c32007dc867885854d886f07|
|RAP-main/rectified_point_flow/utils/checkpoint.py|3b6423cf273d2f471d82bbced635806816d12f5e8e818478842c6e2ef2b54c24|
|RAP-SLAM/scripts/eval_external_trajectory.py|8c9f30337f462035e216bdd2769afb1c0bf7aeb261ad2f92dc07d517d8491237|
|RAP-main/rap_runtime/launch.py|d07c674e0024a44b0f58a66fb7075b50e7377b95035be831ec1213d76bdb9d21|
|RAP-SLAM/rap_slam/rap_backend.py|f6c0c38f39d7135476501290376119a914ae4b90d348c441fd3e783c7632fb83|
