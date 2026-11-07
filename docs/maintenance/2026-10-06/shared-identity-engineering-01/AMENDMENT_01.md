# D1 validator-only correction after sealed bank

The original D1 bank completed all four frozen pairs and sealed96 NPZ files
before independent validation. Source/descriptor/noise validation passed.
The original numerical validator then stopped on its first pair at an
incorrect `len(again)==len(arr)` assertion: the primary arm NPZ includes
root-only elapsed-time metadata `wall_seconds`, whereas its repeat/dummy
NPZs intentionally omit that metadata. The validator had already compared
every scientific raw/clean/state/noise/pose array in that iteration; the
field-count assertion was not a scientific identity check.

The original source, freeze, bank, seal, failed validation attempt and
INCOMPLETE marker remain. A separate validator source is frozen in
`attempt-02/freeze.json`. The only scientific comparison correction is to
require the repeat/dummy key set to equal the primary key set excluding
`wall_seconds`. Additional code binds this v2 source to its own freeze,
references the original validator source in the original freeze, and writes
the result under attempt-02. Samples, controls, solver, thresholds, outputs,
checkpoint, source identities and response gates do not change. The saved
bank is revalidated in place; no model is rerun.

This is a disclosed correctness repair, not a response- or accuracy-driven
choice. A v2 failure leaves the original sealed bank and original failure
intact and requires another separately frozen correction or a stop.
