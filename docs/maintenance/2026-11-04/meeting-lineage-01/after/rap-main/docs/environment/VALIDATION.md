# 分层环境验收

每层分别记录，不把“已安装”“CPU 能导入”“GPU 扩展能执行”“模型正确加载”“可训练”“可精确恢复”混成一个 PASS。

| 层 | 本次结果 | 尚未覆盖 |
| --- | --- | --- |
| L0 元数据与来源 | 四个环境采集；72 条旧 Linux 哈希全部匹配；部分环境资产保全 | 完整 wheel/系统库闭包、PyTorch3D 原提交与构建输入 |
| L1 CPU 依赖与 ABI | 17 项必需检查通过；4 点 PyTorch3D FPS/ball_query/KNN 夹具通过 | GPU 扩展、注册结果、完整模型/样本 I/O |
| L2 路径/配置 | A3 路径与非路径参数保持；本次 Hydra model 子配置解析通过 | 完整训练根配置/数据集资格 |
| L3 目标 GPU 与模型 I/O | 未运行 | 目标架构、扩展 GPU 算子、原权重/样本的严格 I/O、资源与精度合同 |
| L4 训练/恢复 | 未运行；Muon 缺失和入口等缺口已明列 | 有效优化、保存、恢复、跨进程/worker/rank 状态 |
| L5 干净重建/恢复 | 未执行 | 新服务器或独立干净环境的完整安装与包恢复 |

## 可重用命令

这些命令在指定目标环境显式执行；不会通过历史研究工具分派。输出收据必须使用新路径。

```sh
# 元数据工具不导入第三方包，使用 -S 禁止 site/.pth 初始化；site-path 必须明确。
python -I -S -B /path/to/RAP-main/scripts/environment/inspect_metadata.py \
  --site-path /path/to/env/lib/python3.10/site-packages --output /new/metadata.json

# CPU 探针会导入依赖与项目类，使用固定 4 点夹具；不实例化模型、不加载 checkpoint/数据、不 backward。
CUDA_VISIBLE_DEVICES='' WANDB_MODE=disabled HF_HUB_OFFLINE=1 MPLBACKEND=Agg \
  python -I -B /path/to/RAP-main/scripts/environment/cpu_probe.py \
  --rap-root /path/to/RAP-main --slam-root /path/to/RAP-SLAM --output /new/cpu-probe.json
```

CPU 探针退出 0 仅代表其必需 CPU 检查通过；Muon 作为单独训练依赖记录为非必需检查，缺失时仍使 all_optional_training_dependencies_present=false，不能据此宣称训练就绪。--help 和 CUDA_VISIBLE_DEVICES 缺失/非空的前置错误不会导入 Torch；元数据工具要求 -I -S -B 并拒绝覆盖已有收据。

目标 GPU/模型验收需要先确定硬件、环境和新输出位置，再单独约定输入/权重、允许资源与实际模型调用范围。保持 b→a、归一化、点数、特征、RNG、坐标校准、SDPA 和 scoped precision；不能拿 CPU 小夹具代替这些实际合同。训练/恢复的具体前置项见 [TRAINING.md](TRAINING.md)。

原始 [CPU_PROBE.json](../maintenance/2026-11-04/environment-readiness-01/CPU_PROBE.json)记录 17 项通过与 Muon 失败，CUDA 初始化前后均为 false。四次 WSL 维护会话均已恢复停止；不为环境验证自动启动后台研究或跨额度续跑。
