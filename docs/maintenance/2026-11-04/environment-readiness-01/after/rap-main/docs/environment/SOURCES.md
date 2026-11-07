# 环境说明的来源

查阅：2026-11-04，Asia/Shanghai。本机版本和二进制哈希以[实际采集](OBSERVED.md)为准；下列公开文档只支持安装/API 说明，不认证本地构建或目标运行结果。

| 来源 | 本页采用的依据 |
| --- | --- |
| [PyTorch 历史安装页](https://pytorch.org/get-started/previous-versions/) | 2.7.0 配套 torchvision 0.22.0、torchaudio 2.7.0 与 cu128 索引 |
| [PyTorch3D INSTALL](https://github.com/facebookresearch/pytorch3d/blob/main/INSTALL.md) | 原生扩展需考虑 Torch、CUDA、编译器；其版本表不认证本地 2.7.0/0.7.9 构建 |
| [PyG 安装文档](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html) | 额外扩展需匹配 Torch/CUDA；旧版本 wheel 与避免意外源码构建的说明 |
| [Lightning 2.5.2 checkpoint 文档](https://github.com/Lightning-AI/pytorch-lightning/blob/2.5.2/docs/source-pytorch/common/checkpointing_basic.rst) | Trainer.fit 的 ckpt_path 恢复方式及 optimizer/scheduler/step 等状态区别 |
| [Lightning 2.5.2 fit loop](https://github.com/Lightning-AI/pytorch-lightning/blob/2.5.2/src/lightning/pytorch/loops/fit_loop.py) | sampler epoch 更新和 Module/Callback hook；不推断自定义 DataModule hook 已被执行 |
| [Muon 原仓库](https://github.com/KellerJordan/Muon) | 本地优化器导入所指上游；没有认定某个当前 HEAD 为历史原版本 |

未抓取或安装软件包。pytorch3d.org 安装页不可访问、Lightning /2.5.2/ 网页路径返回 404 后，使用上游仓库文档；没有将搜索摘要替代本地安装证明。官方 wheel 索引的文本查询没有提供可用的目标 SHA 匹配证据，因此本地 Torch wheel 哈希只声明与本地 direct_url 一致，远程来源认证仍保留。
