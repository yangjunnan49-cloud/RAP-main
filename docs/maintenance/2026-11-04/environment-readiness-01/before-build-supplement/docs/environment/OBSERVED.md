# 已观察的本机环境与来源

观察日期：2026-11-04，Asia/Shanghai；机器时间见原始收据中的 UTC。数据来自本次只读元数据采集及限定 CPU 探针，历史 9 月/10 月观察单独保留，不冒充本次查询。

## 实际环境分层

| 环境 | 本次观察 | 用途和限制 |
| --- | --- | --- |
| rap-inference | Python 3.10.20；184 个唯一元数据目录；Torch 2.7.0+cu128、NumPy 1.26.4、Open3D 0.19.0、PyTorch3D 0.7.9、Lightning 2.5.2 | RAP 与离线 SLAM；17 项 CPU 必需检查通过，Muon 缺失 |
| kiss-slam-hc1 | Python 3.12.3；86 个元数据目录；kiss-slam 0.0.2、kiss-icp 1.3.0、map_closures 2.1.0、NumPy 2.2.6、Open3D 0.20.0 | 独立比较器环境；本轮只核对元数据/历史二进制哈希，没有重跑官方比较 |
| Miniconda base | Python 3.14.6；88 个元数据目录 | 管理环境，不能代替 RAP Python |
| 系统 /usr | Python 3.12.3；两个 dist-packages 根共 147 个元数据目录 | 系统/ROS2 层，不能把 CPython 3.10 扩展直接塞给它 |

本机 Linux 为 Ubuntu 24.04，WSL2 内核 6.18.33.2，glibc 2.39，GCC/G++ 13.3.0、CMake 3.28.3、CUDA toolkit nvcc 12.8.93。这些是实际观察，不是目标服务器硬件或最低训练资源要求。本轮没有查询 GPU、驱动可用性或显存余量；旧 RTX 5070/驱动观察仍属历史。

rap-inference 的 lib/python3.1/site-packages 与 lib/python3.10/site-packages 实际解析到同目录，device/inode 相同。原始采集有重复行，派生摘要按已核对的实际路径去重；368 行原始包元数据不是 368 个独立安装。Lightning 2.5.2 与 pytorch-lightning 2.6.5 两份 distribution 同时存在，CPU 探针导入的是 lightning 命名空间；不据此自动卸载、升级或将两个名字合并成一个版本。

## 历史引用核对

A1 待核对的 **72 条 Linux 引用、9 个唯一路径/哈希对均 EXACT_MATCH**。包括 Python、Torch 的优化器源码、Open3D 与独立比较器扩展；原声明不改写，新对照见 [LINUX_OBSERVATION.json](../maintenance/2026-11-04/environment-readiness-01/LINUX_OBSERVATION.json)。已保全对应 9 份文件的字节，原 `/root/...` 路径作为来源身份保留。

所选核心 distribution 中 4,701 条去重后的 Python 文件 RECORD 核对均匹配，未观察到这些记录内的本地改写。RECORD 本身属于安装元数据，不能认证上游原始源码、所有二进制或运行期猴子补丁；未把这一结果扩展成整套环境“无补丁”证明。

## 构建与迁移限制

- Torch 的 direct_url 指向本机 wheel；现存文件 1,097,790,941 字节，SHA256 `ac1849553ee673dfafb44c610c60cb60a2890f0e117f43599a526cf777eb8b8c`，与安装元数据一致。它仍在 WSL，未复制成 Windows 交付包；没有因此认证远程下载来源。后续打包须包含它或记录可核验的替代来源。
- PyTorch3D 的 direct_url 只有 file:///tmp/pytorch3d-build，该目录本次不存在，未找到对应受查候选源码树，原提交、原构建日志和完整编译命令尚未恢复。安装版本号 0.7.9 不能代替 Git 提交证明。
- 已保全 PyTorch3D 与 torch_cluster 的 227 份安装文件，共 23,216,081 字节，连同 distribution 元数据和历史引用文件保存在 [linux-preservation](../maintenance/2026-11-04/environment-readiness-01/linux-preservation)。这些是原字节运行资产，不是通用 wheel 或已验证的源码重建包。
- cuobjdump 对 PyTorch3D 扩展列出 sm_120 cubin；其他架构和 PTX 兼容性没有验证。torch_cluster 的部分 CUDA 扩展列出较早架构；当前 miniSpinNet 使用 PyTorch3D ball_query，当前运行源码没有导入 torch_cluster，不能把旧安装清单中的全部扩展都算作核心必需依赖。
- 现有模型 attention 使用 SDPA，没有 flash_attn 导入。旧脚本固定 Torch 2.5.1/cu124 和 FlashAttention wheel，而当前观察为 Torch 2.7.0/cu128；不能混装两套配方。原 build_p3d.sh 的 /root 路径、arch 12.0、临时目录删除与未固定仓库 HEAD 仅作历史来源，不执行该脚本。

上述保全合计只覆盖所列文件，不包含完整 Linux 环境、系统库闭包或所有软件 wheel。目标环境重建与二进制 ABI/GPU 验收仍须按 [SETUP](SETUP.md) 和 [VALIDATION](VALIDATION.md) 进行。

## WSL 操作记录

最初 WSL 为 Stopped。A4 计划第 2 项允许必要的只读环境采集；本轮两次短暂启动，分别采集元数据/源码/哈希和保全关键扩展/CPU 验证，两次均在 finally 中恢复停止状态。没有启动研究作业、模型实例或训练，CPU 探针前后 CUDA context 均未初始化。

脚本未主动改写 Linux 包或环境配置。WSL 启停会产生系统运行态和日志，不能将本次审计解释为 VHDX 镜像字节不变。原始收据：[LINUX_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/LINUX_SESSION.json)、[CPU_SESSION.json](../maintenance/2026-11-04/environment-readiness-01/CPU_SESSION.json)；沙箱控制面拒绝与已成功的宿主查询分别保存，没有将沙箱访问拒绝冒充发行版缺失。
