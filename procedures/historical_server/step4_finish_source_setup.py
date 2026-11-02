from pathlib import Path
import json,hashlib,shutil
O=Path('/mnt/data/physical-RSI/result/25_system2_integration_20261030T050100Z');F=O/'integration-sources/framework';S=O/'integration-sources'
patch=json.loads((O/'isolated-patches.json').read_text())
def change(p,a,b,why):
 old=p.read_bytes();assert a in old.decode(),(p,a);p.write_text(old.decode().replace(a,b));patch['files'].append(dict(file=str(p),original_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),purpose=why))
p=F/'PhysicalRSI_baselines/robodojo/native_worker.py'
change(p,'                    env = factory(*args, **kwargs)\n                    return observer.attach(env)',
'''                    env = factory(*args, **kwargs)
                    app = args[1] if len(args) > 1 else kwargs["app"]
                    original_close = app.close
                    def close_with_receipt(*a, **k):
                        outcomes = observer.finish()
                        atomic_json(observer.output / "completed.json", dict(state="completed", outcomes=outcomes))
                        return original_close(*a, **k)
                    app.close = close_with_receipt
                    return observer.attach(env)''','Publish exact native outcomes before Isaac close exits; supervised clean exit still mandatory')
p=F/'PhysicalRSI_baselines/robodojo/policy_model.py'
change(p,'class Model:', '''class FixedRouteLoop:
    """Self-Harness fixes the evaluation route; no redundant advisory LLM call."""
    def __init__(self): self.ready=set()
    def prepare(self, rows): return list(rows)
    def consume(self, indices): pass
    def reset(self): self.ready.clear()

class Model:''','Declare fixed-route System2 evaluation without System1 advisory planner; 0 hidden HTTP')
change(p,'planner = AgentPlanner(**settings.get("agent", {}))','planner = None','Fixed route selected by frozen harness')
change(p,'self.agent_loop = AgentLoop(planner, settings.get("task_specific_policy_memory", {}), self._record_plan, self.agent_interval, settings.get("agent_max_calls_per_episode", 1))','self.agent_loop = FixedRouteLoop()','No advisory-agent surcharge in fixed native evaluation')
(O/'isolated-patches.json').write_text(json.dumps(patch,indent=2)+'\n')
print(json.dumps(dict(patches=len(patch['files']),source_setup='complete')))
