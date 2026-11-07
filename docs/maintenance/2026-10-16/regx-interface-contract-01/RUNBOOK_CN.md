# 后续首次数值启动顺序

C0当前仅完成准备和静态审查。所有stage目录/结果尚未建立，原启动失败发生在
创建stage目录之前。只有实际提交余量重新满足12GiB，且原15与补充4条绑定
仍完全匹配，才允许首次启动；不清理目录、不降低守卫、不启动替代运行时。

每次都使用invoke_regx_contract_wsl.ps1，OutputDirectory固定为本C0目录。
按以下次序逐个执行，检查完整Windows退出、Linux子退出与阶段报告后才继续：

1. Script scripts/maintenance/regx_interface_contract_execution02.py，Stage synthetic。
   要求SYNTHETIC及其封印成功，全部固定正/负控制通过。
2. 同Script，Stage build。所有源绑定及已封印synthetic再核对后，才首次解码
   实际点/参考；要求全部两记录、五视图出现、三源PLY完成，不丢弃失败case。
3. 同Script，Stage consume，并传PublicInputRoot为
   /mnt/e/githouse/RAP-main/docs/maintenance/2026-10-16/regx-interface-contract-01/inputs。
   只给合作读取器公开输入根路径，不授予参考API；这不是OS权限隔离。
4. Script scripts/maintenance/validate_regx_interface_contract_binding02.py，Stage validation。
   独立源路径身份绑定、所有点的Decimal比较、逆变换与读取清单均通过。

累计900秒包含原预启动调用2.1993678秒和以后所有外层执行/导入/失败，不重置。
阶段已有输出意味着保留并审查，不得直接重跑覆盖。真正数值/资源失败先按
协议停止，本runbook不自动授权新容差、场景、采样或实现救援。

完成后才可写本范围数值验证通过报告。即使通过，也只完成接口前提，不能
开启模型/效能、替代canonical batch、改原参考或重开旧失败家族。
