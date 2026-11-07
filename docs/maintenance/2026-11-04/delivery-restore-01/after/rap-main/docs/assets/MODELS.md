# 模型/权重资产

本次仅原字节 SHA256、大小、文件名和物理别名登记，没有 torch.load/pickle/模型实例。完整清单见 [MODELS.json](../maintenance/2026-11-04/assets-package-01/MODELS.json)。

| 当前文件 | 字节 | SHA256 |
| --- | ---: | --- |
| weights/rap_model_12.ckpt | 355,667,736 | `0c5b9f20ee4dfe2345c3cd47dd0632a3d807a3da69c7653900a755cd06564200` |
| weights/rap_model_10.ckpt | 327,055,496 | `432ab2f4f9c0e22d2420e0de994b9179334001e954ebcae9ff05d41503c2ee7a` |
| weights/mini_spinnet_t.pth | 3,671,729 | `daf910b6e2a79c4346a6ef8eeb18b56ffc15b552cc82af091b8b6c0a18116eef` |

三份唯一权重均另有旧维护快照物理副本，六个原路径全部保留，内容包只为相同字节存一个对象。别名关系不等于额外训练或独立模型证据。weights/.cache 的本地元数据也保留，但未找到可以认证这三份物理权重原下载来源/发行版的完整链，source_url 保持未知。

当前 RAPBackend 显式默认 rap_model_12.ckpt；sample/demo 的原默认 rap_model.ckpt 本地缺失，A3 示例配置显式选择 12，未静默改权重。文件名中的 10/12 与现有配置只是选择线索；本次没有认证参数内容与架构匹配。

checkpoint 是否含 optimizer/scheduler/scaler/step、RNG 或 sampler 状态仍未检查/验收；不能以文件名 .ckpt 或字节保全证明完整续训。Muon、专用训练入口和目标 GPU/干净环境保留项见[训练审计](../environment/TRAINING.md)。

物理分卷、校验与普通文件恢复见[分包说明](PACKAGING.md)。
