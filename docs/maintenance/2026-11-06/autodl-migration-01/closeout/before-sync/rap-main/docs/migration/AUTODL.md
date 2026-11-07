# AutoDL 实际迁移与运行入口

更新：2026-11-06，Asia/Shanghai。A8进行中；尚未声明全量迁移或训练就绪。

所有者已授权将 A5/A7 全量交付包迁至 `root@connect.weste.seetacloud.com:23243`。SSH 已连接，公钥固定在本轮 `known_hosts`；密码不存入项目。原镜像保留，使用独立项目环境。[本轮授权](../maintenance/2026-11-06/autodl-migration-01/AUTHORITY.md) / [原权威文件备份与基线](../maintenance/2026-11-06/autodl-migration-01/BASELINE.json)。

## 路径与用途

| 路径 | 用途与状态 |
| --- | --- |
| `/root/autodl-fs/rap-transfer-20261106/{A5-20261104,A7-20261104}` | 云盘封存包；589文件/125,499,551,391字节，上传中 |
| `/root/autodl-tmp/rap-workspace-20261106` | 全部包校验通过后创建的独立工作区；不在半包上运行项目 |
| `/root/autodl-tmp/rap-envs/rap-20261106` | 独立 Conda Python 3.10.20 环境；依赖安装/验收中 |
| `/root/autodl-tmp/rap-migration-20261106` | 本轮日志、安装输入、恢复程序与运行收据 |

目标实测：Ubuntu22.04.5、GCC11.4、CUDA toolkit12.8.93，驱动595.71.05；GPU报告 `NVIDIA GeForce RTX 4090 / 49140 MiB`。基础镜像 Python3.12.3/Torch2.8.0+cu128/NumPy2.3.2；这是保留的原镜像环境，并非已验收的项目环境。数据盘300GiB、云盘200GiB；容器内存上限72GiB、CPU配额20核，`free` 的宿主机内存不作为实例可用配额。初始证据见[REMOTE_PREFLIGHT](../maintenance/2026-11-06/autodl-migration-01/REMOTE_PREFLIGHT.json)。

封存包使用现有云盘、恢复工作区使用数据盘，未申请额外容量。该布局遵循[AutoDL文件存储说明](https://www.autodl.com/docs/fs/)和[目录说明](https://www.autodl.com/docs/env/)：云端留封存副本，运行使用本地数据盘。A5/A7包及本地原件均保留。

## 迁移门槛

四路压缩 SFTP 传输30个基础卷；控制清单与 A7增量/证据一同传输。服务器受控恢复程序先等待所有文件尺寸稳定，再逐文件核对 SHA256，匹配本地固定的[EXPECTED_UPLOAD](../maintenance/2026-11-06/autodl-migration-01/EXPECTED_UPLOAD.json)。遇到缺卷、坏字节、已有输出或恢复失败停止，保留失败收据。等待上限48小时，无科研任务。

完整上传通过后才执行已封存的 A7恢复工具，重新读取112,972个最终普通文件/135,168,471,508字节，核对25个内部相对链接、2个个人junction不重建、普通文件0644和观察到的目标所有者。此处模式是明确的恢复策略，不是原Linux所有者/ACL来源认证。

服务器文件验收收据位于 `/root/autodl-tmp/rap-migration-20261106/file-acceptance/`：`STATUS.json` 是进度；`UPLOAD_VERIFIED.json`、`RESTORE.json`、`FINAL_TREE_CHECK.json`、`POSIX_CHECK.json`、`ACCEPTANCE.json` 才是相应成功证明；`FAILURE.json` 表示停止。不得仅凭目录存在或上传进程存在宣布成功。

## 环境与后续入口

按[环境搭建顺序](../environment/SETUP.md)对齐 Python3.10.20/Torch2.7.0+cu128/NumPy1.26.4 等已观察组合。PyTorch3D需为实际GPU重新构建，不复用原sm120二进制；新选定明确上游提交的构建与原提交未恢复的事实分别记录。安装解析报告、源码与wheel哈希、CPU/GPU最小检查收据完成后更新本页。

恢复后的仓库为 `.../rap-workspace-20261106/RAP-main` 和同级 `RAP-SLAM`，数据在同级 `Datasets`，报告在 `RAP-SLAM-report`，外部历史在 `archives/Codex`。使用标准启动器和 `config/runtime.example.json`；完整恢复/依赖验收前不执行模型入口。完整训练入口、Muon及断点恢复链仍是[A4训练缺口](../environment/TRAINING.md)，本轮不自动实现或开训。
