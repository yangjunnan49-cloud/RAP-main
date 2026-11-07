# 分卷与恢复合同

本次选择原件保留、文件级 SHA256 去重、标准库 USTAR 原字节分卷。单卷至多 4GiB，payload 内成员名只含 objects/加 64 位 SHA256；重复文件的每个原路径都留在清单，恢复时按原路径身份分别写出，不把不同实验副本当作同一次实验。

## 包目录与校验

本机包位于 RAP-main/.maintenance-archive/migration/A5-20261104，使用已有 ignored 目录，没有改 .gitignore、Git 索引/历史或原数据布局。PACKAGE.json 关联所有卷的字节数/SHA256、控制清单、对象清单和逐物理文件的新字节核对收据。OBJECTS.jsonl 关联内容哈希与所在卷；SOURCE_FILES.jsonl 保留 root_id、相对路径、文件大小、原时间/属性及 hash 来源；后续 SOURCE_BYTE_CHECKS.jsonl 确认每个物理文件按字节再核对。

每个逻辑包都有成员清单与清单 SHA256，并通过对象表关联必需卷。各包共享去重对象，没有为不同数据集重复保存同一内容；传输时须包含索引声明的全部必需卷。所有卷独立完整读回，核对卷哈希、每个成员内容哈希和唯一对象覆盖后才标记验证通过。

包构建拒绝覆盖已有包目录；故障时保留 BUILD_FAILURE.json 和 .partial，不能把部分卷冒充完成。恢复只写新目录，拒绝路径穿越、原目录覆盖和意外 tar 成员。没有调用 tar.extractall，不从归档成员名决定最终源路径。

## 恢复入口

以[内容包工具](../../scripts/migration/content_bundle.py)为入口：

```sh
python /path/to/RAP-main/scripts/migration/content_bundle.py verify --package /path/to/A5-20261104

# 只恢复指定根/前缀的普通文件；输出必须是新目录。
python /path/to/RAP-main/scripts/migration/content_bundle.py restore-files \
  --package /path/to/A5-20261104 --destination /new/restore \
  --root datasets --prefix data_odometry_velodyne/dataset/sequences/00/
```

普通文件恢复位置为 destination/root_id/原相对路径，保留两个代码仓库和外部档案根身份。A5工具只承诺普通文件字节；[A7交付工具](../migration/RESTORE.md)已将基础和增量完整恢复并逐文件复核，25内部相对链接另验。真实Linux权限/所有者、环境和服务器验收仍未完成。

## 链接与范围

27 个 reparse buffer 已不跟随目标地重新读取，与 A1 原字节匹配。25 个 LX 链接的原目标及建议相对目标保留；两个 node_modules junction 的原外部目标只登记，不把个人运行时依赖递归打入基础包。A7已在新恢复树通过一次WSL文件系统维护恢复/验证25个相对内部链接并恢复Stopped；2个人junction不创建。A5普通文件脚本不创建链接，A7显式链接选项也不下载依赖。

基础快照是生成 SOURCE_FILES 时的六根资产视图，不包含 A5 phase 和 A5 包目录，也不包含 WSL 镜像内未导出的环境及那份仅在 WSL 中登记的 Torch wheel。A4 已导出的环境文件属于本次快照资产；这不等于整套 Linux 环境已打包。A5 后改写的当前文档有 before/接续证明，由 A7 最终增量承接，旧快照字节仍保存在内容包。最终项目增量及A7封存控制层见[交付入口](../migration/DELIVERY.md)。

包仍在同一块本地 E 盘，提供可校验交付基础，不提供异地副本或服务器驻留证明。没有清除原件、重新生成实验、修复旧科学验证器或读取 PGC1 部分准确率。
