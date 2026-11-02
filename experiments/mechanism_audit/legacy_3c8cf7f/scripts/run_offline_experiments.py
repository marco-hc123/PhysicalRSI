#!/usr/bin/env python3
"""Offline mechanism checks, surrogate CPU control, and hypothetical amortization.

No model, network, GPU, or simulator is required. NumPy is required by the
real project's package initialization; see requirements-offline.txt.
The real AgentLoop and counter classes are imported from an included source
snapshot when available, otherwise from the surrounding PhysicalRSI checkout.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter

sys.dont_write_bytecode = True


def source_root():
    bundle = Path(__file__).resolve().parents[1]
    candidates = [bundle / "sources" / "code", *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "PhysicalRSI_baselines/robodojo/agent_planner.py").is_file() and (
            candidate / "PhysicalRSI_demos/experiment.py"
        ).is_file():
            return candidate
    raise RuntimeError("PhysicalRSI source checkout or result/sources/code is required")


SOURCE_ROOT = source_root()
sys.path.insert(0, str(SOURCE_ROOT))

from PhysicalRSI_baselines.robodojo.agent_planner import AgentLoop  # noqa: E402
from PhysicalRSI_demos.experiment import CounterEnvironment, CounterVerifier  # noqa: E402


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class CountingPlanner:
    """Scripted stand-in: counts logical planning; does not invoke a model."""

    def __init__(self):
        self.calls = 0

    def plan(self, **kwargs):
        self.calls += 1
        return {"subgoal": "Advisory continuation for " + kwargs["instruction"]}


def scheduling_experiment(data):
    configurations = [
        dict(name=f"grid-h{horizon}-i{interval}-c{cap}", horizon=horizon,
             interval=interval, cap=cap, episodes=1, environments=1, change_at=None)
        for horizon in (1, 10, 100, 1000)
        for interval in (1, 10, 100)
        for cap in (1, 100000)
    ]
    configurations += [
        dict(name=f"reset-multienv-c{cap}", horizon=12, interval=10, cap=cap,
             episodes=3, environments=3, change_at=None)
        for cap in (1, 100000)
    ]
    configurations += [
        dict(name=f"instruction-change-c{cap}", horizon=10, interval=100, cap=cap,
             episodes=1, environments=2, change_at=3)
        for cap in (1, 100000)
    ]
    rows = []
    event_count = 0
    with (data / "scheduling_events.jsonl").open("w", encoding="utf-8") as stream:
        for config in configurations:
            planner = CountingPlanner()
            receipts = []
            loop = AgentLoop(planner, {"scope": "offline-check"}, receipts.append,
                             replan_interval=config["interval"],
                             max_calls_per_episode=config["cap"])
            calls_by_episode = []
            changed_without_replan = 0
            start = perf_counter()
            for episode in range(config["episodes"]):
                loop.reset()
                assert not loop.calls and not loop.previous and not loop.ready
                initial_calls = planner.calls
                for step in range(config["horizon"]):
                    instruction = "reach original goal"
                    if config["change_at"] is not None and step >= config["change_at"]:
                        instruction = "reach changed goal"
                    observations = [dict(env_idx=index, instruction=instruction,
                                         state={"counter": step, "episode": episode})
                                    for index in range(config["environments"])]
                    before = deepcopy(observations)
                    call_counts = dict(loop.calls)
                    returned = loop.prepare(observations)
                    assert returned == before
                    assert all(actual is original for actual, original in zip(returned, observations))
                    for index in range(config["environments"]):
                        called = loop.calls[index] - call_counts.get(index, 0)
                        assert called in (0, 1)
                        if step == config["change_at"] and not called:
                            changed_without_replan += 1
                        event = dict(scenario=config["name"], episode=episode,
                                     env_idx=index, zero_based_step=step,
                                     instruction=instruction, logical_planner_calls=called,
                                     episode_calls=loop.calls[index],
                                     age_before_consume=loop.ages[index],
                                     original_policy_observation_preserved=True,
                                     previous_advisory_plan=deepcopy(loop.previous[index]),
                                     real_model_called=False)
                        stream.write(json.dumps(event, sort_keys=True) + "\n")
                        event_count += 1
                    loop.consume(range(config["environments"]))
                calls_by_episode.append(planner.calls - initial_calls)
            elapsed_ms = (perf_counter() - start) * 1000
            if config["change_at"] is None:
                expected_per_episode = min(config["cap"], math.ceil(config["horizon"] / config["interval"])) * config["environments"]
            else:
                expected_per_episode = min(config["cap"], 2) * config["environments"]
            expected = expected_per_episode * config["episodes"]
            assert planner.calls == expected == len(receipts)
            assert calls_by_episode == [expected_per_episode] * config["episodes"]
            rows.append(dict(
                scenario=config["name"], horizon_chunks_per_episode=config["horizon"],
                replan_interval=config["interval"], max_calls_per_episode=config["cap"],
                episodes=config["episodes"], environments=config["environments"],
                instruction_change_at=config["change_at"] if config["change_at"] is not None else "",
                total_observed_env_chunks=config["horizon"] * config["episodes"] * config["environments"],
                measured_logical_planner_calls=planner.calls, expected_calls=expected,
                changed_instruction_without_replan=changed_without_replan,
                original_policy_observation_preserved=True,
                local_ms_including_event_serialization=round(elapsed_ms, 6),
                real_model_calls=0, actual_model_tokens="not_measured",
            ))
    write_csv(data / "scheduling.csv", rows)
    return rows, event_count


class ScriptedController:
    """Exact-dynamics feedback controller with adjustable observation-use cadence.

    Its inputs are only the public current position and fixed target. It receives
    no scenario identifier, random seed, disturbance schedule, or future state.
    The queued open-loop program is intentionally static after first planning;
    this is one possible skill design, not a statement that all skills are open loop.
    """

    def __init__(self, interval, target, horizon, *, local_feedback=False):
        self.interval, self.target, self.horizon = interval, target, horizon
        self.calls = 0
        self.local_feedback = local_feedback
        self.local_feedback_updates = 0
        self.observation_conditioned_decisions = 0
        self.queue = []

    def act(self, observation):
        if self.local_feedback:
            # A single high-level binding selects a prewritten feedback skill;
            # numeric updates stay inside that skill. This is a declared
            # architecture boundary, not observed LLM usage.
            if not self.calls:
                self.calls = 1
            self.local_feedback_updates += 1
            self.observation_conditioned_decisions += 1
            return min(3, max(0, self.target - observation["position"]))
        if not self.queue:
            self.calls += 1
            self.observation_conditioned_decisions += 1
            predicted = observation["position"]
            count = self.horizon if self.interval is None else self.interval
            for _ in range(count):
                action = min(3, max(0, self.target - predicted))
                self.queue.append(action)
                predicted += action
        return self.queue.pop(0)


def make_case(seed, family):
    rng = random.Random(seed)
    target = rng.randint(20, 32)
    magnitude = rng.randint(1, 4)
    disturbance_step = 3
    delta = 0
    if family == "early_forward":
        delta = magnitude
    elif family == "early_backward":
        delta = -magnitude
    elif family == "late_forward":
        delta = magnitude
        disturbance_step = math.ceil(target / 3) - 1
    elif family != "static":
        raise ValueError("Unknown deterministic scenario family")
    return dict(initial=0, target=target, budget=20,
                disturbances={} if not delta else {disturbance_step: delta})


def run_control_case(seed, family, arm, interval, local_feedback=False):
    case = make_case(seed, family)
    env = CounterEnvironment()
    controller = ScriptedController(interval, case["target"], case["budget"],
                                    local_feedback=local_feedback)
    initial = env.reset({"initial": case["initial"], "target": case["target"]}, None)
    observation = initial["observation"]
    trace = [dict(observation=deepcopy(observation))]
    events = []
    start = perf_counter()
    for step in range(1, case["budget"] + 1):
        # This harness alone knows exogenous changes. It uses the original
        # counter transition method, then exposes the changed public state to
        # every arm before action selection. No controller sees future events.
        delta = case["disturbances"].get(step, 0)
        if delta:
            observation = env.step(delta, None)["observation"]
        public_observation = deepcopy(observation)
        old_calls = controller.calls
        old_feedback_updates = controller.local_feedback_updates
        action = controller.act(public_observation)
        assert public_observation == observation
        assert type(action) is int and 0 <= action <= 3
        result = env.step(action, None)
        observation = result["observation"]
        trace.append(dict(observation=deepcopy(observation)))
        events.append(dict(step=step, exogenous_increment=delta,
                           public_observation=public_observation,
                           scripted_planner_called=controller.calls > old_calls,
                           local_feedback_updated=controller.local_feedback_updates > old_feedback_updates,
                           action=action, result=deepcopy(result)))
        if result["terminated"]:
            break
    elapsed_ms = (perf_counter() - start) * 1000
    verdict = CounterVerifier().verify({"target": case["target"]}, trace)
    row = dict(
        family=family, seed=seed, arm=arm, target=case["target"],
        budget_steps=case["budget"], action_bound=3,
        refresh_interval="local_skill_every_step" if local_feedback else ("episode_start_only" if interval is None else interval),
        disturbance_step=next(iter(case["disturbances"]), ""),
        disturbance_delta=next(iter(case["disturbances"].values()), 0),
        scripted_planning_calls=controller.calls,
        local_feedback_updates=controller.local_feedback_updates,
        observation_conditioned_decisions=controller.observation_conditioned_decisions,
        public_observations_received=len(events), steps=len(events),
        final_position=observation["position"], success=verdict["outcome"] == "success",
        terminated_by_environment=events[-1]["result"]["terminated"],
        local_ms=round(elapsed_ms, 6), real_model_calls=0,
        actual_model_tokens="not_measured", scope="synthetic_counter_control_surrogate",
    )
    return row, dict(family=family, seed=seed, arm=arm, case=case,
                    verdict=verdict, events=events)


def cpu_experiment(data):
    seeds = list(range(32))
    arms = [("every_step_feedback", 1, False), ("every_four_steps_feedback", 4, False),
            ("one_open_loop_program", None, False), ("one_closed_loop_skill", None, True)]
    families = ("static", "early_forward", "early_backward", "late_forward")
    rows, trajectories = [], []
    # Deterministically rotate arm execution order to avoid assigning every
    # warm/cold timing effect to the same arm. Timing remains descriptive only.
    for family in families:
        for seed in seeds:
            rotation = seed % len(arms)
            for arm, interval, local_feedback in arms[rotation:] + arms[:rotation]:
                row, trajectory = run_control_case(seed, family, arm, interval, local_feedback)
                rows.append(row)
                trajectories.append(trajectory)
    rows.sort(key=lambda row: (row["family"], row["seed"], row["arm"]))
    groups = defaultdict(list)
    for row in rows:
        groups[(row["family"], row["arm"])].append(row)
    aggregate = []
    for (family, arm), values in sorted(groups.items()):
        aggregate.append(dict(
            family=family, arm=arm, episodes=len(values),
            successes=sum(row["success"] for row in values),
            success_rate=sum(row["success"] for row in values) / len(values),
            mean_scripted_planning_calls=statistics.mean(row["scripted_planning_calls"] for row in values),
            mean_local_feedback_updates=statistics.mean(row["local_feedback_updates"] for row in values),
            mean_observation_conditioned_decisions=statistics.mean(row["observation_conditioned_decisions"] for row in values),
            mean_steps=statistics.mean(row["steps"] for row in values),
            median_local_ms=statistics.median(row["local_ms"] for row in values),
        ))
    for row in rows:
        if row["family"] == "static" or row["arm"] in {"every_step_feedback", "one_closed_loop_skill"}:
            assert row["success"], row
        if row["arm"] in {"one_open_loop_program", "one_closed_loop_skill"}:
            assert row["scripted_planning_calls"] == 1
        if row["arm"] == "one_closed_loop_skill":
            assert row["local_feedback_updates"] == row["steps"]
        else:
            assert row["local_feedback_updates"] == 0
    paired = []
    by_key = {(row["family"], row["seed"], row["arm"]): row for row in rows}
    trace_by_key = {(row["family"], row["seed"], row["arm"]): row for row in trajectories}
    for family in families:
        for seed in seeds:
            reference = trace_by_key[(family, seed, "every_step_feedback")]
            skill = trace_by_key[(family, seed, "one_closed_loop_skill")]
            def executed_trace(trajectory):
                return [{key: event[key] for key in (
                    "step", "exogenous_increment", "public_observation", "action", "result"
                )} for event in trajectory["events"]]
            assert executed_trace(reference) == executed_trace(skill)
    for family in families:
        for arm, _, _ in arms[1:]:
            reference = [by_key[(family, seed, arms[0][0])] for seed in seeds]
            comparison = [by_key[(family, seed, arm)] for seed in seeds]
            paired.append(dict(family=family, reference_arm=arms[0][0], compared_arm=arm,
                               both_succeed=sum(a["success"] and b["success"] for a, b in zip(reference, comparison)),
                               reference_only_succeeds=sum(a["success"] and not b["success"] for a, b in zip(reference, comparison)),
                               comparison_only_succeeds=sum(not a["success"] and b["success"] for a, b in zip(reference, comparison)),
                               both_fail=sum(not a["success"] and not b["success"] for a, b in zip(reference, comparison))))
    summary = dict(
        schema="physicalrsi.offline-counter-surrogate/v1", seeds=seeds,
        scope="Original counter transitions and verifier with a synthetic disturbance harness and scripted controllers; not a native PhysicalRSI robot benchmark.",
        controllers_receive="Only the same public current position and fixed target; no seed, family, disturbance schedule, or future observations.",
        call_accounting="Scripted high-level planning is a declared boundary, not measured LLM use: first three arms build action queues there; the fourth binds one prewritten feedback skill and records each numeric update separately.",
        local_feedback_updates="Counts updates inside the prewritten feedback skill only; other arms record observation-conditioned decisions at their scripted planning boundary. All arms are offered every public observation.",
        schedule="Exogenous increments are injected before the named one-based action step; all arms are then offered the changed public position.",
        termination="Original counter position >= target or 20 controller actions; success requires exact target equality.",
        timing="Host process control-loop milliseconds only; includes trace construction, excludes model/network/simulator latency. Not a throughput comparison.",
        actual_model_tokens=None, real_model_calls=0,
        token_scope="No real model was called. Zero measured calls does not establish token efficiency or decision quality.",
        episodes=len(rows), aggregate=aggregate, paired_outcomes=paired,
        trajectories=trajectories,
    )
    write_csv(data / "cpu_control.csv", rows)
    write_json(data / "cpu_control_summary.json", summary)
    return summary


def amortization_experiment(data):
    rows = []
    for build_tokens in (0, 10000, 100000):
        for baseline_tokens in (1000, 10000):
            for execution_tokens in (100, 1000, 2000):
                difference = baseline_tokens - execution_tokens
                breakeven = math.floor(build_tokens / difference) + 1 if difference > 0 else "never"
                for reuse_count in (1, 10, 100, 1000):
                    baseline_total = reuse_count * baseline_tokens
                    skill_total = build_tokens + reuse_count * execution_tokens
                    rows.append(dict(
                        evidence_type="hypothetical_formula_only",
                        assumed_build_tokens=build_tokens,
                        assumed_baseline_tokens_per_episode=baseline_tokens,
                        assumed_skill_execution_tokens_per_episode=execution_tokens,
                        reuse_count=reuse_count, baseline_total_tokens=baseline_total,
                        skill_total_tokens=skill_total,
                        amortized_skill_tokens_per_episode=skill_total / reuse_count,
                        savings_fraction=(baseline_total - skill_total) / baseline_total,
                        first_strictly_cheaper_reuse_count=breakeven,
                        assumes_equal_success_and_no_extra_repair=True,
                        actual_token_measurement=False,
                    ))
    write_csv(data / "amortization_scenarios.csv", rows)
    return rows


def report(output, scheduling, event_count, cpu, amortization):
    lines = [
        "# Offline mechanism experiments", "",
        "These experiments make no network or model calls and require no GPU. They do not reproduce robot success, real model token use, provider billing, or online latency.", "",
        "## Reproduce", "", "NumPy is required by the real project package initializer. Install requirements-offline.txt in the selected Python environment before running; the source snapshot does not bundle NumPy binaries.", "", "```bash",
        "env -u PYTHONPATH python3 result/scripts/run_offline_experiments.py --output-dir /tmp/physicalrsi-offline-check",
        "```", "",
        "The default output directory is `result/`. An included `result/sources/code` snapshot is preferred; otherwise the script imports the surrounding checkout. Only this script's named data files and this report are overwritten. Timing columns vary; seeded trajectories and counts are deterministic.", "",
        "## Real AgentLoop scheduling", "",
        f"All {len(scheduling)} configurations passed their analytical call-count and unchanged-observation checks; {event_count} per-environment step events are recorded in `data/scheduling_events.jsonl`.", "",
        "The grid uses horizons 1/10/100/1000, intervals 1/10/100, and per-episode call caps 1/100000. Additional cases reset three episodes across three environments, and change instructions at zero-based step 3 across two environments.", "",
        "| 1,000 chunks, one environment | Logical planner calls |",
        "| --- | ---: |",
    ]
    for interval, cap in ((1, 100000), (100, 100000), (100, 1)):
        row = next(row for row in scheduling if row["scenario"] == f"grid-h1000-i{interval}-c{cap}")
        lines.append(f"| Interval {interval}, cap {cap} | {row['measured_logical_planner_calls']} |")
    lines += [
        "", "The constant-instruction count is `episodes × environments × min(cap, ceil(horizon / interval))`. A changed instruction triggers planning only while the call cap allows it: a cap of one suppresses the second plan even after the instruction changes. Reset restores the per-environment budgets.", "",
        "The original `AgentLoop` returns the same observation objects without inserting the advisory subgoal into policy inputs. Thus this scheduling experiment does not test skill selection, control quality, or a real model's reasoning. The counting planner is scripted. Logical calls are not token counts, and no 100× token advantage is established.", "",
        "## Counter control surrogate", "",
        "The harness uses the repository's real `CounterEnvironment.reset/step` and `CounterVerifier.verify`. The original example has a constant-increment policy and no perturbation scheduler; this experiment adds an explicit outer scheduler and four scripted exact-dynamics controllers. It deliberately does not use `AgentLoop` as an action controller, because that class is advisory.", "",
        "There are 32 seeds per family and four paired arms. Every arm starts at zero with the same seeded target (20–32), maximum action increment (3), budget (20), and perturbation schedule. The controller receives only the public current position and fixed target. It is never given the seed, family, disturbance schedule, or future state. Every arm receives each current observation; the selected refresh cadence determines whether it recomputes its action queue.", "",
        "The fourth arm binds a prewritten local feedback skill once and lets it recompute `min(3, max(0, target - position))` on every step. The first three arms perform their observed-state recomputation at a scripted planning boundary; the fourth performs it inside the bound skill. `scripted_planning_calls` counts that declared high-level boundary, while `local_feedback_updates` counts only numeric updates inside the fourth arm's skill (zero for the other arms). `observation_conditioned_decisions` exposes all actual observed-state recomputations across either boundary. This is an explicit architecture/accounting convention over hand-written controllers, not a measurement of a model's calls or success.", "",
        "Static cases have no disturbance. Early forward/backward cases inject a seeded increment of ±1–4 before action step 3. Late forward cases inject +1–4 before step `ceil(target / 3) - 1`. The environment then exposes the changed position to every arm. The original environment terminates at position >= target; the original verifier requires exact equality. Disturbances are exogenous transitions, not extra controller actions.", "",
        "| Family | Controller | Successes / 32 | Mean planning calls | Mean local skill feedback updates | Mean actions |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in cpu["aggregate"]:
        lines.append(f"| {row['family']} | {row['arm']} | {row['successes']} / {row['episodes']} | {row['mean_scripted_planning_calls']:.3f} | {row['mean_local_feedback_updates']:.3f} | {row['mean_steps']:.3f} |")
    lines += [
        "", "The open-loop arm compiles one fixed action sequence; it is not representative of every executable skill. The fourth arm directly demonstrates that a prewritten skill can contain local feedback with one high-level binding. Its action/observation trajectory matches the every-step scripted planner, while its feedback work is accounted at a different boundary. This does not make that work free or establish that an LLM can discover the skill. The results establish a controlled surrogate tradeoff for these four specific controllers, not that PhysicalRSI necessarily loses quality when it reduces model calls.", "",
        "Each result's complete per-step observations, actions, exogenous increments, termination, and independent verdict are retained in `data/cpu_control_summary.json`; `data/cpu_control.csv` contains episode metrics. All 512 episodes are scripted. The 32 seeds are a fixed diagnostic set, not independent evidence of generalization to robot tasks. Local milliseconds include in-process trace creation and have no cloud/model latency interpretation.", "",
        "## Hypothetical skill amortization", "",
        f"`data/amortization_scenarios.csv` contains {len(amortization)} explicitly hypothetical scenarios. None of its token numbers are measured.", "",
        "Let `B` be all skill-building token costs, `R` execution tokens per episode, `D` baseline tokens per episode, and `n` reuse count. Then baseline cost is `nD`, skill cost is `B+nR`, and amortized skill cost is `B/n+R`. If `D>R`, the first strictly cheaper integer reuse count is `floor(B/(D-R))+1`; otherwise there is no break-even under these assumptions.", "",
        "The scan includes execution costs greater than or equal to the baseline, where reuse never helps. It assumes equal success, no additional repairs, identical accounting, and no excluded failures. A real comparison must include failed/retried/development calls and compare cost per successful task at matched quality. The measured offline zero-model execution is not an input to these hypothetical token scenarios.", "",
        "## Source provenance", "",
        "Imported source files are hashed below. The resolved source location is runtime metadata, not evidence that other checkouts are identical.", "",
        f"Source root: `{SOURCE_ROOT}`", "",
    ]
    for relative in ("PhysicalRSI_baselines/robodojo/agent_planner.py", "PhysicalRSI_demos/experiment.py"):
        checksum = hashlib.sha256((SOURCE_ROOT / relative).read_bytes()).hexdigest()
        lines.append(f"- `{relative}`: SHA-256 `{checksum}`")
    lines += ["", "No observed count or timing in this report establishes a token advantage over the user's other project; that requires matched requests, provider usage logs, success checks, and a baseline implementation."]
    (output / "reports" / "offline_experiments.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    output = args.output_dir.resolve()
    data = output / "data"
    data.mkdir(parents=True, exist_ok=True)
    (output / "reports").mkdir(parents=True, exist_ok=True)
    scheduling, event_count = scheduling_experiment(data)
    cpu = cpu_experiment(data)
    amortization = amortization_experiment(data)
    report(output, scheduling, event_count, cpu, amortization)
    print(json.dumps(dict(output=str(output), source_root=str(SOURCE_ROOT),
                          scheduling_configurations=len(scheduling),
                          scheduling_events=event_count, cpu_episodes=cpu["episodes"],
                          hypothetical_amortization_rows=len(amortization),
                          real_model_calls=0, measured_tokens=None), indent=2))


if __name__ == "__main__":
    main()
