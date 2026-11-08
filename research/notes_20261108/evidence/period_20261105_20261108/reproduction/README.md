# 12个新增批次的具体复现索引

这里记录已保存的入口源码、配置、布局及进程参数。本次没有执行这些程序。源码入口名称和完整启动argv是不同证据：有保存argv时逐字保留，没有时标为缺失，不编造一键命令。

历史绝对路径是原件出处；实验室归档统一根目录为`/mnt/data/joey_tr/physical-RSI/result/`。历史执行路径不能直接在归档目录原地重跑。服务器现有依赖、权重和资源仍需按冻结指纹恢复。

## 环境基线与公开核验入口

[版本对比](environment/version-comparison.json)、[simulator包清单](environment/simulator-installed-packages.json)、[policy包清单](environment/policy-installed-packages.json)绑定11月5日恢复的共同软件基线。simulator与policy的Torch、NumPy和Warp版本不同；[policy pip check](environment/policy-pip-check.txt)保留rerun-sdk需要NumPy>=2而冻结为1.26.4的声明冲突。后续执行契约逐批改变，不存在一个覆盖全周的单一未变runtime。

`../audit/verify_weekly_receipts.py`是本次历史审计源程序，内含本机周包绝对路径，不能当成服务器可直接运行的入口。公开GitHub仓库的标准可携带核验入口是从仓库根运行`python3 -B tools/verify_weekly_package.py --package reports/research_week_20261102_20261108`，它只读取发布证据，不重新调用模型或机器人。

[机器可读复现索引](reproduction-index.json)含全部实际源文件SHA、选取的环境/seed字段、布局SHA以及保存的argv。以下摘要不能替代各批原协议。

## Batch 32

原件根：`/mnt/data/joey_tr/physical-RSI/result/32_system2_lift_gate_diagnosis/20261106_v1`；周志`EXP-2026W45-015`。
协议SHA256：`8253029899c6c8c084c7700693dbdc0304dfddbdf54e210a6efed74efd7ba9b6`。模型：未新生成候选。

lift_guard:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；retreat_destination:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

已保存perception-replay及planning-return/recovery的runtime明确GPU=NVIDIA H100 NVL，属于离线感知/规划；不能据此认定原生RGB使用H100。本次窄读取未单独确认该批原生GPU型号。归档整理未启动GPU作业。

### 已保存源码入口

- [native-validation/inputs/prepare_native.py](sources/32/native-validation/inputs/prepare_native.py) — SHA256 `9ba6f9152ad3b69000bb47db667b7f7f5d9f2928d8b838c79acde01fb2ab6824`。
- [native-validation/inputs/run_native.py](sources/32/native-validation/inputs/run_native.py) — SHA256 `2ff862a2b21488af81998c59f9275c4714f140a840a8807b2b70a452e11b9aa8`。
- [native-validation/prepare_native.py](sources/32/native-validation/prepare_native.py) — SHA256 `ef5f02c1e082af1f1accde47ae84c141876f31917b83f1f940d4eeca81c11bd0`。
- [native-validation/run_native.py](sources/32/native-validation/run_native.py) — SHA256 `2ff862a2b21488af81998c59f9275c4714f140a840a8807b2b70a452e11b9aa8`。
- [prepare_native.py](sources/32/prepare_native.py) — SHA256 `ef5f02c1e082af1f1accde47ae84c141876f31917b83f1f940d4eeca81c11bd0`。
- [retreat-followup/native-validation/prepare_native.py](sources/32/retreat-followup/native-validation/prepare_native.py) — SHA256 `094e093e713bdf1573f56fe9b8bd755658e3a6899057eebb2f700a024c5f7d38`。
- [retreat-followup/native-validation/run_native.py](sources/32/retreat-followup/native-validation/run_native.py) — SHA256 `80f07f9ebdc1f2421672b8062f0874a6a628638a3f2c8477796386a6dbdcb7b5`。
- [retreat-followup/prepare_native.py](sources/32/retreat-followup/prepare_native.py) — SHA256 `094e093e713bdf1573f56fe9b8bd755658e3a6899057eebb2f700a024c5f7d38`。
- [retreat-followup/run_native.py](sources/32/retreat-followup/run_native.py) — SHA256 `80f07f9ebdc1f2421672b8062f0874a6a628638a3f2c8477796386a6dbdcb7b5`。
- [run_native.py](sources/32/run_native.py) — SHA256 `2ff862a2b21488af81998c59f9275c4714f140a840a8807b2b70a452e11b9aa8`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/32_system2_lift_gate_diagnosis/20261106_v1/native-validation/native-campaign/runs/bypass_lift_guard/attempt-001/native/request.json` — SHA256 `cfc9e2c81a60f56741987cb64ea584d0623ee03c4c19b3dd4014c8105ea83b7f`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/32_system2_lift_gate_diagnosis/20261106_v1/native-validation/native-campaign/runs/original/attempt-001/native/request.json` — SHA256 `7096a48e5e396726f5b656852dd2323c5877fd12db2107eb77176fa43f9d03c8`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup/native-validation/native-campaign/runs/bypass_lift_guard/attempt-001/native/request.json` — SHA256 `e2b3a855d4a5a805564e19853c281d15b56bc566f669d31cd3cc15341e6f6c7b`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/perception-replay/gpu-before.json` — SHA256 `883d3d840c9f8c69365fdfd3fff8d21a36922091cce31555983ad38136f13c16`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/perception-replay/runtime.json` — SHA256 `d6b4fd2ddf62e9b3ea6902acb1f8ffc68877ea28982f34f7ffe8cc36bb23007a`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/planning-recovery/gpu-before.json` — SHA256 `52c2c61834fcb9bbd16e09902a92b7eda7a2dd8c8b6d23591096b1b78dc9c62c`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/planning-recovery/runtime.json` — SHA256 `ac11e173cc4a452914b66a9b512892083fab992dd55fd3b767412727fc873ec2`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/planning-return/gpu-before.json` — SHA256 `12f2cc571d0651b2bc47c9e324c37d2438097fe2d0a49b193cf16dfc6bb6d6d6`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/planning-return/runtime.json` — SHA256 `eb66e31740d785fec55b0f3d2d9b98ac3d1391c679d326a20ce4af061a034081`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup/inputs/planning-recovery/runtime.json` — SHA256 `ac11e173cc4a452914b66a9b512892083fab992dd55fd3b767412727fc873ec2`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup/inputs/planning-return/runtime.json` — SHA256 `eb66e31740d785fec55b0f3d2d9b98ac3d1391c679d326a20ce4af061a034081`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup/native-validation/inputs/planning-recovery/runtime.json` — SHA256 `ac11e173cc4a452914b66a9b512892083fab992dd55fd3b767412727fc873ec2`；所选字段见机器可读索引。
- `result/32_system2_lift_gate_diagnosis/20261106_v1/retreat-followup/native-validation/inputs/planning-return/runtime.json` — SHA256 `eb66e31740d785fec55b0f3d2d9b98ac3d1391c679d326a20ce4af061a034081`；所选字段见机器可读索引。

## Batch 33

原件根：`/mnt/data/joey_tr/physical-RSI/result/33_system2_capability_feedback/20261106_v1`；周志`EXP-2026W45-016`。
协议SHA256：`803f851be1245b2f16c8d2c293ec791983de556f683f42ae7a1a7f47b445c8bb`。模型：gpt-6.1-sol/medium；输出上限见原请求，根protocol未单列。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [evaluate_candidates.py](sources/33/evaluate_candidates.py) — SHA256 `daf7a20165d300d02f87d3316042a2baf55a90c2988e1bff548e14f4097110c0`。
- `excluded-transfer-attempt-001/evaluate_candidates.py`（已核manifest指纹，正文未复制至本索引） — SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- [native-validation/prepare_native.py](sources/33/native-validation/prepare_native.py) — SHA256 `43665775127906646d39797a9eb20eb9e82ab507ae94708dc4ce983b1052049b`。
- [native-validation/run_native.py](sources/33/native-validation/run_native.py) — SHA256 `245722a6b742e0a9ea8baafbbb9a13b87946fc9b0f807f40b3015c8fbf142d5c`。
- [run_generation.py](sources/33/run_generation.py) — SHA256 `bbf02ca56b6be2481ca8ad878736c80fc646bda2e2661e24fabc396ae2967bf7`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/33_system2_capability_feedback/20261106_v1/native-validation/native-campaign/runs/capability_feedback_1/attempt-001/native/request.json` — SHA256 `6cdd754163d0ff3161c84e1c8d5facffe7e1ebc777d285584f967a5f7dcf204b`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/33_system2_capability_feedback/20261106_v1/native-validation/native-campaign/runs/capability_feedback_2/attempt-001/native/request.json` — SHA256 `4ceab74fa3d5085f0ad9e00a244f39c7b599d95248b5b82cb4d098ebdccaedca`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/33_system2_capability_feedback/20261106_v1/native-validation/native-campaign/runs/capability_feedback_3/attempt-001/native/request.json` — SHA256 `16f24f64538dbd72d07c20edacc81ef982eef7b04411a9d4effee9ced99cca2e`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
本次未读取到本批单独环境事实快照；软件共同基线与协议继承声明保留，未凭此猜测主机硬件。

## Batch 34

原件根：`/mnt/data/joey_tr/physical-RSI/result/34_system2_trajectory_contract/20261106_v1`；周志`EXP-2026W45-017`。
协议SHA256：`64150745266c14c1406b842ad592576a461f8c6f228cb7af94461d958eaf4d32`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/prepare_native.py](sources/34/native-validation/prepare_native.py) — SHA256 `3200d7777e3d7f9bca4d964c773782f27791a79ec97bef0fff7bb167c6a0de68`。
- [native-validation/run_native.py](sources/34/native-validation/run_native.py) — SHA256 `a9a69800b96785779c796e91b72e1cdbdd3874ea8d1a197afea8f023422cb14b`。
- [offline_contract.py](sources/34/offline_contract.py) — SHA256 `40789bbdf0b156e4da6ecb27238b434204284de3bd5d3a007d916d689bdef28d`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/34_system2_trajectory_contract/20261106_v1/native-validation/native-campaign/runs/dense/attempt-001/native/request.json` — SHA256 `9a53fd12a21d428a98a63766c0175a4e161c14850ba77035ad89ed25cc2556a7`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/34_system2_trajectory_contract/20261106_v1/native-validation/native-campaign/runs/released_waypoint_thinning/attempt-001/native/request.json` — SHA256 `3b0b7031b934daaad18790472c0350d17c7dd4453a0b8de0643c40dd237acbb2`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/34_system2_trajectory_contract/20261106_v1/native-validation/runtimes/dense.json` — SHA256 `abc4c2fc813616950a271b5032fcde174a4f27171ea557aeb988429e274b78d0`；所选字段见机器可读索引。
- `result/34_system2_trajectory_contract/20261106_v1/native-validation/runtimes/released_waypoint_thinning.json` — SHA256 `7a2d3b7a6e89c4003ed20194ba732ea9001d8dcac69c3f54ebcc59d907868dd4`；所选字段见机器可读索引。

## Batch 35

原件根：`/mnt/data/joey_tr/physical-RSI/result/35_system2_postgrasp_diagnosis/20261107_v1`；周志`EXP-2026W45-018`。
协议SHA256：`8503189c0f5d731718f6c16140a9c35fd9fc55aa2dc18642bd95e5ca45e4a56d`。模型：未新生成候选。

development:运行ID[0,1,2]/源ID[0,1,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/offline_contract.py](sources/35/native-validation/offline_contract.py) — SHA256 `9e2ec11de145cfc1b4b5e0d68c2dd1a53d0716da86618bb5406402ce05295a4a`。
- [native-validation/prepare_native.py](sources/35/native-validation/prepare_native.py) — SHA256 `de8097af035e0ab13944b846c4af7c92b9b52cb014aabcecde22c5c1dc0c8c8f`。
- [native-validation/run_native.py](sources/35/native-validation/run_native.py) — SHA256 `c69d1a1fe3cca048a96d0af266f4c834bed6ce591493c930e921858dc58e7e2d`。
- [offline_contract.py](sources/35/offline_contract.py) — SHA256 `9e2ec11de145cfc1b4b5e0d68c2dd1a53d0716da86618bb5406402ce05295a4a`。
- [offline_goal_probe.py](sources/35/offline_goal_probe.py) — SHA256 `440e5a47e345297a10f3a591b7ef7331eac864ff96f43ea5cd0f78a157380056`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/35_system2_postgrasp_diagnosis/20261107_v1/native-validation/native-campaign/runs/logging_only/attempt-001/native/request.json` — SHA256 `2ff444a6c8c73ca52997b8bc77db0622b09b7a5cb7cbb26d843c4ce47526952d`；seed=`0`、gpu索引=`0`、num_envs=`3`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/35_system2_postgrasp_diagnosis/20261107_v1/native-validation/native-campaign/runs/logging_only/attempt-002/native/request.json` — SHA256 `1c8eebc1ab3ace08ce05d1d17d576bf71ff5c6bb5bab7abb33c7cf72d549affb`；seed=`0`、gpu索引=`0`、num_envs=`3`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/35_system2_postgrasp_diagnosis/20261107_v1/goal-probes/gpu-before.json` — SHA256 `df917a151c4c4b99cb8b110e06d47e572e2695fb693aeab2266fbd7453930edb`；所选字段见机器可读索引。
- `result/35_system2_postgrasp_diagnosis/20261107_v1/goal-probes/runtime.json` — SHA256 `da0bc02bff91e8199b4428b24bcc3aaf7f415d7e8b1d30d145072d72f9810f5b`；所选字段见机器可读索引。
- `result/35_system2_postgrasp_diagnosis/20261107_v1/native-validation/runtimes/logging_only-v2.json` — SHA256 `c9e72fb3470bbe61cdc0ffa0d7be4264caba256607c57a20f883bf634d299db0`；所选字段见机器可读索引。
- `result/35_system2_postgrasp_diagnosis/20261107_v1/native-validation/runtimes/logging_only.json` — SHA256 `bbf98be73cb43e808875a4a1d544e4b830f9079d6e9c7097c9b292335f5235c3`；所选字段见机器可读索引。

## Batch 36

原件根：`/mnt/data/joey_tr/physical-RSI/result/36_system2_gripper_command_contract/20261107_v1`；周志`EXP-2026W45-019`。
协议SHA256：`5454b05c4e437949a3754ecafa9e35be2735e2a359964b4bea8f8bcb284e1e52`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/offline_contract.py](sources/36/native-validation/offline_contract.py) — SHA256 `545654e76b91aac14cbb5dc1ea508485732a8a517df245effe12e927c75af09f`。
- [native-validation/prepare_native.py](sources/36/native-validation/prepare_native.py) — SHA256 `742f12e15cb5af57518a54d7d6f618fc46a5c342b2a4f602fe4bfffb5e7ca24d`。
- [native-validation/run_native.py](sources/36/native-validation/run_native.py) — SHA256 `9d5a40131b8f7df8d57fff37410c8aa966464ab84fb25cc169eb342749838e81`。
- [offline_contract.py](sources/36/offline_contract.py) — SHA256 `545654e76b91aac14cbb5dc1ea508485732a8a517df245effe12e927c75af09f`。
- [prepare_native.py](sources/36/prepare_native.py) — SHA256 `742f12e15cb5af57518a54d7d6f618fc46a5c342b2a4f602fe4bfffb5e7ca24d`。
- [run_native.py](sources/36/run_native.py) — SHA256 `9d5a40131b8f7df8d57fff37410c8aa966464ab84fb25cc169eb342749838e81`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/36_system2_gripper_command_contract/20261107_v1/native-validation/native-campaign/runs/latched_command/attempt-001/native/request.json` — SHA256 `6b6247aaf78dbcd6c3fb2ae8ecc1b214c5787b7cf39b3e1e9f4df2c78b2c9d44`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/36_system2_gripper_command_contract/20261107_v1/native-validation/native-campaign/runs/measured_state_control/attempt-001/native/request.json` — SHA256 `058c10c9ce12ffe1e1c3dd43c26ff9b6c3deeec84088be02238a4a2f32b63546`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/36_system2_gripper_command_contract/20261107_v1/native-validation/runtimes/latched_command.json` — SHA256 `ea237cc2b921578e19213af3416db2c36af399151ff951982d3668fe57bd7278`；所选字段见机器可读索引。
- `result/36_system2_gripper_command_contract/20261107_v1/native-validation/runtimes/measured_state_control.json` — SHA256 `326ea0302527c17bb7074585f57106da839b6dbc83b32e116fd2a0519b86fff2`；所选字段见机器可读索引。

## Batch 37

原件根：`/mnt/data/joey_tr/physical-RSI/result/37_system2_candidate_capacity/20261107_v1`；周志`EXP-2026W45-020`。
协议SHA256：`2a6ac7a23af45dfe2db53b8b0371d3fe863af5f3549eb6e2891367d8ccf918f1`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取1份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/run_reference.py](sources/37/native-validation/run_reference.py) — SHA256 `d6f25f9a2e4686f1f237f9dc7612f749e40518c13d27778d91ec90749d7936b8`。
- [native-validation/run_reference_v2.py](sources/37/native-validation/run_reference_v2.py) — SHA256 `146748b7f465b681ec587d9432570db471a12db7ef43ef8ced94057d85a40eab`。
- [run_reference.py](sources/37/run_reference.py) — SHA256 `d6f25f9a2e4686f1f237f9dc7612f749e40518c13d27778d91ec90749d7936b8`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/37_system2_candidate_capacity/20261107_v1/native-validation/native/request.json` — SHA256 `915c5676b70bc6566f513662fce23380562a91f336459d748144e3320aa1399d`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/37_system2_candidate_capacity/20261107_v1/native-validation/environment.json` — SHA256 `cbc5fc768fad35852e6e829f1a7f85f439f1bba71e2c162123a9d52047a3e62d`；所选字段见机器可读索引。
- `result/37_system2_candidate_capacity/20261107_v1/destination-probes/execution/runtime.json` — SHA256 `f3b12712af91fefa146cba83a4b142fdf51bbd56a99cafae63505d9c2dfc4f99`；所选字段见机器可读索引。

## Batch 38

原件根：`/mnt/data/joey_tr/physical-RSI/result/38_system2_transport_destination/20261107_v1`；周志`EXP-2026W45-021`。
协议SHA256：`a18a49f0197b75740613631f9ee221c05b0bbd1d3ad4d8c424597af4559437bc`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/prepare_native.py](sources/38/native-validation/prepare_native.py) — SHA256 `27946a97d223bf0c41e2fafebee8df917d70ca51df0e2232ac0b535e3309dd78`。
- [native-validation/run_native.py](sources/38/native-validation/run_native.py) — SHA256 `b05b2cff73d702d25c9950371c2fbd81ab3b6cbb5e2d7a9376130259f50fdf32`。
- [prepare_native.py](sources/38/prepare_native.py) — SHA256 `27946a97d223bf0c41e2fafebee8df917d70ca51df0e2232ac0b535e3309dd78`。
- [run_native.py](sources/38/run_native.py) — SHA256 `b05b2cff73d702d25c9950371c2fbd81ab3b6cbb5e2d7a9376130259f50fdf32`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/38_system2_transport_destination/20261107_v1/native-validation/native-campaign/runs/offset_transport/attempt-001/native/request.json` — SHA256 `22b2160feb4eee103c0eedd827cfe02774af8de0a9d9a44373b08564746e9c81`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/38_system2_transport_destination/20261107_v1/native-validation/native-campaign/runs/original_transport/attempt-001/native/request.json` — SHA256 `c415b935792e657e67bc44abce2036135e9b5805ec9583db42a8fd19b74665a4`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/38_system2_transport_destination/20261107_v1/native-validation/runtimes/offset_transport.json` — SHA256 `af012f3a742edabec0b8b0c91d4eaa600d9e5339435efe69a9f1676ee450a6d8`；所选字段见机器可读索引。
- `result/38_system2_transport_destination/20261107_v1/native-validation/runtimes/original_transport.json` — SHA256 `0d3e6fe0be99a4df9dd4a180676457cafd50e5df81c56c37b2b1bd38125dd038`；所选字段见机器可读索引。

## Batch 39

原件根：`/mnt/data/joey_tr/physical-RSI/result/39_system2_observation_loop/20261107_v1`；周志`EXP-2026W45-022`。
协议SHA256：`180cf1e785aad457507bc0b9447755bc68f19f9918a2f0bc04c74224aa5d411e`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取1份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/prepare_native.py](sources/39/native-validation/prepare_native.py) — SHA256 `426d1e2ebf55bfd1ae328655981ece5dc2d907f7efd717cfd2fca2e446d3d217`。
- [native-validation/run_native.py](sources/39/native-validation/run_native.py) — SHA256 `5edaf5677ccc67b504c8fc231ec04e3778d4e9a226f4d669063ca83daf20e5c5`。
- [prepare_native.py](sources/39/prepare_native.py) — SHA256 `426d1e2ebf55bfd1ae328655981ece5dc2d907f7efd717cfd2fca2e446d3d217`。
- [run_native.py](sources/39/run_native.py) — SHA256 `5edaf5677ccc67b504c8fc231ec04e3778d4e9a226f4d669063ca83daf20e5c5`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/39_system2_observation_loop/20261107_v1/native-validation/native-campaign/runs/fixed_six_turns/attempt-001/native/request.json` — SHA256 `91aac52cb21a51fdf60733022dd85348c9731457c203b33191709014d0df2924`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/39_system2_observation_loop/20261107_v1/native-validation/runtimes/fixed_six_turns.json` — SHA256 `5cd5280caf01cf12d972ad850f80a6e262921e7df08166cf96bad3aa17fd6a65`；所选字段见机器可读索引。
- `result/39_system2_observation_loop/20261107_v1/offline-rejection-probes/execution/runtime.json` — SHA256 `f3b12712af91fefa146cba83a4b142fdf51bbd56a99cafae63505d9c2dfc4f99`；所选字段见机器可读索引。

## Batch 40

原件根：`/mnt/data/joey_tr/physical-RSI/result/40_system2_rejection_contract/20261107_v1`；周志`EXP-2026W45-023`。
协议SHA256：`5c674832fe746802b3c517abd9a4a61256d163070116482d8d555f9ae9a2c5de`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/prepare_native.py](sources/40/native-validation/prepare_native.py) — SHA256 `48412a1d201abedc8b7fe6455ca47870ded1048277272663c1efe9272484cf2c`。
- [native-validation/run_native.py](sources/40/native-validation/run_native.py) — SHA256 `6b6be5bc3811f61823412a10d026385df4d2a1ad0bb2fb1468d672f9328c692a`。
- [prepare_native.py](sources/40/prepare_native.py) — SHA256 `48412a1d201abedc8b7fe6455ca47870ded1048277272663c1efe9272484cf2c`。
- [run_native.py](sources/40/run_native.py) — SHA256 `6b6be5bc3811f61823412a10d026385df4d2a1ad0bb2fb1468d672f9328c692a`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/40_system2_rejection_contract/20261107_v1/native-validation/native-campaign/runs/structured_rejection/attempt-001/native/request.json` — SHA256 `2d2b80795b77a0af4c97245fe9d1a0b3c9158865cada760b5139a5baab7c11a6`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/40_system2_rejection_contract/20261107_v1/native-validation/native-campaign/runs/structured_rejection/attempt-002/native/request.json` — SHA256 `1a80159509ce2d14082736f4b4e570994f20ef4ddb8c42331143b6368079de26`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/40_system2_rejection_contract/20261107_v1/native-validation/runtimes/structured_rejection.json` — SHA256 `8ea02af77ed249c7ad39639b0f7683a731f8ae2662b69493cd83bb0b5f32fd15`；所选字段见机器可读索引。
- `result/40_system2_rejection_contract/20261107_v1/native-validation/runtimes/structured_rejection_v2.json` — SHA256 `d552f95232db6166d21824d7ff0d17a1845e5dc6615cf9a364974b96f9b56459`；所选字段见机器可读索引。

## Batch 41

原件根：`/mnt/data/joey_tr/physical-RSI/result/41_system2_skill_chain_floor/20261107_v1`；周志`EXP-2026W45-024`。
协议SHA256：`b78df85684a6450ceb80eee14a1cbd51206275e4b3faf0af8ca6a3d5ecf754a2`。模型：未新生成候选。

development:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取2份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

保存硬件事实：/gpu_provenance=NVIDIA L20, 580.126.09, 49140 MiB；逐件来源见复现索引。本次归档只做CPU读取，未据历史GPU状态启动作业。

### 已保存源码入口

- [native-validation/prepare_native.py](sources/41/native-validation/prepare_native.py) — SHA256 `113dead45979006dbbf0b0514c482ad13c66c3393281431391ca8cb7728762f3`。
- [native-validation/reference/run_reference.py](sources/41/native-validation/reference/run_reference.py) — SHA256 `70a26d2a1e1e2ec036c1154c534d05b48a9f8e39635b05a49e55c534c0218199`。
- [native-validation/run_native.py](sources/41/native-validation/run_native.py) — SHA256 `7ef7975229bf6c15add45c70f404d53f9808d0893ae5147d4674f74b87d13ca7`。
- [native-validation/run_route.py](sources/41/native-validation/run_route.py) — SHA256 `ee5c2088299503d4de3e269212eb0438e0258d7586336c4ed5f69e65ecab31ca`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/41_system2_skill_chain_floor/20261107_v1/native-validation/native-campaign/runs/single_cycle/attempt-001/native/request.json` — SHA256 `7db501fccf610d78d790372c9f3ec2a7d61d6c2cb2ee73128e3506f43c69ba35`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/41_system2_skill_chain_floor/20261107_v1/native-validation/reference/native/request.json` — SHA256 `701fb35c42b025456a4fe0ca179ba9972506a7e74dfbd9f7ad8fbafe5c0a477f`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/41_system2_skill_chain_floor/20261107_v1/native-validation/environment-current.json` — SHA256 `4b0a5756d5c04f164be6cccec44fa71fc0520afca61833569ca9910b086729ed`；所选字段见机器可读索引。
- `result/41_system2_skill_chain_floor/20261107_v1/native-validation/preflight-binding.json` — SHA256 `f5743bd647fef09b66d0a4850471d9e67306974cb06fbcc35a255ec46dc21f38`；所选字段见机器可读索引。
- `result/41_system2_skill_chain_floor/20261107_v1/native-validation/reference/environment.json` — SHA256 `b1c8bb2da1c3e8ed9be031c467271f8c64dbafe700d54ca9399d1e0705f9be53`；所选字段见机器可读索引。
- `result/41_system2_skill_chain_floor/20261107_v1/native-validation/runtimes/single_cycle.json` — SHA256 `34e22642c20e427b5c2405aa2dc015ea1661f63fee8981606c916cd29dfb6aa7`；所选字段见机器可读索引。

## Batch 42

原件根：`/mnt/data/joey_tr/physical-RSI/result/42_system2_search_execution_controls/20261107_v1`；周志`EXP-2026W45-025`。
协议SHA256：`9aa00cde30fcc9ca4a3d020d334b07c0569bf3c58829937c02d582ed6a3838bf`。模型：gpt-6.1-sol/high，max_completion_tokens=16000。

heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；repair:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；round2:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；sampling:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects原生1100步。

已读取3份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/heldout/run_native.py](sources/42/native-validation/heldout/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [native-validation/parent/run_native.py](sources/42/native-validation/parent/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [native-validation/prepare_phase.py](sources/42/native-validation/prepare_phase.py) — SHA256 `8da09db00584251717033374f6fb47c9856a709c754f0e3d2a18543fff181733`。
- [native-validation/repair/run_native.py](sources/42/native-validation/repair/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [native-validation/round2/run_native.py](sources/42/native-validation/round2/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [native-validation/run_generation.py](sources/42/native-validation/run_generation.py) — SHA256 `aa8c7cdfd1895f64ef5e0ec6c70f8aec6d64212adb91e2e318628f097209d853`。
- [native-validation/run_phase.py](sources/42/native-validation/run_phase.py) — SHA256 `ff458b38da207e38963223849a1f9e274e17ac0ff4dc520bd531e18688b69aa5`。
- [native-validation/sampling/run_native.py](sources/42/native-validation/sampling/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [native-validation/templates/run_native.py](sources/42/native-validation/templates/run_native.py) — SHA256 `f424e5c4709f433bc038942b4cebb34d3f06462dbd0a0a5fcae458e2a2df0090`。
- [run_generation.py](sources/42/run_generation.py) — SHA256 `aa8c7cdfd1895f64ef5e0ec6c70f8aec6d64212adb91e2e318628f097209d853`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/native-campaign/runs/fixed_parent/attempt-001/native/request.json` — SHA256 `d188666ad8b42fec36f49c8eb31b3a643f265cf691434f972a3ea9337e8a5111`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/native-campaign/runs/target_control/attempt-001/native/request.json` — SHA256 `387b05511d36ab4637e7dee74397aa5fbc785f4fd5a6059bb93400700c8af132`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/native-campaign/runs/target_offset/attempt-001/native/request.json` — SHA256 `58043f602055eda4b831c5208107e1aff405edd973ae5fcd7def28d92ab09562`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/runtimes/fixed_parent.json` — SHA256 `40098d9e719869ecd7567ae4818e04d01f1bf0e6c55bf78df48bc19fff687f02`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/runtimes/target_control.json` — SHA256 `f9144be9432787ad0cf067893747167a6fd1ce9c80026c8ce88ac9172e186db4`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/heldout/runtimes/target_offset.json` — SHA256 `71f0e4d4e764028122fc1019a9f726b5945e92f45e9db9adc9cb9761aa8e6c31`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/parent/runtimes/fixed_parent.json` — SHA256 `599b49b7b0eb9b73094896b3162ba2395b52d711db7fea65bd8fa3677e3888d7`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/repair/runtimes/target_control.json` — SHA256 `8c07907f885e165e22dac5e9bd1bb43d34a904aad0cfeeb87049edf37be0eee1`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/repair/runtimes/target_offset.json` — SHA256 `5d84c1743e11930c01cc6422d9fc13ac7891478ad2c8602b54964b9adea76974`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/round2/runtimes/round2_01.json` — SHA256 `a9fe02939229eb30aadb323c79c5d39141ded44f8f15a22bfcdf6e5d3f16bf56`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/sampling/runtimes/sample_01.json` — SHA256 `71bf5218d0e1572107976ccdbab2c2f8315759f688b3124bfcf1a1b82f884613`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/sampling/runtimes/sample_02.json` — SHA256 `7b5234da479b6b24988d113657fa87912b5bfa15cb4355250d4940cde672c8d8`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/sampling/runtimes/sample_03.json` — SHA256 `b5e572ea2e0872304635faab62f4f437d3df221b625d494878beb10de2197b66`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/sampling/runtimes/sample_04.json` — SHA256 `e7203e0bedf8cacdb447b75f0fafd381f7394cd8cfc66214e4bbf27555e904dc`；所选字段见机器可读索引。
- `result/42_system2_search_execution_controls/20261107_v1/native-validation/sampling/runtimes/sample_05.json` — SHA256 `5fae13c1f4e7ba4be6368b1e507e04d4f416a0ccb63903372c6edcc44a251b7e`；所选字段见机器可读索引。

## Batch 43

原件根：`/mnt/data/joey_tr/physical-RSI/result/43_system2_multitask/20261108_v1`；周志`EXP-2026W45-026`。
协议SHA256：`55c2ea848f3031b4b773c1a65eda99de7f8ec98a42a118651acb44f6470d033d`。模型：gpt-6.1-sol/high，max_completion_tokens=16000。

classify_objects-candidates:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects-heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；classify_objects-parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-candidates:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-heldout:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-parent:运行ID[0,1,2,3,4]/源ID[0,1,2,3,4]；general_pickup-smoke:运行ID[0]/源ID[0]；分类1100步/抓取200步，heldout中断布局保留null。

已读取7份本批native/request.json，记录原生执行seed=[0]；逐件路径/SHA见复现索引。这不是布局生成seed；场景以各阶段layout ID与SHA256绑定，不把求解器seed或重复布局当成独立场景。

本批runtime配置/gpu=0,/resources/gpu=1（设备索引/资源数，不是GPU型号）；窄读取未单独确认物理型号。原生执行与gpuserver3档案归档分开，本次整理无GPU作业。

### 已保存源码入口

- [native-validation/classify_objects-candidates/run_native.py](sources/43/native-validation/classify_objects-candidates/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/classify_objects-heldout/run_native.py](sources/43/native-validation/classify_objects-heldout/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/classify_objects-parent/run_native.py](sources/43/native-validation/classify_objects-parent/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/general_pickup-candidates/run_native.py](sources/43/native-validation/general_pickup-candidates/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/general_pickup-heldout/run_native.py](sources/43/native-validation/general_pickup-heldout/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/general_pickup-parent/run_native.py](sources/43/native-validation/general_pickup-parent/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/general_pickup-smoke/run_native.py](sources/43/native-validation/general_pickup-smoke/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [native-validation/preparation-source-history/a831cf293ec756daa40e87b231b5285c9d9f3d705ea1e5d183cc960cd4ae9598/run_phase.py](sources/43/native-validation/preparation-source-history/a831cf293ec756daa40e87b231b5285c9d9f3d705ea1e5d183cc960cd4ae9598/run_phase.py) — SHA256 `a831cf293ec756daa40e87b231b5285c9d9f3d705ea1e5d183cc960cd4ae9598`。
- [native-validation/preparation-source-history/ff62118945a13f27fe750c2ee677ea716ea3dc7ce230141c73f825b8afbcc8f4/prepare_phase.py](sources/43/native-validation/preparation-source-history/ff62118945a13f27fe750c2ee677ea716ea3dc7ce230141c73f825b8afbcc8f4/prepare_phase.py) — SHA256 `ff62118945a13f27fe750c2ee677ea716ea3dc7ce230141c73f825b8afbcc8f4`。
- [native-validation/prepare_phase.py](sources/43/native-validation/prepare_phase.py) — SHA256 `3a2954bf45205b00cbed601db3e99b498d48ad49aba52299a7dd461544ef3188`。
- [native-validation/run_phase.py](sources/43/native-validation/run_phase.py) — SHA256 `eccdd79636e8c3b5435ab82218b0bdb717b4deb5b3177c3f73c3cf3080ca73c8`。
- [native-validation/templates/run_native.py](sources/43/native-validation/templates/run_native.py) — SHA256 `4dd201b72370ed99531467f1354867b6e4ab9dfb091db2620acfca68aca05702`。
- [run_generation.py](sources/43/run_generation.py) — SHA256 `c516c1a84cb65ea02082a94cdd5d591ede12b3e0609b1e31ea7fa7e6172af748`。

### 保存的进程参数

本次选取原件中未找到完整启动argv。只确认以上源码入口和配置，不推造shell命令。

### 配置/环境字段的原件绑定

- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/native-campaign/runs/classify_objects-basic-1/attempt-001/native/request.json` — SHA256 `1aa35a63036d272c17be9499550ebac379bae95b5861d6e123831d07d32e5d6d`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/classify_objects-heldout/native-campaign/runs/parent/attempt-001/native/request.json` — SHA256 `21965d315b71d987b50c4d3083886e5e82e11410e37ddd1924d72a699622b535`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/classify_objects-parent/native-campaign/runs/parent/attempt-001/native/request.json` — SHA256 `d48f0807cffdbb2af8e4d0013c2cbd87b7a66a1f2ea71dab1df255ef6757d3a3`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`classify_objects`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/native-campaign/runs/general_pickup-basic-1/attempt-001/native/request.json` — SHA256 `2834aebd7bcb27aba2238cc92ba075ae30352989fa92259db20ed7766ffdc1a9`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`general_pickup`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/general_pickup-heldout/native-campaign/runs/parent/attempt-001/native/request.json` — SHA256 `c608d583115a7f59add643c5fd80cff1646b02bf7ef443dcc215b995e09e51a2`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`general_pickup`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/general_pickup-parent/native-campaign/runs/parent/attempt-001/native/request.json` — SHA256 `aea2c20d241d73428e68a044a0d2feb77c0ea446cc26b9ebd940deb999f17a03`；seed=`0`、gpu索引=`0`、num_envs=`5`、task=`general_pickup`。这是原记录的选取字段，完整原件未因此改写。
- 原生request：`result/43_system2_multitask/20261108_v1/native-validation/general_pickup-smoke/native-campaign/runs/parent/attempt-001/native/request.json` — SHA256 `bf9ff0693140cf2e0dcd51eb9f1bb1d397fea2d8aa29846c6f35f3aff67adc7b`；seed=`0`、gpu索引=`0`、num_envs=`1`、task=`general_pickup`。这是原记录的选取字段，完整原件未因此改写。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-basic-1.json` — SHA256 `04ec18fe90e19e7299ccb0d4f77746db11b99c24a203f7254b43d51b5499e24e`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-basic-2.json` — SHA256 `3823b77f2dc53568c89ac442356383333de6070ee603cd1c1ea21dc94f48b018`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-basic-3.json` — SHA256 `4eb97eb4b402475f8001d5d01484be58ee15430c576fdda54dc7d23e7bd06b29`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-execution_feedback-1.json` — SHA256 `49d09d1d368bcadd189dfef7768d7f94974c6034d67eee743b9b9a58a24a822a`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-execution_feedback-2.json` — SHA256 `079f4ce83fce133fd7bd803c05f35bb2cbc78beeac76f2d142e56d3f563c8b54`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-candidates/runtimes/classify_objects-execution_feedback-3.json` — SHA256 `6c92818883b23d037b8d79f8f58878fe49d8c170e3ce53eeb11adb9e604dd57b`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-heldout/runtimes/parent.json` — SHA256 `a3842c8e63d720cf2f69c340cb1e2bb00838fd3a714d88bfa6bcd7a774ab6053`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/classify_objects-parent/runtimes/parent.json` — SHA256 `4489e9812268c5e577e6e21bc4076a6522f66f49eceec73e6198ff52dc90a207`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-basic-1.json` — SHA256 `9602c9a20122aecb794670f4b270cfd7780918d2e8f2f0b5e9c0bdfab98b2443`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-basic-2.json` — SHA256 `9a5c5d0cc62c0976f1342c35b7e31e96b438788d0db6fbfbe6737fcaae0382a2`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-basic-3.json` — SHA256 `04cee02505af48ad1a10918f01e1c32f6a11a9de3bab7bcdd555e5470af862ac`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-execution_feedback-1.json` — SHA256 `c281a53bab746b351687d2ed42078fc1b690440358e7f46984a7986ef3732290`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-execution_feedback-2.json` — SHA256 `96f926913e0d5ec6ce20f61b9a4d1a6430ac1c6bb99ffe4fd4576ee841dacaac`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-candidates/runtimes/general_pickup-execution_feedback-3.json` — SHA256 `daaa8a342f5a1478663c6a7a222f66ab05839d0440bfe41811a846ba12f18801`；所选字段见机器可读索引。
- `result/43_system2_multitask/20261108_v1/native-validation/general_pickup-heldout/runtimes/parent.json` — SHA256 `89340099bb552de675d6869bd152a3ca0fb55838bad6f11961911134b99581cc`；所选字段见机器可读索引。
