# C0 frozen custom interface protocol

Decision dependency: B2 demonstrates that fixed README and viewer disagree about
matrix direction. Before using the package, verify a precise implementation of
X_i=T_i W_i and Q_i=inverse(T_i), relative-pose left-gauge invariance, and the
separation between constructor/reference data and a cooperating input reader.
Downloaded viewer is cited data, never imported or executed. All implementation
is new stdlib-only maintenance code. This is not an official batch replica.

Stages, in order, with exclusive outputs and retained initial marker/failures:

1. Exact Fraction fixtures with three rational proper rigid transforms and four
   asymmetric points. Check inverse/round trip, equivalent row/column forms,
   relative poses under a common LEFT gauge and view permutation. Fixed negatives:
   wrong inverse direction, wrong row convention, RIGHT gauge and reference/view
   order mismatch must fail the expected identities. Schema/path/unknown-key
   reference leakage negatives must be rejected. Freeze success before real data.
2. Verify frozen B1/B2 identities. Select ALL exact-scene JSONL records, not by
   geometry/overlap/error: original lines913/914, pair and triple. Decode only
   these five4x4 matrices and three existing XYZ-only binary PLYs. Decimal50
   rigidity checks: homogeneous bottom row exact; finite; max orthogonality and
   determinant-minus-one<=1e-10. Generic Decimal Gauss-Jordan inverse residual
   <=1e-40. Fail closed, no tolerant variant or alternate scene on a failed gate.
   No graph-value decoding or registration/pose metric.
3. Construct every input point using binary64 affine multiplication, no sampling,
   centering, scaling, normals or coordinate fitting. Serialize full XYZ as
   little-endian doubles. Public inputs contain only anonymous view IDs/order,
   point count, format, relative file names and SHA256. No source-world paths,
   transforms, graph, JSONL or reference keys. Private constructor/reference file
   stores source bindings, original decimal T and derived Q. Seal all public
   input bytes before running the reader/independent reference validation.
4. A separate cooperating reader invocation receives only the public input root,
   checks strict schema/path/size/hash/finite values and logs every requested
   public file. It is NOT a model or adversarial OS sandbox; common workspace
   privileges are unchanged. No universal no-side-channel/least-privilege claim.
5. Independent validator does not import builder math. Reparse frozen source,
   verify every input point using Decimal50 scalar equations and serialized
   binary64 values, all views/points, and inverse round trips. Forward error bound
   per coordinate:128*2^-52*(1+sum(abs(T_ij*W_j))+abs(T_i3)). Round-trip bound:
   propagated forward bounds plus256*2^-52*(1+abs(W_j)). These are conservative
   floating representation budgets, not physical/pose-accuracy thresholds.
   Validate public seal, reader access list, private references and exact source
   identities. No subset selection, resampling or partial favorable completion.

Resources across all stages/attempts/imports:900s enclosing Windows execution,
512MiB per Linux child maxRSS,16MiB complete new dossier,GPU0. CPU thread env1;
Windows12GiB initial commit-headroom guard. Actual Windows receipts include
startup/imports; Linux clock starts after stdlib imports. Reconcile each rather
than add overlapping intervals. Native WSL/observer/process-tree full peaks and
ordinary preparation RSS UNKNOWN. No old cap/gap repair. Existing small writer
performs pre-write census for known controlled outputs and final whole-directory
check; no arbitrary-writer/concurrent filesystem/durability guarantee.

No new source request or efficacy scope follows automatically. On completion,
decide whether the contract prerequisite is met and what still blocks a concrete
mechanism/strong geometry/direct/common-input/capacity/total-work experiment.
