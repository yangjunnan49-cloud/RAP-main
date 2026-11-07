# 环境搭建顺序与故障定位

本指南基于 2026-11-04 实际环境和[公开依据](SOURCES.md)。**下面的安装命令是待目标服务器核验的参考配方，本轮未执行。** CPU 导入通过不代表干净重建、GPU 模型 I/O 或训练已就绪。PyTorch3D 原源码提交和 Muon 输入缺口见 [OBSERVED](OBSERVED.md) 与 [TRAINING](TRAINING.md)。

## 1. 先确定平台与 Python

保留 RAP-main、RAP-SLAM 仓库边界，按[运行说明](../code/RUNNING.md)准备独立路径 JSON。参考环境是 Linux x86_64、Ubuntu 24.04、Python 3.10.20；选择服务器后记录 OS、glibc、CPU/GPU 架构、驱动和存储。训练所需显存、内存与批大小尚未测定，不能把旧 12GB 显卡观察当作最低规格。

若目标使用 Conda，可先在独立环境中准备 Python 3.10.20；也可用经过确认的对应 Python 创建 venv。系统 Python/ROS2 和独立比较器环境分别维护，避免把 NumPy 2.x/Open3D 0.20 的比较器依赖混入当前 NumPy 1.26/Open3D 0.19 的 RAP 环境。不要以 base 的 Python 3.14 代替受查 Python 3.10。

原生扩展重建需要编译器、CMake/Ninja、Python 开发头文件及对应 CUDA toolkit。参考观察是 GCC 13.3、CMake 3.28.3、nvcc 12.8.93，不要求服务器照搬 /root/miniconda3 或 WSL 布局。安装系统库时按目标发行版核对 Open3D 所需 GL/EGL/OpenMP 库；缺失 so 通过 ldd 和系统包清单定位，不用反复更换 Python 包掩盖系统库问题。

## 2. 先装匹配的 Torch 组合

官方历史安装页提供 Torch 2.7.0、torchvision 0.22.0、torchaudio 2.7.0 与 CUDA 12.8 的配套命令；它与当前观察相符，但 GPU/驱动兼容仍需目标验收。[PyTorch 官方依据](https://pytorch.org/get-started/previous-versions/)

```sh
python -m pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu128
```

如使用本地 wheelhouse，应先核对清单和 SHA256，再用 --no-index/--find-links 安装，不把 WSL 的单个 torch wheel 当成完整离线闭包。本次只登记该 wheel，未打包全部依赖。

## 3. 安装核心与 SLAM 的参考配置

[core.txt](../../environment/requirements/core.txt)、[slam.txt](../../environment/requirements/slam.txt)引用 [observed-rap.constraints.txt](../../environment/requirements/observed-rap.constraints.txt)。该 184 项清单保留实际版本，包含一些可选包，不是逐包带哈希的锁文件；constraints 本身不会安装全部条目。

```sh
python -m pip install -r /path/to/RAP-main/environment/requirements/core.txt
python -m pip install -r /path/to/RAP-main/environment/requirements/slam.txt
python -m pip check
```

核心配置覆盖模型、样本读取/处理及现有导入所需的 NumPy、SciPy、h5py、Lightning、Hydra、Diffusers、Open3D 等；SLAM 增加 kiss-icp 1.3.0、gtsam 4.2、evo 1.36.5。遇到解析冲突先保留 pip 报告，核对包、Python 标签和 constraints 来源，不静默升级所有包。目标下载和解析结果均需进入新的安装收据。

## 4. 处理 PyTorch3D 编译扩展

现有预处理使用 sample_farthest_points 与 ball_query；仅安装 Torch 还不够。CPU 探针已验证现有 PyTorch3D 的 CPU 原生算子；这不验证其 GPU 路径或另一张卡。[上游安装说明](https://github.com/facebookresearch/pytorch3d/blob/main/INSTALL.md)要求匹配 Torch、CUDA 和编译器，但其列举的版本范围不能作为本地 2.7.0/0.7.9 组合获官方支持的证明。

目前无法给出“精确原版重建”的已固定提交命令：原临时源码目录不存在，安装元数据未记录提交。可选路径为：保全并测试已安装资产在相同 ABI 条件下的恢复；或在独立构建目录选择并固定明确提交，产出带来源、补丁、构建日志和 SHA256 的 wheel，再作目标数值验收。后者可能改变二进制实现，不能冒充原构建的字节恢复。

以下是固定输入后使用的构建骨架；P3D_SOURCE 必须指向已核对提交/补丁的源码副本，CUDA_ARCH 必须来自目标 GPU，不能默认照搬本机 12.0：

```sh
: "${P3D_SOURCE:?set a reviewed source checkout}"
: "${CUDA_HOME:?set the matching CUDA toolkit}"
: "${CUDA_ARCH:?set the target compute capability}"
: "${WHEELHOUSE:?set a new wheel output directory}"
TORCH_CUDA_ARCH_LIST="$CUDA_ARCH" FORCE_CUDA=1 MAX_JOBS=2 \
  python -m pip wheel --no-deps --no-build-isolation "$P3D_SOURCE" --wheel-dir "$WHEELHOUSE"
```

保留 Python/Torch/CUDA/编译器版本、源码提交、未提交差异、架构列表、编译日志和 wheel 哈希。不要运行旧 build_p3d.sh，也不要将 sm_120 的已安装扩展直接认证为任意租赁 GPU 可用。

当前源码未导入 torch_scatter/torch_sparse/torch_cluster/torch_spline_conv，故它们没有进入核心配方。若未来启用需要这些库的分支，按 Torch/CUDA 对应 wheel 索引单独安装并验证，避免回退到意外源码编译；[PyG 官方表](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html)列出 2.7.* 对应的 cu128 等组合。FlashAttention 不属于当前 SDPA 路径的必需安装项。

## 5. 可选渲染、UI、ROS2 与训练依赖

需要 Mitsuba/Gradio/laspy 时再使用 [render-ui.txt](../../environment/requirements/render-ui.txt)。它没有验收 UI、渲染后端或组会制作链。ROS2 Jazzy 位于系统层，A6 的 Node 构建缓存与 ROS2/比较器依赖也不并入核心模型环境。

训练默认引用 MuonWithAuxAdam，但现有环境没有 muon。旧 pip Git URL 未固定提交，不能复制成已验证安装步骤；先为 Muon 选定并保全明确提交及 API，再在单独实现的训练入口验收，不自动改成 AdamW 来绕过缺口。[训练审计](TRAINING.md)记录其余阻断项。

## 6. 按层验收，再运行模型

先执行[元数据与 CPU 验证](VALIDATION.md)，再检查[运行计划与输入/权重路径](../code/RUNNING.md)。目标服务器确定后才做经界定的 GPU 扩展与模型 I/O；完整训练/恢复需先补齐入口及数据划分，再执行约定的最小工程验收。本指南没有提供会自动开始训练、恢复旧科学路线或覆盖历史输出的快捷命令。

常见故障对应关系：ModuleNotFoundError → 当前 Python 和分层 profile；GLIBC/GLIBCXX/undefined symbol → 系统 ABI 与 Torch/PyTorch3D 标签；no kernel image → 目标架构与扩展构建；Hydra 插值/示例数据集 → 训练根配置缺口；缺失 ckpt → 显式路径配置。先保留失败收据，再在独立新环境修复。
