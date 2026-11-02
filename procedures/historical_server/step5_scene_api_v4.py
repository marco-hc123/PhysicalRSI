"""Explicit scene-name API and pre-execution CPU contract checks.

This study-specific adapter is separate from all frozen experiment sources.
Synthetic primitive replies are interface fixtures, never native task evidence.
"""
from copy import deepcopy
from pathlib import Path
import ast
import json
import math
import time

from PhysicalRSI_core.infra.storage import atomic_json, digest, file_digest
from PhysicalRSI_baselines.robodojo.code_execution import execute_policy
from PhysicalRSI_baselines.robodojo.proposal import CodeProposer
from PhysicalRSI_baselines.robodojo.skill_proposal import validate_policy_source


SCENE_KEY_CONTRACT = {
    "version": "study-scene-object-names/v2",
    "key_type": "string",
    "format": "<category>_<positive integer instance index>",
    "examples": {"basket_1": ["basket", 1], "watch_2": ["watch", 2],
                 "toy_car_1": ["toy_car", 1]},
    "parsing": "Split at the LAST underscore. Keep category as a string; only the final suffix is an integer. Do not call int() on the whole key.",
    "identity": "Equal category strings indicate the same class; full keys identify distinct visible instances, not persistent tracking identities.",
    "scope": "Names are produced by this study's RGB adapter; examples contain no evaluation layout or success signal.",
}


def clarified_api(api):
    result = deepcopy(api)
    result["scene_object_key_contract"] = deepcopy(SCENE_KEY_CONTRACT)
    return result


def _object(x, y, *, basket=False):
    return {"pose": [x, y, 0.79, 1., 0., 0., 0.],
            "dims": [0.20, 0.15, 0.07] if basket else [0.08, 0.03, 0.025]}


def fixtures():
    """Artificial coordinates independent of retained validation geometry."""
    return {
        "empty": {},
        "named": {"basket_1": _object(-0.27, 0.29, basket=True),
                  "watch_1": _object(-0.17, -0.12)},
        "underscore_and_repeated_category": {
            "basket_1": _object(-0.27, 0.29, basket=True),
            "basket_2": _object(0., 0.31, basket=True),
            "basket_3": _object(0.27, 0.29, basket=True),
            "watch_1": _object(-0.22, -0.12),
            "watch_2": _object(0.19, -0.11),
            "toy_car_1": _object(-0.04, -0.14),
            "pen_1": _object(0.08, -0.13),
        },
    }


class SyntheticPrimitives:
    """Validate RPC types/shapes, never simulate grasps, paths or rewards."""
    def __init__(self, objects, mode="normal"):
        self.objects, self.mode, self.calls = deepcopy(objects), mode, []

    def handlers(self):
        return {name: self._handler(name)
                for name in ("scene", "approach", "gripper", "reobserve")}

    def _handler(self, name):
        def handle(args, kwargs, *, deadline):
            if time.monotonic() >= deadline:
                raise TimeoutError("Synthetic primitive deadline")
            if args:
                raise ValueError("Fixture expects keyword-only primitive arguments")
            self.calls.append(dict(method=name, kwargs=deepcopy(kwargs)))
            if name in {"scene", "reobserve"} and kwargs:
                raise ValueError("Observation methods take no arguments")
            if name == "scene":
                return dict(frame="world", unit="m", objects=deepcopy(self.objects),
                            observation={"id": "synthetic-interface-fixture"})
            if name in {"approach", "gripper"} and kwargs.get("arm") not in {"left", "right"}:
                raise ValueError("Invalid arm")
            if name == "approach":
                if set(kwargs) != {"arm", "position_m", "quaternion_wxyz"}:
                    raise ValueError("Unexpected approach signature")
                for key, length in [("position_m", 3), ("quaternion_wxyz", 4)]:
                    value = kwargs[key]
                    if (not isinstance(value, list) or len(value) != length
                            or any(type(v) not in {int, float} or not math.isfinite(v) for v in value)):
                        raise ValueError("Invalid finite vector: " + key)
                if abs(sum(v*v for v in kwargs["quaternion_wxyz"]) - 1.) > 1e-4:
                    raise ValueError("Quaternion must be normalized")
                if self.mode == "transport_timeout":
                    raise TimeoutError("Injected synthetic transport failure; no action")
                if self.mode == "no_path":
                    return {"primitive_error": "no_collision_free_path"}
            if name == "gripper":
                if set(kwargs) != {"arm", "command"} or type(kwargs["command"]) not in {int, float} or not 0 <= kwargs["command"] <= 1:
                    raise ValueError("Invalid gripper signature/command")
            return {"state": {"left_arm_joint_state": [0.]*6,
                              "right_arm_joint_state": [0.]*6,
                              "left_ee_joint_state": [0.], "right_ee_joint_state": [0.]}}
        return handle


def run_case(source, memory, objects, *, runtime, output, mode="normal"):
    tree = validate_policy_source(source)
    if not any(isinstance(node, ast.FunctionDef) and node.name == "policy" for node in tree.body):
        raise ValueError("Missing policy(robot, memory)")
    primitives = SyntheticPrimitives(objects, mode)
    try:
        execute_policy(source, deepcopy(memory), handlers=primitives.handlers(),
                       runtime=runtime, output=output, timeout_s=12, max_calls=100)
        error = None
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    log = Path(output)/"processes/isolated/process.log"
    receipt_path = Path(output)/"processes/isolated/process.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    journal = receipt.get("calls", [])
    # A static interface fixture cannot establish termination of a policy that
    # reobserves objects after moving them. Inspect only its bounded valid prefix;
    # the unchanged native 100-call limit still decides actual execution.
    bounded = (error == "ValueError: Policy call budget or sequence violated"
               and len(journal) == len(primitives.calls) == 100
               and all(row.get("state") == "completed"
                       and row["request"]["id"] == index
                       for index, row in enumerate(journal)))
    return dict(completed=error is None, error=error, calls=primitives.calls,
                contract_prefix_valid=error is None or bounded,
                completion_inconclusive_static_scene=bounded,
                native_call_budget_unchanged=100,
                stderr_tail=log.read_text(errors="replace")[-3000:] if log.exists() else "",
                output=str(output), scope="CPU synthetic RPC contract only; no native task score")


def semantic_gate(source, memory, *, runtime, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, objects in fixtures().items():
        results[name] = run_case(source, memory, objects, runtime=runtime, output=output/name)
        if results[name]["completion_inconclusive_static_scene"]:
            rejection = run_case(source, memory, objects, runtime=runtime,
                                 output=output/(name+"-planner-rejection"), mode="no_path")
            results[name]["planner_rejection_check"] = rejection
            results[name]["contract_prefix_valid"] &= rejection["completed"]
        atomic_json(output/"gate-result.json", dict(
            passed=all(row["contract_prefix_valid"] for row in results.values()),
            source_sha256=digest(source), cases=results,
            qualification="Bounded RPC interface inspection only. Static-scene termination is inconclusive; native execution enforces its original 100-call limit.",
            native_episodes=0, api_calls=0, physical_qualification=False))
        if not results[name]["contract_prefix_valid"]:
            raise ValueError("CPU scene contract gate rejected candidate: " + name)
    return results


class CheckedCodeProposer(CodeProposer):
    """For a NEW registered workflow only. Reject once; never auto-regenerate."""
    def __init__(self, *args, isolation_runtime, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolation_runtime = Path(isolation_runtime)

    def identity(self):
        return dict(base=super().identity(), gate_implementation=file_digest(Path(__file__)),
                    scene_contract_sha256=digest(SCENE_KEY_CONTRACT),
                    isolation_manifest_sha256=file_digest(self.isolation_runtime/"manifest.json"))

    def propose(self, *, task, source, memory, feedback, skill_api, output):
        if task != "classify_objects" or skill_api.get("scene_object_key_contract") != SCENE_KEY_CONTRACT:
            raise ValueError("Register the clarified classify_objects API in the frozen runtime before proposing")
        candidate = super().propose(task=task, source=source, memory=memory,
            feedback=feedback, skill_api=skill_api, output=output)
        semantic_gate(candidate["source"], candidate["memory"],
                      runtime=self.isolation_runtime, output=Path(output)/"cpu-contract-gate")
        return candidate
