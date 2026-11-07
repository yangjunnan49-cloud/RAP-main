# WSL迁移完成记录（2026-10-22）

用户明确批准后，Ubuntu-24.04已从C盘迁移到E盘。当前状态为CLOSED_COMPLETE_WITH_COMPATIBILITY_JUNCTION；验收后已恢复迁移前的Stopped状态，可以重新正常打开WSL。

- 新虚拟磁盘：E:/WSL/Ubuntu-24.04/ext4.vhdx。
- 完整备份：E:/WSL-Backup/Ubuntu-24.04-before-move-20261022.vhdx，约41.8GiB，继续保留，不自动删除。
- C盘当前空闲约55.72GiB，相对迁移前增加约41.98GiB；受后台应用活动影响，实时数值会略有变化。
- 从本次开始记录至文档收尾约15.14分钟，包括准备、失败诊断、备份、完整哈希、迁移和环境验收；详细原生命令时间见各收据。

官方export VHD备份与原磁盘的字节数和完整SHA256一致；官方manage --move已完成文件移动，但在最后阶段返回权限错误，未更新注册路径。在首次启动前完整校验E盘镜像与原盘的字节数和SHA256一致，随后仅修正该发行版BasePath，其他注册值及类型保持。原C盘镜像由官方迁移处理，未手工删除或注销发行版。

4个Python环境的解释器路径、版本、包版本及所选项目/配置文件哈希前后完全一致；发行版名称、WSL2类型、默认UID/用户/home目录保持。原生KISS/Open3D/MapClosures扩展可导入；rap-inference环境中的PyTorch、PyTorch3D编译扩展、GTSAM、Open3D、Hydra、Lightning可导入，PyTorch可识别RTX5070，WSL nvidia-smi型号/驱动/显存信息前后一致。这里只验证导入和设备可见性，未加载模型、执行求解器、训练、配准或重跑实验；不构成新性能/精度结果。

路径兼容处理已保留并明确记录：虽然BasePath注册值已指向E盘，正常服务重启及管理员上下文停服务写入后，WSL仍尝试旧C盘挂载路径，精确原因未确定。保留原目录仅有的shortcut.ico后，将旧C盘发行版目录设为指向E:/WSL/Ubuntu-24.04的NTFS目录联接（Junction），随后启动及全部环境验收通过。链接本身不存储42GiB镜像，实际镜像只有E盘活跃副本及E盘离线备份。旧路径能看到文件是链接解析结果，不能通过旧路径清空其内容。以后正常重启Windows后，如已验证不再依赖旧引用，才考虑单独移除链接；本次不自动移除。

失败原样保留：01_backup.ps1错误枚举PowerShell属性集合Count，误报环境缺失；实际4个环境查询已成功，后续复用该成功快照。第一次export因Stopped发行版的VHD仍被WSL虚拟机持有而报ERROR_SHARING_VIOLATION；确认只有该发行版后正常shutdown，第二次export成功。官方move移动镜像后报MoveDistro/E_ACCESSDENIED，原C盘文件已不存在但注册项仍指旧路径；目标镜像完整哈希确认后，导出该发行版注册键，仅修正BasePath，逐项确认其他注册值和类型不变。REGISTRATION_REPAIR.json及原始official_move.json保留完整证据，没有通过重试移动、修改文件ACL、注销发行版或重装绕过。没有强制结束其他应用或放宽科学判据。

Windows的.wslconfig、D盘分页文件、休眠设置、SolidWorks配置和工程文件保持不变；没有额外清理、Git/生产默认/外联/调度操作。曾通过UAC管理员脚本正常刷新WslService，服务启动方式保持Auto，未强制结束进程或重启Windows。启动失败及全部服务尝试的收据保留，不能把修正注册路径本身写成已独立解决问题。最终启动通过依赖上述兼容链接。原研究状态仍未解决，所有旧失败/预算/封存继续有效，不自动恢复额度耗尽任务。

迁移收据：PRECHECK.json、BACKUP_CHECKS.json、MOVED_IMAGE_CHECKS.json、REGISTRATION_REPAIR.json、COMPATIBILITY_JUNCTION.json、COMPATIBILITY_BOOT_CHECK.json、VALIDATION_CHECKS.json、FINAL_STATUS.json及所有步骤输出。保留备份至数次日常使用确认稳定后，再由用户决定删除；备份不是活跃发行版，不能直接用文件管理器替换正在运行的镜像。