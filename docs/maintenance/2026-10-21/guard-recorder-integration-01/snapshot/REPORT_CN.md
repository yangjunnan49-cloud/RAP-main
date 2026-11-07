# 独立监控进程与边界记录器：集成合成检查完成

九项控制全部通过，没有修复后重跑或挑选成功样本。冻结的十个工作文件在执行后全部保持原哈希，旧 boundary_contract.py 精确复制且算法未改。八个实际启动的 worker 各完成 15 项 stub 断言，共 120 项；source-binding 故障在 worker 启动前拒绝。

| 控制 | 结果 |
|---|---|
| 正常完成 | 记录器保持参数和返回对象身份、点字节、调用次数、事件顺序、原异常对象及自然 callee mutation；预采集错误阻止调用 |
| 宿主先到期 | 精确停止 watcher，watcher 验证并清理 worker 组 |
| Linux 先到期 | 依据 Linux 本地与宿主 stage elapsed 最大值停止 |
| 宿主失联且工作调用阻塞 | 独立 watcher 在最后有效租约后 2.112962903 秒停止 worker 和同组 grandchild；两个退出收据齐全 |
| nonce 错误 | 首个错误回复被拒绝，停止 worker |
| 注入 headroom 不足 | 仅伪造已标注的回复字段，真实 12 GiB 启动门槛未降低 |
| RSS 故障 | 64 MiB 合成分配使观测 worker RSS 达 84,234,240 bytes，触发本控制专用 32 MiB 故障阈值 |
| 身份伪造 | start tick=-1 的停止请求被拒绝，watcher 继续存活；正确身份随后完成清理 |
| 源绑定错误 | worker.py 预期哈希被故意替换为错误值，worker 未启动 |

Linux watcher 与工作进程分离，因此阻塞 stub 不会占住租约/时限检查循环。工作组由 PID/PGID/start ticks/脚本路径和哈希绑定；宿主和 Linux 都执行全范围时间界限，原 12 GiB、两秒内新鲜 nonce 规则保留。各 case 的 stage 时限为故障注入，全部准备和测试仍共用本轮 900 秒范围，关闭成本见 COSTS_FINAL.json。

全部计算仅用标准库、合成字节和 stub，没有真实 raw、GT、native 数值库、模型、求解器或新预测。常规 worker 观测 RSS 约 17 MiB，watcher 峰值不超过 16,789,504 bytes；上述 84 MiB 是有意的分配故障。观测 RSS 及已知子进程清理不等于操作系统隔离或所有瞬时峰值证明。

记录器尚未接入真实 native 工作负载，不能据此宣称真实 Open3D/MapClosures/PGO 的非干预性、隐藏状态完整性或开销。健康采集路径下的异常身份保持已测试；若异常本身无法记录，仍须停止并保留双重错误，不能承诺这种路径也透明。P0 等价失败和历史预算失败均保留，没有新增 RAP 效益。
