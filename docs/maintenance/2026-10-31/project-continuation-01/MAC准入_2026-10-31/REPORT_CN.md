# MAC准入与独立Windows路径

**官方MAC数值比较未准入；已完成固定版本的源码审阅。** 当前WSL控制接口在获批的网络/环境读取权限后仍返回E_ACCESSDENIED。已核实的Windows捆绑Python运行时没有igraph、Torch、Open3D或SciPy；PCL原生构建依赖未完成检测，不能宣称整台机器没有PCL。没有安装、克隆仓库或运行MAC演示。另行冻结的PGC1是独立NumPy图一致性对照，其差异写入专属协议，不能用它声称复现官方MAC性能。

固定作者仓库提交为 `b0d19635c4c9d69399397495d02422eda94248c2`，代码和MIT许可证的字节数、SHA与原始URL保存在 `work/mac_admission/pinned/SOURCE_RECORD.json`。这里只保存审阅所需的几个源码文件；没有取得训练权重或新数据。来源为[作者仓库](https://github.com/zhangxy0517/3D-Registration-with-Maximal-Cliques)。

## 入口的真值依赖

固定版本Python演示的 `test()` 读取GTmat并在第240–241行根据精化前后的旋转/平移真值误差选择最终变换。该入口不满足本项目“先封存预测、后读取参考”的要求。[固定Python入口](https://github.com/zhangxy0517/3D-Registration-with-Maximal-Cliques/blob/b0d19635c4c9d69399397495d02422eda94248c2/Python_implement/example.py)。

固定版本C++注册函数第1317行附近已保存精化后的 `est.txt`，后续第1384行附近才出现基于真值误差的回退/打印分支；`GT_cmp_mode` 默认关闭。因此，不能把Python演示的依赖直接推广为“全部C++保存矩阵由真值挑选”。后续适配应把预测矩阵输出与评价返回值分别审计。[固定C++入口](https://github.com/zhangxy0517/3D-Registration-with-Maximal-Cliques/blob/b0d19635c4c9d69399397495d02422eda94248c2/Linux/registration.cpp)。

以上是静态入口审阅，不证明论文实验使用了某个具体入口，也不据此改写作者论文结论。原论文机制仍可作为普通求解器比较依据。[原论文](https://openaccess.thecvf.com/content/CVPR2023/html/Zhang_3D_Registration_With_Maximal_Cliques_CVPR_2023_paper.html)。

## PGC1的独立问题

PGC1保留原全部200对和273份4000点支持及32维miniSpinNet描述子，显式生成一份互选对应列表，供图求解器和RANSAC共享。图模块采用基本极大团/刚性拟合/对应MAE选择；RANSAC补足不小于图模块的求解墙钟。其float64算术、确定性排序、简化图选择、无参考精化、无GICP等差异均已事先写明。

它只回答“这一套独立普通求解器输出能补足多少现有缺口，是否带来安全接受增益”，不能替代官方MAC运行、证明最强基线已穷尽，或认证独立泛化。原有模型与来源限制、全部历史失败和预算保留。

原CIM内存接口也被当前环境拒绝。PGC1改用公开Windows GetPerformanceInfo接口取得同一系统提交量/上限，在外部父进程保留12GiB余量、查询/nonce往返2秒要求；这是实际测量的替代接口。字节换算依据[微软接口定义](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information)及[微软计数映射](https://github.com/MicrosoftDocs/win32/blob/docs/desktop-src/Memory/memory-performance-information.md)。没有把可用物理内存误当成提交余量。

PGC1原36项控制通过，但第一次准备在首个NPZ解码前因标准库zipfile延迟导入被严格读取守护拒绝。原测试先写NPZ再读，掩盖了这条冷路径。该失败与回收收据完整保留；单独冻结仅导入/目录连线修复，并新增第一次NPZ操作即为受限读取的冷控制。求解核、准备、预测、评价和审计代码逐字节不变，失败1.672秒计入原准备预算，原00:35UTC总时钟和全部资源上限继续有效。没有改参数、重提特征、重新选样本或重跑成功数值阶段。

PGC1后续在第8对触发固定64个RANSAC动作仍不足图求解墙钟下界的断言，已停止；只有7对部分预测，未读取部分准确率。完整结论见 `outputs/portable_graph_20261031/REPORT_CN.md`，不能宣称更强普通对照已经完成。
