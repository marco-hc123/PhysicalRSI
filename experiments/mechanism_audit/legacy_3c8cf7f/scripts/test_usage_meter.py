#!/usr/bin/env python3
"""Offline contract tests for usage_meter; no real HTTP requests or credentials."""

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from usage_meter import UsageMeter, normalize_usage, summarize


CHAT = {"usage": {"prompt_tokens": 1000, "completion_tokens": 100,
                  "total_tokens": 1100, "prompt_tokens_details": {"cached_tokens": 950},
                  "completion_tokens_details": {"reasoning_tokens": 70}}}
RESPONSES = {"usage": {"input_tokens": 200, "output_tokens": 30,
                       "input_tokens_details": {"cached_tokens": 150},
                       "output_tokens_details": {"reasoning_tokens": 20}}}


class Response(io.BytesIO):
    def getcode(self):
        return 200


def response(payload=CHAT):
    return Response(json.dumps(payload).encode())


def request(**extra):
    body = {"messages": [{"role": "user", "content": "PRIVATE_PROMPT_MARKER"}], **extra}
    return urllib.request.Request(
        "https://test.invalid/private-path-secret/chat/completions?api_key=QUERY_SECRET",
        data=json.dumps(body).encode(), headers={"Authorization": "Bearer HEADER_SECRET"},
    )


class UsageMeterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "usage.jsonl"

    def tearDown(self):
        self.temporary.cleanup()

    def capture(self, payload=CHAT, **options):
        with patch("urllib.request.urlopen", return_value=response(payload)):
            with UsageMeter(self.path, **options) as meter:
                with urllib.request.urlopen(request()) as stream:
                    actual = stream.read()
            self.assertEqual(json.loads(actual), payload)
        return meter

    def test_chat_subsets_are_not_double_counted(self):
        usage = normalize_usage(CHAT)
        self.assertEqual(usage["status"], "complete")
        self.assertEqual(usage["total_tokens"], 1100)
        self.assertEqual(usage["uncached_input_tokens"], 50)
        self.assertEqual(usage["reasoning_output_tokens"], 70)

    def test_responses_schema(self):
        usage = normalize_usage(RESPONSES)
        self.assertEqual(usage["schema"], "responses")
        self.assertEqual(usage["total_tokens"], 230)
        self.assertEqual(usage["uncached_input_tokens"], 50)

    def test_missing_usage_and_optional_details_remain_null(self):
        self.assertIsNone(normalize_usage({})["total_tokens"])
        usage = normalize_usage({"usage": {"input_tokens": 0, "output_tokens": 0}})
        self.assertEqual(usage["total_tokens"], 0)
        self.assertIsNone(usage["cached_input_tokens"])
        self.assertIsNone(usage["reasoning_output_tokens"])

    def test_invalid_usage_formats_are_flagged(self):
        for usage in ([], {"tokens": 12}, {"prompt_tokens": 1, "input_tokens": 1},
                      {"input_tokens": True, "output_tokens": 3},
                      {"input_tokens": -1, "output_tokens": 3},
                      {"input_tokens": 2}):
            with self.subTest(usage=usage):
                self.assertNotEqual(normalize_usage({"usage": usage})["status"], "complete")

    def test_inconsistent_subsets_and_provider_total_are_flagged(self):
        cases = [
            {"input_tokens": 10, "output_tokens": 2, "input_tokens_details": {"cached_tokens": 11}},
            {"input_tokens": 10, "output_tokens": 2, "output_tokens_details": {"reasoning_tokens": 3}},
            {"input_tokens": 10, "output_tokens": 2, "total_tokens": 999},
            {"input_tokens": 10, "output_tokens": 2, "input_tokens_details": "unknown"},
        ]
        for case in cases:
            with self.subTest(case=case):
                usage = normalize_usage({"usage": case})
                self.assertEqual(usage["status"], "invalid")
                self.assertTrue(usage["issues"])

    def test_response_and_bytes_are_preserved(self):
        meter = self.capture()
        self.assertEqual(len(meter.rows), 1)
        self.assertEqual(meter.rows[0]["usage"]["total_tokens"], 1100)
        self.assertEqual(meter.rows[0]["http_status"], 200)
        self.assertGreaterEqual(meter.rows[0]["elapsed_seconds"], 0)
        self.assertEqual(meter.telemetry_errors, 0)

    def test_url_keyword_argument_is_supported(self):
        with patch("urllib.request.urlopen", return_value=response()) as opener:
            with UsageMeter(self.path) as meter:
                with urllib.request.urlopen(url=request(), timeout=2) as stream:
                    json.load(stream)
            self.assertEqual(opener.call_args.kwargs, {"timeout": 2})
        self.assertEqual(meter.rows[0]["usage"]["total_tokens"], 1100)

    def test_retry_transport_error_and_explicit_group(self):
        error = urllib.error.URLError("PRIVATE_ERROR_MESSAGE")
        with patch("urllib.request.urlopen", side_effect=[error, response()]):
            with UsageMeter(self.path) as meter:
                with meter.logical_call():
                    with self.assertRaises(urllib.error.URLError) as raised:
                        urllib.request.urlopen(request())
                    self.assertIs(raised.exception, error)
                    with urllib.request.urlopen(request()) as stream:
                        json.load(stream)
        result = summarize(meter.rows)
        self.assertEqual(result["physical_attempts"], 2)
        self.assertEqual(result["grouped_additional_attempts"], 1)
        self.assertEqual(result["transport_error_attempts"], 1)
        self.assertEqual(result["measured_complete_attempts"], 1)
        self.assertEqual(result["unknown_or_invalid_usage_attempts"], 1)
        self.assertEqual(result["usage_coverage"], 0.5)
        self.assertNotIn("PRIVATE_ERROR_MESSAGE", self.path.read_text())

    def test_http_error_body_and_identity_are_preserved(self):
        body = io.BytesIO(b"PRIVATE_ERROR_BODY")
        error = urllib.error.HTTPError("https://test.invalid", 429, "PRIVATE_REASON", {}, body)
        with patch("urllib.request.urlopen", side_effect=error):
            with UsageMeter(self.path) as meter:
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request())
                self.assertIs(caught.exception, error)
                self.assertEqual(caught.exception.read(), b"PRIVATE_ERROR_BODY")
        self.assertEqual(meter.rows[0]["http_status"], 429)
        self.assertIsNone(meter.rows[0]["usage"]["total_tokens"])
        self.assertNotIn("PRIVATE_", self.path.read_text())

    def test_invalid_json_does_not_change_caller_exception(self):
        with patch("urllib.request.urlopen", return_value=Response(b"invalid JSON")):
            with UsageMeter(self.path) as meter:
                with self.assertRaises(json.JSONDecodeError):
                    with urllib.request.urlopen(request()) as stream:
                        json.load(stream)
        row = meter.rows[0]
        self.assertEqual(row["caller_error_type"], "JSONDecodeError")
        self.assertIn("response_not_json", row["usage"]["issues"])

    def test_missing_usage_is_unknown_not_zero(self):
        meter = self.capture({"choices": []})
        result = summarize(meter.rows)
        self.assertIsNone(result["total_tokens"])
        self.assertEqual(result["unknown_or_invalid_usage_attempts"], 1)
        self.assertEqual(result["ungrouped_attempts_retry_status_unknown"], 1)

    def test_no_secrets_or_content_in_log(self):
        meter = self.capture({**CHAT, "private_response": "PRIVATE_RESPONSE_MARKER"}, include_endpoint=True)
        text = self.path.read_text()
        for value in ("PRIVATE_PROMPT_MARKER", "PRIVATE_RESPONSE_MARKER", "HEADER_SECRET",
                      "QUERY_SECRET", "private-path-secret", "Authorization", "messages"):
            self.assertNotIn(value, text)
        self.assertEqual(meter.rows[0]["endpoint_host"], "test.invalid")
        self.assertEqual(meter.rows[0]["endpoint_kind"], "chat_completions")

    def test_default_endpoint_absent_estimator_separate(self):
        meter = self.capture(text_estimator=lambda payload: len(payload["messages"]))
        row = meter.rows[0]
        self.assertNotIn("endpoint_host", row)
        self.assertEqual(row["request_text_token_estimate"], 1)
        self.assertEqual(row["usage"]["total_tokens"], 1100)

    def test_estimator_and_logging_failures_do_not_change_requests(self):
        def bad_estimator(payload):
            raise ValueError("PRIVATE_ESTIMATOR_ERROR")
        self.path.mkdir()
        meter = self.capture(text_estimator=bad_estimator)
        self.assertEqual(meter.telemetry_errors, 1)
        self.assertEqual(meter.rows[0]["estimate_error"], "estimator_failed")

    def test_logging_failure_does_not_mask_transport_error(self):
        self.path.mkdir()
        original_error = TimeoutError("PRIVATE_TIMEOUT")
        with patch("urllib.request.urlopen", side_effect=original_error):
            with UsageMeter(self.path) as meter:
                with self.assertRaises(TimeoutError) as caught:
                    urllib.request.urlopen(request())
                self.assertIs(caught.exception, original_error)
        self.assertEqual(meter.telemetry_errors, 1)

    def test_original_opener_restored_on_exception(self):
        original = urllib.request.urlopen
        with self.assertRaisesRegex(RuntimeError, "test exception"):
            with UsageMeter(self.path):
                self.assertIsNot(urllib.request.urlopen, original)
                raise RuntimeError("test exception")
        self.assertIs(urllib.request.urlopen, original)

    def test_streaming_forwarded_without_claiming_usage(self):
        content = b"data: PRIVATE_STREAM\n\ndata: [DONE]\n\n"
        with patch("urllib.request.urlopen", return_value=Response(content)):
            with UsageMeter(self.path) as meter:
                with urllib.request.urlopen(request(stream=True)) as stream:
                    self.assertEqual(stream.read(), content)
        self.assertIn("streaming_not_supported", meter.rows[0]["usage"]["issues"])
        self.assertIsNone(meter.rows[0]["usage"]["total_tokens"])
        self.assertNotIn("PRIVATE_STREAM", self.path.read_text())

    def test_partial_response_is_not_claimed_complete(self):
        with patch("urllib.request.urlopen", return_value=response()):
            with UsageMeter(self.path) as meter:
                with urllib.request.urlopen(request()) as stream:
                    self.assertEqual(stream.read(1), b"{")
        self.assertIn("response_not_fully_consumed", meter.rows[0]["usage"]["issues"])

    def test_incremental_reads_preserve_content(self):
        raw = json.dumps(CHAT).encode()
        with patch("urllib.request.urlopen", return_value=Response(raw)):
            with UsageMeter(self.path) as meter:
                with urllib.request.urlopen(request()) as stream:
                    first = stream.read(7)
                    self.assertEqual(first + stream.read(), raw)
        self.assertEqual(meter.rows[0]["usage"]["total_tokens"], 1100)

    def test_capture_size_limit_does_not_truncate_caller_bytes(self):
        meter = self.capture(max_response_bytes=2)
        self.assertIn("response_exceeded_capture_limit", meter.rows[0]["usage"]["issues"])

    def test_summary_excludes_invalid_counts_and_exposes_subset_denominators(self):
        cases = [CHAT, RESPONSES, {}, {"usage": {"input_tokens": 3, "output_tokens": 4}},
                 {"usage": {"input_tokens": 10, "output_tokens": 1, "total_tokens": 999}}]
        rows = [{"usage": normalize_usage(case)} for case in cases]
        result = summarize(rows)
        self.assertEqual(result["measured_complete_attempts"], 3)
        self.assertEqual(result["unknown_or_invalid_usage_attempts"], 2)
        self.assertEqual(result["total_tokens"], 1337)
        self.assertEqual(result["cached_input_tokens"], 1100)
        self.assertEqual(result["cached_input_tokens_known_attempts"], 2)

    def test_append_scopes_do_not_merge_logical_groups(self):
        for _ in range(2):
            with patch("urllib.request.urlopen", return_value=response()):
                with UsageMeter(self.path) as meter:
                    with meter.logical_call():
                        with urllib.request.urlopen(request()) as stream:
                            stream.read()
        rows = [json.loads(line) for line in self.path.read_text().splitlines()]
        result = summarize(rows)
        self.assertEqual(result["explicit_logical_calls"], 2)
        self.assertEqual(result["grouped_additional_attempts"], 0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(UsageMeterTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "scope": "Offline fake HTTP contract tests; no real model requests, token measurements, or billing",
        "tests_run": result.testsRun,
        "successful": result.wasSuccessful(),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "test_names": sorted(unittest.defaultTestLoader.getTestCaseNames(UsageMeterTests)),
    }
    target = Path(__file__).resolve().parents[1] / "data" / "usage_meter_selftest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
