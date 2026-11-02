#!/usr/bin/env python3
"""Produce an offline, final report for the paired catalogue projection suite.

Usage: python3 cloud_catalogue_report.py --suite /path/to/completed/suite

Only the Python standard library is needed. This program never starts an
experiment, contacts a provider, or reads credentials. It refuses unfinished
controllers and malformed coverage. Evidence deficiencies are retained in the
report as audit failures, rather than dropping cases. Exit 2 means a report was
written but the comparison did not pass its evidence/validity checks.

Required protocol.json: jobs, exactly 30 records containing name, condition,
layout, repeat, pair_id, phase. Required controller-status.json: finished=true,
jobs mirroring those records with native_complete, outcome, exit_code, error.
Job status offsets are monotonic seconds since wrapper start. Replay source
verification is accepted only from source_pin_verified=true (or
source_pin.verified=true), and each pair requires an explicit verified identity
flag. Plain hashes, a success flag, or a valid plan are not verification flags.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import sys


CONDITIONS = ("projected", "unprojected")
JOB_FIELDS = ("name", "condition", "layout", "repeat", "pair_id", "phase")
OUTCOMES = ("native_completed", "planner_failure", "execution_failure", "infrastructure_failure")
TOKEN_FIELDS = ("input_tokens", "output_tokens", "total_tokens", "cached_tokens", "reasoning_tokens")
NOTES = [
    "This is a developmental comparison on the same five layouts, not a new held-out evaluation.",
    "Full projection restores static task-label/code identities; it is not pure prompt compression and can change output selection.",
    "Native evaluator outcomes are the success authority. Contract-valid plans and replay calls are not robot successes.",
    "All 15 planned attempts per condition remain in the success denominator, including planning and execution failures. Infrastructure failures invalidate the comparison and remain visible in that denominator.",
    "There are five layout units and three repeat measurements per layout. Paired repeat effects are descriptive; no confidence interval treats the repeats as independent layouts.",
    "Cached tokens are a subset of input tokens; reasoning tokens are a subset of output tokens. Neither is added to total tokens.",
    "Token sums include provider-reported usage for every recorded transport attempt, including failed attempts. Missing provider usage is disclosed and is not evidence of zero billed tokens.",
    "Replay compares identical saved observations only when every pair audit explicitly verifies identity and source pin verification is explicit. Replay has no native execution.",
    "API latency, action-batch latency, native execution, and wrapper wall time overlap and must not be added together.",
    "Cold-start time is wrapper start through policy readiness, including configuration/loading; it does not isolate weight loading alone.",
]


class ReportError(Exception):
    """Suite is not final or does not identify exactly the planned cases."""


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReportError("{}: {}".format(path, error)) from error


def evidence_json(path, issues, context, required=True):
    if not path.exists():
        if required:
            issues.append("{}: missing {}".format(context, path.name))
        return {}
    try:
        value = read_json(path)
        if not isinstance(value, dict):
            raise ReportError("expected a JSON object")
        return value
    except ReportError as error:
        issues.append("{}: {}".format(context, error))
        return {}


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def nonnegative(value):
    return value if finite_number(value) and value >= 0 else None


def mean(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def artifact(path, suite):
    try:
        return str(path.relative_to(suite))
    except ValueError:
        return str(path)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_jobs(protocol, controller):
    planned = protocol.get("jobs")
    observed = controller.get("jobs")
    if not isinstance(planned, list) or not isinstance(observed, list):
        raise ReportError("protocol and controller must each contain a jobs array")
    if controller.get("finished") is not True:
        raise ReportError("controller is not finished; a final report requires all 30 terminal attempts")
    if len(planned) != 30 or len(observed) != 30:
        raise ReportError("expected exactly 30 planned and 30 controller jobs")
    expected = {(condition, layout, repeat) for condition in CONDITIONS
                for layout in range(1, 6) for repeat in range(1, 4)}
    names, coverage, pairs = set(), set(), {}
    for job in planned:
        if not isinstance(job, dict) or any(field not in job for field in JOB_FIELDS):
            raise ReportError("each protocol job must define {}".format(", ".join(JOB_FIELDS)))
        name = job["name"]
        if not isinstance(name, str) or not name or Path(name).name != name or name in (".", ".."):
            raise ReportError("job names must be nonempty direct directory names")
        if name in names:
            raise ReportError("duplicate protocol job name: " + name)
        names.add(name)
        if type(job["layout"]) is not int or type(job["repeat"]) is not int:
            raise ReportError("layout and repeat must be integers: " + name)
        key = job["condition"], job["layout"], job["repeat"]
        if key not in expected or key in coverage:
            raise ReportError("unexpected or duplicate condition/layout/repeat: " + repr(key))
        coverage.add(key)
        if job["phase"] not in ("pilot", "repeat"):
            raise ReportError("invalid phase: " + name)
        if not isinstance(job["pair_id"], str) or not job["pair_id"]:
            raise ReportError("pair_id must be a nonempty string: " + name)
        pairs.setdefault(job["pair_id"], []).append(job)
    if coverage != expected or len(pairs) != 15:
        raise ReportError("protocol must cover five layouts x two conditions x three repeats in 15 pairs")
    for pair_id, pair in pairs.items():
        if (len(pair) != 2 or {job["condition"] for job in pair} != set(CONDITIONS)
                or len({(job["layout"], job["repeat"], job["phase"]) for job in pair}) != 1):
            raise ReportError("pair does not match condition, layout, repeat, and phase: " + pair_id)
    by_name = {}
    for job in observed:
        if not isinstance(job, dict) or job.get("name") not in names or job["name"] in by_name:
            raise ReportError("controller jobs contain missing, extra, or duplicate names")
        by_name[job["name"]] = job
    for job in planned:
        result = by_name[job["name"]]
        if any(type(result.get(field)) is not type(job[field]) or result.get(field) != job[field]
               for field in JOB_FIELDS):
            raise ReportError("controller does not mirror protocol job: " + job["name"])
        if result.get("outcome") not in OUTCOMES or type(result.get("native_complete")) is not bool:
            raise ReportError("job lacks a valid terminal outcome/native_complete: " + job["name"])
        if result["native_complete"] != (result["outcome"] == "native_completed"):
            raise ReportError("native_complete contradicts outcome: " + job["name"])
        if "exit_code" not in result or "error" not in result:
            raise ReportError("terminal job must retain exit_code and error: " + job["name"])
        if result["exit_code"] is not None and type(result["exit_code"]) is not int:
            raise ReportError("exit_code must be an integer or null: " + job["name"])
    return [by_name[job["name"]] for job in planned]


def normalize_usage(raw):
    """Normalize Chat Completions/Responses usage without counting subsets twice."""
    raw = raw if isinstance(raw, dict) else {}
    input_tokens = nonnegative(raw.get("input_tokens", raw.get("prompt_tokens")))
    output_tokens = nonnegative(raw.get("output_tokens", raw.get("completion_tokens")))
    total_tokens = nonnegative(raw.get("total_tokens"))
    total_derived = total_tokens is None and input_tokens is not None and output_tokens is not None
    if total_derived:
        total_tokens = input_tokens + output_tokens
    input_details = raw.get("input_tokens_details", raw.get("prompt_tokens_details")) or {}
    output_details = raw.get("output_tokens_details", raw.get("completion_tokens_details")) or {}
    input_details = input_details if isinstance(input_details, dict) else {}
    output_details = output_details if isinstance(output_details, dict) else {}
    return dict(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens,
                cached_tokens=nonnegative(input_details.get("cached_tokens", raw.get("cached_tokens"))),
                reasoning_tokens=nonnegative(output_details.get("reasoning_tokens", raw.get("reasoning_tokens"))),
                total_tokens_derived=total_derived)


def token_summary(attempts):
    tokens = {field: sum(attempt["tokens"][field] or 0 for attempt in attempts) for field in TOKEN_FIELDS}
    return dict(**tokens, transport_calls=len(attempts),
                successful_transport_calls=sum(attempt.get("transport_success") is True for attempt in attempts),
                api_seconds=sum(attempt["seconds"] or 0 for attempt in attempts),
                mean_api_seconds=mean([attempt["seconds"] for attempt in attempts]),
                api_seconds_reported_calls=sum(attempt["seconds"] is not None for attempt in attempts),
                missing_usage_calls={field: sum(attempt["tokens"][field] is None for attempt in attempts)
                                     for field in TOKEN_FIELDS},
                mean_tokens_per_transport_attempt={
                    field: ratio(tokens[field], len(attempts)) for field in TOKEN_FIELDS},
                mean_tokens_per_usage_reporting_attempt={
                    field: mean([attempt["tokens"][field] for attempt in attempts]) for field in TOKEN_FIELDS})


def usage_from_metadata(metadata):
    for key in ("provider_usage", "raw_provider_usage", "usage"):
        if isinstance(metadata.get(key), dict):
            return metadata[key]
    return {}


def audit_attempts(directory, job, suite, issues):
    attempts = []
    metadata_paths = sorted((directory / "api").glob("call-*-metadata.json"))
    seen = set()
    for path in metadata_paths:
        match = re.fullmatch(r"call-(\d+)-metadata\.json", path.name)
        if not match:
            issues.append(job["name"] + ": unexpected API metadata filename " + path.name)
            continue
        call_id = match.group(1)
        if int(call_id) in seen:
            issues.append(job["name"] + ": duplicate API attempt id " + call_id)
        seen.add(int(call_id))
        metadata = evidence_json(path, issues, job["name"])
        request = directory / "api" / ("call-" + call_id + "-request.json")
        response = directory / "api" / ("call-" + call_id + "-response.json")
        if metadata.get("condition") != job["condition"]:
            issues.append(job["name"] + ": API metadata condition does not match protocol")
        if not request.is_file():
            issues.append(job["name"] + ": missing API request for call " + call_id)
        if metadata.get("success") is True and not response.is_file():
            issues.append(job["name"] + ": successful transport is missing response " + call_id)
        seconds = nonnegative(metadata.get("seconds"))
        if seconds is None:
            issues.append(job["name"] + ": API attempt lacks a nonnegative seconds field")
        raw = usage_from_metadata(metadata)
        tokens = normalize_usage(raw)
        if (tokens["cached_tokens"] is not None and tokens["input_tokens"] is not None
                and tokens["cached_tokens"] > tokens["input_tokens"]):
            issues.append(job["name"] + ": cached tokens exceed input tokens")
        if (tokens["reasoning_tokens"] is not None and tokens["output_tokens"] is not None
                and tokens["reasoning_tokens"] > tokens["output_tokens"]):
            issues.append(job["name"] + ": reasoning tokens exceed output tokens")
        attempts.append(dict(attempt=int(call_id), condition=job["condition"],
                             transport_success=metadata.get("success"), seconds=seconds,
                             tokens=tokens, provider_usage=raw,
                             metadata_artifact=artifact(path, suite),
                             request_artifact=artifact(request, suite) if request.is_file() else None,
                             response_artifact=artifact(response, suite) if response.is_file() else None))
    for request in (directory / "api").glob("call-*-request.json"):
        if not request.with_name(request.name.replace("-request.json", "-metadata.json")).is_file():
            issues.append(job["name"] + ": API request has no transport metadata: " + request.name)
    summary = evidence_json(directory / "usage-summary.json", issues, job["name"])
    if summary and summary.get("api_attempts") != len(attempts):
        issues.append(job["name"] + ": usage-summary api_attempts differs from recorded transports")
    reported = summary.get("provider_reported_usage")
    if isinstance(reported, dict):
        aggregate = token_summary(attempts)
        normalized = normalize_usage(reported)
        for field in ("input_tokens", "output_tokens", "total_tokens"):
            if normalized[field] is not None and normalized[field] != aggregate[field]:
                issues.append(job["name"] + ": usage-summary disagrees with raw metadata for " + field)
    return attempts, summary


def timing_summary(state, job, issues):
    names = ("policy_ready_seconds", "client_started_seconds", "first_native_observation_seconds",
             "native_finished_seconds", "elapsed_seconds")
    points = {name: nonnegative(state.get(name)) for name in names}
    ordered = [points[name] for name in names]
    known = [value for value in ordered if value is not None]
    if any(left > right for left, right in zip(known, known[1:])):
        issues.append(job["name"] + ": monotonic runtime offsets are out of order")
        return dict(offsets=points, valid=False)
    if job["native_complete"] and any(value is None for value in ordered):
        issues.append(job["name"] + ": native completion lacks one or more runtime offsets")

    def delta(end, start):
        return points[end] - points[start] if points[end] is not None and points[start] is not None else None

    launch_gap = delta("client_started_seconds", "policy_ready_seconds")
    simulator_startup = delta("first_native_observation_seconds", "client_started_seconds")
    teardown = delta("elapsed_seconds", "native_finished_seconds")
    overhead = sum([launch_gap, simulator_startup, teardown]) if all(
        value is not None for value in (launch_gap, simulator_startup, teardown)) else None
    return dict(offsets=points, valid=True,
                cold_start_until_policy_ready_seconds=points["policy_ready_seconds"],
                launch_gap_seconds=launch_gap, simulator_startup_seconds=simulator_startup,
                native_execution_seconds=delta("native_finished_seconds", "first_native_observation_seconds"),
                native_client_elapsed_seconds=delta("native_finished_seconds", "client_started_seconds"),
                teardown_seconds=teardown, wrapper_overhead_seconds=overhead,
                wrapper_elapsed_seconds=points["elapsed_seconds"])


def collect_videos(native_path, directory, job, suite, issues):
    """Link/copy the original three camera files; never replace existing evidence."""
    if not native_path:
        issues.append(job["name"] + ": missing native_result_path for video evidence")
        return []
    source_result = Path(native_path)
    if not source_result.is_absolute():
        source_result = suite / source_result
    source_dir = source_result.parent
    sources = sorted(source_dir.glob("episode_0000000_*.mp4"))
    if len(sources) != 3:
        issues.append("{}: expected exactly three original camera videos, found {} in {}".format(
            job["name"], len(sources), source_dir))
    video_dir = directory / "videos"
    video_dir.mkdir(exist_ok=True, parents=True)
    rows = []
    for source in sources:
        destination = video_dir / source.name
        row = dict(job=job["name"], condition=job["condition"], layout=job["layout"],
                   repeat=job["repeat"], source=artifact(source, suite),
                   artifact=artifact(destination, suite), bytes=source.stat().st_size,
                   method="existing", verified=False)
        if row["bytes"] <= 0:
            issues.append(job["name"] + ": empty video: " + str(source))
            rows.append(row)
            continue
        try:
            if not destination.exists():
                try:
                    os.link(source, destination)
                    row["method"] = "hardlink"
                except OSError:
                    # Exclusive create prevents overwriting an artifact on a rerun/race.
                    with source.open("rb") as src, destination.open("xb") as dst:
                        shutil.copyfileobj(src, dst)
                    row["method"] = "copy"
            row["sha256"] = sha256(source)
            row["verified"] = (destination.stat().st_size == row["bytes"]
                               and sha256(destination) == row["sha256"])
            if not row["verified"]:
                issues.append(job["name"] + ": existing video differs from original: " + str(destination))
        except OSError as error:
            issues.append(job["name"] + ": could not preserve video: " + str(error))
            row["error"] = str(error)
        rows.append(row)
    return rows


def collect_case(job, suite, issues):
    directory = suite / job["name"]
    state = evidence_json(directory / "status.json", issues, job["name"])
    attempts, usage_summary = audit_attempts(directory, job, suite, issues)
    policy = evidence_json(directory / "policy-status.json", issues, job["name"],
                           required=job["outcome"] != "infrastructure_failure")
    observation = directory / "observation-000.npz"
    observations = sorted(directory.glob("observation-*.npz"))
    if job["outcome"] in ("native_completed", "planner_failure") and (
            observations != [observation] or not observation.is_file() or observation.stat().st_size == 0):
        issues.append(job["name"] + ": expected one nonempty observation-000.npz")
    native = {}
    detail = {}
    native_verified = False
    videos = []
    if job["native_complete"]:
        native = evidence_json(directory / "native-result.json", issues, job["name"])
        details = native.get("details", {})
        details = list(details.values()) if isinstance(details, dict) else details
        if (native.get("eval_time") != 1 or not isinstance(details, list) or len(details) != 1
                or not isinstance(details[0], dict) or details[0].get("layout_id") != job["layout"]
                or type(details[0].get("success")) is not bool):
            issues.append(job["name"] + ": native result does not verify exactly the planned layout")
        else:
            detail = details[0]
            native_verified = True
        if state.get("completed") is not True or state.get("client_exit_code") != 0 or job["exit_code"] != 0:
            issues.append(job["name"] + ": native completion is inconsistent with wrapper/client exit state")
        if state.get("native_result") is not None and state["native_result"] != native:
            issues.append(job["name"] + ": native-result.json differs from embedded status native_result")
        videos = collect_videos(state.get("native_result_path"), directory, job, suite, issues)
    elif (directory / "native-result.json").exists():
        issues.append(job["name"] + ": failed job unexpectedly has a native-result.json; review outcome classification")
    decisions = []
    for path in sorted((directory / "runtime").glob("*/episodes/*/agent-decision.json")):
        decision = evidence_json(path, issues, job["name"])
        decisions.append(dict(instruction=decision.get("instruction"), plan=decision.get("plan"),
                              artifact=artifact(path, suite)))
    if job["native_complete"] and len(decisions) != 1:
        issues.append(job["name"] + ": expected exactly one bound agent-decision.json")
    action_rows = []
    action_file = directory / "action-timing.jsonl"
    if action_file.exists():
        for index, line in enumerate(action_file.read_text(encoding="utf-8").splitlines(), 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or nonnegative(row.get("seconds")) is None:
                    raise ValueError("missing nonnegative seconds")
                action_rows.append(row)
            except (ValueError, TypeError) as error:
                issues.append("{}: invalid action-timing line {}: {}".format(job["name"], index, error))
    if job["native_complete"] and not action_rows:
        issues.append(job["name"] + ": native completion has no action timing evidence")
    timing = timing_summary(state, job, issues)
    token_totals = token_summary(attempts)
    case = {field: job[field] for field in JOB_FIELDS}
    case.update(outcome=job["outcome"], exit_code=job["exit_code"], error=job["error"],
                native_complete_declared=job["native_complete"], native_completed=native_verified,
                success=bool(native_verified and detail.get("success") is True),
                native_success=detail.get("success"), score=detail.get("score"),
                infrastructure_failure=job["outcome"] == "infrastructure_failure",
                status_artifact=artifact(directory / "status.json", suite),
                native_result_path=state.get("native_result_path"),
                observation_artifact=artifact(observation, suite) if observation.exists() else None,
                observation_sha256=sha256(observation) if observation.is_file() else None,
                policy_state=policy.get("state"), usage_summary=usage_summary,
                api=token_totals, api_attempts=attempts, runtime=timing,
                decisions=decisions, videos=[row["artifact"] for row in videos],
                action_batch_calls=len(action_rows),
                action_batch_seconds=sum(row["seconds"] for row in action_rows))
    return case, videos


def summarize_condition(cases):
    attempts = [attempt for case in cases for attempt in case["api_attempts"]]
    api = token_summary(attempts)
    successes = sum(case["success"] for case in cases)
    outcomes = {outcome: sum(case["outcome"] == outcome for case in cases) for outcome in OUTCOMES}
    runtime_fields = ("cold_start_until_policy_ready_seconds", "launch_gap_seconds", "simulator_startup_seconds",
                      "native_execution_seconds", "native_client_elapsed_seconds", "teardown_seconds",
                      "wrapper_overhead_seconds", "wrapper_elapsed_seconds")
    runtime = {field: dict(mean=mean([case["runtime"].get(field) for case in cases]),
                           observed_cases=sum(case["runtime"].get(field) is not None for case in cases))
               for field in runtime_fields}
    return dict(condition=cases[0]["condition"], successes=successes, evaluations=len(cases),
                native_completed=sum(case["native_completed"] for case in cases),
                success_rate=ratio(successes, len(cases)), outcomes=outcomes,
                comparison_valid=not outcomes["infrastructure_failure"],
                api=api, runtime=runtime,
                mean_total_tokens_per_planned_attempt=ratio(api["total_tokens"], len(cases)),
                total_tokens_per_observed_success=ratio(api["total_tokens"], successes),
                token_efficiency_usage_complete=api["missing_usage_calls"]["total_tokens"] == 0)


def paired_effects(cases):
    pairs = {}
    for case in cases:
        pairs.setdefault(case["pair_id"], {})[case["condition"]] = case
    rows = []
    for pair_id, pair in pairs.items():
        projected, unprojected = pair["projected"], pair["unprojected"]

        def difference(left, right):
            return left - right if left is not None and right is not None else None

        rows.append(dict(pair_id=pair_id, layout=projected["layout"], repeat=projected["repeat"],
                         phase=projected["phase"], projected=projected["name"], unprojected=unprojected["name"],
                         comparison_valid=not any(case["infrastructure_failure"] for case in pair.values()),
                         success_difference=int(projected["success"]) - int(unprojected["success"]),
                         native_completed_difference=int(projected["native_completed"]) - int(unprojected["native_completed"]),
                         total_tokens_difference=projected["api"]["total_tokens"] - unprojected["api"]["total_tokens"],
                         api_seconds_difference=projected["api"]["api_seconds"] - unprojected["api"]["api_seconds"],
                         wrapper_elapsed_seconds_difference=difference(projected["runtime"].get("wrapper_elapsed_seconds"),
                                                                       unprojected["runtime"].get("wrapper_elapsed_seconds")),
                         native_execution_seconds_difference=difference(projected["runtime"].get("native_execution_seconds"),
                                                                        unprojected["runtime"].get("native_execution_seconds"))))
    rows.sort(key=lambda row: (row["layout"], row["repeat"]))
    effects = ("success_difference", "native_completed_difference", "total_tokens_difference",
               "api_seconds_difference", "wrapper_elapsed_seconds_difference", "native_execution_seconds_difference")
    layouts = []
    for layout in range(1, 6):
        subset = [row for row in rows if row["layout"] == layout]
        condition_means = {}
        for condition in CONDITIONS:
            group = [case for case in cases if case["layout"] == layout and case["condition"] == condition]
            condition_means[condition] = dict(evaluations=len(group), successes=sum(case["success"] for case in group),
                                               success_rate=mean([int(case["success"]) for case in group]),
                                               mean_total_tokens=mean([case["api"]["total_tokens"] for case in group]),
                                               mean_api_seconds=mean([case["api"]["api_seconds"] for case in group]))
        layouts.append(dict(layout=layout, paired_repeats=len(subset),
                            comparison_valid=all(row["comparison_valid"] for row in subset),
                            mean_effects={effect: mean([row[effect] for row in subset]) for effect in effects},
                            effect_observed_pairs={effect: sum(row[effect] is not None for row in subset) for effect in effects},
                            conditions=condition_means))
    return dict(direction="projected minus unprojected", pairs=rows, layouts=layouts,
                independent_layout_units=5, repeat_measurements_per_layout=3,
                equal_weight_layout_mean_effects={
                    effect: mean([layout["mean_effects"][effect] for layout in layouts]) for effect in effects},
                confidence_interval=None,
                uncertainty_note="Descriptive effects over five developmental layouts; repeats are not independent layout units.")


def verified_identity(audit):
    if audit.get("input_identical_verified") is True or audit.get("identical_observation_verified") is True:
        return True
    # Explicit component verification is also valid; hashes alone are insufficient.
    return (audit.get("observation_identical_verified") is True
            and audit.get("request_context_identical_verified") is True)


def replay_report(suite, issues):
    path = suite / "replay" / "replay-summary.json"
    replay = evidence_json(path, issues, "replay")
    rows, audits = replay.get("rows", []), replay.get("pair_audits", [])
    if replay.get("finished") is not True:
        issues.append("replay: expected finished=true")
    if not isinstance(rows, list):
        rows = []
    if not isinstance(audits, list):
        audits = []
    expected = {(layout, condition) for layout in range(1, 6) for condition in CONDITIONS}
    observed = [(row.get("layout"), row.get("condition")) for row in rows if isinstance(row, dict)]
    coverage_verified = len(observed) == 10 and set(observed) == expected
    if not coverage_verified:
        issues.append("replay: expected exactly ten calls, one per layout/condition")
    audit_layouts = [audit.get("layout") for audit in audits if isinstance(audit, dict)]
    audit_coverage = len(audit_layouts) == 5 and set(audit_layouts) == set(range(1, 6))
    identity_verified = audit_coverage and all(verified_identity(audit) for audit in audits)
    if not identity_verified:
        issues.append("replay: five identical-input pair audits are not all explicitly verified")
    source_pin = replay.get("source_pin") or {}
    source_verified = replay.get("source_pin_verified") is True or (
        isinstance(source_pin, dict) and source_pin.get("verified") is True)
    if not source_verified:
        issues.append("replay: source pin verification is absent or false")
    summaries = []
    normalized_rows = []
    transport_attempts = []
    for row in rows:
        if not isinstance(row, dict):
            issues.append("replay: non-object result row")
            continue
        normalized = dict(row)
        normalized["seconds"] = nonnegative(row.get("seconds"))
        if normalized["seconds"] is None:
            issues.append("replay: call lacks nonnegative API seconds")
        # A replay row is a logical planner call. Frozen transport retries are
        # separate attempts and may each consume tokens; never add final usage
        # to the attempt ledger again.
        ledgers = row.get("attempts")
        ledgers = ledgers if isinstance(ledgers, list) and ledgers else [row]
        attempts = []
        for index, ledger in enumerate(ledgers, 1):
            if not isinstance(ledger, dict):
                issues.append("replay: non-object transport attempt")
                continue
            attempt = dict(layout=row.get("layout"), condition=row.get("condition"),
                           attempt=ledger.get("attempt", index),
                           transport_success=ledger.get("http_success", ledger.get("success", not bool(ledger.get("error")))),
                           tokens=normalize_usage(usage_from_metadata(ledger)),
                           provider_usage=usage_from_metadata(ledger), seconds=nonnegative(ledger.get("seconds")))
            if attempt["seconds"] is None:
                issues.append("replay: transport attempt lacks nonnegative API seconds")
            attempts.append(attempt)
        aggregate = token_summary(attempts)
        normalized["tokens"] = {field: aggregate[field] for field in TOKEN_FIELDS}
        normalized["tokens_usage_complete"] = aggregate["missing_usage_calls"]["total_tokens"] == 0
        normalized["api_attempts"] = attempts
        normalized["api"] = aggregate
        transport_attempts.extend(attempts)
        normalized_rows.append(normalized)
    for condition in CONDITIONS:
        subset = [row for row in normalized_rows if row.get("condition") == condition]
        summaries.append(dict(condition=condition, calls=len(subset),
                              valid_plans=sum(row.get("contract_valid") is True for row in subset),
                              failed_calls=sum(bool(row.get("error")) for row in subset),
                              api=token_summary([attempt for row in subset for attempt in row["api_attempts"]]),
                              robot_executed=False))
    pair_effects = []
    for layout in range(1, 6):
        pair = {row["condition"]: row for row in normalized_rows if row.get("layout") == layout
                and row.get("condition") in CONDITIONS}
        if len(pair) == 2:
            projected, unprojected = pair["projected"], pair["unprojected"]
            pair_effects.append(dict(layout=layout,
                                     input_tokens_difference=(projected["tokens"]["input_tokens"] - unprojected["tokens"]["input_tokens"])
                                     if projected["tokens"]["input_tokens"] is not None and unprojected["tokens"]["input_tokens"] is not None else None,
                                     total_tokens_difference=(projected["tokens"]["total_tokens"] - unprojected["tokens"]["total_tokens"])
                                     if projected["tokens"]["total_tokens"] is not None and unprojected["tokens"]["total_tokens"] is not None else None,
                                     api_seconds_difference=(projected["seconds"] - unprojected["seconds"])
                                     if projected["seconds"] is not None and unprojected["seconds"] is not None else None,
                                     projected_plan=projected.get("plan"), unprojected_plan=unprojected.get("plan"),
                                     selection_changed=projected.get("plan") != unprojected.get("plan")))
    passed = replay.get("finished") is True and coverage_verified and identity_verified and source_verified
    return dict(artifact=artifact(path, suite), finished=replay.get("finished") is True,
                audit_passed=passed, coverage_verified=coverage_verified,
                identical_inputs_verified=identity_verified, source_pin_verified=source_verified,
                source_pin=source_pin, pair_audits=audits, conditions=summaries,
                logical_calls=len(normalized_rows), transport_calls=len(transport_attempts),
                api_attempts=transport_attempts,
                rows=normalized_rows, paired_effects=pair_effects, robot_executed=False)


def csv_text(cases):
    fields = list(JOB_FIELDS) + ["outcome", "exit_code", "success", "native_completed", "native_success", "score",
                                "infrastructure_failure", "error", "transport_calls", *TOKEN_FIELDS,
                                "mean_api_seconds", "api_seconds", "missing_total_usage_calls",
                                "cold_start_until_policy_ready_seconds", "simulator_startup_seconds",
                                "native_execution_seconds", "native_client_elapsed_seconds",
                                "wrapper_overhead_seconds", "wrapper_elapsed_seconds", "observation_artifact",
                                "native_result_path", "videos"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for case in cases:
        row = {field: case.get(field) for field in fields}
        for field in ("transport_calls", *TOKEN_FIELDS, "mean_api_seconds", "api_seconds"):
            row[field] = case["api"].get(field)
        for field in ("cold_start_until_policy_ready_seconds", "simulator_startup_seconds", "native_execution_seconds",
                      "native_client_elapsed_seconds", "wrapper_overhead_seconds", "wrapper_elapsed_seconds"):
            row[field] = case["runtime"].get(field)
        row["missing_total_usage_calls"] = case["api"]["missing_usage_calls"]["total_tokens"]
        row["error"] = json.dumps(case["error"], ensure_ascii=False) if case["error"] is not None else ""
        row["videos"] = json.dumps(case["videos"], ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue()


def display_number(value):
    return "null" if value is None else ("{:.3f}".format(value) if isinstance(value, float) else str(value))


def english_summary(report):
    lines = ["Catalogue projection experiment — final offline report",
             "Suite: " + report["suite"],
             "Comparison validity: " + ("PASS" if report["comparison_valid"] else "INVALID / evidence requires review"),
             "Planned attempts: 30; five developmental layouts x two conditions x three repeats.",
             ""]
    for condition in report["conditions"]:
        api = condition["api"]
        lines.extend([
            "{}: {}/{} observed native successes; {} native completions; outcomes={}".format(
                condition["condition"], condition["successes"], condition["evaluations"],
                condition["native_completed"], json.dumps(condition["outcomes"], sort_keys=True)),
            "  API transport calls: {}; input/output/total tokens: {}/{}/{}; cached/reasoning subsets: {}/{}.".format(
                api["transport_calls"], *[display_number(api[field]) for field in TOKEN_FIELDS]),
            "  Mean API seconds: {}; reported total tokens/planned attempt: {}; total tokens/observed success: {}.".format(
                display_number(api["mean_api_seconds"]), display_number(condition["mean_total_tokens_per_planned_attempt"]),
                display_number(condition["total_tokens_per_observed_success"])),
            "  Missing provider-usage calls: " + json.dumps(api["missing_usage_calls"], sort_keys=True),
            "  Mean runtime seconds (observed count): " + "; ".join("{}={} (n={})".format(
                key, display_number(value["mean"]), value["observed_cases"])
                for key, value in condition["runtime"].items()),
            ""])
    lines.append("Paired effects are projected minus unprojected, averaged within each layout:")
    for row in report["paired_effects"]["layouts"]:
        lines.append("  Layout {}: {}".format(row["layout"], json.dumps(row["mean_effects"], sort_keys=True)))
    replay = report["replay"]
    lines.extend(["", "Identical-input replay audit: {}; source pin verified: {}; identical inputs verified: {}.".format(
        "PASS" if replay["audit_passed"] else "NOT VERIFIED", replay["source_pin_verified"], replay["identical_inputs_verified"]),
        "Video files verified: {}/{} expected for completed native cases.".format(
            report["audit"]["verified_video_files"], report["audit"]["expected_video_files"]), ""])
    if report["audit"]["issues"]:
        lines.append("Audit issues:")
        lines.extend("  - " + issue for issue in report["audit"]["issues"])
        lines.append("")
    lines.extend("Note: " + note for note in report["notes"])
    lines.extend(["", "Artifacts: suite-report.json, cases.csv, video-manifest.json."])
    return "\n".join(lines) + "\n"


def chinese_summary(report):
    lines = ["目录投影实验：最终离线报告", "实验目录：" + report["suite"],
             "比较有效性：" + ("已通过证据审计" if report["comparison_valid"] else "无效或证据尚需核查"),
             "固定分母为每个条件15次，共30次；规划和执行失败保留在分母内。基础设施失败会使比较无效。"]
    for condition in report["conditions"]:
        lines.append("{}：成功 {}/{}，完成原生评估 {}，API调用 {}，已报告总令牌 {}，每次观测成功的总令牌 {}。".format(
            condition["condition"], condition["successes"], condition["evaluations"], condition["native_completed"],
            condition["api"]["transport_calls"], condition["api"]["total_tokens"],
            display_number(condition["total_tokens_per_observed_success"])))
    lines.extend([
        "完整投影恢复了静态任务标签与代码身份，并非纯粹压缩，也可能改变输出选择。",
        "这是同一组5个开发布局的比较，不是新的留出测试集。每个布局3次重复不能视为独立布局。",
        "缓存令牌属于输入令牌子集，推理令牌属于输出令牌子集，不重复计入总令牌。",
        "运行时间区分策略冷启动、模拟器启动、原生执行与封装开销；API与动作时间可能重叠。",
        "相同输入回放与源版本固定只有显式 verified 标记通过时才记为审计通过。",
        "详细失败、缺失用量、逐对差值、5个布局均值及视频清单见 suite-report.json 和英文报告。"])
    return "\n".join(lines) + "\n"


def write_text(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", type=Path, required=True, help="Completed suite directory; no CURRENT pointer is consulted")
    parser.add_argument("--chinese-summary", action="store_true", help="Also write experiment-summary-zh.txt")
    args = parser.parse_args(argv)
    suite = args.suite.expanduser().resolve()
    try:
        protocol = read_json(suite / "protocol.json")
        controller = read_json(suite / "controller-status.json")
        if not isinstance(protocol, dict) or not isinstance(controller, dict):
            raise ReportError("protocol and controller must be JSON objects")
        jobs = validate_jobs(protocol, controller)
        issues, cases, videos = [], [], []
        for job in jobs:
            case, case_videos = collect_case(job, suite, issues)
            cases.append(case)
            videos.extend(case_videos)
        cases.sort(key=lambda case: (case["layout"], case["repeat"], case["condition"]))
        replay = replay_report(suite, issues)
        infrastructure = [case["name"] for case in cases if case["infrastructure_failure"]]
        if infrastructure:
            issues.append("Infrastructure failures invalidate the comparison: " + ", ".join(infrastructure))
        conditions = [summarize_condition([case for case in cases if case["condition"] == condition]) for condition in CONDITIONS]
        native_attempts = [attempt for case in cases for attempt in case["api_attempts"]]
        all_attempts = native_attempts + replay["api_attempts"]
        audit = dict(coverage_verified=True, terminal_planned_attempts=30,
                     native_completed_verified=sum(case["native_completed"] for case in cases),
                     expected_video_files=3 * sum(job["native_complete"] for job in jobs),
                     verified_video_files=sum(row["verified"] for row in videos),
                     infrastructure_failures=infrastructure, issues=issues)
        report = dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
                      suite=str(suite), final_controller_finished=True, comparison_valid=not issues,
                      planned_cases=30, layout_units=5, repeats_per_layout=3,
                      protocol=protocol, conditions=conditions, cases=cases,
                      paired_effects=paired_effects(cases), replay=replay,
                      native_api=token_summary(native_attempts),
                      all_recorded_api_including_replay=token_summary(all_attempts),
                      audit=audit, notes=NOTES,
                      runtime_definitions=dict(
                          cold_start_until_policy_ready_seconds="policy_ready_seconds - wrapper start (0); includes configuration and model load",
                          launch_gap_seconds="client_started_seconds - policy_ready_seconds",
                          simulator_startup_seconds="first_native_observation_seconds - client_started_seconds",
                          native_execution_seconds="native_finished_seconds - first_native_observation_seconds",
                          native_client_elapsed_seconds="native_finished_seconds - client_started_seconds; overlaps startup and execution",
                          teardown_seconds="elapsed_seconds - native_finished_seconds",
                          wrapper_overhead_seconds="launch gap + simulator startup + teardown; excludes cold start and native execution",
                          wrapper_elapsed_seconds="elapsed_seconds; full wrapper wall time"))
        write_text(suite / "video-manifest.json", json.dumps(dict(schema_version=1, videos=videos,
                   expected_files=audit["expected_video_files"], verified_files=audit["verified_video_files"]),
                   indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        write_text(suite / "cases.csv", csv_text(cases))
        write_text(suite / "suite-report.json", json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        write_text(suite / "experiment-summary.txt", english_summary(report))
        if args.chinese_summary:
            write_text(suite / "experiment-summary-zh.txt", chinese_summary(report))
        print(json.dumps(dict(report=str(suite / "suite-report.json"), comparison_valid=report["comparison_valid"],
                              planned_cases=30, native_completed=audit["native_completed_verified"],
                              infrastructure_failures=len(infrastructure), audit_issues=len(issues)), indent=2))
        return 0 if report["comparison_valid"] else 2
    except (ReportError, OSError, ValueError) as error:
        print("Report refused: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
