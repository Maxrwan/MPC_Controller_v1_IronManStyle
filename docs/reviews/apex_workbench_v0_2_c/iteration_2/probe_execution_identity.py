"""Admission-only review fixtures: calculation sentinel prevents qualification creation."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path('/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle')
OUT = Path('/private/tmp/apex-v02c-independent-review-2')
sys.path[:0] = [str(ROOT),str(ROOT/'scripts'),str(ROOT/'src')]
from tools.apex_workbench import qualification as q, storage
from tools.apex_workbench.lab_configuration import execution_context, request_for

class CalculationSentinel(Exception): pass
results = []
for mode in ('unique','duplicate_run','duplicate_worker','duplicate_manifest','pid_reuse_new_birth'):
    references,records,workers = {},{},{}
    for i,slot in enumerate(q.SLOTS):
        case,grid=('VDL1_BASE','nominal') if slot in {'repeat','reference'} else slot.split('/')
        values=request_for(case,grid_id=grid)
        directory=str(OUT/'admission-fixtures'/str(i))
        records[slot]={'directory':directory,'request':{'run_id':'fixture-'+str(i),'effective':values,'execution_context':execution_context(values,qualification=True,reference=slot=='reference')},'status':{'scientific_outcome':'completed'},'review_fixture_only':True}
        references[slot]={'directory':directory,'manifest_sha256':f'{i:064x}'}
        workers[directory]={'role':'worker','pid':1000+i,'created':1000.0+i}
    first=q.SLOTS[0]
    if mode=='duplicate_run': records['repeat']['request']['run_id']=records[first]['request']['run_id']
    if mode=='duplicate_worker': workers[records['repeat']['directory']]=dict(workers[records[first]['directory']])
    if mode=='duplicate_manifest': references['repeat']['manifest_sha256']=references[first]['manifest_sha256']
    if mode=='pid_reuse_new_birth': workers[records['repeat']['directory']]['pid']=workers[records[first]['directory']]['pid']
    lookup={ref['directory']:records[slot] for slot,ref in references.items()}
    reached=False
    rejected=False
    with patch.object(q,'bound_run',side_effect=lambda ref:lookup[ref['directory']]), patch.object(storage,'artifact_json',side_effect=lambda path,name:workers[str(path)]), patch.object(q,'scientific_identity',return_value={'review_fixture_only':True}), patch.object(q,'calculate',side_effect=CalculationSentinel()):
        try: q.evaluate_references(references)
        except CalculationSentinel: reached=True
        except storage.IntegrityError as error:
            rejected=True
            assert 'distinct execution identities' in str(error),str(error)
    expected=mode in {'unique','pid_reuse_new_birth'}
    assert reached==expected and rejected!=expected,(mode,reached,rejected)
    results.append({'mode':mode,'reached_calculation_sentinel':reached,'identity_rejected':rejected})
report={'schema':'review-admission-only/1','revision':'4897686e79c13757d5ef5b4373b44d4cab99b5bf','results':results,'calculation_completed':False,'qualification_document_created':False,'new_model_trajectories':0}
(OUT/'execution-identity-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
