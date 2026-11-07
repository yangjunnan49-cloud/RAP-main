"""Render observed data/model facts without inferring provider completeness or identity."""
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent
OUTPUT = PHASE / "updates/docs/assets"


def main():
    data = json.loads((PHASE / "DATASETS.json").read_text(encoding="utf-8"))
    models = json.loads((PHASE / "MODELS.json").read_text(encoding="utf-8"))
    lines = ["# 数据集：本地覆盖与来源边界", "", "观察：2026-11-04，Asia/Shanghai。下列为本地文件名、字节、文本行/列数及校验清单；没有读取点云数组、进行坐标/校准变换或认证原始提供方来源。完整机器记录见 [DATASETS.json](../maintenance/2026-11-04/assets-package-01/DATASETS.json)。", "",
             "## KITTI 命名的本地里程计目录", "", "根为 Datasets/data_odometry_velodyne/dataset。22 个序列的观测点云编号在各自范围内连续，时间文件计数匹配；00–10 的本地 pose 行数匹配，11–21 未见本地 pose 文件。未见不等于证明提供方缺文件，也不将这些计数提升为来源认证或训练划分准入。", "",
             "| 序列 | .bin 数 | 观测编号（含端点） | pose 行 | time 行 | calib |", "| --- | ---: | --- | ---: | ---: | --- |"]
    for row in data["odometry_format_collections"]:
        if not row["id"].startswith("datasets:"):
            continue
        pose = row["pose_text"]["nonempty_lines"] if row["pose_text"] else "未见"
        times = row["timestamps_text"]["nonempty_lines"] if row["timestamps_text"] else "未见"
        lines.append(f"| {row['sequence']} | {row['observed_cloud_files']} | {row['first_frame_id']}–{row['last_frame_id']} | {pose} | {times} | {'有' if row['calibration_asset'] else '未见'} |")
    lines += ["", "每个序列的 .bin 字节长度是否可按 16 字节划分、编号间隙、pose/time 格式与所有文件 SHA256 均在机器表中单独登记。这些结构检查不证明 x/y/z/intensity 的物理语义、测距真实性、原始/0.205° 校正状态或坐标参考。", "",
              "RAP-SLAM/data/kitti/dataset 的 55 份文件是 22 个序列的 calibration/time 与 00–10 pose 参考副本，本地该目录没有点云 .bin；不能把它当作完整 KITTI 点云数据根。", "", "## POSS 命名的下游数据", ""]
    for row in data["odometry_format_collections"]:
        if "data/poss/dataset" not in row["id"]:
            continue
        intervals = "、".join(f"{start}–{end}" for start, end in row["observed_frame_intervals_inclusive"])
        lines += [f"RAP-SLAM/data/poss/dataset：观测 {row['observed_cloud_files']:,} 份点云，编号区间为 **{intervals}**，pose/time 各 {row['pose_text']['nonempty_lines']:,} 行。点云是本地片段集合，pose/time 覆盖更长序列；不按首末编号间的缺口自动补下载、插帧或截改原参考。", ""]
    lines += ["KITTI 相机位姿与 POSS LiDAR/world 角色继续按各次协议和 real_dataset.py 的 apply_calib 合同解释，不互换；本次没有对物理参考重新认证。", "", "## Oxford Spires 与示例输入", "",
              "Datasets/oxford_spires 只观测到 5 份 GT 文本，未见 PCD 点云，标记 GT_ONLY_PARTIAL。每个文件的原路径/字节/SHA256保留，目录存在不等于整个数据集已下载或可运行。", "",
              "RAP-main/demo_example_data 下 27 组本地示例按原文件保存，属于示例位置和格式集合，不作为独立采集或训练数据资格。原始数据、派生样本、特征、预测和参考分别按原路径/协议关联；没有统一重采样或生成新数据。", "", "## 其它保留项", "",
              "- raw/OXTS 包没有新的来源认证；本次在 Datasets 根的文件清单没有看到 OXTS 命名文件。旧下载/URL-enforcement 停止不恢复。", "- Datasets/part2 的四份 EPUB 单列非研究/待判定保留资料，不读内容、不删原件、不计作研究数据。", "- 所有 dataset source_url/原发行版未在 A5 重新认证，未知字段保留 null；本地路径和现有下载脚本只是来源线索。", "- Datasets/ 是混合资产根，不能直接等同于 RAP 训练样本树。训练/验证/测试成员、特征/GT 合同与泄漏核验仍待专用训练入口和 A4 保留项验收。", "",
              "详见[资产入口](README.md)、[训练审计](../environment/TRAINING.md)和[A5 保全报告](../maintenance/2026-11-04/assets-package-01/REPORT_CN.md)。", ""]
    (OUTPUT / "DATASETS.md").write_text("\n".join(lines), encoding="utf-8")
    lines = ["# 模型/权重资产", "", "本次仅原字节 SHA256、大小、文件名和物理别名登记，没有 torch.load/pickle/模型实例。完整清单见 [MODELS.json](../maintenance/2026-11-04/assets-package-01/MODELS.json)。", "",
             "| 当前文件 | 字节 | SHA256 |", "| --- | ---: | --- |"]
    for model in models["unique_models_or_weight_artifacts"]:
        current = next(p for p in model["physical_aliases"] if p.startswith("rap-main:weights/"))
        lines.append(f"| {current.split(':',1)[1]} | {model['bytes']:,} | `{model['sha256']}` |")
    lines += ["", "三份唯一权重均另有旧维护快照物理副本，六个原路径全部保留，内容包只为相同字节存一个对象。别名关系不等于额外训练或独立模型证据。weights/.cache 的本地元数据也保留，但未找到可以认证这三份物理权重原下载来源/发行版的完整链，source_url 保持未知。", "",
              "当前 RAPBackend 显式默认 rap_model_12.ckpt；sample/demo 的原默认 rap_model.ckpt 本地缺失，A3 示例配置显式选择 12，未静默改权重。文件名中的 10/12 与现有配置只是选择线索；本次没有认证参数内容与架构匹配。", "",
              "checkpoint 是否含 optimizer/scheduler/scaler/step、RNG 或 sampler 状态仍未检查/验收；不能以文件名 .ckpt 或字节保全证明完整续训。Muon、专用训练入口和目标 GPU/干净环境保留项见[训练审计](../environment/TRAINING.md)。", "",
              "物理分卷、校验与普通文件恢复见[分包说明](PACKAGING.md)。", ""]
    (OUTPUT / "MODELS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"rendered": ["DATASETS.md", "MODELS.md"]}))


if __name__ == "__main__":
    main()
