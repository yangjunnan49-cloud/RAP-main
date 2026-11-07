# 逐文件处置表说明

主表 DISPOSITION_DRY_RUN.csv 可用表格软件阅读；ASSET_LEDGER.jsonl 保留较完整机器字段。当前均为建议，没有执行移动或删除。

| 字段 | 含义 |
| --- | --- |
| asset | 根 ID + 原相对路径，作为稳定身份 |
| category / ownership_basis | 保守归属及判定依据，目录归属不是实验有效性认证 |
| git_status | 原 Git 清单对应状态；ignored/untracked 不代表可删 |
| sha256 | 普通文件的原始字节校验 |
| reparse_metadata_sha256 | 链接的原始 reparse 元数据校验，完整表示见 LINKS_RESOLVED.json |
| protected / seal_claim_count | 保护边界或历史哈希引用；false 也不是删除授权 |
| direct_static_reference_count | 静态引用数量，不涵盖所有动态构造的路径 |
| proposed_target | 保留根内布局的暂存建议，尚未迁移或确定服务器路径 |
| rollback_location | 原件当前保留位置 |
| preservation_copy | 本轮 source-store 中已校验副本；Git 另有完整 tar 保全 |
| proposed_action / action_executed | 建议动作及是否已执行；本轮全部 false |

动作约定：retain_in_place 保留；preserve_git_history 保全 Git；preserve_link_metadata_for_staging 保存链接并在暂存恢复时按映射重建；hold_for_review 保留并核对来源；cache_removal_candidate_after_A4_recipe 是环境重建约定验证后的缓存候选，当前保留。

重复内容采用 DUPLICATE_GROUPS.jsonl 描述；不在主表选择“删除副本”。所有历史实验路径最终必须可恢复并在服务器常驻。

新旧记录的解析过程也有界限：analysis01/ 保存首次有限 schema 扫描的摘要与差异；后续增加路径键哈希、相对仓库根和已恢复历史版本的支持。HASHES.jsonl 的全量原始观察不变；没有通过重跑科学实验消除差异。
