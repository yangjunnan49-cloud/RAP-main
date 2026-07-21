import torch

# Test model instantiation with dummy data using actual config params
from rectified_point_flow.flow_model.point_cloud_dit import PointCloudDiT

print("Creating PointCloudDiT model (rap_12 config)...")
model = PointCloudDiT(
    in_dim=0,
    out_dim=3,
    embed_dim=512,
    num_layers=2,  # use 2 for speed, real model uses 12
    num_heads=8,
    dropout_rate=0.0,
    max_points_per_part=500,
    max_points_per_batch=40000,
    local_feat_dim=32,
).cuda()

print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

# Create dummy input
B = 1
tp = 1000  # total points
x = torch.randn(tp, 3).cuda()
cond_coord = torch.randn(tp, 3).cuda()
timesteps = torch.randn(B).cuda()
scales = torch.ones(B).cuda()
anchor_indices = torch.zeros(tp, dtype=torch.bool).cuda()
cu_seqlens_batch = torch.tensor([0, tp], dtype=torch.int32).cuda()
cu_seqlens_part = torch.tensor([0, tp//2, tp], dtype=torch.int32).cuda()
local_features = torch.randn(tp, 32).cuda()
latent_features = None

print("Running forward pass...")
with torch.no_grad():
    output = model(x, timesteps, cond_coord, local_features, latent_features, scales, anchor_indices, cu_seqlens_batch, cu_seqlens_part)

print(f"Output shape: {output.shape}")
print("Forward pass successful!")

# Test attention specifically
from rectified_point_flow.flow_model.layer import _flash_attn_varlen
qkv = torch.randn(100, 3, 8, 64).cuda()
cu_seqlens = torch.tensor([0, 50, 100], dtype=torch.int32).cuda()
out = _flash_attn_varlen(qkv, cu_seqlens, max_seqlen=100)
print(f"FlashAttention replacement output shape: {out.shape}")
print("All tests passed!")
