# G06 原生路径只读审查

本轮只审查已冻结的本地源码，没有加载实际点云、GT、模型或求解器，没有生成新轨迹。八个 Python 源文件的 SHA256 均与原 S1 冻结一致，见 SOURCE_BINDINGS.json。当前证据支持下一步先补充边界观测，不支持调整并行队列、随机种子、优化参数或等价阈值。

## 已有实测证据及限制

P0 的 G 串行/并行 r1_06 最大平移差为 0.004310536749657923 m，超过原 0.001 m 门槛。G06 的串行重复之间也出现约 4.31 mm 差异，故不能把并行执行认定为唯一原因。frontend 位姿仅相差约 2.8e-13，但这不是逐字节相同输入的证明。原 packet 全摘要包含新位姿，也不能单独证明传入 native 地图的点、顺序和状态完全相同。

## 冻结源码中的实际调用链

| 边界 | 本地源码位置 | 需要区分的内容 |
|---|---|---|
| frontend → mapping | sources/kiss_slam__slam.py:61 | register_frame 输出、下采样点的字节与顺序、current_pose |
| map update | sources/kiss_slam__voxel_map.py:33 | float32 转换后的实际 native 输入，integrate/add/clear 的顺序 |
| node split/reset | sources/kiss_slam__slam.py:86 | split 帧号、relative_motion、逆变换后的继承点、clear/add 状态 |
| closure query | sources/kiss_slam__slam.py:99 | point_cloud 返回顺序、query_id、detector 历史状态 |
| finalized local maps | sources/kiss_slam__local_map_graph.py:85 | native 输出的位置及法向量（Float32），源图与目标图 |
| detector result | sources/kiss_slam__loop_closer.py:44 | source/query ID、inlier 数、initial_guess；包括拒绝候选 |
| ICP and acceptance | sources/kiss_slam__loop_closer.py:58 | 源/目标点和法向、初始变换、返回变换、体素计数和 overlap |
| coarse graph | sources/kiss_slam__slam.py:71 | 每次加入的变量/因子、固定节点、优化前后 keyposes |

源码仅显示 Python 包装层。MapClosures 与 VoxelMap 内部均进入冻结的 native 二进制；本轮没有证明其随机性、线程行为、遍历顺序或确定性。配置包装层没有显式 seed 控制，也不等于 native 内部没有随机过程。Open3D ICP 在此只显式设置 relative_rmse=1e-4；其余默认值不能凭包装层推断。PGO 包装层也不足以证明输出字典内部次序或优化器确定性。

## 下一轮的可证伪问题

先建立只记录、不改写输入的边界契约，将 prepared points/timestamps、frontend pose、map 变换、native 调用顺序、detector 结果、ICP 输入输出及 graph 状态分开。摘要必须绑定 dtype、shape、字节序、行顺序、事件顺序和组件名称。不得以四舍五入或排序使摘要相同，也不得把 derived pose 变化解释为 raw input 变化。

后续真实运行若被另行完整准入，首先比较同一串行调度的两次 frozen-input 原生重放；只在同一边界所有输入及前序状态逐字节相同、输出首次不同时，才把该边界作为进一步隔离对象。若 native 隐藏状态不能完整观测，必须保留原因未知，不能仅凭已记录的输入摘要相同判定内部不确定性。历史 raw packet 并未完整保存所有上述 native 边界，不能把从轨迹反推或新构造的点云冒充原始输入。状态型 detector/地图不能只重放一个孤立调用。

本轮不准入真实重放，也不重开 P0 queue4。下一项独立工程工作仅实现并用合成数据检验摘要/首次差异判定契约；真实 native 集成及其开销、非干预性仍需以后验证。G06 这一失败样本仅用于故障定位，不能据此宣称六序列效益、RAP 增益或新默认资格。
