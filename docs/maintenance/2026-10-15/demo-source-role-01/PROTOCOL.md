# DSR0 Prospective Source-Role Audit

Freeze complete regular-file names, lengths and chunked SHA256 under the exact
demo_example_data root, all audited source/config/protocol and PRI0 delivery seal.
The observed namespace contains27 directories/156 files,151PLY+5PCD; these are
preparation observations, not success predicates or an efficacy sample selection.
Reconstruct rather than hard-code the complete population and scene counts.

Read each PLY only through end_header, each PCD only through DATA, at most64KiB
per header. Preserve raw header text and header byte length/hash; parse format,
declared counts/schema only. Never decode coordinate payload or infer common
world frame from view count, scene name, PCD VIEWPOINT or visual plausibility.
Whole-file chunked hashes read bytes without numeric decoding. Check complete
namespace before and after; inventory absence claims are root-local only.

Static source contract: demo enumerates direct lowercase .ply only, creates its
own val split, calls save_processed_sample with3 positional arguments and no
input_sample_dir, then runs trainer.test. Optional --eval_on only wraps printing.
The default test datamodule uses split='val'. Folder loader assigns sampled input
pcs to pointclouds_gt. _transform references that array, centers/scales it,
uses identity rotations outside training and derives translation references
from supplied coordinates; evaluator consumes those dataset references.
Save code excerpts with exact source identities and verified AST line ranges.
Do not claim no other loader/path supports poses, or that local demo clouds are
wrong/unregistered. Check only this default source path.

An independent validator reconstructs file/scene/extension populations with
os.walk, uses its own64KiB hash loop and own header terminator parser, checks
the source citation slices/AST contracts and unchanged repository state.

Decision is role feasibility, not scene selection: external measured reference
and per-scene author/RegX byte linkage remain unauthenticated unless present in
the frozen namespace/evidence. No checkpoint training exclusion is inferred
from PRI0 byte identity. Existing demos may support honestly labeled qualitative
engineering, but default self-reference metrics are not external-truth accuracy.
No cohort, benchmark run, head, derivative pilot, crop/noise rescue or pipeline
integration automatically follows. Deliver a concrete next-mechanism/control
design and precise minimal evidence request, preserving all old stops.
