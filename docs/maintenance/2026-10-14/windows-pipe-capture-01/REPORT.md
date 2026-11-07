# WPC0 Windows Byte Controls And Resource Stop

Decision: AUDITED_WINDOWS_PIPE_BYTE_CONTROLS_PASS_NATIVE_PEAK_COMPLETENESS_STOP. Byte/native-exit validation passes, but the complete native working-set gate is NOT established. Keep WPC0 INCOMPLETE.

All8 fixed Windows children have native exit codes, pipe EOF and binary journal/terminal files within3072 cooperating bytes. Normal/empty/binary cases are byte-admitted; three overflows/exit7/timeout are not. Original validation.json records these local assertions; it is not a certificate of complete native resource capture or successful whole-scope admission.

Source review found two empty catch blocks around native memory/CPU queries. The loop uses Process.Refresh(), but post-exit peak access is not independently shown fresh; query failures and final-observation coverage were not logged. Process-group property caching is documented by Microsoft; without explicit final-query evidence the maximum observed PeakWorkingSet64 is not admitted as the full-lifetime peak. No specific number of actual query failures, unique cause, or real cap overrun is inferred. This is a completeness stop, not a measured cap exceedance.

Native controller observed peak126459904bytes; the individual observed peaks are retained in native_controller.json. These observed values remain descriptive, not proof of the original256MiB full-lifetime caps. The original frozen source, scope, validator, all8 outcomes and receipts remain unchanged; no threshold downgrade or rerun makes the original resource gate pass.

All23 frozen identities match. Three successful enclosing commands take Windows16.541476300s incl startup/imports, Linux-child11.532625935s after bootstrap. Linux-driver RSS18731008bytes/GPU0; time/Linux-RSS/new-dossier caps pass. Full outer native/Windows exits/host samples,0 outer logging retries/0 outer gaps. Native statistics query gap count/completeness UNKNOWN; it must not be merged into an all-native zero-gap claim. Nested Windows controller and8 child intervals are not added again to the enclosing duration. Ordinary setup RSS unknown/stdlib stop audit separate/old gaps unchanged.

Next separate DESIGN_ONLY question: can an explicitly retained native process handle and direct OS memory query return valid final peak statistics after exit, with every return/error recorded? No conclusion or retry is authorized by this report alone. No Windows supervisor/real-model/archive/fit integration, old LCP0/HFIT0 repair, physical/system gain or acquisition/install/reference/default/backbone/manuscript/restart/commit/Git sync.
