"""Explicit review fixtures; stop before calculation, never create qualification evidence."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

ROOT = Path('/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle')
OUT = Path('/private/tmp/apex-v02c-independent-review-1')
sys.path[:0] = [str(ROOT), str(ROOT/'scripts'), str(ROOT/'src')]
from tools.apex_workbench import qualification as q
from tools.apex_workbench.lab_configuration import execution_context, request_for

# A real copied retained record keeps all checksum anchors unchanged. It is still
# interactive software evidence; this probe never tries to promote or publish it.
source = OUT/'retained-input-copies/VDL1_BASE'
copy = OUT/'exact-base-directory-copy'
shutil.copytree(source, copy)
original_reference, original_record = q.bind_run(source)
copy_reference, copy_record = q.bind_run(copy)
exact_copy = {
    'different_directories': original_reference['directory'] != copy_reference['directory'],
    'same_manifest': original_reference['manifest_sha256'] == copy_reference['manifest_sha256'],
    'same_run_id': original_record['request']['run_id'] == copy_record['request']['run_id'],
    'same_worker_bytes': (source/'worker.json').read_bytes() == (copy/'worker.json').read_bytes(),
}
assert all(exact_copy.values())

# Test the evaluator's distinct-execution admission using an explicitly mocked
# source loader. No model runs and no real qualification record are constructed.
# Leave actual require_protocol_run and scientific_identity in use; abort at
# calculate, before any qualification document or result can be produced.
records, references = {}, {}
for index, slot in enumerate(q.SLOTS):
    case, grid = ('VDL1_BASE', 'nominal') if slot in {'repeat', 'reference'} else slot.split('/')
    record = deepcopy(original_record)
    record['review_fixture_only'] = True
    record['request']['effective'] = request_for(case, grid_id=grid)
    record['request']['execution_context'] = execution_context(record['request']['effective'], qualification=True, reference=slot=='reference')
    record['request']['run_id'] = 'fixture_execution_' + str(index)
    # identity reads the genuine retained geometry/environment/schema only;
    # mock record contents are never serialized as scientific evidence.
    record['directory'] = source
    if slot == 'repeat':
        record['request']['run_id'] = 'fixture_execution_0'
    records[slot] = record
    references[slot] = {'directory': str(OUT/'synthetic-loader-paths'/str(index)), 'manifest_sha256': '0'*64}
lookup = {ref['directory']: records[slot] for slot, ref in references.items()}
class CalculationSentinel(Exception):
    pass
reached = False
with patch.object(q, 'bound_run', side_effect=lambda reference: lookup[reference['directory']]), patch.object(q, 'calculate', side_effect=CalculationSentinel('duplicate execution passed admission')):
    try:
        q.evaluate_references(references)
    except CalculationSentinel:
        reached = True
result = {
    'classification': 'review_fixture_admission_probe_not_qualification_evidence',
    'revision': 'a6917a00c2ac48e69d3a28ca4e7c9fbf6d964052',
    'exact_copy': exact_copy,
    'distinct_fixture_paths': len({r['directory'] for r in references.values()}),
    'distinct_fixture_run_ids': len({r['request']['run_id'] for r in records.values()}),
    'duplicate_run_id_reached_calculation_sentinel': reached,
    'calculation_completed': False,
    'qualification_document_created': False,
    'new_model_trajectories': 0,
}
assert reached
(OUT/'execution-identity-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
