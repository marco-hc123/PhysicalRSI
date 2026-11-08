"""Official RGB observation boundary and natural episode loop."""


def public(obs):
    return {
        'vision': {name: {'color': value['color']} for name, value in obs['vision'].items()},
        'state': obs['state'],
        'instruction': obs['instruction'],
        'env_idx': obs.get('env_idx', 0),
    }


def eval_one_episode_batch(TASK_ENV, model_client):
    model_client.call(func_name='reset')
    while not TASK_ENV.is_episode_end():
        indices = list(TASK_ENV.get_running_env_idx_list())
        observations = [public(obs) for obs in TASK_ENV.get_obs_batch(indices)]
        model_client.call(func_name='update_obs_batch', obs=observations)
        chunks = model_client.call(func_name='get_action_batch', obs=indices)
        for step in range(len(chunks[0])):
            running = set(TASK_ENV.get_running_env_idx_list())
            positions = [position for position, index in enumerate(indices) if index in running]
            if not positions:
                break
            TASK_ENV.take_action_batch(
                [chunks[position][step] for position in positions],
                [indices[position] for position in positions],
            )
            if TASK_ENV.is_episode_end():
                break
    model_client.call(func_name='reset')
    print('CLASSIFY_OBJECTS_NATURAL_END', flush=True)


def eval_one_episode(TASK_ENV, model_client):
    return eval_one_episode_batch(TASK_ENV, model_client)
