"""Write the verified route report without changing raw native outcomes."""
import json,os,datetime,collections
from pathlib import Path
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
d=read(O/'chain-analysis.json');visual=read(O/'visual-review.json')
assert d['state']=='completed' and visual['state']=='reviewed'
assert read(O/'analysis/independent-validation.json')['state']=='passed'
assert read(O/'reference/analysis/independent-validation.json')['state']=='passed'
text=['Skill-chain capability floor: completed diagnostic route','',
'Question: can the existing execution interfaces carry out a basic pick-lift-transport-release chain before attributing low full-task scores to System 2?',
'',
'Scope: 10 new native episodes, two conditions x five exposed development layouts. No training, new generated candidate, paid API call, lab GPU use or policy promotion. Original objects, layout hashes, scoring and 1100-step task budget are unchanged. All experiment and analysis compute was on the execution server.',
'',
'Conditions: the current corrected candidate is limited to one outer-loop cycle. The released reference is limited to its first basket-transfer return and retains internal recovery/handoff. They can choose different objects and use different API capabilities. This is a descriptive capacity reference, not a matched causal policy or LLM comparison.',
'',
'Primary evidence: object identities are matched only under the preregistered distance/margin checks. Lift is a root-rise proxy, not a contact-force certificate. Complete-chain proxy requires lift, completed transport, an explicit release and stable final membership in the selected target basket. Failure-cleanup release is separately labelled. Native success and score remain those in original receipts.',
'',
'Condition summaries:']
for g in d['groups']:text.append(json.dumps(g,ensure_ascii=False))
text.extend(['','Per-layout evidence:'])
for r in d['cases']:
    text.append(json.dumps({k:r.get(k) for k in ['condition','layout_id','source_instance','source_label','target_basket','lift_root_rise_m','object_transport_xy_m','object_ee_comotion_residual_m','release_kind','final_gripper_normalized','selected_object_delivered_proxy','complete_chain_proxy','basket_boundary_reached','physical_diagnosis','first_error','native_score_100','native_full_success']},ensure_ascii=False))
candidate=[r for r in d['cases'] if r['condition']=='single_cycle'];reference=[r for r in d['cases'] if r['condition']=='released_first_basket_cycle']
text.extend(['','Interpretation:',
f"The currently corrected generated candidate has verified complete-chain kinematic evidence in {sum(r.get('complete_chain_proxy') is True for r in candidate)}/5 tested first-object attempts. This establishes some operational capability, not reliable performance across objects or layouts.",
'All20 candidate approach calls returned successfully. Successful RPC completion did not guarantee that the selected object remained carried or settled in the intended basket.',
'Candidate layout1 illustrates a delivered object with native task score0: remaining same-category and other objects prevent full classification completion. Task score alone is insufficient to locate the failure phase.',
'Candidate layout0: root rises44.9mm, then returns close to table height during transport before deliberate release; object/end-effector displacement residual139.4mm supports loss of carry. Layout2: object root is already outside the selected basket at transport end and remains outside after release. Layout3: root is horizontally within the basket at transport end but above the settling height, then falls outside membership during release/settling. These are different failure locations, not a single generic planning failure. Contact forces are unknown.',
f"The richer released reference had {sum(r.get('basket_boundary_reached',False) for r in reference)}/5 normal first-basket-transfer returns; its native endpoint/recovery failures are preserved. A physical delivery via exception cleanup is not a normal transfer return.",
'This route does not isolate a universal PhysicalRSI defect or a model-capability limit. It does not test whether a newly generated System2 repair improves performance. The current candidate includes historical manual execution-contract repairs.',
'',
'Recommended next controlled tests:',
'1. Separate pick/carry retention from placement. On fixed development cases, change only one of grasp dwell/capture stabilization or transport motion profile, then check carry co-motion, retention and delivered objects under the same task budget.',
'2. For objects that remain carried but miss the basket, examine the measured object-to-gripper offset at release and object-relative destination geometry. Keep perception source, original basket membership and scoring unchanged.',
'3. Audit released endpoint failures with the logged position/joint/rotation errors. Any change to endpoint checks or recovery needs its own declared control; relaxed completion checks do not prove task success.',
'4. Once a minimal chain is reliable, rerun System2 feedback comparison with aligned candidate-visible interfaces, equal generation/validation rules, and later held-out layouts. Report generation, validation and reuse costs separately.',
'',
'Accounting and validation:',
'Five candidate episodes and five reference episodes, 30 original native videos, full decode validation and original receipt/harness/layout checks. CPU fixtures and the failed initial reference startup are not episodes. No candidate episode was rerun during launcher repair.',
'The first reference startup inherited stdin EOF and exited before simulation. Original service exit code was not persisted. CPU watchdog reproduction and successful pipe-owned relaunch support the diagnosis. Only launcher lifecycle handling changed; policy source and environment remained fixed.',
'',
'Evidence index:',
'chain-analysis.json; chain-results.csv; analysis-criteria.json; visual-review.json; keyframes*/frame-index.json;',
'analysis/independent-validation.json; reference/analysis/independent-validation.json;',
'native-campaign/runs/; reference/native/; backend-traces/; sim-diagnostics/; reference/model-traces/;',
'reference/deployment-attempt01/; reference/deployment-repair.json; environment-current.json;',
'protocol.json; reference/protocol.json; REPRODUCE.txt; migration/source-manifest.json.',
'',
'Limits: five exposed layouts are not independent generalization evidence. One cycle deliberately leaves most multi-object tasks incomplete. Reference and candidate have different selectors/APIs. Proxy thresholds and object-association uncertainty are explicit. Neither higher action counts nor partial points establish robust System2 improvement.'])
(O/'REPORT.txt').write_text('\n'.join(text)+'\n')
os.environ['MPLCONFIGDIR']=str(O/'analysis-cache/matplotlib')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4))
for offset,group,label in [(-.18,candidate,'Candidate: one cycle'),(.18,reference,'Released: first basket attempt')]:
    values=[sum(r['source_association']['qualified'] for r in group),sum(r.get('lift_proxy',False) for r in group),sum(r.get('release_observed',False) for r in group),sum(r.get('complete_chain_proxy') is True for r in group)]
    axes[0].bar([i+offset for i in range(4)],values,.36,label=label)
    axes[1].bar([r['layout_id']+offset for r in group],[r['native_score_100'] for r in group],.36,label=label)
axes[0].set(xticks=range(4),xticklabels=['Matched\nsource','Root rise\n>=2 cm','Post-lift\nrelease','Complete-chain\nproxy'],ylabel='Cases /5',ylim=(0,5.8))
axes[1].set(xticks=range(5),xlabel='Exposed development layout',ylabel='Original task score /100',ylim=(0,100))
for ax in axes:ax.legend(fontsize=7)
fig.suptitle('Capability diagnostic: different controllers / interfaces; descriptive only',fontsize=10);fig.tight_layout(rect=[0,.12,1,.95]);fig.text(.5,.02,'Reference: 3 normal deliveries + 2 failure-cleanup deliveries. Five exposed layouts; selected objects differ.',ha='center',fontsize=8)
(O/'figures').mkdir(exist_ok=True)
for ext in ['png','svg']:fig.savefig(O/('figures/skill_chain_floor.'+ext),dpi=160)
plt.close(fig)
print(json.dumps(dict(state='report_written',native_cases=10,api_calls=0)))
