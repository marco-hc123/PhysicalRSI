#!/usr/bin/env python3
"""Version two offline corrections to a finished catalogue experiment report.

Run with system Python: python3 cloud_catalogue_analysis_corrections.py --suite PATH

Reads suite-report.json, controller-status.json, and replay/replay-summary.json.
All three must describe a finished experiment: exactly 30 terminal native
attempts and ten replay logical calls. This script does not import or modify
frozen experiment code, issue API requests, read credentials, or run robots.

Writes suite-report-v2.json, experiment-summary-v2.txt, and
experiment-summary-v2-zh.txt. The original report and summaries are preserved.
Corrections affect replay selection comparison and replay latency labels only.
Exit 0: corrected report written with the original valid comparison; exit 2:
corrected report written retaining original invalid comparison; exit 1: refused.
"""

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


CONDITIONS = ("projected", "unprojected")
JOB_FIELDS = ("name", "condition", "layout", "repeat", "pair_id", "phase")
OUTCOMES = ("native_completed", "planner_failure", "execution_failure", "infrastructure_failure")
REVISION = "catalogue-analysis-v2"


class CorrectionError(Exception):
    pass


def read_object(path):
    try:
        data = path.read_bytes()
        value = json.loads(data)
    except (OSError, ValueError) as error:
        raise CorrectionError("{}: {}".format(path, error)) from error
    if not isinstance(value, dict):
        raise CorrectionError(str(path) + ": expected a JSON object")
    return value, data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def nonnegative(value):
    return (value if isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0 else None)


def difference(left, right):
    return left - right if left is not None and right is not None else None


def average(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def indexed(rows, fields, context):
    if not isinstance(rows, list):
        raise CorrectionError(context + ": expected an array")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or any(field not in row for field in fields):
            raise CorrectionError(context + ": missing identifying fields")
        key = tuple(row[field] for field in fields)
        try:
            if key in result:
                raise CorrectionError(context + ": duplicate record " + repr(key))
            result[key] = row
        except TypeError as error:
            raise CorrectionError(context + ": invalid identifying fields") from error
    return result


def validate_finished(report, controller, raw_replay):
    if (report.get("schema_version") != 1 or report.get("final_controller_finished") is not True
            or report.get("planned_cases") != 30):
        raise CorrectionError("original report must be a finished schema version 1 report with 30 planned cases")
    if type(report.get("comparison_valid")) is not bool:
        raise CorrectionError("original report must retain an explicit comparison_valid flag")
    if controller.get("finished") is not True:
        raise CorrectionError("controller is unfinished; corrections cannot create a provisional report")
    cases = indexed(report.get("cases"), ("name",), "original report cases")
    jobs = indexed(controller.get("jobs"), ("name",), "controller jobs")
    expected_native = {(condition, layout, repeat) for condition in CONDITIONS
                       for layout in range(1, 6) for repeat in range(1, 4)}
    if len(cases) != 30 or set(cases) != set(jobs):
        raise CorrectionError("original report and controller must identify the same 30 cases")
    for name, case in cases.items():
        job = jobs[name]
        if any(case.get(field) != job.get(field) for field in JOB_FIELDS):
            raise CorrectionError("original report/controller job mismatch: " + str(name))
        if (job.get("outcome") not in OUTCOMES or type(job.get("native_complete")) is not bool
                or job["native_complete"] != (job["outcome"] == "native_completed")
                or "exit_code" not in job or "error" not in job):
            raise CorrectionError("controller has a nonterminal or inconsistent job: " + str(name))
        if (case.get("outcome") != job["outcome"] or case.get("exit_code") != job["exit_code"]
                or case.get("native_complete_declared") != job["native_complete"]):
            raise CorrectionError("original report/controller outcome mismatch: " + str(name))
    covered = indexed(list(cases.values()), ("condition", "layout", "repeat"), "native coverage")
    if set(covered) != expected_native:
        raise CorrectionError("native coverage must be five layouts x two conditions x three repeats")
    replay = report.get("replay")
    if not isinstance(replay, dict) or replay.get("finished") is not True or raw_replay.get("finished") is not True:
        raise CorrectionError("both original report replay and raw replay must be finished")
    report_rows = indexed(replay.get("rows"), ("layout", "condition"), "report replay")
    raw_rows = indexed(raw_replay.get("rows"), ("layout", "condition"), "raw replay")
    expected_replay = {(layout, condition) for layout in range(1, 6) for condition in CONDITIONS}
    if set(report_rows) != expected_replay or set(raw_rows) != expected_replay:
        raise CorrectionError("original and raw replay must cover the same ten logical calls")
    for key, raw in raw_rows.items():
        old = report_rows[key]
        for field in ("plan", "contract_valid", "error", "seconds", "usage"):
            if old.get(field) != raw.get(field):
                raise CorrectionError("original/raw replay mismatch for {} at {}".format(field, key))
    paired = indexed(replay.get("paired_effects"), ("layout",), "original replay pairs")
    if set(paired) != {(layout,) for layout in range(1, 6)}:
        raise CorrectionError("original report must contain exactly five replay pair effects")
    return report_rows, raw_rows


def selection(plan):
    """A selection comprises composition and ordered operations, never rationale."""
    if (not isinstance(plan, dict) or not isinstance(plan.get("composition"), str)
            or not plan["composition"].strip() or not isinstance(plan.get("operations"), list)
            or any(not isinstance(operation, str) for operation in plan["operations"])):
        return None
    return dict(composition=plan["composition"], operations=list(plan["operations"]))


def transport_seconds(report_row, raw_row):
    """Use the same complete attempt-duration sum as the report's API summary."""
    api = report_row.get("api")
    if not isinstance(api, dict):
        raise CorrectionError("report replay row lacks its API attempt summary")
    recorded = nonnegative(api.get("api_seconds"))
    attempts = raw_row.get("attempts")
    if isinstance(attempts, list) and attempts:
        if any(not isinstance(attempt, dict) for attempt in attempts):
            raise CorrectionError("raw replay has a malformed transport ledger")
        values = [nonnegative(attempt.get("seconds")) for attempt in attempts]
        if any(value is None for value in values):
            return None, "incomplete raw transport durations"
        total = sum(values)
        if recorded is None or not math.isclose(recorded, total, rel_tol=1e-12, abs_tol=1e-9):
            raise CorrectionError("report API seconds disagree with raw transport ledger")
        if api.get("transport_calls") != len(attempts):
            raise CorrectionError("report transport count disagrees with raw replay ledger")
        return total, "sum(raw replay attempts[].seconds), verified against row.api.api_seconds"
    count = api.get("transport_calls")
    if recorded is None or api.get("api_seconds_reported_calls") != count or not count:
        return None, "incomplete report API durations"
    # Compatibility with the original replay schema, which had one attempt per
    # row and no retry ledger. Keep the evidence source explicit in v2.
    return recorded, "row.api.api_seconds; raw replay has no separate attempt ledger"


def apply_corrections(report, report_rows, raw_rows):
    corrected = copy.deepcopy(report)
    changes = []
    for row in corrected["replay"]["rows"]:
        key = row["layout"], row["condition"]
        seconds, source = transport_seconds(report_rows[key], raw_rows[key])
        row["transport_api_seconds"] = seconds
        row["transport_api_seconds_source"] = source
        row["logical_call_seconds"] = nonnegative(raw_rows[key].get("seconds"))
        row["selection_identity"] = selection(raw_rows[key].get("plan"))
    rows = indexed(corrected["replay"]["rows"], ("layout", "condition"), "corrected replay")
    for pair in corrected["replay"]["paired_effects"]:
        layout = pair["layout"]
        projected, unprojected = rows[layout, "projected"], rows[layout, "unprojected"]
        projected_selection, unprojected_selection = projected["selection_identity"], unprojected["selection_identity"]
        comparable = projected_selection is not None and unprojected_selection is not None
        previous = {key: pair.get(key) for key in ("selection_changed", "api_seconds_difference")}
        pair.update(selection_comparable=comparable,
                    projected_selection=projected_selection, unprojected_selection=unprojected_selection,
                    selection_changed=projected_selection != unprojected_selection if comparable else None,
                    selection_comparison_fields=["composition", "operations (ordered)"],
                    api_seconds_difference=difference(projected["transport_api_seconds"], unprojected["transport_api_seconds"]),
                    logical_call_seconds_difference=difference(projected["logical_call_seconds"], unprojected["logical_call_seconds"]),
                    projected_transport_api_seconds=projected["transport_api_seconds"],
                    unprojected_transport_api_seconds=unprojected["transport_api_seconds"],
                    projected_logical_call_seconds=projected["logical_call_seconds"],
                    unprojected_logical_call_seconds=unprojected["logical_call_seconds"])
        if not comparable:
            pair["selection_unavailable_reason"] = "At least one plan lacks a usable composition and ordered operations list."
        changes.append(dict(layout=layout, version_1=previous,
                            version_2={key: pair[key] for key in ("selection_changed", "api_seconds_difference", "logical_call_seconds_difference")}))
    pairs = corrected["replay"]["paired_effects"]
    corrected["replay"]["selection_summary"] = dict(
        definition="composition plus ordered operations; rationale and other metadata are ignored",
        comparable_pairs=sum(pair["selection_comparable"] for pair in pairs),
        changed_pairs=sum(pair["selection_changed"] is True for pair in pairs),
        unchanged_pairs=sum(pair["selection_changed"] is False for pair in pairs),
        unavailable_pairs=sum(pair["selection_changed"] is None for pair in pairs))
    corrected["replay"]["latency_definitions"] = dict(
        api_seconds_difference="projected minus unprojected sum of transport attempts[].seconds; consistent with condition api.api_seconds",
        logical_call_seconds_difference="projected minus unprojected replay row.seconds; includes retry backoff and local call processing",
        overlap="Transport duration and logical call latency overlap; do not add them.")
    corrected["replay"]["latency_summary"] = dict(
        mean_paired_transport_api_seconds_difference=average([pair["api_seconds_difference"] for pair in pairs]),
        mean_paired_logical_call_seconds_difference=average([pair["logical_call_seconds_difference"] for pair in pairs]),
        transport_pairs_observed=sum(pair["api_seconds_difference"] is not None for pair in pairs),
        logical_call_pairs_observed=sum(pair["logical_call_seconds_difference"] is not None for pair in pairs))
    return corrected, changes


def format_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    return "{:.6f}".format(value) if isinstance(value, float) else str(value)


def summaries(report):
    provenance = report["correction_provenance"]
    summary = report["replay"]["selection_summary"]
    english = ["Catalogue projection experiment — corrected final report v2",
               "Suite: " + report["suite"],
               "Original comparison validity retained: " + str(report["comparison_valid"]),
               "Original report: suite-report.json; SHA-256: " + provenance["inputs"]["suite-report.json"],
               "Correction script SHA-256: " + provenance["script_sha256"],
               "Correction time (UTC): " + provenance["generated_utc"], "",
               "Corrections:",
               "- Replay selection identity uses composition and ordered operations. Rationale and other metadata are ignored.",
               "- Replay API differences use summed transport-attempt seconds, matching condition API summaries.",
               "- Logical call latency, including retry backoff and local processing, is reported separately.",
               "- Missing or malformed selections yield null; they are not counted as unchanged selections.", ""]
    chinese = ["目录投影实验：修正后的最终报告 v2", "实验目录：" + report["suite"],
               "原报告的比较有效性保持不变：" + str(report["comparison_valid"]),
               "原报告 suite-report.json 的 SHA-256：" + provenance["inputs"]["suite-report.json"],
               "修正脚本 SHA-256：" + provenance["script_sha256"],
               "修正时间（UTC）：" + provenance["generated_utc"], "",
               "修正内容：回放选择只比较 composition 与有序 operations，忽略理由等元数据；API耗时差使用各次传输耗时之和；逻辑调用耗时单列，包含重试等待与本地处理。缺失或格式错误的选择记为 null。", ""]
    for condition in report["conditions"]:
        api = condition["api"]
        english.append("{}: {}/{} successes; {} native completions; {} transport attempts; {} reported total tokens; tokens/success={}.".format(
            condition["condition"], condition["successes"], condition["evaluations"], condition["native_completed"],
            api["transport_calls"], api["total_tokens"], format_value(condition["total_tokens_per_observed_success"])))
        chinese.append("{}：成功 {}/{}，完成原生评估 {}，传输 {} 次，已报告总令牌 {}，每次成功令牌 {}。".format(
            condition["condition"], condition["successes"], condition["evaluations"], condition["native_completed"],
            api["transport_calls"], api["total_tokens"], format_value(condition["total_tokens_per_observed_success"])))
    english.extend(["", "Replay pairs: {} comparable, {} changed selections, {} unchanged, {} unavailable.".format(
        summary["comparable_pairs"], summary["changed_pairs"], summary["unchanged_pairs"], summary["unavailable_pairs"])])
    chinese.extend(["", "回放配对：可比较 {} 对，选择改变 {} 对，未改变 {} 对，不可用 {} 对。".format(
        summary["comparable_pairs"], summary["changed_pairs"], summary["unchanged_pairs"], summary["unavailable_pairs"])])
    for pair in report["replay"]["paired_effects"]:
        values = [pair["layout"], format_value(pair["selection_changed"]),
                  format_value(pair["api_seconds_difference"]), format_value(pair["logical_call_seconds_difference"])]
        english.append("Layout {}: selection_changed={}; transport API seconds difference={}; logical call seconds difference={}.".format(*values))
        chinese.append("布局 {}：选择改变={}，传输API耗时差={}秒，逻辑调用耗时差={}秒。".format(*values))
    english.extend(["", "All differences are projected minus unprojected. Transport and logical timings overlap.",
                    "Native outcomes, denominators, token totals, replay audit flags, and original audit issues are preserved.",
                    "The five layouts are developmental layouts. Three repeats per layout are not independent layouts; no new confidence interval is introduced.",
                    "Full projection restores static task-label/code identities and is not pure compression.",
                    "Original artifacts remain unchanged. See suite-report-v2.json for correction provenance and original audit findings."])
    chinese.extend(["", "差值方向均为 projected 减 unprojected；传输时间与逻辑调用时间重叠，不相加。",
                    "原生结果、评估分母、令牌总数、回放验证标记及原始审计问题均保留。",
                    "这5个布局属于开发集，每个布局3次重复不是独立布局；本修正不添加置信区间。",
                    "完整投影恢复静态任务标签与代码身份，并非纯粹压缩。",
                    "原始文件保持不变；完整修正来源与审计问题见 suite-report-v2.json。"])
    issues = report.get("audit", {}).get("issues", [])
    if issues:
        english.extend(["", "Original audit issues (preserved):"] + ["- " + str(issue) for issue in issues])
        chinese.extend(["", "原始审计问题（原样保留）："] + ["- " + str(issue) for issue in issues])
    return "\n".join(english) + "\n", "\n".join(chinese) + "\n"


def write_text(path, text):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", type=Path, required=True)
    args = parser.parse_args(argv)
    suite = args.suite.expanduser().resolve()
    try:
        inputs = {}
        objects = {}
        for name in ("suite-report.json", "controller-status.json", "replay/replay-summary.json"):
            objects[name], inputs[name] = read_object(suite / name)
        original = objects["suite-report.json"]
        report_rows, raw_rows = validate_finished(original, objects["controller-status.json"], objects["replay/replay-summary.json"])
        corrected, changes = apply_corrections(original, report_rows, raw_rows)
        generated = datetime.now(timezone.utc).isoformat()
        corrected["schema_version"] = 2
        corrected["report_revision"] = REVISION
        corrected["original_generated_utc"] = original.get("generated_utc")
        corrected["generated_utc"] = generated
        corrected["correction_provenance"] = dict(
            revision=REVISION, generated_utc=generated, original_report="suite-report.json",
            original_schema_version=original["schema_version"], original_comparison_valid=original["comparison_valid"],
            inputs={name: digest(data) for name, data in inputs.items()},
            script=Path(__file__).name, script_sha256=digest(Path(__file__).read_bytes()),
            raw_evidence_consistency_verified=True, original_artifacts_preserved=True,
            correction_scope=["replay selection_changed and selection identity",
                              "replay transport API timing differences and separate logical-call timing"],
            pair_changes=changes)
        english, chinese = summaries(corrected)
        # Detect concurrent changes before publishing v2. Never rewrite inputs.
        if any((suite / name).read_bytes() != data for name, data in inputs.items()):
            raise CorrectionError("input evidence changed during postprocessing; refusing to write v2")
        write_text(suite / "suite-report-v2.json", json.dumps(corrected, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        write_text(suite / "experiment-summary-v2.txt", english)
        write_text(suite / "experiment-summary-v2-zh.txt", chinese)
        print(json.dumps(dict(report=str(suite / "suite-report-v2.json"), revision=REVISION,
                              comparison_valid=corrected["comparison_valid"],
                              replay_selection_summary=corrected["replay"]["selection_summary"],
                              original_report_sha256=digest(inputs["suite-report.json"])), indent=2))
        return 0 if corrected["comparison_valid"] else 2
    except (CorrectionError, OSError, ValueError, TypeError, KeyError) as error:
        print("Corrections refused: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
