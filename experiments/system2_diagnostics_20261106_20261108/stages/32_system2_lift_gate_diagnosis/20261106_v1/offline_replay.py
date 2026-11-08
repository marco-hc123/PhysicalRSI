"""CPU-only, recorded-prefix replay of a frozen candidate and explicit ablations.

All writes are constrained to the new project result directory. Candidate code
has a reviewed AST, restricted builtins, no imports, and only a replay robot.
No RPC, GPU, API, environment step, or invented post-intervention observation.
"""
import ast
import copy
import datetime
import difflib
import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path

ROOT = Path('/mnt/data/joey_tr/physical-RSI')
SOURCE = ROOT / 'result/31_system2_rgb_validation/20261105_v1'
OUT = ROOT / 'result/32_system2_lift_gate_diagnosis/20261106_v1'
EXPECTED = 'c083d296b7708688356311749727ce410c8a0d09d2380f1722a94cea2bccd4db'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(path, value):
    assert path.resolve().is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

class ReplayBoundary(BaseException):
    pass

class ReplayMismatch(BaseException):
    pass

def equal(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12)
    return a == b

class ReplayRobot:
    def __init__(self, calls):
        self.calls = calls
        self.trace = []
        self.index = 0
        self.pending = None

    def _call(self, method, *args, **kwargs):
        request = dict(method=method, args=list(args), kwargs=kwargs)
        if self.index == len(self.calls):
            self.pending = request
            self.trace.append(dict(request=request, state='not_executed_unobserved_boundary'))
            raise ReplayBoundary()
        old = self.calls[self.index]
        wanted = {k:old['request'][k] for k in ['method','args','kwargs']}
        if not equal(request, wanted):
            raise ReplayMismatch(json.dumps(dict(index=self.index, actual=request, expected=wanted)))
        assert old['state'] == 'completed' and 'value' in old['response']
        self.trace.append(dict(request=request, original_call_id=old['request']['id'],
                               state='matched_recorded_response', response=old['response']))
        self.index += 1
        return copy.deepcopy(old['response']['value'])

    def scene(self, *args, **kwargs): return self._call('scene', *args, **kwargs)
    def approach(self, *args, **kwargs): return self._call('approach', *args, **kwargs)
    def gripper(self, *args, **kwargs): return self._call('gripper', *args, **kwargs)

SAFE_BUILTINS = {n:getattr(__import__('builtins'), n) for n in (
    'list','isinstance','str','int','float','all','abs','len','sum','sorted','set',
    'next','iter','range','enumerate','min','max','any','dict','Exception','RuntimeError')}

def checked_code(source, filename):
    tree = ast.parse(source)
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)
    assert tree.body[0].name == 'policy'
    allowed_attrs = {'scene','approach','gripper','get','items','rsplit','isdigit',
                     'append','add','remove','sort'}
    allowed_calls = set(SAFE_BUILTINS) | {'read_scene','normalize','inside','move'}
    forbidden = (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef,
                 ast.AsyncFunctionDef, ast.With, ast.AsyncWith)
    for node in ast.walk(tree):
        assert not isinstance(node, forbidden), type(node).__name__
        if isinstance(node, ast.Name): assert not node.id.startswith('__')
        if isinstance(node, ast.Attribute): assert node.attr in allowed_attrs, node.attr
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name): assert node.func.id in allowed_calls, node.func.id
            else: assert isinstance(node.func, ast.Attribute)
    env = {'__builtins__': SAFE_BUILTINS}
    exec(compile(tree, filename, 'exec'), env)
    return env['policy']

def replay(source, calls, filename):
    policy = checked_code(source, filename)
    robot = ReplayRobot(calls)
    events = []
    steps = 0
    guard_line = next(i+1 for i,s in enumerate(source.splitlines()) if s.strip().startswith('if len(lifted)') or 'if False: # diagnostic' in s)
    def tracer(frame, event, arg):
        nonlocal steps
        if frame.f_code.co_filename != filename: return None
        if event == 'line':
            steps += 1
            if steps > 100000: raise ReplayMismatch('Line budget exceeded')
            if frame.f_code.co_name == 'policy' and frame.f_lineno == guard_line:
                loc=frame.f_locals
                events.append(dict(event='guard_evaluated',line=guard_line,
                                   category=loc['category'],target_xyz=[loc['x'],loc['y'],loc['z']],
                                   matching_objects=copy.deepcopy(loc['lifted']),
                                   detected_objects=copy.deepcopy(loc['lifted_scene'])))
        if event == 'return' and frame.f_code.co_name == 'policy':
            events.append(dict(event='policy_frame_return_or_unwind',line=frame.f_lineno))
        return tracer
    sys.settrace(tracer)
    state = 'returned'
    try:
        policy(robot, {})
    except ReplayBoundary:
        state = 'next_unobserved_call_requested'
    finally:
        sys.settrace(None)
    assert robot.index == len(calls), ('Recorded prefix not fully consumed',robot.index)
    assert len([e for e in events if e['event']=='guard_evaluated']) == 1
    return dict(state=state,matched_recorded_calls=robot.index,next_call=robot.pending,
                next_call_executed=False,events=events,trace=robot.trace,candidate_lines_executed=steps)

def main():
    assert ROOT.is_dir() and SOURCE.is_dir()
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'summary.json').exists(), 'Existing completed replay must not be overwritten'
    original_path=SOURCE/'analysis/reference-contract/augmented_3.py'
    assert sha(original_path)==EXPECTED
    source=original_path.read_text()
    dx="(o['p'][0]-x)**2 + (o['p'][1]-y)**2 < 0.0036"
    dz="o['p'][2] > z + 0.025"
    assert source.count(dx)==source.count(dz)==1
    variants={
        'original':source,
        'remove_z_only':source.replace(' and '+dz,''),
        'remove_xy_only':source.replace(' and '+dx,''),
        'remove_xy_and_z':source.replace(' and '+dx,'').replace(' and '+dz,''),
        'bypass_lift_guard':source.replace('if len(lifted) != 1:', 'if False: # diagnostic bypass; not a grasp verifier'),
    }
    provenance=json.loads((SOURCE/'analysis/lift-gate-diagnosis.json').read_text())
    inputs=[]
    for row in sorted(provenance['rows'],key=lambda x:x['layout_id']):
        assert row['mapping_qualified']
        p=SOURCE/row['source_record'];assert sha(p)==row['source_sha256']
        proc=json.loads(p.read_text());calls=sorted(proc['calls'],key=lambda x:x['request']['id'])
        assert [c['request']['method'] for c in calls]==['scene','scene','gripper','approach','approach','gripper','approach','scene']
        inputs.append(dict(layout_id=row['layout_id'],path=str(p),sha256=sha(p),calls=calls))
    sources=[]
    for name,text in variants.items():
        p=OUT/'candidates'/name/'candidate.py';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        (p.parent/'change.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),text.splitlines(True),fromfile='original.py',tofile=name+'.py')))
        sources.append(dict(name=name,path=str(p.relative_to(OUT)),sha256=sha(p)))
    protocol=dict(created_utc=stamp(),kind='Exploratory recorded-prefix CPU mechanism study',
        prior_inspection='The archived lift diagnosis and original source were inspected before specifying these probes; this is not heldout confirmation.',
        goal='Decompose the lift gate, test the proposed Z-only ablation, and stop before any unobserved action.',
        source_archive=str(SOURCE),original_sha256=EXPECTED,variants=sources,
        inputs=[{k:x[k] for k in ['layout_id','path','sha256']} for x in inputs],
        fixed=['All recorded responses and pre-gate code','Target, arm, quaternions, budget, scoring unchanged'],
        interventions={'remove_z_only':'Remove Z predicate only; retain category, XY and exact-one guard',
                       'remove_xy_only':'Remove XY predicate only',
                       'remove_xy_and_z':'Factorial diagnostic; retain category and exact-one guard',
                       'bypass_lift_guard':'Positive control of the stopping branch only, not a deployable grasp verifier'},
        accounting=dict(recorded_native_cases_reused=5,new_native_cases=0,planned_cpu_replays=25,new_api_calls=0,gpu_used=False),
        boundaries=['No scene edits or synthetic action success','No GT passed to candidate','No execution after recorded prefix','No automatic promotion or native launch'])
    save(OUT/'protocol.json',protocol)
    save(OUT/'status.json',dict(stage='offline_replay_running',utc=stamp(),pid=os.getpid(),host=platform.node(),writes_root=str(OUT),gpu_used=False,api_calls=0))
    results=[];gate_rows=[]
    for item in inputs:
        save(OUT/'inputs'/f"layout_{item['layout_id']}.json",item)
        for name,text in variants.items():
            result=replay(text,item['calls'],str(OUT/'candidates'/name/'candidate.py'))
            result.update(layout_id=item['layout_id'],variant=name,source_record_sha256=item['sha256'])
            save(OUT/'replays'/f"{name}_layout_{item['layout_id']}.json",result)
            results.append({k:result[k] for k in ['layout_id','variant','state','matched_recorded_calls','next_call','next_call_executed']})
            if name=='original':
                event=next(e for e in result['events'] if e['event']=='guard_evaluated')
                x,y,z=event['target_xyz'];cat=event['category']
                objects=[]
                for o in event['detected_objects']:
                    if o['category']==cat:
                        px,py,pz=o['p'][:3];dist=math.hypot(px-x,py-y)
                        objects.append(dict(pose=o['p'],xy_distance_m=dist,xy_pass=dist*dist<.0036,z_change_m=pz-z,z_pass=pz>z+.025))
                nxy=sum(o['xy_pass'] for o in objects);nz=sum(o['z_pass'] for o in objects)
                gate_rows.append(dict(layout_id=item['layout_id'],category=cat,target_xyz=[x,y,z],
                    same_category_count=len(objects),xy_passing_count=nxy,z_passing_count=nz,
                    combined_passing_count=sum(o['xy_pass'] and o['z_pass'] for o in objects),
                    remove_z_only_eligible_count=nxy,remove_xy_only_eligible_count=nz,
                    remove_both_eligible_count=len(objects),objects=objects,
                    observation_failure='same_category_absent' if not objects else 'all_same_category_outside_xy_radius'))
    totals={name:dict(replays=5,returned=sum(r['state']=='returned' for r in results if r['variant']==name),
        next_call_requests=sum(r['state']=='next_unobserved_call_requested' for r in results if r['variant']==name)) for name in variants}
    summary=dict(completed_utc=stamp(),host=platform.node(),python=platform.python_version(),totals=totals,
        gate_rows=gate_rows,replays=results,accounting=dict(new_cpu_replays=25,reused_native_cases=5,new_native_cases=0,new_api_calls=0,gpu_used=False,new_task_scores=None),
        z_only_branch_changes=[r['layout_id'] for r in results if r['variant']=='remove_z_only' and r['state']=='next_unobserved_call_requested'],
        limitations=['These are counterfactual prefix replays on saved observations, not new physical outcomes.',
                     'Multiple predicates fail simultaneously; height is not established as the sole cause.',
                     'After the first new call no observations or success results are invented.',
                     'Bypassing the guard does not establish grasp or placement.'])
    save(OUT/'summary.json',summary)
    save(OUT/'status.json',dict(stage='offline_replay_complete',utc=stamp(),pid=None,host=platform.node(),
        outputs=['summary.json','protocol.json','replays/','candidates/'],gpu_used=False,api_calls=0,new_native_cases=0,
        next_action='Review branch changes before freezing a justified RGB experiment; do not run a Z-only native matrix if all replay decisions are unchanged.'))
    print(json.dumps({'state':'complete','root':str(OUT),'totals':totals,'new_native_cases':0,'gpu_used':False,'api_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
