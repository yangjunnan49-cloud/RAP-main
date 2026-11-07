# Guard05: bounded challenge response, no protection relaxation

run04 completed five cells and stopped before G06 launch because Windows UTC observation was 0.045564 seconds ahead of Linux UTC. The original implementation already reads the file before sampling Linux UTC; an ordinary Python read-order fix would be incorrect. Cross-host clock discrepancy is observed; its OS cause is UNKNOWN.

Preserve failed run04 source/receipts and all five complete cells byte-for-byte; no metric read, no replay or best-run selection. New run05 continues the original remaining31 cells under the same7200s shared account, including the773.4728936s failed enclosing run04. New output routes do not overwrite old files. Algorithm/config/prepared byte/source-E0 gates unchanged.

Linux issues a unique nonce, then Windows reads that nonce BEFORE a new CIM memory measurement and publishes the response. Linux accepts matching nonce only when its local monotonic request-to-consume interval is <=2s and the measured headroom is >=12GiB. Thus actual measurement-to-consume time is bounded by the original2s even with different UTC clocks. No absolute clock-offset epsilon, negative-age clamp, cached response acceptance, relaxed freshness/headroom or process control. A missing/late response fails the guard.
