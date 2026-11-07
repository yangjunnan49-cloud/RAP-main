# RAP-SLAM 交接审查报告

日期：2026-09-09。对象：研究生论文项目。审查目标是建立证据链并制定维护计划，不在本轮改进算法指标。

## 范围、证据等级和限制

审查覆盖双仓库状态、AGENTS/README/论文大纲、数据加载、RAP 适配、检索、门控、PGO、ROS 生命周期、评估脚本、结果保存、S0/S1、P0–P4 研究叙述。111 个受版本控制的非 vendor Python 文件通过 AST 解析，20 个 shell 脚本通过 `bash -n`。核心模型冒烟、SC 批量/标量一致性、归一化回算、簇门控与 NMS 小例、7 组保存 PGO 重跑均已执行。

证据等级：**A** 为本次执行复现；**B** 为直接代码/产物/原始文献证据；**C** 为需额外实验确认影响范围的风险。高优先级表示可能改变论文结论或核心正确性，不等于整个项目无效。

本次没有完整重跑每一个 GPU 研究矩阵、ROS 全序列、PPT/PDF 的每页图表，也没有进行依赖 CVE 穷举、全部点云逐字节验证或 checkpoint 训练成员重建。报告是全面覆盖主要链路的审查，不是这些未执行工作的完成证明。作者身份/继承来源不作为质量判断依据。

详细机器证据在同目录 `audit_results.json`；可复核脚本为 `audit_checks.py`；561 项已读取的小文件指纹在 `manifest.json`。指纹清单不是数据备份，也没有覆盖全部大型缓存和权重。

## 高优先级：影响论文解释或基础正确性

### F01 — “未再训练”与“模型未见域”的零样本概念混用（B，必须澄清）

[AGENTS P4计划](E:/githouse/RAP-main/AGENTS.md:364) 将 Oxford Spires 当成新传感器零样本测试；部分 KITTI 比较也用 ZERO-SHOT 表述。但 RAP 原论文 §4.1、附录表4把 **KITTI 与 Oxford Spires 均列入训练数据**。表4记载 KITTI 22 scenes、Spires 6 scenes。来源：[RAP v2](https://arxiv.org/html/2512.01850v2#S4.SS1)、[训练数据表](https://arxiv.org/html/2512.01850v2#A2.SS4)。

因此不能据“本项目冻结网络”推出“RAP 未见这两个域/传感器”。具体本地 checkpoint 是否同训练配方、评测序列是否与预训练重合，仍须独立追溯。维护前采用“冻结预训练 RAP、无任务级微调”；将 unseen-domain 宣称挂起，而不是否定现有系统实验。

### F02 — TF32 使刚体拟合的旋转偏离 SO(3)，历史小角度误差不可靠（A）

[后端开启 TF32](E:/githouse/RAP-SLAM/rap_slam/rap_backend.py:80)，[Procrustes](E:/githouse/RAP-main/rectified_point_flow/procrustes.py:26) 在 float32 语境下做矩阵乘法，仍受 TF32 影响。“float32 autocast”本身不保证禁用 TF32。

七组保存边的最大逐元素 `|RᵀR−I|` 约 0.0011–0.0017。小型真实 CUDA 拟合复现：TF32 开启为 4.33e-4，关闭为 4.77e-7；说明这条数值路径确实会产生问题。

现有角度用 `acos(clip((trace(R)-1)/2))`，但非正交矩阵不满足公式前提。仅将保存边旋转投影至 SO(3) 后进行诊断，POSS offline 原先 4/4 个 0°变成非零，中位约 0.256°；POSS live 单边指标最大变化约 2.513°。投影诊断不是重跑后的真值，也没有写回原边。

影响：RAP 边旋转精度、P2/S1 旋转标签与 σ、N-way 旋转比较，以及 GTSAM 接收的变换。修复应保护最终刚体拟合及必要的刚性强制步骤，加入合法性验证，然后重新生成有代表性的边；不能直接用投影后的旧边悄悄替换论文结果。

### F03 — KITTI “官方 ter”实际是长度宏平均，另有帧对应漏洞（A/B）

[kitti_drift](E:/githouse/RAP-SLAM/scripts/eval_paper_metrics.py:117) 先分别平均每种长度，再对有样本的长度等权平均；这与按全部子段误差汇总不同。`kitti_segments` 返回的是长度种类数，不是子段数。官方说明按子序列误差汇总：[KITTI](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)。

本次保持现有 LiDAR 坐标系，只比较长度宏平均与全部子段平均，里程计 ter[%] 已有差异：03 为 1.119→0.940，04 为 1.064→0.927，06 为 0.583→0.642。上述新值是审计对照值，**未标为官方最终分数**；尚须与官方 C++/选定参考实现逐项对拍，统一 camera/LiDAR 参考点、末端选择规则和跨序列平均。

[evaluate_pair](E:/githouse/RAP-SLAM/scripts/eval_paper_metrics.py:146) 将不同长度序列截成较短者继续打分；小例已复现。`gt_from_summary` 不应用 `real_stride`；TUM 读取抛弃时间戳。缺帧或抽帧时可能输出看似正常但错配的指标。七组基线本次长度一致，这项不直接推翻它们。

### F04 — S1 把不同采样结果的特征和标签拼成一条记录（A/B）

[build_s1_features](E:/githouse/RAP-SLAM/scripts/build_s1_features.py:241) 对多生成取 max overlap 与 min mean_dist，却不确保来自同一次生成；[attach_labels](E:/githouse/RAP-SLAM/scripts/build_s1_features.py:288) 又按 `(dataset,i,j)` 从旧配准结果借用 GT 误差。随机注册的误差属于具体 T_rel，不只属于点云对。

195 条多生成记录中，114 条的 mean_dist 不是运行时 best-overlap 所选生成的 mean_dist。按保存 best-generation T_rel 重算后，3 条 safe/dangerous 标签与保存标签不同（详见 JSON）。此外没有 T_rel 时退回 GT 距离标签，混合了“地点是否接近”和“位姿估计是否正确”两个任务。

修复：每次验证持久化 run_id、pair_id、generation_id、T_rel、同次诊断与误差；地点标签与变换正确性标签分列。无法恢复同次结果的记录标为不可用，不能借用另一轮结果补齐。

### F05 — SC margin 数据库包含查询自身/未来帧（A/B）

[attach_sc_margin](E:/githouse/RAP-SLAM/scripts/build_s1_features.py:403) 排除的是 i 附近帧，没有排除查询 j，也没有约束到 j 时刻已可访问的历史关键帧。828 条特征记录中 695 条 `margin ≈ -d1`，自匹配把第二地点距离压到零。

该特征不能按预期解释为检索歧义，也不与未来在线特征等价。修复后须生成新版本特征及重新评估 A2/S1b，不能延用现有权重。

### F06 — S1 划分泄漏，验收混入训练样本并允许未评分通过（A/B）

[stratified_split](E:/githouse/RAP-SLAM/scripts/eval_conformal_s1.py:117) 按记录与数据集别名分层，没有按真实序列/配准对/回环地点分组。本次复现 FIT/CALIB/TEST 为 347/173/178；FIT–TEST 有 50 个相同物理配准对，TEST 中 50 条见过训练配准对。CALIB–TEST 也有 30 对相交。

[clause1](E:/githouse/RAP-SLAM/scripts/eval_conformal_s1.py:275) 使用全部记录的 per-set 结果（含 FIT/CALIB），且未评分不阻止 PASS。报告中 bigbudget 121 条未评分仍 True。单独的 overlap-only 分支不能充当 A2 在该集合上的完整评估。

S1b 的 leave-one-golden-out 只排除 ds 名称，POSS offline/live 与 KITTI06 offline/live 实际同一物理序列；这是留出“产物”而非独立序列。需要物理序列与回环区域分组、按组划分 manifest；数据不足就缩小结论，不重复抽边冒充独立样本。

### F07 — 部署版 conformal 的训练/校准不独立（B）

[ConformalGate.fit](E:/githouse/RAP-SLAM/rap_slam/conformal_gate.py:70) 用全部标签训练 logistic，再从同一数据计算阈值。与评估版 split-conformal 不同；拟合内危险接受率≤5%不是独立测试保证。参考：[Angelopoulos & Bates](https://arxiv.org/html/2107.07511v6)。

还需区别 `P(accept | dangerous)` 与“接受边中危险边比例”，两者不是同一个概率；交换性假设在强相关、多次采样、混合筛选数据下也需明确。TEST 5.3% 本身不构成定理被违反，经验频率可波动；随意加 `1/(n+1)` 也不能替代置信分析。

默认仍是启发式，因此直接影响可选 conformal 臂及论文声明。导出的模型、阈值和验收模型必须相同；特征不足时不能把启发式 fallback 算作 conformal 通过。

### F08 — P2 的 σ 覆盖率定义与代码阈值不一致（B）

[coverage_report](E:/githouse/RAP-SLAM/scripts/eval_calibrated_weighting.py:247) 把 1.347/2.448/3.478 标为 half-normal 的 68.3/95.4/99.7% 阈值；这不是标准半正态对应分位数。拟合却按 `P(error≤sigma)=0.683` 缩放，报告再按 `error<1.347*sigma` 评估，拟合与测量不一致。

此外 TE 是三维平移误差范数，GTSAM 的 sigma_t 被复制为三个坐标轴标准差，两种量不能直接等同。在理想各向同性三维高斯下，范数应按 χ(3) 而非单变量绝对值解释。当前模型可以保留为经验权重，但不能据这些覆盖率直接声称协方差已校准。建议使用 SE(3) tangent 残差和 Mahalanobis/χ² 检查，或明确仅预测标量误差上界。

## 中优先级：评估边界、实验一致性与工程可靠性

### F09 — S1b 等覆盖宽度属于事后诊断，阴性实验不能推出无信号（B/C）

[eval_sigma](E:/githouse/RAP-SLAM/scripts/eval_conformal_s1.py:363) 用 TEST 真值计算等覆盖缩放。**这并非自动无效的描述性比较**：比较不同模型在同一测试集的宽度曲线可以有意义；但不能解释为可部署校准器的无泄漏性能。这是对上轮简审措辞的补充限定。

选模型还使用 CALIB 等覆盖宽度，然后用同一 CALIB 校准，若要保留严格保证应增加独立选择集或嵌套流程。0.937 未达 0.90 只说明这个受限实验未达到预设改善幅度；在特征错误、相关划分和旋转误差修复前，更不能推导“误差与诊断无关”。

### F10 — Spires 忽略的是 180°外参旋转，不只是小杆臂（B）

[加载器注释与实现](E:/githouse/RAP-SLAM/rap_slam/spires_dataset.py:13) 省略基座–雷达外参。官方值 `[0,0,0.124,0,0,1,0]`（xyzw）含 180° yaw：[官方传感器说明](https://github.com/ori-drs/oxford_spires_dataset/wiki/Sensors#extrinsics)。

若 `X=T_base_lidar`，正确 LiDAR GT 为 `T_world_base @ X`；首次位姿归一后仍是 `X⁻¹ @ T_base_relative @ X`，不是直接的基座相对轨迹。未下载点云、未跑端到端，故这是已证实的入口问题，不是已发生的某个 Spires 分数错误。

### F11 — 地图 crispness 不是真正的 leave-one-scan-out 最近邻（A/B）

[crispness](E:/githouse/RAP-SLAM/scripts/eval_map_consistency.py:97) 只查最近8点，没有异标签就赋1m；真实异帧近邻可能排在第9名之后。11点反例得到0.9128m，精确异帧搜索为0.04509m。全局 voxel 又只留一个扫描标签，完全重合处的多帧观测被删掉，进一步影响定义。

不要将当前 crispness 当作已验证部署监控器。Chamfer 与它独立，不因该 bug 自动失效；但其参考是同源扫描按 GT 位姿合成地图，不是独立测绘真值。

### F12 — 主对比表混合不同管线配置，S0b 尚未吸收到表中（B）

[make_comparison_table](E:/githouse/RAP-SLAM/scripts/make_comparison_table.py:36) 混用 budget40 offline、budget12 offline、live NMS10，文字却称所有 full 都启用 NMS10；离线注册实际有 NMS0。主指标注册表未含205臂；生成一次“最新表”仍会产出旧口径。

维护时保留 legacy regression 与 paper reporting 两个明确命名的表，不拼各序列最佳结果成一个统一默认。与文献的输入模态、训练数据、预处理、指标统计方式逐项对齐；已有文献抄表不是完整系统重跑。

### F13 — 缓存未绑定参数/代码，部分命中改变随机流（B/C）

[N-way 缓存](E:/githouse/RAP-SLAM/scripts/eval_nway_matrix.py:223) 名称只有 golden/cluster/seed，内容只有 members/T_parts，不含 points_budget、checkpoint、代码版本或预处理。改变预算但 members 不变仍复用旧结果。其他 descriptor/submap 缓存也有类似模式。

模型只在构造时设置全局随机种子；部分缓存命中会跳过随机数消耗，后续缺失项不等价于完整重跑。必须在请求级固定可重建种子，缓存以输入/参数/权重版本 hash 为键；冷缓存、全命中、部分命中三种路径要相互核验。

### F14 — P3 不同实验脚本使用不同重门控，替换位姿后仍留旧诊断（B/C）

[matrix](E:/githouse/RAP-SLAM/scripts/eval_nway_matrix.py:272) 替换 T_rel，但 overlap/mean_dist 仍来自 pairwise，PGO/NMS 权重并未随新测量更新。matrix 的门为簇中位 mean_dist≤2.0；[submap](E:/githouse/RAP-SLAM/scripts/eval_submap_nway.py:28) 是逐边 overlap≥0.5 且 mean_dist≤2.0。不是同一门控定义。

固定旧权重可以作为有意的“仅替换位姿”消融，但必须这样命名；否则不符合“后端消费当前 RAP 边诊断”的叙述。统一实验配置，分别报告 pose-only 与 pose+diagnostics，避免未经验证直接改默认。

### F15 — 在线连接中断与关闭流程缺乏可恢复状态（B）

[RapClient](E:/githouse/RAP-SLAM/ros2/loop_closure_node.py:198) 失败后把 socket 置 None，却没有重连；下次 sendall 会 AttributeError，不在现有捕获范围。worker 可终止而主 ROS 节点继续。PGO 失败后 pending 也被清除。关闭仅等5秒，而请求超时600秒，可能在 worker 尚未完成时保存不一致产物。

应有明确的 RUNNING/DRAINING/FAILED/COMPLETE 状态、失败重连/有限重试、最终 PGO 和原子保存；整条任务失败不能只靠日志警告。

### F16 — 数据加载和评估仍依赖顺序，不保证 frame ID 对应（A/B）

[real_dataset](E:/githouse/RAP-SLAM/rap_slam/real_dataset.py:104) 对现存文件列表抽 stride，GT 对原始时间范围抽 stride。小例缺 frame1 时 `stride=2`，读取 scans `[0,3,5]`，却配 GT `[0,2,4]`，数量相同所以 assert 通过。

流式播放器 stamp 是发布时间而非原始数据时间，轨迹行号不再可靠地代表源帧。维护须贯穿保留 source_frame_id 与原始 timestamp；完整性失败停止评估，不通过缩短GT掩盖缺失。

### F17 — 回归脚本会覆盖证据，且 PASS/FAIL 判据失衡（A/B）

[verify_step3_kitti](E:/githouse/RAP-SLAM/ros2/verify_step3_kitti.sh:61) 启动删除旧结果；[198行](E:/githouse/RAP-SLAM/ros2/verify_step3_kitti.sh:198) 用统一10m阈值判长序列失败，但缺校正轨迹、PGO变差仅警告。`output*` 被 Git 忽略，且历史日志确实已有覆盖记录。

存证、运行完整性与算法指标三种门分开；使用独立 run 目录、原子完成标记和机器可读全部候选记录。缺失产物不得 PASS；长序列用固定基线回归而不是统一绝对阈值。

### F18 — 空图可选分支崩溃、失败可退成另一算法（A/B）

`loop_clique_width>0` 且无回环时，[pose_graph.py:290](E:/githouse/RAP-SLAM/rap_slam/pose_graph.py:290) 的 max([]) 已复现 ValueError。`run_odometry` 捕获任意 KISS 初始化/首帧异常后退成 Open3D；虽然 summary 记录 backend，但批处理若只看成功退出会把另一种算法混入实验。fallback 的 max_range 也未用于 `_prep`。

研究运行应 fail-fast 或显式允许 fallback，产物和总表按实际后端检查。该项不影响本次七组保存后端复现。

### F19 — 历史路线图与论文大纲存在过度概括（B）

[main.tex](E:/githouse/RAP-SLAM-report/paper/main.tex:190) 仍有“零误收”“0/37→全覆盖”；后续日志已记录严格标签下6条危险接受，检索32/37≈86%。几组失败实验被叙述为“唯一上限”“in principle无法识别”，证据不足以支持普遍结论。

特别是 AGENTS 的 N-way 后续建议用同批次的三角闭合残差发现 warp：若边都来自 `Tij=Ti⁻¹Tj`，则 `Tij*Tjk*Tki=I` 代数恒成立，即使布局错误也如此。需要独立估计或跨批次约束才能形成非平凡一致性检查。

原论文框架与自己实验贡献需要清楚分开。模型是否“核心”不是可验证的创新指标；本次也不对论文创新性或毕业可行性作保证。修正后再以独立对照、明确问题和可复现收益确定贡献。

## 其他维护债务（不阻断本轮存证）

- `sample.py:76` 默认缺失的 RAP_base；test_smoke 是依赖 CUDA 的 shape smoke，不能称 dependency-free，也没有数值断言。
- RAPBackend 推理计时在 `.cpu()` 同步之前结束，不能作为准确 GPU latency；需 CUDA events 或同步计时并记录预处理/排队/总耗时。
- SDPA softcap 参数被忽略，但当前配置未检出非零配置；标为将来接口兼容风险，不当作当前精度 bug。默认 softcap=0 的小例与显式注意力结果差约5.96e-7。
- PGO 段内用最近关键帧的常量校正，不做连续插值；变长关键帧间隔共用里程计噪声。这是建模选择与潜在 RPE/地图边界风险，需要对照，不能直接判错或贸然替换。
- ROS map_max_points 只限制输出，缓存扫描仍随时长增长；长序列资源上限需明确。
- `requirements.txt` 仅锁三项 SLAM 包，S1 使用的 sklearn 等依赖靠既有环境；尚无完整锁定和自动 CI。
- socket 默认本机但使用无长度上限 pickle，不能视为适合公开服务；Gradio 默认0.0.0.0并分享。未发现本次正在对外部署的证据，故属边界说明，不是要求现在扩展安全改造。
- 原始权重训练来源、内容 hash、预处理版本没有贯穿结果 manifest；报告目录独立于代码 Git，备份状态不明。

## 本次正向验证

七组后端重算均复现；保存边均为有限数；111个Python文件和20个shell语法通过；小模型前向输出(1000,3)；归一化回算最大误差8.24e-7；SC scalar/batch小例数值和shift一致；簇 immediate/strong 与NMS保留最高overlap小例通过。KITTI00–21目录无帧号空洞，已核对00–10数量；两仓库本地/远端HEAD一致。

这些是保留成果的依据。优先维护论文证据链和基础数值，而非推倒系统重写。
