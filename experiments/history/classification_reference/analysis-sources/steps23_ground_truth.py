def ground_truth(env, phase):
    """Read-only native diagnostics. Never inject truth into observations/actions."""
    if os.environ.get('PHYSICALRSI_LOG_GT') != '1': return
    tick=time.monotonic()
    row=dict(phase=phase, layout=episode['layout'], episode_index=episode['index'],
             steps=list(env.take_action_cnt), monotonic=tick, objects=[],
             scope='Observer-only ground truth; not sent to policy')
    try:
        lm=env.scene_manager.layout_manager
        parser=env.reward_manager.func_parser
        for category in range(3):
            for label in lm.get_labels_by_prefix(0, 'cat'+str(category)):
                pos,rot=lm.get_instance_pose(env_idx=0,label=label)
                matrix=[parser.is_A_in_B(dict(env_idx=0,label_A=label,label_B='basket'+str(b))) for b in range(3)]
                settled=[parser.is_A_z_lower_than_B_bbox_zmax(dict(env_idx=0,label_A=label,label_B='basket'+str(b),z_threshold=0.01)) for b in range(3)]
                row['objects'].append(dict(label=label,category=category,position=list(map(float,pos)),
                    orientation=list(map(float,rot)),in_basket=matrix,below_basket_top=settled))
        row['home']=parser.all_robot_back_to_origin(dict(env_idx=0,pos_threshold=0.15,rot_threshold=20))
        row['grippers_open']=parser.is_all_gripper_open(dict(env_idx=0,open_threshold=0.8))
        row['native_success_flags']=list(env.success)
    except Exception as exc:
        row['error']=type(exc).__name__+': '+str(exc)
    row['observer_seconds']=time.monotonic()-tick
    with (OUT/'ground-truth.jsonl').open('a') as f:
        f.write(json.dumps(row,default=lambda v:v.item() if hasattr(v,'item') else str(v))+'\n')
