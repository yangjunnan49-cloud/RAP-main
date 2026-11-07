"""Pre-delivery wording correction for the NOC2 control-only prerequisite stop.

Keep the original frozen closure template and all scientific sources unchanged.
Only report wording and next design interpretation change; all closure checks,
resource accounts, gates and seals execute the original implementation.
"""
from pathlib import Path
import local_motion_common as c
import native_pose_fit as r


def run():
    r.check();assert not c.read(r.BASE/'bank/control/fit.json')['passed']
    original=Path(__file__).with_name('close_native_pose_fit.py');source=original.read_text()
    old='Independent Horn geometry versus evaluator SVD reconstructs every saved first/fifth-step pose, error, clean equation, rigid feedback recurrence and metric objective; aggregate code is shared on independent records, while complete pairwise gates are separately duplicated. Selected final native and cache/full forwards and initial gradients replay; full details in validation files.'
    new='Independent Horn geometry versus evaluator SVD reconstructs the final control pose errors. The36-parameter affine output is independently reconstructed from saved parameters. Mathematical target/gauge/output-directional gradients are repeated; full details in validation_control.json. Native trace reconstruction, cache/forward replay and neural gradient checks were not reached.'
    assert source.count(old)==1;source=source.replace(old,new,1)
    old='Scientific prediction banks seal before deriving their new native evaluation errors.'
    new='The failed prerequisite stops before RAP checkpoint loading, native updates/predictions or any real-window payload. Read CONTROL_OPTIMIZATION_AUDIT.md for the declared post-outcome scalar audit; no extra optimizer/forward calls.'
    assert source.count(old)==1;source=source.replace(old,new,1)
    old='The affine fixed-budget control failed its prerequisite. Stop dependent native/real fits. Next design only: inspect the declared objective/control optimization evidence; analytic representability does not prove fixed-step convergence. No rates/steps/control reinitialization rescue in NOC2, and no native learnability conclusion.'
    new='The affine fixed-budget control failed its prerequisite with20.442/19.929mm translation error, while rotation passes and analytic representation/target/gauge/directional-gradient checks reproduce. Last100 pre-update losses oscillate and every gradient is clipped; fixed-budget convergence is unestablished, not a unique diagnosed cause. Stop dependent native/real fits. Next DESIGN_ONLY: assess control conditioning using proper metric translation/radian rigid relative-pose parameters with fixed anchor gauge and independent gradient checks, with a new prospective optimizer/stopping/resource scope. No rates/steps/control reinitialization rescue in NOC2, no newly implemented/frozen control and no native learnability conclusion.'
    assert source.count(old)==1;source=source.replace(old,new,1)
    snap=r.BASE/'delivery_source_snapshot';snap.mkdir();(snap/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    c.save(r.BASE/'DELIVERY_WORDING_SCOPE.json',dict(purpose='Control-only accurate report wording and next design interpretation before delivery',
        original_frozen_closure_preserved=True,scientific_source_or_gate_changes=False,optimizer_updates=0,
        files={str(p):c.sha(p) for p in (Path(__file__),original,r.BASE/'freeze.json',r.BASE/'CONTROL_OPTIMIZATION_AUDIT.md')},
        closure_template_executed_sha256=__import__('hashlib').sha256(source.encode()).hexdigest()))
    namespace={'__name__':'noc2_delivery_wording','__file__':str(original)}
    exec(compile(source,str(original),'exec'),namespace);namespace['run']()


if __name__=='__main__': run()
