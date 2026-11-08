"""Frozen Reader on decoded historical frames: stage audit, not robot evaluation."""
import datetime, hashlib, importlib.util, json, os, subprocess, sys, time, traceback
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI')
L=R/'result/32_system2_lift_gate_diagnosis/20261106_v1'
O=L/'perception-replay'
P=R/'models/recorded_policy_assets/skill-assets/implementations/code-skills/implementations/rdj_v1_classify_objects/6bb861ace4b706d9/rdj_v1_classify_objects'
I=R/'result/16_system2_integration/25_system2_integration_20261030T050100Z/integration-sources'
def read(p):return json.loads(Path(p).read_text())
def convert(v):
    if isinstance(v,dict):return {str(k):convert(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [convert(x) for x in v]
    if hasattr(v,'detach'):return v.detach().cpu().tolist()
    if hasattr(v,'tolist'):return v.tolist()
    return v
def write(p,d):
    p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(convert(d),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
spec=importlib.util.spec_from_file_location('approved_gpu_guard',R/'result/28_h100_offline_acceptance/20261104_v5/run_gpu_batch.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.O=O
def worker():
    guard.configure()
    write('gpu-idle-before-worker.json',guard.check_idle())
    write('write-isolation.json',guard.guard())
    import ctypes
    init=ctypes.CDLL('libcuda.so.1').cuInit(0);assert init==0,init
    import numpy as np, torch, transformers
    from PIL import Image
    assert torch.cuda.device_count()==1
    runtime=read(R/'result/17_system2_iterations/31_system2_final_validation_20261030T121000Z/runtime.json')
    for k,v in runtime['experts']['pi05']['service']['environment'].items():
        if k in ('CLASSIFY_CLIP_MODEL','CLASSIFY_DINO_MODEL'):os.environ[k]=str(guard.mapped(v))
    sys.path[:0]=[str(P.parent),str(I),str(I/'framework-validation-v3')]
    from rdj_v1_classify_objects import perception,robot_mask
    from PhysicalRSI_baselines.robodojo.camera_geometry import PinholeCamera
    camera=PinholeCamera(**runtime['policy_spec']['configuration']['camera'])
    def ray(pixel,z):
        pixels=np.asarray([pixel],dtype=float)
        return camera.unproject(pixels,camera.plane_depth(pixels,world_z=float(z)))[0]
    perception.ray=ray
    robot_mask.project=lambda points:camera.project(np.asarray(points,dtype=float))[0]
    np.random.seed(0);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
    write('runtime.json',dict(python=sys.version,torch=torch.__version__,transformers=transformers.__version__,gpu=torch.cuda.get_device_name(0),visible_devices=torch.cuda.device_count(),camera=runtime['policy_spec']['configuration']['camera'],source=str(P/'perception.py'),source_sha256=sha(P/'perception.py'),model_paths={k:os.environ[k] for k in ['CLASSIFY_DINO_MODEL','CLASSIFY_CLIP_MODEL']}))
    reader=perception.Reader()
    raw=[];post=reader.proc.post_process_grounded_object_detection
    def record_post(*a,**kw):
        out=post(*a,**kw);raw.append(convert(out));return out
    reader.proc.post_process_grounded_object_detection=record_post
    source=(P/'perception.py').read_text().splitlines()
    markers={}
    for text,name,variable in [('  from .foreground import','after_dino_geometry','result'),('  from .robot_mask import','before_robot_mask','outputs'),('  proposals=[','after_robot_mask','outputs'),('  from .grasp_shape import','after_clip','outputs')]:
        line=next(i+1 for i,s in enumerate(source) if s.startswith(text));markers[line]=(name,variable)
    calls=read(L/'inputs/layout_4.json')['calls']
    frame_index=read(L/'video-review/historical-frame-index.json')
    frames=[x for x in frame_index if x['camera']=='head' and x['encoded_frame'] in (0,635)]
    assert len(frames)==2
    results=[];original_fraction=robot_mask.robot_fraction
    for frame in frames:
        rgb=np.asarray(Image.open(frame['image']).convert('RGB'))
        state=calls[2 if frame['encoded_frame']==0 else 6]['response']['value']['state']
        for treatment in ['original_filter','no_robot_overlap_filter']:
            raw.clear();stages={}
            def trace(f,event,arg):
                if f.f_code is perception.Reader.read_batch.__code__ and event=='line' and f.f_lineno in markers:
                    name,var=markers[f.f_lineno];stages[name]=convert(f.f_locals[var])
                return trace
            robot_mask.robot_fraction=original_fraction if treatment=='original_filter' else lambda mask,box:0.
            np.random.seed(0);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
            t=time.monotonic();sys.settrace(trace)
            try:out=reader.read_batch([rgb],[state])
            finally:sys.settrace(None);robot_mask.robot_fraction=original_fraction
            row=dict(frame=frame['encoded_frame'],treatment=treatment,input=frame,state=state,
                state_source=f'inputs/layout_4.json calls[{2 if frame["encoded_frame"]==0 else 6}].response.value.state',
                alignment='Approximate encoded frame / observation sequence alignment; decoded lossy video, not original native sensor tensor',
                seconds=time.monotonic()-t,raw_dino_postprocessing=list(raw),stages=stages,
                final_objects=convert(out),robot_exclusions=convert(reader.last_robot_exclusions),basket_exclusions=convert(reader.last_basket_exclusions))
            name=f'frame{frame["encoded_frame"]:04}_{treatment}.json';write(name,row)
            results.append(dict(frame=frame['encoded_frame'],treatment=treatment,record=name,
                stage_categories={k:[[x['category'] for x in items] for items in v] for k,v in stages.items()},
                final_categories=[[x['category'] for x in items] for items in out],robot_exclusions=row['robot_exclusions']))
            print(json.dumps(convert(results[-1])),flush=True)
    # Stage-local probe: full image DINO watch boxes, without downstream geometry/filter changes.
    extra=[]
    for frame in frames:
        rgb=Image.open(frame['image']).convert('RGB')
        inp=reader.proc(images=[rgb],text=['wrist watch.'],padding=True,return_tensors='pt').to('cuda')
        with torch.inference_mode():out=reader.net(**inp)
        boxes=post(out,inp.input_ids,threshold=.18,text_threshold=.18,target_sizes=[(rgb.height,rgb.width)])
        extra.append(dict(frame=frame['encoded_frame'],input_sha256=frame['image_sha256'],raw_full_image_watch=convert(boxes),note='Changes detector input crop only; diagnostic proposal, not a deployed Reader repair or a robot outcome'))
    write('full-image-watch-probe.json',extra)
    # Original source remains immutable; modified bindings exist only inside this worker.
    assert sha(P/'perception.py')==read(O/'protocol.json')['source_sha256']
    write('summary.json',dict(state='completed',utc=now(),new_native_episodes=0,api_calls=0,
        frozen_reader_calls=len(results),full_image_detector_probes=len(extra),paired_frames=2,
        single_gpu=guard.GPU,results=results,limits=['Lossy decoded historical video and approximate joint-state alignment; not exact native sensor replay.','One diagnostic layout, no independent generalization test.','Mask-filter ablation does not estimate true 3D object height or verify grasp.']))
def main():
    O.mkdir(exist_ok=True)
    assert not (O/'status.json').exists(),'Existing attempt must be reconciled, not overwritten'
    write('protocol.json',dict(utc=now(),question='At which perception stage is a visibly lifted watch lost?',inputs='Historical augmented_3 layout4 head frame0/frame635, logged joint states',treatment='Original Reader versus only robot_fraction forced to zero in memory',invariants='Same decoded RGB, states, weights, source, detector thresholds, seed, camera and all other filters; no file edits to deployed runtime',secondary_probe='Full-image DINO wrist-watch query, no policy execution',source_sha256=sha(P/'perception.py'),native_episodes=0,api_calls=0,gpu=guard.GPU,maximum_visible_gpus=1))
    write('gpu-before.json',guard.check_idle())
    with (O/'worker.log').open('x') as f:
        p=subprocess.Popen([str(R/'envs/policy/bin/python'),'-B',str(O/'perception_replay.py'),'worker'],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        write('status.json',dict(state='running',controller_pid=os.getpid(),worker_pid=p.pid,utc=now()))
        t=time.monotonic()
        while p.poll() is None:
            with (O/'gpu-samples.jsonl').open('a') as out:out.write(json.dumps(dict(utc=now(),gpu=guard.smi(['-i',guard.GPU,'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'])))+'\n')
            if time.monotonic()-t>900:
                import signal
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(15)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                write('timeout.json',dict(seconds=900));break
            time.sleep(5)
    write('status.json',dict(state='completed' if p.returncode==0 else 'failed',exit_code=p.returncode,worker_pid=None,controller_pid=None,utc=now(),seconds=time.monotonic()-t))
    write('gpu-after.json',dict(utc=now(),devices=guard.smi(['--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader']),compute=guard.smi(['--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'])))
if __name__=='__main__':
    try:worker() if len(sys.argv)>1 else main()
    except BaseException as e:
        write('failure.json',dict(utc=now(),error=repr(e),traceback=traceback.format_exc()));raise
