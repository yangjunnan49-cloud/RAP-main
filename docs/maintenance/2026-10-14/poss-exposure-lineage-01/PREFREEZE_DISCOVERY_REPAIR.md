# PEL0 discovery implementation repair before input freeze

Original freeze failed with FileNotFoundError('rg') in the existing WSL runtime,
before candidate discovery, source freeze or role census. Native/Windows exits
and full child resources are preserved. Original source and protocol are copied
exactly under prefreeze-attempt01. Use the mandated available-tool fallback:
recursive os.scandir with exactly the same roots/name patterns/directory exclusions,
counts and byte bounds. Independent validator still uses os.walk/fnmatch.
New freeze02 binds original source/failure/receipts and new source/protocol before
source roles. All original+new attempted stage Windows time remains<=900s,
RSS512MiB/artifacts32MiB/GPU0. No install/restart, data/metric/role/gate rescue
or original freeze-stage replay.
