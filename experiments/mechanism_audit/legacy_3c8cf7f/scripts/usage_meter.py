#!/usr/bin/env python3
"""Scoped, content-free urllib usage accounting; standard library only.

No requests are sent by this module. See ../reports/usage_accounting.md.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import datetime as dt
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request


def _integer(value):
    return type(value) is int and value >= 0


def normalize_usage(payload):
    """Normalize provider counts without inventing absent or inconsistent counts."""
    result = dict(
        status="missing", schema=None, input_tokens=None, output_tokens=None,
        total_tokens=None, cached_input_tokens=None, uncached_input_tokens=None,
        reasoning_output_tokens=None, issues=[],
    )
    if not isinstance(payload, dict) or "usage" not in payload or payload["usage"] is None:
        return result
    usage = payload["usage"]
    if not isinstance(usage, dict):
        result.update(status="invalid", issues=["usage_is_not_an_object"])
        return result
    chat = any(key in usage for key in ("prompt_tokens", "completion_tokens"))
    responses = any(key in usage for key in ("input_tokens", "output_tokens"))
    if chat == responses:
        result.update(status="unknown", issues=["mixed_or_unrecognized_usage_schema"])
        return result
    in_key, out_key = (("prompt_tokens", "completion_tokens") if chat
                       else ("input_tokens", "output_tokens"))
    result["schema"] = "chat_completions" if chat else "responses"
    for source, target in ((in_key, "input_tokens"), (out_key, "output_tokens")):
        if _integer(usage.get(source)):
            result[target] = usage[source]
        else:
            result["issues"].append("missing_or_invalid_" + source)
    for source, child, target, parent in (
        (in_key + "_details", "cached_tokens", "cached_input_tokens", "input_tokens"),
        (out_key + "_details", "reasoning_tokens", "reasoning_output_tokens", "output_tokens"),
    ):
        details = usage.get(source)
        if details is None:
            continue
        if not isinstance(details, dict):
            result["issues"].append("invalid_" + source)
        elif child in details:
            value = details[child]
            if not _integer(value):
                result["issues"].append("invalid_" + target)
            elif result[parent] is not None and value > result[parent]:
                result["issues"].append(target + "_exceeds_parent")
            else:
                result[target] = value
    if result["input_tokens"] is not None and result["output_tokens"] is not None:
        result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
        if "total_tokens" in usage and (
            not _integer(usage["total_tokens"])
            or usage["total_tokens"] != result["total_tokens"]
        ):
            result["issues"].append("provider_total_mismatch")
    if result["input_tokens"] is not None and result["cached_input_tokens"] is not None:
        result["uncached_input_tokens"] = result["input_tokens"] - result["cached_input_tokens"]
    if result["issues"]:
        result["status"] = "invalid"
    elif result["total_tokens"] is None:
        result["status"] = "incomplete"
    else:
        result["status"] = "complete"
    return result


def _unknown_usage(reason):
    result = normalize_usage(None)
    result.update(status="unavailable", issues=[reason])
    return result


class _ResponseProxy:
    def __init__(self, meter, response, row, started):
        self._meter = meter
        self._response = response
        self._row = row
        self._started = started
        self._chunks = []
        self._size = 0
        self._complete = False
        self._finished = False
        self._truncated = False
        self._capture_error = False

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __enter__(self):
        entered = self._response.__enter__()
        if entered is not None:
            self._response = entered
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self._row["caller_error_type"] = exc_type.__name__
        try:
            return self._response.__exit__(exc_type, exc_value, traceback)
        except BaseException as error:
            self._row["error_type"] = type(error).__name__
            self._row["transport_outcome"] = "error"
            raise
        finally:
            self._finish()

    def _capture(self, value, complete=False):
        # Telemetry must never turn a successful read into an application error.
        try:
            if not self._row["stream_requested"] and not self._truncated:
                data = value.encode("utf-8") if isinstance(value, str) else bytes(value)
                self._size += len(data)
                if self._size > self._meter.max_response_bytes:
                    self._truncated = True
                    self._chunks.clear()
                else:
                    self._chunks.append(data)
            self._complete = self._complete or complete
        except Exception:
            self._capture_error = True

    def _read(self, method, *args, **kwargs):
        try:
            value = getattr(self._response, method)(*args, **kwargs)
        except BaseException as error:
            self._row["transport_outcome"] = "error"
            self._row["error_type"] = type(error).__name__
            self._finish()
            raise
        amount = args[0] if args else kwargs.get("amt", kwargs.get("size", -1))
        full_read = method == "read" and (amount is None or amount < 0)
        eof = not value and amount != 0
        self._capture(value, complete=full_read or eof)
        return value

    def read(self, *args, **kwargs):
        return self._read("read", *args, **kwargs)

    def read1(self, *args, **kwargs):
        return self._read("read1", *args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._read("readline", *args, **kwargs)

    def readlines(self, *args, **kwargs):
        # Delegate to preserve the underlying hint semantics.
        try:
            lines = self._response.readlines(*args, **kwargs)
        except BaseException as error:
            self._row.update(transport_outcome="error", error_type=type(error).__name__)
            self._finish()
            raise
        hint = args[0] if args else kwargs.get("hint", -1)
        self._capture(b"".join(lines), complete=hint is None or hint <= 0 or not lines)
        return lines

    def readinto(self, buffer):
        try:
            count = self._response.readinto(buffer)
        except BaseException as error:
            self._row.update(transport_outcome="error", error_type=type(error).__name__)
            self._finish()
            raise
        if count is not None:
            self._capture(memoryview(buffer)[:count], complete=count == 0 and len(buffer) > 0)
        return count

    def __iter__(self):
        return self

    def __next__(self):
        value = self.readline()
        if not value:
            raise StopIteration
        return value

    def close(self):
        try:
            return self._response.close()
        finally:
            self._finish()

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        try:
            if self._row["stream_requested"]:
                usage = _unknown_usage("streaming_not_supported")
            elif self._capture_error:
                usage = _unknown_usage("response_capture_failed")
            elif self._truncated:
                usage = _unknown_usage("response_exceeded_capture_limit")
            elif not self._complete:
                usage = _unknown_usage("response_not_fully_consumed")
            else:
                try:
                    usage = normalize_usage(json.loads(b"".join(self._chunks)))
                except (ValueError, UnicodeError):
                    usage = _unknown_usage("response_not_json")
            self._row["usage"] = usage
            self._row["elapsed_seconds"] = time.perf_counter() - self._started
            self._meter._emit(self._row)
        except Exception:
            self._meter.telemetry_errors += 1
        finally:
            self._chunks.clear()


class UsageMeter:
    """Temporarily wrap urllib.request.urlopen in this process.

    Single-threaded experiments only. The hook is process-global, captures every
    urllib urlopen in its scope, and neither alters authentication nor retries.
    """

    def __init__(self, path, *, include_endpoint=False, text_estimator=None,
                 max_response_bytes=16 * 1024 * 1024):
        if type(max_response_bytes) is not int or max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        self.path = Path(path)
        self.include_endpoint = include_endpoint
        self.text_estimator = text_estimator
        self.max_response_bytes = max_response_bytes
        self.rows = []
        self.telemetry_errors = 0
        self._original = None
        self._active = False
        self._responses = []
        self._attempt = 0
        self._logical_counter = 0
        self._logical_id = contextvars.ContextVar("physicalrsi_meter_logical_id", default=None)
        self._scope_id = None

    def __enter__(self):
        if self._active:
            raise RuntimeError("UsageMeter is already active")
        # A fresh scope ID makes appended JSONL logs safe to aggregate.
        import uuid
        self._scope_id = uuid.uuid4().hex
        self._original = urllib.request.urlopen
        self._hook = self._urlopen
        urllib.request.urlopen = self._hook
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        urllib.request.urlopen = self._original
        self._active = False
        for response in self._responses:
            response._finish()
        self._responses.clear()
        return False

    @contextlib.contextmanager
    def logical_call(self):
        """Group one caller operation's attempts; do not infer retries from bodies."""
        self._logical_counter += 1
        logical_id = self._logical_counter
        token = self._logical_id.set(logical_id)
        try:
            yield logical_id
        finally:
            self._logical_id.reset(token)

    def _request_metadata(self, request, args, kwargs):
        row = dict(request_bytes=None, request_text_token_estimate=None,
                   stream_requested=False)
        try:
            body = kwargs.get("data", args[0] if args else getattr(request, "data", None))
            if isinstance(body, (bytes, bytearray)):
                row["request_bytes"] = len(body)
                try:
                    payload = json.loads(body)
                except (ValueError, UnicodeError):
                    payload = None
                if isinstance(payload, dict):
                    row["stream_requested"] = payload.get("stream") is True
                    if self.text_estimator is not None:
                        try:
                            estimate = self.text_estimator(payload)
                            if _integer(estimate):
                                row["request_text_token_estimate"] = estimate
                            else:
                                row["estimate_error"] = "invalid_estimate"
                        except Exception:
                            row["estimate_error"] = "estimator_failed"
            if self.include_endpoint:
                url = urllib.parse.urlsplit(getattr(request, "full_url", request))
                row["endpoint_host"] = url.hostname
                row["endpoint_kind"] = ("chat_completions" if url.path.endswith("/chat/completions")
                                        else "responses" if url.path.endswith("/responses") else "other")
        except Exception:
            row["metadata_error"] = "request_metadata_unavailable"
        return row

    def _urlopen(self, url, *args, **kwargs):
        self._attempt += 1
        row = dict(
            schema_version=1, scope_id=self._scope_id, attempt_id=self._attempt,
            logical_call_id=self._logical_id.get(),
            timestamp_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            transport_outcome="response", http_status=None, error_type=None,
            caller_error_type=None, open_seconds=None,
        )
        row.update(self._request_metadata(url, args, kwargs))
        started = time.perf_counter()
        try:
            response = self._original(url, *args, **kwargs)
        except BaseException as error:
            row.update(
                transport_outcome="error", error_type=type(error).__name__,
                elapsed_seconds=time.perf_counter() - started,
                usage=_unknown_usage("opener_failed"),
            )
            code = getattr(error, "code", None)
            if type(code) is int:
                row["http_status"] = code
            self._emit(row)
            raise
        row["open_seconds"] = time.perf_counter() - started
        try:
            code = response.getcode()
            row["http_status"] = code if type(code) is int else None
        except Exception:
            pass
        proxy = _ResponseProxy(self, response, row, started)
        self._responses.append(proxy)
        return proxy

    def _emit(self, row):
        self.rows.append(row)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        except Exception:
            # Rows remain inspectable in memory. Never hide a transport exception.
            self.telemetry_errors += 1


def summarize(rows):
    """Aggregate only validated complete usage, exposing every denominator."""
    rows = list(rows)
    complete = [row for row in rows if row.get("usage", {}).get("status") == "complete"]
    summary = dict(
        physical_attempts=len(rows),
        response_attempts=sum(row.get("transport_outcome") == "response" for row in rows),
        transport_error_attempts=sum(row.get("transport_outcome") == "error" for row in rows),
        caller_error_attempts=sum(row.get("caller_error_type") is not None for row in rows),
        measured_complete_attempts=len(complete),
        unknown_or_invalid_usage_attempts=len(rows) - len(complete),
        usage_coverage=(len(complete) / len(rows) if rows else None),
        token_totals_scope="validated complete usage attempts only; unknown attempts excluded",
        input_tokens=None, output_tokens=None, total_tokens=None,
        elapsed_seconds_sum=sum(row.get("elapsed_seconds", 0) for row in rows),
        usage_issue_counts={},
    )
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        if complete:
            summary[key] = sum(row["usage"][key] for row in complete)
    for key in ("cached_input_tokens", "uncached_input_tokens", "reasoning_output_tokens"):
        subset = [row["usage"][key] for row in complete if row["usage"].get(key) is not None]
        summary[key] = sum(subset) if subset else None
        summary[key + "_known_attempts"] = len(subset)
    groups = {}
    for row in rows:
        logical = row.get("logical_call_id")
        if logical is not None:
            key = (row.get("scope_id"), logical)
            groups[key] = groups.get(key, 0) + 1
        for issue in row.get("usage", {}).get("issues", []):
            summary["usage_issue_counts"][issue] = summary["usage_issue_counts"].get(issue, 0) + 1
    summary["explicit_logical_calls"] = len(groups)
    summary["grouped_additional_attempts"] = sum(count - 1 for count in groups.values())
    summary["ungrouped_attempts_retry_status_unknown"] = sum(row.get("logical_call_id") is None for row in rows)
    summary["retry_interpretation"] = "additional attempts are retries only when each explicit group wraps one retrying operation"
    return summary


def main():
    parser = argparse.ArgumentParser(description="Summarize UsageMeter JSONL; never makes network calls.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    with args.log.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict) or row.get("schema_version") != 1:
                    raise ValueError("unsupported row schema")
                rows.append(row)
            except ValueError as error:
                parser.error(f"Invalid log row {line_number}: {type(error).__name__}")
    rendered = json.dumps(summarize(rows), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
