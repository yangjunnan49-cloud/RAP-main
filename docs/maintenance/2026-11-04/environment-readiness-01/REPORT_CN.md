# A4：环境、依赖与完整训练链审计

日期：2026-11-04，Asia/Shanghai。授权见 [AUTHORITY.md](AUTHORITY.md)。**审计、搭建说明和现有环境 CPU 检查完成；干净重建、目标 GPU 模型 I/O、完整训练/恢复尚未验收。** 研究 UNRESOLVED，论文 PAUSED，未恢复 SSC1/PGC1 等停止路线。

## 交付与实际结果

- [环境总入口](../../../environment/README.md)、[搭建顺序](../../../environment/SETUP.md)、[实际环境](../../../environment/OBSERVED.md)、[训练缺口](../../../environment/TRAINING.md)、[分层验收](../../../environment/VALIDATION.md)和[公开来源](../../../environment/SOURCES.md)。
- [依赖图](../../../environment/DEPENDENCIES.json)：72 份当前运行相关源码、552 条静态导入边，区分函数内延迟导入；不宣称动态依赖闭包完整。
- [参考依赖配置](../../../../environment/requirements)：核心、SLAM、可选渲染/UI，以及基于 184 个实际 distribution 的 observed constraints；不是逐包来源认证或干净重建锁。
- [隔离元数据工具](../../../../scripts/environment/inspect_metadata.py)和[显式 CPU 探针](../../../../scripts/environment/cpu_probe.py)。五项任务启动器不新增训练分派；代码角色索引更新为 903 条。

四个 Linux 环境的当前采集见 [LINUX_OBSERVATION.json](LINUX_OBSERVATION.json)、[补充采集](LINUX_SUPPLEMENT.json)和[去重摘要](ENVIRONMENT_SUMMARY.json)。RAP 环境为 Python 3.10.20、Torch 2.7.0+cu128、NumPy 1.26.4、Open3D 0.19.0、PyTorch3D 0.7.9、Lightning 2.5.2；比较器、base、系统/ROS2 环境分别登记，不混成一个依赖表。RAP 的 python3.1 与 python3.10 site-packages 路径实际指向同目录，摘要以实际路径去重，原始重复行保留。

**A1 原待核对的 72 条 Linux 引用、9 个唯一路径/哈希对全部精确匹配。** 当前状态将待核对数更新为 0，旧 A1 声明和验证程序不改写。五个旧项目源码哈希、一个旧 AGENTS 中间版本及工作区外动态闭包保留项不因此消失。

所选 distribution 的 4,701 条唯一 Python 文件 RECORD 检查匹配；补充保全的 PyTorch3D/torch_cluster 227 份安装文件（其中 19 个原生二进制）也与对应 RECORD 匹配。RECORD 是安装记录，不提供上游源码或全部运行期补丁认证。

[CPU_PROBE.json](CPU_PROBE.json)记录 **17 项必需检查通过，Muon 训练依赖检查失败**。通过范围是依赖/项目类导入、Hydra model 子配置、4 点 CPU FPS/ball_query/KNN；没有构造模型、加载 checkpoint/数据、backward、优化或训练，CUDA context 前后均为 false。现有环境 CPU 检查成功不是完整训练或 GPU 数值证明。

## 明确发现的缺口

1. 无受维护的训练入口或六个有效入口中的 Trainer.fit 调用；现有 sample.py 执行 test。训练根配置仍未闭合，含示例数据集和缺少的 experiment_name 等输入。
2. Muon 不在现有环境，实际导入失败；旧 Git 安装来源未固定提交。没有自动切换优化器或修改训练参数。
3. PyTorch3D 安装来源指向已不存在的临时源码目录，两份原构建日志和原脚本已补查保全，包含编译命令与架构设置，但没有恢复精确原构建提交/完整源码输入。其安装扩展 ELF 列出 sm_120，其他架构/PTX 与目标 GPU 未验证；不能凭版本号宣称可重建或跨 GPU 通用。
4. 数据成员/划分/来源、sampler/epoch/DDP、有效 batch、监控保存节奏、warm-start 与完整 resume 的区别及跨进程状态恢复仍需实现/验收。[TRAINING_AUDIT.json](TRAINING_AUDIT.json)列出 8 项发现和 12 份带行号/哈希的源码证据；静态风险不冒充实际训练失败。

这些项作为 A4 保留项继续跟踪，不将“审计完成”写成“服务器已可训练”。后续 A5 数据/模型/全部历史清单可以继续，目标环境和专用训练入口的验收仍需在正式迁移前闭合。

## 原件、环境资产与执行范围

[BASELINE.json](BASELINE.json)和 [before](before)保全 931 份文件，含 A3 的全部 49 份当前权威文件和 896 份代码/配置。生产算法、数据处理、训练组件、原参数及旧安装脚本原字节保持；只更新两个现有维护工具（代码索引覆盖/角色与当前状态渲染），新增两个环境工具、一份测试和四份参考依赖文件。

[LINUX_PRESERVATION_MANIFEST.json](LINUX_PRESERVATION_MANIFEST.json)登记 384 份环境来源/安装/构建记录文件，共 **332,636,737 字节**。这包含历史引用原件、distribution/Conda/系统元数据及关键扩展，不是完整环境打包。Torch 的 1,097,790,941 字节本地 wheel 已核对 SHA256 与 direct_url 一致，仍只在 WSL 中登记，未复制到交付包；远程来源认证与所有 wheel/系统库闭包未完成。

本轮四次 WSL 维护会话先确认 Stopped，采集/CPU 验证后均恢复停止：[元数据会话](LINUX_SESSION.json)、[CPU 会话](CPU_SESSION.json)、[构建日志会话](BUILD_SESSION.json)、[原脚本补查](BUILD_SCRIPT_SESSION.json)及[最终宿主观察](HOST_after_build.json)。沙箱查询的访问拒绝保留在 [HOST_sandbox.json](HOST_sandbox.json)，提升到宿主的只读查询和采集均成功，没有自动审批拒绝或等待用户许可的未完成动作。没有软件包安装/下载、模型/训练/研究作业、Git 操作、原资产移动/删除或对外发送。WSL 的系统运行态/日志变化不等于 VHDX 字节不变。

旧代码用户修改保留；两个仓库边界、分支/HEAD/索引和原封存继续核对。A2 的 482 条历史目录原字节保留，当前入口另链接本次维护记录；PGC1 两处未读部分结果未解释读取。

补查先发现并保全旧失败克隆日志和成功构建日志，又读取了原脚本；失败 Git object ID、未固定 @stable 和成功本地构建没有提交绑定，详见 [BUILD_REVIEW.json](BUILD_REVIEW.json)。原扫描对 .sh 路径的存在性标签错误由独立字节证据纠正，未改写第一次扫描。补查驱动有一次隔离 Python 辅助导入失败，发生在启动 WSL 前，原驱动及修正见 [VALIDATION_FAILURE_01.json](VALIDATION_FAILURE_01.json)。

## 验证与接续

本轮 [5 项标准库工具测试](../../../../tests/test_environment_tools.py)通过。总验收见 [CHECKS.json](CHECKS.json)与 [verify_a4.py](verify_a4.py)，当前可变入口通过 [AUTHORITY_PROOF.json](AUTHORITY_PROOF.json)接续 A3，旧源码/文档快照和旧验证器保留。CPU 和元数据脚本的执行结果与来源范围分开记录，不用后补绑定冒充执行时签名。

最终总验收通过：931 份 before、63 份当前文件、693 个导航链接；2,047 项科学封存与 A0–A3 阶段封存保持。A1 的 106,767 个原普通文件作身份/元数据接续核对，3,181 份原源码/配置与 3,982 个 Git 文件另核对 SHA256；2,857 个已知 Git 时间戳差异的字节仍匹配。没有将这些分层检查冒充全资产 130GB 的本轮全量内容重哈希。

下一阶段 A5：数据、模型及全部实验历史的来源、范围、校验清单与分包组织；服务器未选定、正式迁移未完成。A4 的目标/训练保留项及原科学边界持续有效。
