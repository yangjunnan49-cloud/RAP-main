"""Prepare separate standard-library ADR0 metadata closer only."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];old=(ROOT/'scripts/maintenance/close_native_double_tail.py').read_text(encoding='utf-8')
new=old.replace('native-double-tail-control-01','activated-adapter-derivatives-01').replace('DTC0','ADR0').replace('VALIDATED_FIXED_PREFIX_DOUBLE_TAIL_CONTROL_COMPLETE','VALIDATED_ACTIVATED_ADAPTER_DERIVATIVE_CONTROL_COMPLETE')
new=new.replace("<256*2**20","<1024*2**20").replace('256MiB prospective caps','1GiB prospective caps')
new=new.replace('Original initialized443904 trainable values/checkpoint/modes retained', 'Original checkpoint/modes/nominal443904 trainables retained; only four B matrices temporarily activated with target-independent seed2026101307/global Frobenius norm1e-3; original values restored afterwards')
new=new.replace("{d['original_FPC_D']['error']:.9g}", "{('NA' if d['original_FPC_D'] is None else format(d['original_FPC_D']['error'],'.9g'))}")
new=new.replace('}/12 predeclared', '}/18 predeclared').replace('24 temporary symmetric shadow forwards','36 temporary symmetric shadow forwards')
new=new.replace('same original vectors/three steps/signs', 'same finalMLP/B vectors plus predeclared A vector seed2026101308/three steps/signs')
new=new.replace("lines+=['',f", "lines+=['',f\"Original stored A gradients are zero; all{len(v['core']['activated_A'])} activated A matrix records have nonzero finite gradients: {all(x['A_nonzero']>0 for x in v['core']['activated_A'])}. Full independent local A/B products {sum(x['pass_bound'] for x in v['core']['local_A_B_checks'])}/{len(v['core']['local_A_B_checks'])} pass; max delta {max(x['delta'] for x in v['core']['local_A_B_checks']):.9g}. This checks complete local linear derivatives, not complete transformer backward or Jacobian rank.\",f",1)
start=new.index("(BASE/'NEXT_ROUND_PLAN.md').write_text(");end=new.index('\nsave(BASE/\'BOOKKEEPING.json\'',start)
new=new[:start]+"(BASE/'NEXT_ROUND_PLAN.md').write_text('# Next distinct prerequisite — DESIGN_ONLY\\n\\nIf activated A/B/finalMLP derivatives pass, specify and independently validate exact five-tau state/prefix casting and a target-free mixed-precision shadow sampler before any retained-update feasibility study. Original native function/failed gates remain distinct; nominal parameter count is not a full-rank active-capacity claim. No next sampler protocol/runner/freeze/prefix/full-forward/fit executed by ADR0.\\n')"+new[end:]
ast.parse(new);(ROOT/'scripts/maintenance/close_activated_adapter.py').write_text(new,encoding='utf-8',newline='\n');print('ADR0 metadata closer prepared')
