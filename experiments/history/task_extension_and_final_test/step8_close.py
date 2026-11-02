"""Audit, derive reproducible metrics, and close only verified completed cohorts."""
from pathlib import Path
from datetime import datetime,timezone
import json,csv,hashlib,subprocess,sys,statistics,shutil,math
R=Path('/mnt/data/physical-RSI');O=Path(sys.argv[1]);E=O/'exports';E.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def lines(p):return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
def table(p,rows):
 keys=list(dict.fromkeys(k for row in rows for k in row))
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
def mean(vals):return statistics.mean(vals) if vals else None
def wilson(k,n):
 z=1.96;d=1+z*z/n;mid=(k/n+z*z/(2*n))/d;rad=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/d;return [max(0,mid-rad),min(1,mid+rad)]
def videos(job,native):
 files=sorted((job/'videos').glob('*.mp4'));assert len(files)==3*len(native),(job,len(files),len(native))
 expected=sorted([e['steps'][0]+1 for e in native for _ in range(3)]);actual=[]
 for p in files:
  v=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,width,height','-of','json',str(p)],text=True))['streams'][0]
  actual.append(int(v['nb_read_frames']))
 assert sorted(actual)==expected,(job,actual,expected)
 return dict(path=str(job),count=len(files),frames=sum(actual))
def measurement_jobs(suite,tag,audit=False):
 rows=[];calls=[];proof=[];p=read(suite/'protocol.json')
 for job in p['jobs']:
  if job.get('retained'):continue
  path=suite/job['name'];s=read(path/'status.json');assert s['complete'],path
  native=lines(path/'native-events.jsonl');policy=lines(path/'policy-events.jsonl');term=[x for x in native if x['kind'] in ['episode_end','episode_error','reset_error']]
  assert not any(x['kind']=='reset_error' for x in term)
  assert {x['layout'] for x in term}==set(job['layouts'])
  results=read(path/'native-result.json')['details'] if (path/'native-result.json').exists() else {}
  environment=next(x for x in native if x['kind']=='native_environment_created')
  for t in term:
   idx=t['episode_index'];layout=t['layout'];pe=[x for x in policy if x['episode_index']==idx];ne=[x for x in native if x['episode_index']==idx]
   metadata=[read(x) for x in sorted((path/'api').glob('*metadata.json')) if read(x)['episode_index']==idx]
   for m in metadata:
    u=m.get('usage') or {};calls.append(dict(cohort=tag,job=job['name'],task=job['task'],case_index=idx,layout=layout,attempt=m['attempt'],provider_usage_known=bool(u),http_success=m['success'],input_tokens=u.get('prompt_tokens'),output_tokens=u.get('completion_tokens'),total_tokens=u.get('total_tokens'),cached_input_tokens=u.get('prompt_tokens_details',{}).get('cached_tokens',0),reasoning_output_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),http_seconds=m['seconds'],evidence=str(path/'api'/('call-%03d-metadata.json'%m['attempt']))))
   native_ok=t['kind']=='episode_end';detail=next((x for x in results.values() if x['layout_id']==layout),None)
   if native_ok:assert detail is not None and detail['success']==t['success'][0] and not t['unstable_envs']
   plans=[x['plan'] for x in pe if x['kind'] in ['logical_plan_end','fixed_route_end']]
   starts={k:next((x['monotonic'] for x in ne if x['kind']==k),None) for k in ['reset_start','reset_ready','episode_start']}
   usage=[x['usage'] for x in metadata if x.get('usage')]
   row=dict(cohort=tag,purpose=job.get('stage',job['condition']),task=job['task'],route=job['route'],job=job['name'],case_index=idx,layout=layout,native_completed=native_ok,success=bool(t.get('success',[False])[0]),partial_score=detail['score'] if native_ok else 0,
    termination=t['kind'],error=t.get('error'),control_steps=t['steps'][0] if t.get('steps') else 0,native_step_limit=environment['step_limit'],
    logical_planner_calls=sum(x['kind']=='logical_plan_start' for x in pe),http_attempts=len(metadata),unknown_usage_attempts=sum(not bool(x.get('usage')) for x in metadata),
    input_tokens=sum(u['prompt_tokens'] for u in usage),output_tokens=sum(u['completion_tokens'] for u in usage),total_tokens=sum(u['total_tokens'] for u in usage),cached_input_tokens=sum(u.get('prompt_tokens_details',{}).get('cached_tokens',0) for u in usage),
    http_seconds=sum(x['seconds'] for x in metadata),reset_to_result_seconds=t['monotonic']-starts['reset_start'] if starts['reset_start'] is not None else None,
    ready_to_result_seconds=t['monotonic']-starts['reset_ready'] if starts['reset_ready'] is not None else None,
    control_ack_seconds=sum(x['seconds'] for x in ne if x['kind']=='control_ack'),policy_action_seconds=sum(x['seconds'] for x in pe if x['kind']=='action_batch'),
    selected_compositions=';'.join(x['composition'] for x in plans),selected_operations=json.dumps([x.get('operations',[]) for x in plans]),
    job_wrapper_seconds=s['elapsed_seconds'],wrapper_time_is_shared_not_per_episode=True,evidence_directory=str(path))
   assert row['total_tokens']==row['input_tokens']+row['output_tokens'];rows.append(row)
  if audit:proof.append(videos(path,[x for x in term if x['kind']=='episode_end']))
 return rows,calls,proof
assert read(O/'smoke-controller-status.json')['complete']
assert read(O/'formal-controller-status.json')['complete']
assert read(O/'final-test/completion.json')['complete']
new,calls,proof=measurement_jobs(O,'new_representative',True)
assert len(new)==18 and sum(r['purpose']=='formal' for r in new)==15
old,oldcalls,_=measurement_jobs(R/'result/24_steps23_20261030T013742Z_v3','historical_reference',False)
# The two reconciled diagnostic records remain separately archived, never silently duplicated here.
final=read(O/'final-test/results.json');assert len(final)==20
for r in final:
 assert r['state']=='completed' and r['natural_terminal']
 for p,h in r['evidence'].items():assert sha(p)==h,p
 assert r['new_http_calls']==0
# All shared pinned deployment/procedure files still match registration.
for p,h in read(O/'protocol.json')['source_hashes'].items():assert sha(p)==h,p
F=R/'result/23_protocol_freeze_20261029T132917Z';frozen=read(F/'source-freeze.json')
for row in frozen['deployment_files']:assert sha(row['path'])==row['sha256']
for p,h in frozen['recorded_protocol_and_framework_hashes'].items():assert sha(p)==h
for p,h in read(O/'final-test/protocol.json')['reference_files'].items():assert sha(p)==h,p
for p,h in read(O/'procedure-registration.json').items():assert sha(O/'analysis-sources'/p)==h,p
flatfinal=[dict(cohort='independent_final_test',purpose='report_only',task=r['task'],route=r['expert'],case_index=r['case_index'],layout_sha256=r['layout_sha256'],success=r['success'],partial_score=r['episode_score'],control_steps=r['diagnostics'].get('action_count'),native_step_limit=r['diagnostics'].get('step_limit'),elapsed_seconds=r['elapsed_s'],logical_planner_calls=0,http_attempts=0,input_tokens=0,output_tokens=0,total_tokens=0,weight_revision=r['revision'],evidence_directory=r['wrapper_batch']) for r in final]
table(E/'representative-episodes.csv',new);table(E/'historical-reference-episodes.csv',old);table(E/'model-http-attempts.csv',calls+oldcalls);table(E/'independent-final-episodes.csv',flatfinal)
summaries=[]
for purpose in ['smoke','formal']:
 for task in read(O/'protocol.json')['tasks']:
  rows=[r for r in new if r['purpose']==purpose and r['task']==task];k=sum(r['success'] for r in rows);n=len(rows)
  summaries.append(dict(cohort=purpose,task=task,episodes=n,successes=k,success_rate=k/n,descriptive_wilson95=wilson(k,n),mean_partial_score=mean([r['partial_score'] for r in rows]),input_tokens=sum(r['input_tokens'] for r in rows),output_tokens=sum(r['output_tokens'] for r in rows),total_tokens=sum(r['total_tokens'] for r in rows),cached_input_tokens=sum(r['cached_input_tokens'] for r in rows),http_attempts=sum(r['http_attempts'] for r in rows),logical_calls=sum(r['logical_planner_calls'] for r in rows),mean_reset_to_result_seconds=mean([r['reset_to_result_seconds'] for r in rows]),mean_control_steps=mean([r['control_steps'] for r in rows]),native_errors=sum(not r['native_completed'] for r in rows)))
for task in ['classify_objects','classify_objects_by_language']:
 rows=[r for r in flatfinal if r['task']==task];k=sum(r['success'] for r in rows)
 summaries.append(dict(cohort='independent_final',task=task,episodes=10,successes=k,success_rate=k/10,descriptive_wilson95=wilson(k,10),mean_partial_score=mean([r['partial_score'] for r in rows]),total_tokens=0,http_attempts=0,logical_calls=0,mean_wrapper_seconds=mean([r['elapsed_seconds'] for r in rows])))
table(E/'task-summary.csv',summaries);write(E/'task-summary.json',summaries)
A=R/'result/20_cross_project_evidence_20261029T075456Z'
for name in ['a-public-task-reference.csv','cold-continuous-pairs.csv','evidence-citations.json','a-public-numerical-audit.json']:
 shutil.copy2(A/name,E/name)
phase=[]
for row in summaries:phase.append(dict(phase='System1 '+row['cohort'],task=row['task'],http_attempts=row['http_attempts'],total_tokens=row['total_tokens'],native_episodes=row['episodes'],source=str(E/'task-summary.json')))
s2=read(R/'result/31_system2_final_validation_20261030T121000Z/step5-results.json')
phase.append(dict(phase='System2 formal two proposals',task='classify_objects',http_attempts=s2['proposal_http_attempts'],total_tokens=s2['proposal_total_tokens'],native_episodes=s2['native_episodes'],source=str(R/'result/31_system2_final_validation_20261030T121000Z/step5-results.json')))
phase.append(dict(phase='System2 including prior failed proposal; overlaps formal row',task='classify_objects',http_attempts=s2['cumulative_with_prior_failed_proposal'].get('proposal_http_attempts'),total_tokens=s2['cumulative_with_prior_failed_proposal'].get('proposal_total_tokens'),source=str(R/'result/31_system2_final_validation_20261030T121000Z/step5-results.json')))
table(E/'phase-costs.csv',phase)
# No credentials are exported; scan small text outputs against the configured secret.
private=read('/home/ecs-user/.config/physicalrsi/agent.json')
for p in E.iterdir():
 if p.is_file():assert private['api_key'].encode() not in p.read_bytes(),p
comparison=[
 dict(item='Task/control interface',project_a='GPT-as-Policy official selected public cases; direct short action chunks and hybrid skill/tool behavior',physicalrsi='Actual Qwen Agent chooses a frozen composition; local code/VLA executes many native controls',qualification='Same task names do not establish identical layouts, model, success level or training.'),
 dict(item='Provider total tokens',project_a='Use a-public-task-reference.csv mean_total_tokens, per episode; includes cached input',physicalrsi='Use actual prompt_tokens+completion_tokens from provider usage per attempt',qualification='Different providers/tokenizers; cached input and reasoning are subsets, not additional tokens.'),
 dict(item='Uncached comparison',project_a='mean_uncached_input_plus_output is diagnostic, not a bill or latency measurement',physicalrsi='total_tokens-cached_input_tokens; report alongside total',qualification='No equal-success savings ratio or price comparison claimed.'),
 dict(item='Calls',project_a='Public action segments are not verified HTTP request counts',physicalrsi='Separate logical planning, real HTTP attempts, native robot controls',qualification='A request count unavailable remains blank; never substitute action count.'),
 dict(item='Speed',project_a='Public physical duration=steps*0.04; complete wall clock unavailable',physicalrsi='Separate process startup, API, policy, simulator/reset and batch elapsed',qualification='No end-to-end inter-project speed ratio supported.'),
 dict(item='Cold/continuous',project_a='No matched public process timing',physicalrsi='Reuse six prior paired measurements and batch accounting',qualification='Early format failures not speedups; OS/GPU caches were not flushed.'),
 dict(item='System2',project_a='Official metrics only, no new execution',physicalrsi='Two proposal/selection rounds retained parent; final reports test frozen policy',qualification='Generation+development+failed-attempt costs stay separate from online System1.'),
 dict(item='New task scope',project_a='No new A benchmark',physicalrsi='Three smoke plus fifteen representative formal cases',qualification='One Memory task is not memory-on/off causality; one precision task not full dexterity proof; stack_bowls not random variant.'),
 dict(item='Final transfer',project_a='Not applicable',physicalrsi='Ordinary selected artifact unchanged; language assembly only binds same pi05',qualification='No language System2 gain or improved candidate is claimed.')]
table(E/'measurement-comparison.csv',comparison)
report=['本轮有限范围实验收尾结果','', '新增三项：每项1个预跑+5个正式评估；原计划最终验收：两项分类各10个新布局。完整榜单、额外训练和新System2轮次不在本轮范围。','']
for row in summaries:report.append(f"{row['cohort']} / {row['task']}: 成功 {row['successes']}/{row['episodes']}，平均部分得分 {row['mean_partial_score']:.4f}，Token {row['total_tokens']}，HTTP {row['http_attempts']}。")
report+=['','两轮System2均保留父版本；最终验收只评估一次等价策略，不将相同策略重复运行伪装成独立改进组。语言分类是相同pi05的预注册迁移评估，仅新增任务绑定，无模型/权重/技能源代码修订。',
 '项目间Token差异主要对应调用粒度和重复上下文：A公开均值含大量缓存输入，B在本固定版本中通常单次高层规划后由本地技能/VLA控制；任务难度、模型和成功率不一致，不能解释为等效果下的成本节省。A数值是每回合均值，不是5回合总数。',
 '速度方面，A公开物理时长不能与B端到端墙钟直接相除。原有冷启动/连续运行证据继续保留：小批次启动与预热摊销未证明整批加速，格式失败缩短耗时也不算加速。',
 '本轮各任务样本小，成功率和区间仅为描述。低成功率本身是结果；未自动更换场景或反复重试直至成功。预跑、正式、最终验收、恢复测试和历史诊断不混合计算。',
 '完整原始证据留在服务器；exports目录包含逐回合、逐HTTP、分阶段成本、对照口径和来源文件。']
(E/'results-zh.txt').write_text('\n'.join(report)+'\n')
write(E/'verification.json',dict(complete=True,utc=datetime.now(timezone.utc).isoformat(),new_agent_episodes=len(new),formal_agent_episodes=15,final_episodes=20,videos=proof,original_deployment_files_verified=len(frozen['deployment_files']),final_reference_files_unchanged=True,api_usage_arithmetic_verified=True,credential_matches=0,qualifications=comparison))
write(E/'file-manifest.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in E.iterdir() if p.is_file() and p.name!='file-manifest.json'})
write(O/'completion.json',dict(complete=True,utc=datetime.now(timezone.utc).isoformat(),stage='limited_scope_complete_verified',new_native_or_counted_episode_attempts=38,model_http_attempts=sum(r['http_attempts'] for r in new),model_total_tokens=sum(r['total_tokens'] for r in new),result_summary=str(E/'task-summary.json'),export_manifest_sha256=sha(E/'file-manifest.json'),raw_retention='cloud_only',full_leaderboard_completed=False))
print(json.dumps(dict(complete=True,summary=summaries),ensure_ascii=False))
