"""Bound a released episode at its first basket transfer return, not success."""
class CycleBoundary(BaseException):
    pass

def install(Episode):
    original_run=Episode.run
    original_transfer=Episode.transfer
    def transfer(self,obj,arm,dest,tag,qualified_plan=None):
        self.event(capacity_transfer_begin=True,capacity_transfer_tag=tag,capacity_source=obj,capacity_arm=arm,capacity_destination=dest)
        result=yield from original_transfer(self,obj,arm,dest,tag,qualified_plan=qualified_plan)
        self.event(capacity_transfer_return=True,capacity_transfer_tag=tag,capacity_reported_result=bool(result))
        if tag=='basket':
            raise CycleBoundary()
        return result
    def run(self):
        try:
            yield from original_run(self)
        except CycleBoundary:
            self.event(capacity_cycle_boundary=True,reason='First basket transfer returned; reported result may be false; no task success inferred')
            self.stage='complete_hold'
            return
    Episode.transfer=transfer
    Episode.run=run
