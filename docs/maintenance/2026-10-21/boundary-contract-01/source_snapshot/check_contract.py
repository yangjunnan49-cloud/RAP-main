"""Strong synthetic integrity controls, with no numerical runtime or data imports."""
import copy
import json
from pathlib import Path
import resource
import struct
from boundary_contract import artifact, compare, stream, verify

OUT = Path(__file__).resolve().parents[2] / 'outputs/boundary_contract_20261021'
binding = dict(source_sha256='a' * 64, runtime='synthetic-stdlib', config_sha256='b' * 64)
points = struct.pack('<6f', 1, 2, 3, 4, 5, 6)
pose = struct.pack('<2d', 0, 1)
events = [dict(id='frame:0', boundary='map.integrate', state_coverage='unobserved', components={
    'points': artifact(points, 'f4', [2, 3], 'little', 'prepared_input'),
    'pose': artifact(pose, 'f8', [2], 'little', 'derived_input'),
    'output': artifact(b'\x00', 'u1', [1], 'na', 'output')})]
baseline = stream(binding, events)
checks = []


def expect(name, actual, expected):
    assert actual == expected, (name, actual, expected)
    checks.append(dict(name=name, passed=True, result=actual))


def rejected(name, action):
    try:
        action()
    except (ValueError, TypeError):
        checks.append(dict(name=name, passed=True, result='rejected'))
    else:
        raise AssertionError(name)


expect('equal_recorded_bytes_keep_native_state_unknown', compare(baseline, copy.deepcopy(baseline))['status'],
       'recorded_bytes_equal_native_state_unknown')
changed = copy.deepcopy(events)
changed[0]['components']['pose'] = artifact(struct.pack('<2d', 1e-14, 1), 'f8', [2], 'little', 'derived_input')
expect('tiny_derived_pose_not_mislabelled_as_point_change', compare(baseline, stream(binding, changed))['status'], 'derived_input_difference')
changed = copy.deepcopy(events)
changed[0]['components']['points'] = artifact(struct.pack('<6f', 4, 5, 6, 1, 2, 3), 'f4', [2, 3], 'little', 'prepared_input')
expect('row_order_change_detected', compare(baseline, stream(binding, changed))['status'], 'prepared_input_difference')
changed = copy.deepcopy(events)
changed[0]['components']['output'] = artifact(b'\x01', 'u1', [1], 'na', 'output')
expect('same_recorded_inputs_different_output_no_causal_claim', compare(baseline, stream(binding, changed))['status'], 'output_difference_cause_unknown')
changed = copy.deepcopy(events)
changed[0]['components']['points']['shape'] = [3, 2]
expect('shape_metadata_bound_even_when_bytes_match', compare(baseline, stream(binding, changed))['status'], 'prepared_input_difference')
changed = copy.deepcopy(events)
changed[0]['components']['points']['byteorder'] = 'big'
expect('byteorder_metadata_bound', compare(baseline, stream(binding, changed))['status'], 'prepared_input_difference')
expect('different_runtime_binding_incomparable', compare(baseline, stream(dict(binding, runtime='other'), events))['status'], 'incomparable_bindings')
second = copy.deepcopy(events[0]); second['id'] = 'frame:1'
pair = stream(binding, events + [second])
expect('count_difference_detected', compare(baseline, pair)['status'], 'event_count_difference')
expect('order_difference_detected', compare(pair, stream(binding, [second] + events))['status'], 'event_metadata_difference')
tampered = copy.deepcopy(pair); tampered['events'].reverse()
rejected('tampered_order_rejected', lambda: verify(tampered))
tampered = copy.deepcopy(pair); tampered['events'][1]['event']['components']['pose']['sha256'] = '0' * 64
rejected('tampered_component_rejected', lambda: verify(tampered))
rejected('duplicate_event_id_rejected', lambda: stream(binding, events + events))
rejected('shape_length_mismatch_rejected', lambda: artifact(points, 'f4', [3, 3], 'little', 'prepared_input'))
rejected('oversize_artifact_rejected', lambda: artifact(b'', 'f8', [100000], 'little', 'prepared_input'))
rejected('unsupported_complete_native_state_claim_rejected', lambda: stream(binding, [dict(events[0], state_coverage='complete')]))
rejected('strided_memoryview_rejected', lambda: artifact(memoryview(points)[::2], 'u1', [12], 'na', 'prepared_input'))
bad = copy.deepcopy(events); bad[0]['components']['points']['nbytes'] = 1
rejected('malformed_descriptor_length_rejected', lambda: stream(binding, bad))
bad = copy.deepcopy(events); bad[0]['components']['points']['sha256'] = 'not-a-sha'
rejected('malformed_descriptor_hash_rejected', lambda: stream(binding, bad))
changed = copy.deepcopy(events + [second]); changed[1]['components']['pose'] = artifact(struct.pack('<2d', 2, 1), 'f8', [2], 'little', 'derived_input')
expect('first_divergence_index_is_second_event', compare(pair, stream(binding, changed))['first_index'], 1)
mutable = bytearray(points)
snapshot = artifact(mutable, 'f4', [2, 3], 'little', 'prepared_input')
mutable[0] ^= 1
expect('mutable_source_snapshot_is_immutable', snapshot, events[0]['components']['points'])
frozen = stream(binding, events)
events[0]['components']['pose']['sha256'] = 'f' * 64
expect('stream_freezes_caller_metadata', frozen, baseline)
result = dict(status='PASS', controls=checks, count=len(checks),
              max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
              raw_reads=0, GT_reads=0, native_imports=0, new_predictions=0,
              limitation='Synthetic descriptors only; native integration and full-state observability untested')
(OUT / 'RESULTS.json').write_text(json.dumps(result, indent=2))
(OUT / 'EXAMPLE_STREAM.json').write_text(json.dumps(baseline, indent=2))
print(json.dumps(dict(status=result['status'], count=result['count'], max_rss_bytes=result['max_rss_bytes'])))
