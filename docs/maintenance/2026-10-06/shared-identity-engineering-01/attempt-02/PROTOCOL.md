# D1 independent-validator attempt-02

Original bank: the complete, unchanged96-NPZ GT-free D1 bank and bank seal.
Original freeze, protocol, original validator and its failed first attempt
remain preserved. See `../AMENDMENT_01.md` and `../FAILURE_01.json`.

Only replace the metadata key-set assertion with
`set(repeat)==set(primary)-{"wall_seconds"}`. Retain all numerical identity,
Horn, source/noise, old replay, repeat/dummy array, state recurrence, response,
resource and four-pair gates exactly. Bind this validator, original freeze,
bank seal and source-validation seal before running it. Save its result only
in this attempt directory. No new model inference, source reconstruction,
parameter adjustment, data selection or evaluator GT read.
