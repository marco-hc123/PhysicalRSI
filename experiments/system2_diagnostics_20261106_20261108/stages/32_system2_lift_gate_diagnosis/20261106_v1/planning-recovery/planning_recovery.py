"""Actual failed-call start/target replay, varying only target Z in solver probes."""
import ctypes,datetime,hashlib,importlib.util,json,os,re,subprocess,sys,time,traceback
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
L=R/'result/32_system2_lift_gate_diagnosis/20261106_v1'
N=L/'native-validation';O=L/'planning-recovery'
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
spec=importlib.util.spec_from_file_location('approved_gpu_guard',R/'result/28_h100_offline_acceptance/20261104_v5/run_gpu_batch.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.O=O
def prepare():
    assert read(N/'migration/ARCHIVE_VERIFIED.json')['state']=='verified'
    d=read(N/'analysis/matrix-analysis.json');jobs=[];inputs=[]
    for a in sorted(d['actors'],key=lambda x:(x['condition'],x['mapped_layout_id'])):
        if a['condition']!='bypass_lift_guard':continue
        assert a['mapping_qualified'] and a['rejected_approach_calls']==1
        p=N/a['process_record'];calls=read(p)['calls']
        failed=next(c for c in calls if c.get('response',{}).get('value',{}).get('primitive_error'))
        assert failed['response']['value']['primitive_error']=='no_collision_free_path'
        before=[c for c in calls if c['request']['id']<failed['request']['id'] and 'state' in c.get('response',{}).get('value',{})]
        state=before[-1]['response']['value']['state'];action=failed['request']['kwargs'];arm=action['arm']
        inp=dict(layout=a['mapped_layout_id'],failed_call_id=failed['request']['id'],failed_action=action,start=state[arm+'_arm_joint_state'],state_call_id=before[-1]['request']['id'],record=str(p),record_sha256=sha(p),phase='transport' if failed['request']['id']==8 else 'retreat')
        inputs.append(inp)
        for seed in [0,1,2]:
            for dz in [0.,-.04,-.08]:
                target=dict(action);target['position_m']=list(action['position_m']);target['position_m'][2]+=dz
                jobs.append(dict(job_id=len(jobs),layout=inp['layout'],phase=inp['phase'],seed=seed,delta_z_m=dz,action=target,start=inp['start'],source_record_sha256=inp['record_sha256']))
    assert len(inputs)==5 and len(jobs)==45
    write('protocol.json',dict(utc=now(),question='Does lowering only failed target Z improve offline planner feasibility?',inputs=inputs,jobs=jobs,
        invariants='Logged start joints, target XY/quaternion/arm, frozen planner source, robot geometry, scene and solver configuration; only target Z varies within each seed',
        limits=['45 solver calls, not robot episodes.','Repeated seeds within the same resident planner are robustness probes, not independent scene samples.','No collision-free solution is not a proof of geometric impossibility.','Lower target feasibility does not establish contact safety, placement, grasp or task success.','Lab solver acceptance is a preflight and must be confirmed in the native runtime.'],native_episodes=0,api_calls=0))
def worker():
    guard.configure();write('gpu-idle-before-worker.json',guard.check_idle());write('write-isolation.json',guard.guard())
    assert ctypes.CDLL('libcuda.so.1').cuInit(0)==0
    cfg=read(R/'result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/runtime.json');pc=cfg['policy_spec']['configuration']
    source=guard.mapped(pc['robot_yml']);code=source.parents[3]
    sys.path[:0]=[str(code),str(R/'repos/lab-runtime/curobo')]
    import numpy as np,torch,warp
    warp.config.kernel_cache_dir=str(O/'cache/warp')
    import curobo._src.runtime as cruntime
    cruntime.cache_dir=str(O/'cache/curobo')
    assert torch.cuda.device_count()==1
    y=source.read_text();replacements={}
    for s in set(re.findall(r'/mnt/data/physical-RSI/[^\s\"\']+',y)):
        replacements[s]=str(guard.mapped(s));y=y.replace(s,replacements[s])
    local_yml=O/'config/robot-paths-only.yml';local_yml.parent.mkdir(exist_ok=True);local_yml.write_text(y)
    for asset in source.parent.iterdir():
        if asset.name!='curobo.yml':(local_yml.parent/asset.name).symlink_to(asset)
    from rdj_v1_classify_objects.curobo_planner import CuroboPlanner
    import inspect
    write('runtime.json',dict(python=sys.version,torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(0),planner_file=inspect.getfile(CuroboPlanner),planner_sha256=sha(inspect.getfile(CuroboPlanner)),original_yml_sha256=sha(source),path_only_substitutions=replacements,arm_bases=pc['arm_bases'],table_height=-.025))
    jobs=read(O/'protocol.json')['jobs'];planners={};results=[]
    try:
        for arm in sorted(set(j['action']['arm'] for j in jobs)):
            planners[arm]=CuroboPlanner(robot_origin_pose=[0,0,0,1,0,0,0],active_joints_name=['joint'+str(i) for i in range(1,7)],all_joints=['joint'+str(i) for i in range(1,7)],dt=.004,yml_path=str(local_yml),table_height=-.025)
        for job in jobs:
            np.random.seed(job['seed']);torch.manual_seed(job['seed']);torch.cuda.manual_seed_all(job['seed']);a=job['action'];t=time.monotonic()
            res=planners[a['arm']].plan_path(curr_joint_pos=job['start'],target_ee_pose=[*a['position_m'],*a['quaternion_wxyz']],real_robot_pose=pc['arm_bases'][a['arm']]);torch.cuda.synchronize()
            row=dict(job,planner_status=res.get('status'),seconds=time.monotonic()-t,trajectory_returned='position' in res)
            if 'position' in res:
                v=np.asarray(res['position']);np.save(O/f'trajectories/job{job["job_id"]:02}.npy',v);row.update(trajectory_shape=list(v.shape),all_finite=bool(np.isfinite(v).all()))
                assert row['all_finite']
            results.append(row);write(f'probes/job{job["job_id"]:02}.json',row);write('results.json',results)
            print(json.dumps(row),flush=True)
    finally:
        for p in planners.values():p.__del__()
    summary=[]
    for layout in range(5):
        for dz in [0.,-.04,-.08]:
            rows=[r for r in results if r['layout']==layout and r['delta_z_m']==dz]
            summary.append(dict(layout=layout,phase=rows[0]['phase'],delta_z_m=dz,returned_trajectory=sum(r['trajectory_returned'] for r in rows),calls=len(rows),statuses=[r['planner_status'] for r in rows]))
    write('summary.json',dict(utc=now(),state='completed',solver_calls=len(results),new_native_episodes=0,api_calls=0,groups=summary))
def main():
    assert not (O/'status.json').exists(),'Existing attempt requires reconciliation'
    prepare();(O/'trajectories').mkdir();write('gpu-before.json',guard.check_idle())
    with (O/'worker.log').open('x') as f:
        p=subprocess.Popen([str(R/'envs/simulator/bin/python'),'-B',str(O/'planning_recovery.py'),'worker'],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        write('status.json',dict(state='running',controller_pid=os.getpid(),worker_pid=p.pid,utc=now()));t=time.monotonic()
        while p.poll() is None:
            with (O/'gpu-samples.jsonl').open('a') as out:out.write(json.dumps(dict(utc=now(),gpu=guard.smi(['-i',guard.GPU,'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'])))+'\n')
            if time.monotonic()-t>1800:
                import signal
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(15)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                write('timeout.json',dict(seconds=1800));break
            time.sleep(5)
    write('status.json',dict(state='completed' if p.returncode==0 else 'failed',exit_code=p.returncode,controller_pid=None,worker_pid=None,utc=now(),seconds=time.monotonic()-t))
    write('gpu-after.json',dict(utc=now(),devices=guard.smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader']),compute=guard.smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])))
if __name__=='__main__':
    try:worker() if len(sys.argv)>1 else main()
    except BaseException as e:write('failure.json',dict(utc=now(),error=repr(e),traceback=traceback.format_exc()));raise
