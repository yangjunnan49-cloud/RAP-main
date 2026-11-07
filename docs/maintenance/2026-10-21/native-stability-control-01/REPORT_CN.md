# N1 关闭：前端完成，原生对照因记录容量不足而不完整

新生成的 G06 前端 1,101 帧已完成并封存，逐帧原始/准备输入检查通过。第一个原生串行对照在帧833停止，第二个未启动。没有完整的两次原生结果，不能据此判断重复稳定性、精度、速度或 RAP 效益。

故障发生在 detector._GetBestClosure 的输入采集前。最后一个完整点云返回包含841,107行、3列float32，共10,093,284bytes；原包装层按原算法转换为float64后需20,186,568bytes，超过本轮预设16,777,216bytes单数组记录上限。记录器在调用该次检测之前拒绝继续；原阈值未放宽，native2未启动，native1未重跑。PARTIAL_AUDIT.json核对完整事件链及已记录packet前缀；这只是部分证据，不替代完整比较。

独立worker峰值RSS716,955,648bytes，watcher观测worker峰值651,153,408bytes；两者采样口径不同，均未触及4GiB界限。1800s总范围与8MiB工作/输出界限未因失败重置，关闭成本和源/进程清理见COSTS_FINAL.json。没有读取GT、调用fine graph或RAP模型；真实raw与前端/native调用确已发生，不能沿用旧合成收据的零数据标签。

原始故障与修复记录保留：prepare_guard.ps1的只读$Host变量冲突发生在任何preflight/raw之前；prepare_guard02仅机械改名。front的守护收据继承了合成版计数字段，其这三个字段无效，原文保留，RECEIPT_CLASSIFICATION_CORRECTION.json单独纠正；后续守护版本02仅更改标签/文件身份路由，数值代码未变，front不重跑。16项前置控制、原freeze及SOURCE_FREEZE02、PREFLIGHT、ADMISSION和新runtime绑定均保留。

下一项仅做合成工程验证：在保持完整字节哈希、dtype/shape/endian/strides的同时，以固定大小块读取大数组，测量临时内存；不得将N1改标成功或把16MiB失败悄悄放宽。真实再比较需要新方法先验证、重新完整定义准入与成本，并显式保留本次不完整结论。P0 queue4关闭失败、历史预算失败、S1保护失败和原研究目标未解决的状态保持。
