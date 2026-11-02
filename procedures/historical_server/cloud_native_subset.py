"""Select preregistered layout IDs without changing assets, dynamics or rewards."""
import json
import os
from pathlib import Path
import runpy
from env.seed_manager.seed_manager import SeedManager

selected = [int(x) for x in os.environ['PHYSICALRSI_EVAL_LAYOUTS'].split(',')]
if not selected or len(selected) != len(set(selected)) or min(selected) < 0:
    raise ValueError('Unique nonnegative layout IDs required')
original_init = SeedManager.init_eval

def subset_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    missing = set(selected) - set(self.seed_info)
    if missing:
        raise ValueError('Requested layouts absent from native inventory: '+str(missing))
    self.seed_list = [x for x in selected if x in self.seed_list]
    self.st_idx = 0
    self.ed_idx = len(self.seed_list)
    self.idx = 0
    self._current_batch_seeds = None
    print('PREREGISTERED_LAYOUT_SUBSET', json.dumps(self.seed_list), flush=True)

SeedManager.init_eval = subset_init
runpy.run_path('/mnt/data/physical-RSI/code/RoboDojo/src/eval_client/main.py',run_name='__main__')
