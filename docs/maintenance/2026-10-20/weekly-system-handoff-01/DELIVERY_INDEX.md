# 本轮可交付清单

- `REPORT.md`：完整六序列B/G/KISS指标、验证、代价、原负结果及下一步边界。
- `experimental_fixed_E0_BG_20261020.zip`：全部六序列B/G轨迹，LiDAR与KITTI相机坐标各一份；未作真值对齐，保留完整帧序号与时间戳。
- `trajectory_package/README.md`：轨迹格式、源身份和实验性使用边界。06/10 ATE及07 ter、10 rer的退化均披露。
- `EXPORT_CHECKS.json`：全部24个pose文件和逆坐标转换的roundtrip、ZIP逐成员字节核对及哈希。
- `six_sequence_comparison.png`与`target_trajectories.png`：已逐图目视检查的静态科学图。
- `ANCHOR_CONTRACT_REVIEW.md`：已验证的源帧锚点契约问题与隔离实现。
- `COSTS.json`：原科学预算及扩展共享账本；没有重置上限。
- `DELIVERY_SEAL.json`与单独后续验证记录：文件身份，不等于物理源/训练排除认证。

G达到用户选定的平均ATE/ter目标，额外个体保护未全过；保留B默认配置。这里没有新完整原始前端速度测量，也不声称RAP特有增量。所有历史停止和失败不改判。账户实际边界单独记录，不从百分比低于100%推断耗尽。
