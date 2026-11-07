# A8 目标环境实际修复与恢复

本页接续A4参考配方。目标项目环境为数据盘中的独立Python3.10.20/Torch2.7.0+cu128；基础镜像Python包集保留。核心/SLAM138项输入以首次PyPI解析报告的版本与SHA256固定，经镜像下载时仍使用 `--require-hashes`；不是任意升级或换包。原输入和失败日志保存在迁移目录attempts。

## GTSAM 4.2 的包装元数据

本次上游wheel的SHA256为 `979b7c886724ac403d5c323613fd9800c8ac7ab224e2909faa8b266e5de742b2`；内部WHEEL写作 `cp310-cp310-none-manylinux2014_x86_64`，与已发布文件名中的三段标签不符。pip26.2.2的check因此解析异常；26.1.2上游源码也具有相同解析路径，未以降级pip绕过。

显式维护工具repair_gtsam_metadata.py只将Tag对齐到原发布文件名 `cp310-cp310-manylinux2014_x86_64`，并重新计算RECORD。原wheel保留，派生wheel SHA256为 `29385d4c0bcf58d02990f9e8e67abe282fe021c3fc7ff44b4584107a1f10db140`。**其它119个成员以及安装后的对应文件逐字节一致**，包含原生库与Python源；Version仍为4.2。Pose3恒等小夹具通过、未导入Torch，修复后pip check返回0。没有修改GTSAM算法、阈值或优化参数，也不据此认证历史WSL环境的GTSAM字节。

完整原件、派生wheel、修复程序与JSON收据保存在服务器 `A8-environment-20261106` 环境资产目录。以后按参考配置安装原始gtsam4.2后，在同一Python中显式安装上述已校验派生wheel：

```sh
python -m pip install --no-deps --force-reinstall /root/autodl-fs/rap-transfer-20261106/A8-environment-20261106/gtsam-derived-wheel/gtsam-4.2-cp310-cp310-manylinux2014_x86_64.whl
python -m pip check
```

也可用同目录原wheel和修复程序重建，程序必须匹配原SHA，并拒绝修改WHEEL/RECORD之外的成员。依据：[PyPA wheel规范](https://packaging.python.org/en/latest/specifications/binary-distribution-format/)。不可把原件、派生件的不同哈希混记。

## PyTorch3D 与验收

使用明确上游提交33824be3cbc87a7dd1db0f6a9a9de9ac81b2d0ba的新构建，目标Torch查询架构为8.9；原历史构建提交依旧未知。构建参数、源码归档、wheel哈希及GPU/模型受测范围以实际JSON收据为准。此wheel仅针对记录的Python/Torch/CUDA/架构组合，迁到另一GPU时需要重新核对。

环境包安装与pip check通过，仍须分别查看CPU、GPU扩展、原权重严格加载和单对示例I/O收据。完整训练/精确resume仍未验收，Muon与训练入口等原缺口不会由包装修复自动闭合。
