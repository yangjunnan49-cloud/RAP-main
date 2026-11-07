# AutoDL 迁移完成后的使用交接

2026-11-06。服务器文件与有界运行验收于北京时间13:36完成，本地83项核心文件于13:37同步完成。依据为 `MIGRATION_COMPLETE.json`、`remote-final/SERVER_FINALIZED.json` 和各层原始收据；本页补充使用方法，不替换已封存的A8权威清单。

## 登录与进入项目

```bash
ssh -p 23243 root@connect.weste.seetacloud.com
source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/rap-envs/rap-20261106
cd /root/autodl-tmp/rap-workspace-20261106/RAP-main
```

密码不写入项目。先阅读当前 `AGENTS.md`、`docs/CURRENT_STATE.md` 和 `docs/code/RUNNING.md`。标准启动器 `python scripts/run.py --help`；默认只生成命令计划，`--check` 检查路径，`--execute` 才实际运行。正式任务需按运行文档提供输入和新的输出目录。

## 资产与环境

- 运行工作区：`/root/autodl-tmp/rap-workspace-20261106`，包含独立的 `RAP-main`、`RAP-SLAM`、`Datasets`、`RAP-SLAM-report` 和 `archives/Codex`。实验、失败、预算、组会和Git历史一同保留。
- 云盘封存包：`/root/autodl-fs/rap-transfer-20261106` 下的A5、A7、A8目录。服务器589项基础/交付包共125,499,551,391字节全量SHA256匹配；恢复后112,972个普通文件共135,168,471,508字节再次逐文件校验，之后安装162项A8控制覆盖层并保留替换前版本。
- 传输加速：19个纯KITTI分卷由服务器现有只读公共缓存重建。每个数据对象与完整分卷均匹配原封存SHA256后才发布，其余分卷走SFTP。此举只证明相同字节，不增加数据来源、身份或物理参考认证。
- 项目环境：独立Python3.10.20、Torch2.7.0+cu128、NumPy1.26.4。原镜像Python包集保留。PyTorch3D按新选定明确提交为实际8.9架构构建，未恢复原历史构建提交。
- GTSAM4.2原wheel有不合法的WHEEL Tag；派生wheel仅修复该元数据及RECORD，119项代码/原生文件字节保持。原件、派生件、修复程序和证据均保留，细节见 `remote/logs/ENVIRONMENT_FIXES.md`。
- 环境安装输入、Torch/PyTorch3D/GTSAM源码或wheel及哈希存于云盘 `A8-environment-20261106`；这是已留存的关键构建资产，不是完整离线wheelhouse或整个操作系统镜像。
- 原始安装、恢复、公共缓存核对和功能收据：`/root/autodl-tmp/rap-migration-20261106`，以及本阶段 `remote/`。本地原件和A5/A7包保留。

## 已通过与仍待处理

五项路径合同、17项必需CPU检查、4点GPU扩展及一对原示例的GPU模型I/O通过。两个权重严格匹配，真实特征有效，沿用默认参数；单对配准约8.79秒，输出有限4×4变换，方向b→a。未进行准确率比较、反向传播或训练。

完整训练入口/根配置、Muon来源与安装、数据资格及精确断点恢复仍见 `docs/environment/TRAINING.md`。研究UNRESOLVED、论文PAUSED，所有旧实验停止和来源限制继续有效。迁移成功不表示完整训练链或科学复现已验收。
