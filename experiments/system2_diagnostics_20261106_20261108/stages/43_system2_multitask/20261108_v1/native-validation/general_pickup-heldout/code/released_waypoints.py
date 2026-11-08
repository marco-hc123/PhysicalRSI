"""Thin only public native planner samples, preserving bends and endpoint gates."""
import numpy as np


def thin_native_path(path, current, max_joint_step=.12, chord_tolerance=.01):
    path = np.asarray(path, dtype=np.float64)
    current = np.asarray(current, dtype=np.float64)
    if path.ndim != 2 or len(path) == 0 or not np.isfinite(path).all():
        raise RuntimeError('invalid native joint path')
    selected = []
    anchor = current
    begin = 0
    deviations = []
    while begin < len(path):
        chosen = begin
        chosen_deviation = 0.
        for end in range(begin, len(path)):
            delta = path[end] - anchor
            if np.max(np.abs(delta)) > max_joint_step:
                break
            segment = path[begin:end + 1] - anchor
            length2 = float(delta @ delta)
            alpha = np.clip(segment @ delta / length2, 0., 1.) if length2 > 1e-16 else np.zeros(len(segment))
            deviation = float(np.max(np.abs(segment - alpha[:, None] * delta)))
            if deviation > chord_tolerance:
                break
            chosen, chosen_deviation = end, deviation
        selected.append(chosen)
        deviations.append(chosen_deviation)
        anchor = path[chosen]
        begin = chosen + 1
    chosen_path = np.vstack([current, path[selected]])
    jumps = np.max(np.abs(np.diff(chosen_path, axis=0)), axis=1)
    return selected, dict(max_joint_step_rad=max_joint_step, chord_tolerance_rad=chord_tolerance,
                          max_selected_joint_delta_rad=float(jumps.max()),
                          max_chord_deviation_rad=max(deviations),
                          native_adjacent_over_bound=int((jumps > max_joint_step + 1e-7).sum()))
