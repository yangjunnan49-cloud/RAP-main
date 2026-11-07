# NJC0 prospective metadata-only feasibility

Freeze current source/protocol/independent validator, the six original accepted
loop lists and their binding seals, original all71 attempt metadata, full98-scan
input seal/census, source_frames/keyframes manifests, previous stops and original
repository state. Source snapshots are namespaced by relative path. No basename
flattening. Exclusive new output; retain failures and full receipts.

Parse JSON numbers as strings. Convert only i/j/frame IDs and declared array
shape/count integers. Retain only exact whitelisted ID/status/measurement keys;
never convert poses, overlaps, errors, scores or coordinates numerically. Point
cache files may be SHA256-hashed and their NPY headers parsed with literal_eval;
coordinate payloads are never decoded. No NumPy/torch/Open3D/GTSAM import.

Population: sequences00/05/06/07/09/10, original12/12/12/12/10/0accepted loops,
all71 attempt records. Exact loop i/j/measurement IDs must match the accepted
attempt rows and original seals. No endpoint substitutes or missing-data skips.

Build the undirected loop-only graph independently for each sequence. Nodes
are exact measured scan IDs; edges are the original accepted measurements.
No odometry edges, temporal neighbours, reference edges or artificial links.
Keep all components, including two-view components, and sequence10's empty
population. Record degree, nodes, measurements and complete source/cache mapping.

An eligible component needs at least3distinct IDs, at least2distinct observed
loop measurements, at least3distinct existing raw SHA256 identities and complete
already-frozen cached inputs. This is necessary only: distinct bytes do not
authenticate independent sessions, overlap or physical truth. Model input
finiteness, descriptors, solver baselines and useful joint gain remain unproved.

All original caches used by any loop endpoint must match input_seal.json and
the original raw identities. Parse only exact NPY shape(N,3),float32,C-order and
length consistency. Do not reconstruct coordinates or scores. Headers do not
prove finite input values or equal total work. Part order in any future design
would be ascending source ID; it is not fixed by this feasibility result.

Independent validation uses union-find rather than the primary breadth-first
walk, verifies maximal components/edge partition/degree sum and every complete
ID mapping/cache header/hash. Check all58/71denominators and all6sequences.
If no eligible group exists, stop this exact observation-unit construction
before model execution, without merging components or adding favourable views.
If groups exist, only a separate common-input G/P/J/W design may be proposed;
eligibility does not admit inference or accuracy claims. Algebraically derived
cycle closure remains unusable as accuracy/confidence evidence.

All attempted CPU children including freeze/imports/validation<=300s,full
processRSS<=128MiB,GPU0,new whole dossier including source/logs<=8MiB. Existing
Windows headroom guard/full exits and Linux ru_maxrss receipts apply. Ordinary
preparation RSS and observer lifetime remain UNKNOWN; no old resource-gap
repair. No network body acquired; previous1,357,466/4,194,304byte accounting is
unchanged. No external message, installation, process restart or old family retry.
