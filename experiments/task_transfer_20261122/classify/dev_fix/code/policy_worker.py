"""C3 retained, with a post-deposit return and dynamic assignment of unused baskets."""
from pathlib import Path
import os
import numpy as np
import policy_worker_guardlog as original
import teacher_kin as kin
from shared_io import R as work,write
from scene_setup import load,digest

FIX=Path(__file__).resolve().parent

def extend(current,baskets,assignments,inside):
    """Add new visible classes only. Original assignments and occupied baskets stay fixed."""
    visible=[o for o in current if o['category']=='basket']
    objects=[o for o in current if o['category']!='basket']
    pending=set(o['category'] for o in objects)-set(assignments)
    free={}
    for i,anchor in enumerate(baskets):
        if i in assignments.values():continue
        matches=[b for b in visible if sum((b['p'][j]-anchor['p'][j])**2 for j in (0,1))<.0025]
        if len(matches)==1 and not any(inside(item,matches[0]) for item in objects):
            free[i]=matches[0]
    added={}
    while pending and free:
        costs=[]
        for c in pending:
            group=[o for o in objects if o['category']==c]
            for i,b in free.items():
                cost=sum(sum((o['p'][j]-b['p'][j])**2 for j in (0,1)) for o in group)/len(group)
                costs.append((cost,c,i))
        _,c,i=min(costs)
        assignments[c]=i;added[c]=i;pending.remove(c);free.pop(i)
    return added

class FixSession(original.Session):
    def __init__(self):
        original.B=FIX
        super().__init__()
        self.initial={arm:list(self.joints(arm)) for arm in ('left','right')}
        self.assignment_events=[]
    def update_assignments(self,current,baskets,assignments,inside):
        old=dict(assignments)
        added=extend(current,baskets,assignments,inside)
        self.assignment_events.append(dict(sequence=self.seq,before=old,added=added,after=dict(assignments)))
        write('assignment-updates.json',self.assignment_events)
    def detected(self):
        objects=self.scene()['objects']
        return sorted(objects)
    def migrated_turn(self,*args):
        keep=super().migrated_turn(*args)
        if not self.record.get('deposited'):return keep
        arm=self.record['arm']
        start=self.seq
        before=self.detected()
        pose=kin.fk(arm,self.initial[arm])
        refused=None
        try:
            ok=self.move('retreat_after_deposit',arm,pose[:3,3],kin.quat_wxyz(pose[:3,:3]))
        except ValueError as exc:
            if str(exc)!='Native CuRobo path exceeds primitive bound' or self.seq!=start:raise
            ok=False
            refused=str(exc)
        after=self.detected()
        self.record['after_deposit_retreat']=dict(arm=arm,accepted=ok,refusal=refused,start=start,end=self.seq,visible_before=before,visible_after=after,new_categories=sorted({n.rsplit('_',1)[0] for n in after}-{n.rsplit('_',1)[0] for n in before}))
        return keep
if __name__=='__main__':
    import traceback
    try:FixSession().run()
    except BaseException:
        write('policy-error.json',dict(error=traceback.format_exc()));raise
