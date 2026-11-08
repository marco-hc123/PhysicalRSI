#!/usr/bin/env python3
"""Read-only verification of the frozen 2026-11-02 through 2026-11-08 report.

Uses only the standard library and files inside --package. It never executes
archived programs, connects to a host, regenerates results, or writes files.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8)


def verify(package: Path):
    package = package.resolve(strict=True)

    def path(name):
        candidate = package / name
        require(not candidate.is_symlink(), f"Symlink is not portable: {name}")
        resolved = candidate.resolve(strict=True)
        require(resolved.is_relative_to(package), f"Path escapes package: {name}")
        require(resolved.is_file(), f"Not a file: {name}")
        return resolved

    def digest(name):
        return hashlib.sha256(path(name).read_bytes()).hexdigest()

    def read(name):
        return json.loads(path(name).read_text(encoding="utf-8"))

    expected = {}
    for line in path("MANIFEST.sha256").read_text().splitlines():
        sha, name = line.split("  ", 1)
        require(name not in expected, f"Duplicate manifest path: {name}")
        require(digest(name) == sha, f"Manifest SHA mismatch: {name}")
        expected[name] = sha
    actual = set()
    total_bytes = 0
    sizes = defaultdict(lambda: {"files": 0, "bytes": 0})
    large = []
    for entry in package.rglob("*"):
        require(not entry.is_symlink(), f"Unexpected symlink: {entry}")
        if entry.is_file():
            name = entry.relative_to(package).as_posix()
            actual.add(name)
            size = entry.stat().st_size
            total_bytes += size
            group = sizes[Path(name).parts[0]]
            group["files"] += 1
            group["bytes"] += size
            large.append({"path": name, "bytes": size})
    require(actual == set(expected) | {"MANIFEST.sha256"}, "Manifest does not cover exact package contents")

    sources = read("07_verification/selected-source-index.json")
    seen_sources = set()
    for row in sources:
        name = row["package_path"]
        require(name not in seen_sources, f"Duplicate selected source: {name}")
        seen_sources.add(name)
        require(path(name).stat().st_size == row["bytes"] and digest(name) == row["sha256"],
                f"Selected source bytes/hash mismatch: {name}")

    rows = read("03_data/native_episodes_all.json")
    require(len(rows) == 312, "Expected 312 terminal-scored native executions")
    identities = set()
    partial_receipt_rows = []
    cohorts = defaultdict(list)
    for row in rows:
        identity = (row["batch"], row["phase"], row["task"], row["condition"], str(row["layout_key"]))
        require(identity not in identities, f"Duplicate native execution: {identity}")
        identities.add(identity)
        source = row["source"].split("#", 1)[0]
        name = "06_batch_evidence/" + source
        raw = read(name)
        if row["receipt_sha256"]:
            require(digest(name) == row["receipt_sha256"], f"Native receipt hash mismatch: {source}")
        else:
            require(row["batch"] == 43 and "natural_terminal_in_interrupted_cohort" in row["evidence_role"],
                    f"Unexplained absence of framework receipt: {identity}")
            partial_receipt_rows.append(row)
        if "episode_score" in raw:
            require(raw["state"] == "completed" and raw["natural_terminal"] and raw["native_exit_code"] == 0,
                    f"Nonterminal receipt included in scored ledger: {source}")
            score, success = raw["episode_score"], raw["success"]
            require(raw["layout_sha256"] == row["layout_sha256"], f"Layout hash mismatch: {source}")
        else:
            require("details" in raw, f"Unknown native result schema: {source}")
            matches = [value for key, value in raw["details"].items()
                       if value.get("layout_id", int(key)) == row["source_layout_id"]]
            require(len(matches) == 1, f"Ambiguous raw layout: {identity}")
            score, success = matches[0]["score"], matches[0]["success"]
        require(close(100 * score, row["score_100"]) and success is row["success"],
                f"Native score/success disagreement: {identity}")
        cohorts[identity[:4]].append(row)
    require(len(partial_receipt_rows) == 8, "Expected eight evaluator terminals without completed-cohort receipts")
    summary = read("03_data/recomputation_summary.json")
    batch_counts = dict(sorted(Counter(str(row["batch"]) for row in rows).items()))
    require(batch_counts == summary["native_batches"] and summary["native_total"] == len(rows),
            "Batch accounting mismatch")
    cohort_rows = read("03_data/cohort_results_all.json")
    require(len(cohort_rows) == len(cohorts), "Cohort count mismatch")
    cohort_keys = set()
    for row in cohort_rows:
        key = (row["batch"], row["phase"], row["task"], row["condition"])
        require(key not in cohort_keys, f"Duplicate cohort: {key}")
        cohort_keys.add(key)
        episodes = cohorts[key]
        require(row["native_executions"] == len(episodes), f"Cohort denominator mismatch: {key}")
        require(row["full_successes"] == sum(e["success"] for e in episodes), f"Cohort successes mismatch: {key}")
        require(close(row["mean_score_100"], sum(e["score_100"] for e in episodes) / len(episodes)),
                f"Cohort mean mismatch: {key}")
        require(json.loads(row["scores_100"]) == [e["score_100"] for e in episodes],
                f"Cohort score vector mismatch: {key}")

    b43 = "06_batch_evidence/43_system2_multitask/20261108_v1/native-validation/"
    final = read(b43 + "FINAL_SUMMARY.json")
    interruptions = read("03_data/interrupted_native_attempts_batch43.json")
    require(final["state"] == "completed" and interruptions == final["runtime_interruptions"],
            "Batch43 interruption table disagrees with final summary")
    require(len(interruptions) == final["runtime_interrupted_episodes"] == 2,
            "Expected two batch43 runtime interruptions")
    require(final["actual_native_episodes"] == 89 and final["formal_native_episodes"] == 88
            and final["actual_native_attempts"] == 91, "Batch43 smoke/scored/attempt counts mismatch")
    for row in interruptions:
        require(row["score"] is None and row["success"] is None and row["natural_terminal"] is False,
                "Interrupted outcome must remain unknown, not zero")
        detail = read(b43 + row["phase"] + "/analysis/partial-evidence-verification.json")
        require(detail["state"] == "verified_partial" and detail["valid_native_episodes"] == 4
                and detail["interrupted_attempts"] == 1 and detail["policy_zero_score"] is False,
                "Partial-cohort classification mismatch")
        require(detail["interrupted_layout_id"] == row["layout_id"]
                and detail["interrupted_actor_uuid"] == row["actor_uuid"], "Interrupted identity mismatch")
        terminals = [r for r in partial_receipt_rows if r["phase"] == row["phase"]]
        require(sorted(r["source_layout_id"] for r in terminals) == sorted(detail["completed_layout_ids"]),
                "Partial-cohort terminal layouts mismatch")
        require(row["layout_id"] not in [r["source_layout_id"] for r in terminals],
                "Interrupted layout incorrectly included as terminal")
    legacy = read("06_batch_evidence/25_system2_model_swap/38_system2_gpt61sol_20261102/analysis-summary.json")
    require(legacy["infrastructure_interrupted_attempts"] == 1
            and legacy["validation_native_completed"] == 10 and legacy["total_native_dispatch_attempts"] == 11,
            "Nov2 infrastructure interruption accounting mismatch")

    # These checks reconcile saved usage ledgers, not independent vendor billing.
    ledger_entries = {}
    duplicate_entries = 0
    for ledger in sorted((package / "06_batch_evidence").rglob("*ledger*.json")):
        name = ledger.relative_to(package).as_posix()
        batch = int(ledger.relative_to(package / "06_batch_evidence").parts[0][:2])
        records = read(name)
        records = records["attempts"] if isinstance(records, dict) else records
        for entry in records:
            key = (batch, entry.get("id", entry.get("request_id")))
            require(key[1] is not None, f"Missing ledger request identity: {name}")
            if key in ledger_entries:
                prior = ledger_entries[key]
                require(prior["usage"] == entry["usage"] and prior["http_status"] == entry["http_status"]
                        and prior.get("request_sha256") == entry.get("request_sha256"),
                        f"Cumulative ledger snapshots disagree: {key}")
                duplicate_entries += 1
            else:
                ledger_entries[key] = entry
    api_rows = read("03_data/api_requests.json")
    require(len(api_rows) == len(ledger_entries) == 44, "Expected 44 unique saved API requests")
    api_keys = set()
    for row in api_rows:
        key = (row["batch"], row["id"])
        require(key not in api_keys, f"Repeated derived API request: {key}")
        api_keys.add(key)
        entry = ledger_entries[key]
        usage = entry["usage"]
        inp, out = usage["prompt_tokens"], usage["completion_tokens"]
        details = usage.get("prompt_tokens_details") or {}
        cached, written = details.get("cached_tokens", 0), details.get("cache_write_tokens", 0)
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        require(inp + out == usage["total_tokens"] and 0 <= cached + written <= inp and 0 <= reasoning <= out,
                f"Invalid token accounting: {key}")
        values = {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out,
                  "cached_input_subset": cached, "cache_write_input_subset": written,
                  "reasoning_output_subset": reasoning, "http_status": entry["http_status"]}
        require(all(row[k] == v for k, v in values.items()), f"Derived API usage differs from ledger: {key}")
        cost = ((inp - cached - written) * 2 + cached * .1 + written * 2.5 + out * 10) / 1e6
        require(close(cost, row["recomputed_estimate_usd"]), f"Frozen usage estimate differs: {key}")
    totals = {"input": sum(r["input_tokens"] for r in api_rows),
              "output": sum(r["output_tokens"] for r in api_rows),
              "total": sum(r["total_tokens"] for r in api_rows),
              "historical_usage_estimate_usd": sum(r["recomputed_estimate_usd"] for r in api_rows)}
    require(totals["input"] == summary["total_input_tokens"] == 415830
            and totals["output"] == summary["total_output_tokens"] == 146476
            and close(totals["historical_usage_estimate_usd"], summary["recomputed_estimate_usd"]),
            "Overall API accounting mismatch")

    return {"state": "passed", "package_files": len(actual), "package_bytes": total_bytes,
            "manifest_members_verified": len(expected), "selected_source_copies_verified": len(sources),
            "terminal_scored_native_executions": len(rows), "native_batches": batch_counts,
            "cohorts_verified": len(cohort_rows), "evaluator_terminals_without_complete_cohort_receipts": 8,
            "batch43_runtime_interruptions_unknown_score": 2,
            "batch25_historical_infrastructure_interruptions": 1,
            "api_requests_from_unique_saved_ledger_entries": len(api_rows),
            "cumulative_ledger_entries_deduplicated": duplicate_entries, "api_usage": totals,
            "directory_sizes": dict(sorted(sizes.items())),
            "largest_files": sorted(large, key=lambda r: r["bytes"], reverse=True)[:10],
            "limitations": ["Execution counts are not a pooled benchmark success-rate denominator.",
                            "Eight heldout terminals use raw evaluator evidence, not complete-cohort framework receipts.",
                            "API checks reconcile archived ledgers; usage estimates are not invoices.",
                            "This checks selected reporting evidence, not a complete server/raw-media mirror.",
                            "Frozen 08_methods build scripts retain their original source-directory assumptions."],
            "new_experiments": 0, "new_model_requests": 0, "writes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True, help="Root containing MANIFEST.sha256")
    args = parser.parse_args()
    print(json.dumps(verify(args.package), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
