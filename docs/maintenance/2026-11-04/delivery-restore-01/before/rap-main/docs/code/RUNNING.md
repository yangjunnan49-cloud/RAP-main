# 可迁移的离线运行入口

更新：2026-11-04，Asia/Shanghai。入口脚本只需 Python 标准库即可生成计划或检查路径；执行五项任务仍需 A4 核对的依赖。[A4 环境说明](../environment/README.md)已提供搭建与 CPU 验证结果；目标环境及完整训练仍未验收。**A3 只做路径/CLI 和源码保持验证，没有加载模型、运行配准或训练。**

## 路径配置

默认布局为同级 RAP-main、RAP-SLAM、Datasets；新输出根为工作区下 RAP-runs，缓存根为 .cache/rap。有效入口不再默认依赖 E:/、/mnt/e/ 或 /root/。可以分别覆盖代码仓库、数据和权重位置，不要求目标服务器保留本机盘符。

复制 [runtime.example.json](../../config/runtime.example.json) 到本地自选位置，用 `--paths /absolute/local.json` 指定；示例内相对路径以示例所在 config 目录为基准，复制后需相应调整。也可以只设置环境变量 `RAP_PATHS_FILE`。没有自动读取当前工作目录里的隐藏配置。

优先级为 **启动器参数 > JSON > 环境变量 > 布局默认值**。JSON 路径相对于 JSON 文件所在目录；命令行和环境变量里的相对路径相对于调用时工作目录。子进程收到的路径全部为绝对路径，工作目录固定到对应仓库。JSON 不做 `${...}` 或 shell 命令展开；支持 `~`。

| JSON 键 / 启动器参数 | 环境变量 | 默认 |
| --- | --- | --- |
| workspace / --workspace | RAP_WORKSPACE | 启动器所在 RAP-main 的父目录 |
| rap_root / --rap-root | RAP_ROOT | workspace/RAP-main |
| slam_root / --slam-root | RAP_SLAM_ROOT | workspace/RAP-SLAM |
| datasets_root / --datasets-root | RAP_DATASETS_ROOT | workspace/Datasets |
| weights_root / --weights-root | RAP_WEIGHTS_ROOT | rap_root/weights |
| output_root / --output-root | RAP_OUTPUT_ROOT | workspace/RAP-runs |
| cache_root / --cache-root | RAP_CACHE_ROOT | workspace/.cache/rap |
| sample_checkpoint / --sample-checkpoint | RAP_SAMPLE_CHECKPOINT | weights_root/rap_model.ckpt |
| demo_checkpoint / --demo-checkpoint | RAP_DEMO_CHECKPOINT | weights_root/rap_model.ckpt |
| backend_checkpoint / --backend-checkpoint | RAP_BACKEND_CHECKPOINT | weights_root/rap_model_12.ckpt |
| spinnet_checkpoint / --spinnet-checkpoint | RAP_SPINNET_CHECKPOINT | weights_root/mini_spinnet_t.pth |

原 sample/demo 默认文件名 rap_model.ckpt 在当前 weights 中不存在；启动器会报缺失，不静默改用其他模型。示例 JSON **显式**指定现存 rap_model_12.ckpt，与示例采用的 rap_12 配置配套；它是可修改的路径示例，不是模型加载成功证明。其它型号同时需要明确匹配权重和模型配置，不按文件名自动猜测。

`--run-id` 只能是一个字母/数字开头的目录名，输出为 output_root/task/run-id；或用 `--output` 明确指定一个新目录，两者必选其一。旧目录一律拒绝复用，输入/输出不能包含彼此。sample 的可视化/results、demo 的 logs、features 的默认 HDF5、SLAM 和外部评测结果均写到指定新输出树。cache_root 作为子进程 RAP_CACHE_ROOT，并在没有 HF_HOME 时设为 HF_HOME 的父根；不重写其它库已有的缓存设置。

## 命令计划、检查与执行

以下命令的 `/path/to`、输入和路径配置须按实际位置替换；可以从任意工作目录调用脚本。

```sh
# 默认只输出命令计划；缺失路径列在 errors，计划模式退出码仍为 0。
python /path/to/RAP-main/scripts/run.py demo --paths /path/to/local.json --input /data/ply --run-id demo01

# --check 只检查路径，缺失时退出码 2；不导入模型、不创建输出。
python /path/to/RAP-main/scripts/run.py sample --paths /path/to/local.json --input /data/prepared --run-id sample01 --check

python /path/to/RAP-main/scripts/run.py features --paths /path/to/local.json --input /data/samples --run-id features01 --check

# SLAM real-root 的合同是其下包含 dataset/；帧范围/校准参数必须按原协议显式指定。
python /path/to/RAP-main/scripts/run.py slam --paths /path/to/local.json --real-root /data/kitti-wrapper --run-id slam01 --check -- --source real --real-seq 00 --real-start 0 --real-end 10 --real-apply-calib

# 外部评测 dataset-root 的合同是其下直接包含 poses/ 与 sequences/。
python /path/to/RAP-main/scripts/run.py evaluate --paths /path/to/local.json --poses-dir /results/external --dataset-root /data/kitti/dataset --sequences 00 --method-label external --run-id eval01 --check
```

确认配置和环境后，使用 `--execute` 替代 `--check` 才会启动对应子进程。启动器沿用自身的 Python 解释器，不调用 PATH 中另一个 python，不使用 shell 拼接。需要先在目标受测环境调用启动器；解释器、依赖、GPU 和数值 I/O 的验收待 A4。

`--` 后的选项原样传递给底层入口，保留原算法默认值。例如 demo 的 `-- --inference_sampling_steps 10`、sample 的 `-- model.inference_sampling_steps=10`。路径由启动器负责，不能在透传选项里再次覆盖输入/输出/权重或 Hydra 工作目录。evaluate 仅接受其已列出的显式参数。除 SLAM 会解析整份 argparse 参数外，其他任务的 `--check` 只检查路径，不替代底层参数或 Hydra 配置的完整验证。

## 直接入口和兼容性

- `sample.py` 默认配置名已由不存在的 RAP_base 改为 RAP_inference；旧的显式 `--config-name RAP_inference` 仍可用。demo 只为四个路径/数据集名的 Hydra 字符串加引号，计算与参数不变。
- SLAM 管线的原参数仍可直接调用；解析已拆到 cli.py，数值依赖推迟到路径检查之后。`--rap-ckpt` 和 `--spinnet-ckpt` 是新增的显式权重参数。直接调用采用布局/环境默认根，不读取启动器 JSON；显式相对参数仍按调用目录解释。
- RAPBackend 的可选 rap_root 默认为布局/环境根，显式旧绝对路径仍可传入；在随机数初始化和模型构造前检查配置与所需权重。关闭特征时不要求 miniSpinNet 文件。register(a,b) 的 b→a、归一化、RNG、精度和采样均未改动。
- 直接 sample/demo 仍保留其上游下载后备逻辑与相对目录约定。受维护的迁移运行路径通过本启动器先验证现有权重，不依赖自动下载；本轮没有触发下载。可选 app.py 与 ROS2 不在这个离线合同内。

数据目录存在不证明帧完整、校准适用或来源认证；权重存在不证明其型号/参数与配置匹配。源代码保持与路径测试也不代表目标环境数值等价或训练/恢复链已验收。完整范围见[职责说明](README.md)与[A3 检查](../maintenance/2026-11-04/code-paths-01/REPORT_CN.md)。
