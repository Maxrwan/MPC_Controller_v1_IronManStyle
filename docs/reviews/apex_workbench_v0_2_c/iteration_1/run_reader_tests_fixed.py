"""Review-only adapter for existing tests: retained copies replace worker fixture."""
import json
from pathlib import Path
import shutil
import sys
import pytest

ROOT = Path('/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle')
OUT = Path('/private/tmp/apex-v02c-independent-review-1')
sys.path[:0] = [str(ROOT), str(ROOT/'scripts'), str(ROOT/'src')]
source = ROOT/'results/apex_workbench_v02c_work_20261029/affected-2/real-lab-workers0'
inputs = OUT/'retained-input-copies'
inputs.mkdir(exist_ok=True)
selected = {}
for path in sorted(source.iterdir()):
    if not (path/'request.json').is_file():
        continue
    request = json.loads((path/'request.json').read_text())
    selected.setdefault(request['effective']['case_id'], path)
paths = []
for case in ('VDL1_BASE', 'VDL1_STEER_HIGH'):
    dest = inputs/case
    
    if not dest.exists():
        shutil.copytree(selected[case], dest)
    paths.append(dest)
class RetainedCopies:
    @pytest.fixture(scope='session')
    def lab_runs(self):
        return paths

# Patch the conftest fixture after collection; fixture closures bind via pytest's mapping.
class Override:
    def pytest_collection_modifyitems(self, session, config, items):
        fm = session._fixturemanager
        for item in items:
            defs = item._fixtureinfo.name2fixturedefs.get('lab_runs')
            if defs:
                for definition in defs:
                    definition.func = lambda **kwargs: paths

args = ['-q', str(ROOT/'tools/apex_workbench/tests/test_lab_closure.py'), str(ROOT/'tools/apex_workbench/tests/test_qualification.py'), '-k', 'not one_refinement_software_smoke and not c3_ui', '--basetemp='+str(OUT/'pytest-temp-fixed'), '--durations=5']
result = pytest.main(args, plugins=[Override()])
(OUT/'pytest_exit_fixed.json').write_text(json.dumps({'exit_code':result,'worker_fixture_replaced':True,'new_scientific_trajectories':0},indent=2)+'\n')
raise SystemExit(result)
