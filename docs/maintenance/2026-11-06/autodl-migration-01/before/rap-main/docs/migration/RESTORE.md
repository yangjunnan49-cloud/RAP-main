# 从交付包恢复到新工作区

使用 A7-20261104/tools/delivery.py，仅 Python 3.10+ 标准库即可恢复原字节。按[交付布局](DELIVERY.md)同时携带完整 A5 与 A7 目录，先核对交付时提供的 DELIVERY.json 和阶段 seal 摘要。输出必须是新的独立目录；不在原仓库、已有恢复树或原数据上执行。

## 完整恢复

在目标 Linux 上，从任意工作目录运行：

```sh
python /transfer/A7-20261104/tools/delivery.py restore-delivery \
  --delivery /transfer/A7-20261104/DELIVERY.json \
  --destination /new/workspace --create-internal-links
```

该命令先验证核心/附加控制清单，依次读完整基础和增量卷，校验卷/对象字节，恢复每个物理源身份，再重新读取恢复后的项目文件核对 SHA256。A5 中被替换的旧入口字节存入 archives/source-versions/A5；随后核对封存证据层、补入本轮审计记录，并按已登记旧 SHA256 更新最终当前入口和晚到 Git 元数据，旧入口另存 A7-control。

完整恢复约需 135GB 项目逻辑空间，另需控制证据、旧版本及余量；基础去重包自身约 125GB，也需保留。路径过长时 Windows 工具使用扩展绝对路径；本机原生符号链接权限不足，普通文件恢复与链接验证分开执行。目标 Linux 使用相对内部链接；两个人运行时 junction 只登记、不创建。

Linux 上普通文件按已保存 Git 模式或显式普通文件策略恢复，未知未跟踪文件默认 0644，不依据 .sh 后缀猜执行位；目录策略 0755。所有者、ACL 和未跟踪文件原 Linux 模式没有完整来源，仍须在真实目标验收。通过 Python/bash 显式调用脚本，不把 NTFS 或小型 POSIX 夹具通过当作整棵服务器权限认证。

任何缺卷、坏字节、路径穿越、映射碰撞、未知 tar 成员、错误旧版本或已有输出都会停止。失败副本/收据保留，修复后使用另一个新目录；不要删改原件或把部分恢复标为完成。恢复工具不会安装、下载、运行模型、训练、研究实验或历史图表脚本。

## 最终文件复核

需要单独重新读取最终恢复树时运行：

```sh
python /transfer/A7-20261104/tools/delivery.py check-delivery-tree \
  --delivery /transfer/A7-20261104/DELIVERY.json --workspace /new/workspace
```

最终文件表覆盖项目源、版本保留、最终当前控制和完整 A7 证据；恢复过程中产生的运行收据单独记账。普通文件核对不解释 PGC1 部分准确率，不对数据来源、校准、训练资格或科学优势作新认证。

## 路径预检与后续运行

```sh
# 只生成计划/检查路径，不加载模型；输出须新建。
python /new/workspace/RAP-main/scripts/run.py sample \
  --paths /new/workspace/RAP-main/config/runtime.example.json \
  --input /new/workspace/RAP-main/demo_example_data \
  --run-id acceptance-sample --check
```

这是路径合同检查，示例目录存在不保证其内容适用于 sample 的数据格式。实际数据、坐标/帧、校准、模型/配置对应和依赖必须按各任务说明确认；--execute 才运行实际任务。现有配置明确选择 rap_model_12，缺少原默认 rap_model.ckpt 时不静默替换。

先按[环境搭建](../environment/SETUP.md)、[训练缺口](../environment/TRAINING.md)和[迁移交接](HANDOFF.md)闭合目标保留项，再做获准的最小功能验收。本地归档/恢复不授权继续已停止研究、扩大预算、训练、对外发送或正式部署。
