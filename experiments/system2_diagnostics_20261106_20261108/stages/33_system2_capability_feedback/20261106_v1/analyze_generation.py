"""Describe generated code and API use independently of native task outcomes."""
import ast,collections,datetime,hashlib,json,statistics
from pathlib import Path
R=Path('/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1')
O=R/'generation-analysis';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not (O/'summary.json').exists()
ledger=read(R/'ledger.json');protocol=read(R/'protocol.json');assert len(ledger)==6
control=read(R/'requests/legacy_feedback_1.json');treatment=read(R/'requests/capability_feedback_1.json')
assert treatment['messages'][:-1]==control['messages']
assert {k:v for k,v in treatment.items() if k!='messages'}=={k:v for k,v in control.items() if k!='messages'}
for row in ledger:
 req=read(R/row['request_file']);assert req==({'legacy_feedback':control,'capability_feedback':treatment}[row['arm']])
features=[];usage=[]
expected_recovery={'legacy_feedback_1':False,'legacy_feedback_2':False,'legacy_feedback_3':False,'capability_feedback_1':True,'capability_feedback_2':True,'capability_feedback_3':True}
retreat={'legacy_feedback_1':1.06,'legacy_feedback_2':None,'legacy_feedback_3':1.06,'capability_feedback_1':1.06,'capability_feedback_2':None,'capability_feedback_3':1.055}
for row in ledger:
 name=row['id'];p=R/'candidates'/name/'candidate.py';source=p.read_text();tree=ast.parse(source)
 assert sha(p)==row['source_sha256'];lines=source.splitlines()
 memory_reads=[n.lineno for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id=='memory' and isinstance(n.ctx,ast.Load)]
 terms=['no_collision_free_path','primitive_error','contact_z =','contact =','for arm in','for candidate in','abs(p[2]-','abs(dz)','1.06','1.055']
 evidence=[dict(line=i+1,text=l) for i,l in enumerate(lines) if any(t in l for t in terms)]
 features.append(dict(candidate=name,arm=row['arm'],source=str(p),sha256=sha(p),evidence=evidence,
  source_review='Entire source inspected before native cohort outcomes.',
  dynamic_height_lift_gate=False,postlift_disappearance_gate=False,
  explicit_no_path_zero_execution_fallback=expected_recovery[name],
  fallback_scope='At most two pre-contact arm choices; transfer/lift failures still stop' if expected_recovery[name] else 'Generic primitive error raises and top-level catch returns',
  nominal_z_used_in_basket_membership=name.startswith('legacy'),
  contact_uses_half_object_height=name in ['capability_feedback_2','capability_feedback_3'],
  postrelease_vertical_retreat_z=retreat[name],memory_read_lines=memory_reads,
  interpretation='These are observed source features, not task success. Generated policies differ in multiple behavioral details; the experimental treatment here is generation feedback, not a single manual action change.'))
 u=row['usage'];d=u.get('prompt_tokens_details') or {};co=u.get('completion_tokens_details') or {}
 inp,out=u['prompt_tokens'],u['completion_tokens'];cached,cw=d.get('cached_tokens',0),d.get('cache_write_tokens',0)
 assert u['total_tokens']==inp+out and 0<=cached+cw<=inp
 cost=((inp-cached-cw)*2+cached*.1+cw*2.5+out*10)/1e6
 assert abs(cost-row['estimated_standard_usd'])<1e-10
 usage.append(dict(candidate=name,arm=row['arm'],input_tokens=inp,cached_input_subset=cached,cache_write_input_subset=cw,uncached_nonwrite_input=inp-cached-cw,output_tokens_including_reasoning=out,reasoning_subset=co.get('reasoning_tokens'),total_tokens=inp+out,seconds=row['seconds'],estimated_usd=cost))
arms=[]
for arm in ['legacy_feedback','capability_feedback']:
 us=[u for u in usage if u['arm']==arm];fs=[f for f in features if f['arm']==arm]
 arms.append(dict(arm=arm,generation_calls=len(us),mean_input=statistics.mean(u['input_tokens'] for u in us),mean_output=statistics.mean(u['output_tokens_including_reasoning'] for u in us),mean_total=statistics.mean(u['total_tokens'] for u in us),mean_api_seconds=statistics.mean(u['seconds'] for u in us),estimated_usd=sum(u['estimated_usd'] for u in us),dynamic_lift_guards=sum(f['dynamic_height_lift_gate'] for f in fs),bounded_no_path_fallbacks=sum(f['explicit_no_path_zero_execution_fallback'] for f in fs)))
save('source-features.json',features);save('api-usage.json',usage)
summary=dict(state='completed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=arms,
 exact_shared_messages_equal=True,additional_treatment_input_tokens=arms[1]['mean_input']-arms[0]['mean_input'],
 additional_input_percent=(arms[1]['mean_input']/arms[0]['mean_input']-1)*100,
 paid_generation_calls=6,estimated_total_usd=sum(u['estimated_usd'] for u in usage),
 previous_reviewed_api_estimate_usd=protocol['previous_reviewed_estimate_usd'],
 cumulative_reviewed_api_estimate_usd=protocol['previous_reviewed_estimate_usd']+sum(u['estimated_usd'] for u in usage),
 combined_conservative_reserve_usd=protocol['combined_reserved_upper_usd'],
 native_outcomes='Pending; source inspection is not a performance conclusion.',
 limitations=['Fixed balanced generation order, not paired deterministic seeds.','Cache warmth differs by request order; cost/latency difference is not an isolated feedback effect.','Three generated candidates per arm; five exposed native layouts per candidate, not independent scene samples.','Both groups independently remove the earlier lift guard; any such change cannot be credited solely to capability treatment.','Exact generated memory is bound, but all six sources currently do not read the memory parameter.'])
save('summary.json',summary)
(O/'REPORT.txt').write_text('''候选生成与代码机制检查（尚不包含原生任务结论）

两组均收到同一历史增强反馈、相同augmented_3失败源码和停止证据；处理组只附加已验证的接口能力说明。
6次生成均HTTP200、JSON和Python语法有效；6个候选均通过代码准入和120项CPU检查。CPU检查不能证明物理成功。
两个组均自行去掉了原候选的动态高度/抬升后漏检门槛，因此不能将“去掉该门槛”单独归功于处理组。
三个处理组候选显式区分no_collision_free_path并允许有限的接触前换臂；三个对照候选遇primitive_error仍通过异常结束。处理组的搬运/抬升失败仍可能直接退出。
处理组不再用名义Z判断篮筐成员；其中两个修改了接触目标的高度计算。所有这些行为差异均来自生成结果，不能当作手工单一动作消融解释。
两个候选省略显式放置后撤离，其余保留不同高度的撤离。是否降低步数或改善得分，须等待原生证据。
本轮将每个proposal的memory按框架接口传入，但静态检查表明6个候选代码均未读取该参数。历史运行记忆绑定未被悄悄改写。
每次处理组输入增加439Token（约2.87%）。缓存读/写属于输入的互斥子集，reasoning属于输出子集，均未重复累计。
新API费用估算0.1846203美元；与此前审计0.1932249合计约0.3778452美元，发票为准。保守预留合计5.659308美元，低于用户10美元上限。
逐请求用量、精确源码行号、哈希和解释限制见本目录JSON。不要从缓存条件不同的几次请求给出模型速度提升结论。
''')
print(json.dumps(summary))
