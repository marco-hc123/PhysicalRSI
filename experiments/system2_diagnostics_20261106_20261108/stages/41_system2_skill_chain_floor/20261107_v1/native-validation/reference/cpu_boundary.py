"""Check that the prefix wrapper stops on first basket result, including false."""
import json
from pathlib import Path
from first_cycle import install
rows=[]
for result in [False,True]:
    class Fake:
        stage='initial'
        def __init__(self):self.events=[]
        def event(self,**x):self.events.append(x)
        def transfer(self,obj,arm,dest,tag,qualified_plan=None):
            yield tag
            return result
        def run(self):
            yield from self.transfer({},'left',[],'handoff_source')
            yield from self.transfer({},'left',[],'basket')
            yield 'unexpected second source'
    install(Fake);f=Fake();out=list(f.run())
    assert out==['handoff_source','basket'] and f.stage=='complete_hold'
    assert sum(x.get('capacity_cycle_boundary',False) for x in f.events)==1
    rows.append(dict(reported_result=result,outputs=out,events=f.events))
(Path(__file__).parent/'cpu-boundary-results.json').write_text(json.dumps(dict(state='passed',fixtures=2,rows=rows,physical_success_claim=False),indent=2)+'\n')
print(json.dumps(dict(state='passed',fixtures=2)))
