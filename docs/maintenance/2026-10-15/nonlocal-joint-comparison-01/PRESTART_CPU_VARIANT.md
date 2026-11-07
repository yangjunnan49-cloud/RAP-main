# Exact CPU selection variant after retained prestart failure

Original geometry attempt exits at line165's device-selection assertion before
loading inputs, estimating normals, FGR/GICP or any real geometric numerical call.
The installed Open3D initializer selects cuda when a device is visible. Original
MGR0 isolated CPU source set CUDA_VISIBLE_DEVICES='' before import; NJE0 omitted
that required process-local selection. This was an implementation mistake.

Original driver/wrapper/source snapshots/freeze, initial INCOMPLETE and geometry
failure/full receipts remain immutable. No partial real geometry result exists
to replay. The protocol's prohibition on partial numerical reruns is preserved.
This independent variant changes only selection before importing Open3D, not a
matcher, count, threshold, seed, input, output route, hypothesis or stop condition.

Variant driver is byte-exact original except one insertion before its existing
Open3D import: import os; os.environ['CUDA_VISIBLE_DEVICES']=''. Variant wrapper
routes the separately named geometry-cpu02 enclosing attempt to that driver and
sets its action argument to geometry. Bindings and exact text comparisons are
checked before launch. All old and new attempts share original2400s/6GiB/8GiB/
256MiB caps. No original source edited, GPU task affected or cap reset. Geometry
outputs stay at the original exclusive empty paths. This is not native repair
or a scientific parameter rescue. No external installation/restart.
