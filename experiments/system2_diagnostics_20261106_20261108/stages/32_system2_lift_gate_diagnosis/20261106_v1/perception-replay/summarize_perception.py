"""Read-only calculation over the completed perception replay; outputs in its folder."""
import datetime,hashlib,json,math
from pathlib import Path
L=Path('/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1')
O=L/'perception-replay'
def read(p):return json.loads(p.read_text())
def stable(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def iou(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return inter/max(1,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)
assert read(O/'status.json')['state']=='completed'
summ=read(O/'summary.json');pairs=[]
for f in [0,635]:
    a=read(O/f'frame{f:04}_original_filter.json');b=read(O/f'frame{f:04}_no_robot_overlap_filter.json')
    pairs.append(dict(frame=f,raw_dino_outputs_identical=a['raw_dino_postprocessing']==b['raw_dino_postprocessing'],
        raw_dino_hash=stable(a['raw_dino_postprocessing']),
        before_robot_mask_identical=a['stages']['before_robot_mask']==b['stages']['before_robot_mask'],
        original_final_watch_count=sum(x['category']=='watch' for x in a['final_objects'][0]),
        disabled_mask_final_watch_count=sum(x['category']=='watch' for x in b['final_objects'][0])))
post=read(O/'frame0635_original_filter.json');nms=[]
for x in post['stages']['after_dino_geometry'][0]:
    if x['category']!='watch':continue
    hits=[dict(category=y['category'],box=y['box'],score=y['score'],iou=iou(x['box'],y['box'])) for y in post['stages']['before_robot_mask'][0] if iou(x['box'],y['box'])>.4]
    nms.append(dict(watch_box=x['box'],watch_score=x['score'],overlapping_retained_proposals=hits))
analysis=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pairs=pairs,postlift_watch_nms_audit=nms,
    conclusion='Disabling robot-overlap filter alone does not recover final watch detection on this decoded postlift image. Detector proposal generation, class-agnostic deduplication and semantic fusion must be distinguished.',
    limits=summ['limits'],native_cases=0,api_calls=0)
(O/'analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
lines=['历史录像感知链离线诊断','',
 '问题：历史 augmented_3/layout4 的抬升后画面可见夹爪附近手表，但 scene() 没有返回 watch。这是否仅由 robot-overlap 过滤造成？',
 '方法：使用同一段真实录像解码的 head frame0 与 frame635，以及相邻已记录关节状态。在一张空闲 GPU 上加载冻结的 DINO/CLIP 与 Reader；每张图分别保留原过滤和仅在内存中把 robot_fraction 置零。共4次 Reader 推理，另做2次整图 wrist-watch 检测探针。无训练、无 API、无新增机器人回合。',
 '写入隔离限制为当前 perception-replay 目录。原模型、源文件和部署配置未修改。GPU已释放。','',
 '结果：']
for p in pairs:lines.append(f"frame {p['frame']}: 原始最终 watch={p['original_final_watch_count']}，关闭mask最终 watch={p['disabled_mask_final_watch_count']}；两条件原始DINO结果完全一致={p['raw_dino_outputs_identical']}，mask之前候选完全一致={p['before_robot_mask_identical']}。")
lines += ['',
 '抬升后有DINO watch提案，并不意味着提案定位在真正手表上。逐阶段记录显示：部分提案在跨类别IoU去重中被其他类别覆盖；余下一个watch提案在CLIP语义融合后改为camera。移除mask过滤也没有得到最终watch。整图探针同样存在较大、含机械臂的模糊候选框，不能认定扩大裁剪范围已经解决问题。',
 '因此，本实验否定“只关掉robot mask就能恢复这个观测中的watch”的局部预测，并没有证明所有布局都不受mask影响，也没有把漏检唯一归因于CLIP或DINO。需要结合候选框图像、原始无损观测及目标跟踪进一步定位。',
 '同时，Reader输出高度仍为类别固定平面高度。即便类别识别恢复，也不会自动满足候选要求的动态Z增量；感知识别问题与接口高度语义不一致是不同层次。','',
 '限制：输入是有损MP4解码图像；帧号与关节状态仅近似对齐，不能称为原生传感器逐像素复现。仅一个历史诊断布局、两帧，无独立泛化。所有探针只是感知输出，不是抓取成功、放置成功或任务得分。',
 '证据：protocol.json、runtime.json、frame*_*.json、analysis.json、full-image-watch-probe.json、worker.log、gpu-before.json/gpu-after.json。',
 '运行记录：启动SSH等待超时发生在已启动的后台任务期间；worker独立完成且exit0，未重启。joblib因写入隔离改用串行，模型推理结果已产生；此警告不是策略失败。']
(O/'REPORT.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(analysis,ensure_ascii=False))
