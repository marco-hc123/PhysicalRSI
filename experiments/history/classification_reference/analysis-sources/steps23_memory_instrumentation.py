# Injected after the event recorder exists, before any model is instantiated.
from PhysicalRSI.Embodied_Harness.memory.store import Snapshot
_snapshot_read = Snapshot.read
_memory_reads = {}
def _observed_snapshot_read(self):
    value = _snapshot_read(self)
    _memory_reads[self.revision] = _memory_reads.get(self.revision, 0)+1
    if _memory_reads[self.revision] == 1 or _memory_reads[self.revision] % 100 == 0:
        event('immutable_memory_read', revision=self.revision, count=_memory_reads[self.revision])
    return value
Snapshot.read = _observed_snapshot_read

from openpi.policies.sparse_memory import SparseVisualHistory
_history_append = SparseVisualHistory.append
_history_materialize = SparseVisualHistory.materialize
_history_reset = SparseVisualHistory.reset
def _observed_history_append(self, session_id, images, **kwargs):
    value = _history_append(self, session_id, images, **kwargs)
    if value == 0 or value % 25 == 0:
        event('sparse_history_append', session=str(session_id), step=value,
              sessions=sorted(map(str,self.session_ids)), retained=len(self._sessions[session_id].frames),
              camera_keys=sorted(images))
    return value
def _observed_history_materialize(self, session_id, **kwargs):
    value = _history_materialize(self, session_id, **kwargs)
    if value['memory_step'] == 0 or value['memory_step'] % 25 == 0:
        event('sparse_history_materialize', session=str(session_id), step=value['memory_step'],
              masks={k:int(v.sum()) for k,v in value['history_image_masks'].items()},
              frame_counts={k:int(v.shape[0]) for k,v in value['history_images'].items()})
    return value
def _observed_history_reset(self, session_id=None):
    before=sorted(map(str,self.session_ids))
    value=_history_reset(self, session_id)
    event('sparse_history_reset', session=str(session_id), before=before, after=sorted(map(str,self.session_ids)))
    return value
SparseVisualHistory.append = _observed_history_append
SparseVisualHistory.materialize = _observed_history_materialize
SparseVisualHistory.reset = _observed_history_reset
