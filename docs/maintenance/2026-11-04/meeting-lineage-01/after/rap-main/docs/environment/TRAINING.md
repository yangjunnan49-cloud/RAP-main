# 完整训练与断点恢复链审计

结论：**存在训练组件，但没有受维护、已验收的完整训练入口；不能宣称迁移后已可训练或精确恢复。** A4 没有创建训练作业，也没有替换优化器、参数、划分或任何研究停止条件。机器证据见 [TRAINING_AUDIT.json](../maintenance/2026-11-04/environment-readiness-01/TRAINING_AUDIT.json)。

## 当前已有组件

| 环节 | 现有代码 | 本轮核对到的能力 |
| --- | --- | --- |
| 输入与划分 | [dataset.py](../../rectified_point_flow/data/dataset.py)、[datamodule.py](../../rectified_point_flow/data/datamodule.py) | 文件夹/HDF5、train/val、标准/随机划分回退、动态点数 batching |
| 前向与损失 | [modeling.py](../../rectified_point_flow/modeling.py) | _prepare_data、噪声/时间采样、流目标、training_step、loss、validation_step |
| 优化器 | [optimizers.py](../../rectified_point_flow/utils/optimizers.py)、[Muon 配置](../../config/model/optimizer/muon.yaml) | 模型 configure_optimizers 接 partial；Muon 与向量 Adam 组，原参数保留 |
| Trainer 片段 | [trainer/main.yaml](../../config/trainer/main.yaml) | DDP、16-mixed、2000 epochs、验证与回调配置片段 |
| 权重加载 | [checkpoint.py](../../rectified_point_flow/utils/checkpoint.py) | 加载 state_dict，默认 strict=False；这是参数加载，不是完整 Trainer 恢复 |
| RNG hook | [modeling.py](../../rectified_point_flow/modeling.py) | 保存/读取 rng_state hook，包含 Python/NumPy/Torch/CUDA 状态 |
| 日志续接 | [training.py](../../rectified_point_flow/utils/training.py) | W&B run ID 与 logger 帮助函数，不能代替优化器/调度器/步数恢复 |

## 仍需独立实现和验证的范围

1. **启动入口缺失。** 六个受维护入口文件没有 Trainer.fit 调用，没有 train.py 或训练任务分派；sample.py 调用 trainer.test 并禁用 checkpointing。不能把其 --execute 当成训练启动。
2. **顶层训练配置不完整。** 没有已验收的训练根配置；data_tmp.yaml 仍有 your_dataset_name_*，trainer/main 与 W&B 需要 experiment_name 等顶层输入。RAP_inference 的 model 子配置能解析，不能证明全部训练/logger 插值均已闭合。
3. **数据资格和划分未核验。** 需为明确数据版本固定训练/验证/测试成员、特征/GT/归一化语义、重叠或场景泄漏检查及样本计数。标准/随机划分有回退逻辑，必须记录实际使用者；不能按空 dataset_names 自动发现结果认定训练集合。A5 承接数据来源与清单。
4. **Muon 缺失且原提交未固定。** 本次实际 import muon 失败。保全一个确定 API 的提交、依赖和安装来源后再验收；不自动切 AdamW 或调整学习率来让任务启动。
5. **Warm start 与 resume 需分开设计。** load_checkpoint_for_module 只提取 state_dict；完整恢复应通过受维护入口把 ckpt_path 传给 Trainer.fit，并证明 optimizer、scheduler、epoch/global_step、scaler、callbacks 及数据/随机状态均恢复。Lightning 2.5.2 的[官方 checkpoint 说明](https://github.com/Lightning-AI/pytorch-lightning/blob/2.5.2/docs/source-pytorch/common/checkpointing_basic.rst)明确区分这些内容；本地权重文件名不能认证其包含全套状态。
6. **Sampler 与 epoch 钩子存在未闭合项。** DynamicBatchSampler 自行按 rank 分片，默认 drop_last=True、seed=0，train_dataloader 没传 DataModule.seed；RandomSampledDataset 的 epoch 更新写在 DataModule.on_train_epoch_start。Lightning 的[2.5.2 fit loop](https://github.com/Lightning-AI/pytorch-lightning/blob/2.5.2/src/lightning/pytorch/loops/fit_loop.py)会调用 sampler epoch 更新及 Module/Callback hook，不能据此推断自定义 DataModule hook 必然被调用。需分别验证数据重采样、DDP 包装、rank 分片和恢复位置，不能为迁移整洁直接改变这些行为。
7. **最小批次与验证/保存节奏需验证。** drop_last 可能令极小夹具没有训练 batch；check_val_every_n_epoch=10 与每 epoch 的保存/monitor 设置需检查指标在保存时是否存在。不能把“进程退出 0”当作发生了有效优化步骤，也不在本轮改默认值掩盖问题。
8. **精确恢复与硬件链尚无实测。** RNG hook 的定义不证明跨 worker/rank、epoch 中断或跨 GPU 的连续轨迹一致。需要明确承诺是功能续训、epoch 边界恢复还是逐步等价，并保存其证据；现有 CPU 导入和源码检查均不能代替。

## 后续训练入口的验收合同

实现范围应包括一个专用入口和完整根配置，明确区分 fresh/warm-start/resume，配置输出新目录、日志离线/在线选择、数据版本/划分清单、seed、设备/精度、优化器和停止预算。保存 resolved config、源码哈希、权重/数据哈希与恢复状态收据。输出遵守历史保全，不覆盖旧模型或结果。

在明确数据资格和入口后，先用新建的微小工程夹具完成：有效前向/有限损失、实际一次 backward/optimizer 更新、保存完整 checkpoint、在新进程恢复并核对步数和优化器状态；再作指定数据的一批验证及受约束 GPU 检查。是否要求精确数值等价要先定义，并保留失败。本轮没有执行这些训练动作，也没有为其创建后台任务。

这项工程就绪工作不恢复 SSC1/PGC1、改变原门槛或授予新研究训练资格。原有停止、预算、来源与论文边界继续有效。
