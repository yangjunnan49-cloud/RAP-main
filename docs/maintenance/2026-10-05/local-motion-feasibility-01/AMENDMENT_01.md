# LMF0 engineering runner repair

The original frozen runner passed all12 synthetic algebra/ICP cases and two
saved native00/08 raw/state replays exactly (maxdelta0). It then stopped on
the first local repeated-pipeline comparison: the shared array dictionary
also contains a Python float scale, and `.max()` was called on that float.
No local NPZ, complete bank/seal, GT output or efficacy decision was produced.
Original scripts/freeze/partial synthetic/native bank and STOPPED status stay.

Runner v2 uses np.max(np.abs(...)), supporting both scalar and array entries.
It writes a new attempt-02 directory; validator v2 only changes its directory.
The identical protocol is copied into that directory and separately frozen
with the v2 scripts and all original data/source identities before retry.
No input, seed, preprocessing, model, control, tolerance, census or resource
gate changes. This is an engineering repair, not a method/result rescue.
Any final report must disclose the original failed attempt.
