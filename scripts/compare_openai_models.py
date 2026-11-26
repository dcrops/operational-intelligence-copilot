"""Controlled gpt-4.1-mini versus gpt-6-luna narrative comparison.

Runs deterministic analysis first, inspects the exact prompts, and only then
makes one Chat Completions call per scenario per model. Production retries are
not changed. This script disables both the application retry loop and the SDK
retry loop for its own client instances.

Usage:
    .venv\\Scripts\\python.exe scripts\\compare_openai_models.py
    .venv\\Scripts\\python.exe scripts\\compare_openai_models.py --live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import truststore

truststore.inject_into_ssl()

import pandas as pd
from openai import OpenAI

from src.operational_intelligence.llm.deterministic_narrative_generator import (
    DeterministicNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import NarrativeRuntimeConfig
from src.operational_intelligence.llm.narrative_errors import NarrativeGenerationError
from src.operational_intelligence.llm.openai_client import LUNA_CHAT_MODEL, OpenAIClient
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.openai_response_parser import OpenAINarrativeResponseParser
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from src.operational_intelligence.profiling import DatasetProfiler
from ui.analysis_service import run_analysis
from ui.narrative_service import build_deterministic_analysis_snapshot

DATASET_PATH = PROJECT_ROOT / "data" / "sample" / "manufacturing_demo.csv"
OUTPUT_PATH = Path(os.environ.get("TEMP", ".")) / "oic_model_comparison.json"
MODELS = ("gpt-4.1-mini", LUNA_CHAT_MODEL)
SCENARIOS = (
    ("variance", "Which production line has the highest defects?"),
    ("trend", "How has downtime changed over time?"),
    ("anomaly", "What looks unusual and what should I investigate?"),
)
PLANNED_MODEL_CALLS = len(SCENARIOS) * len(MODELS)


def _load_local_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _jsonable(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _fingerprint(result) -> dict:
    report = result.report
    return {
        "routes": list(result.routes),
        "direct_answer": result.direct_answer,
        "deterministic_answer": result.deterministic_answer,
        "findings": _jsonable(result.findings),
        "tool_results": _jsonable(result.tool_results),
        "operational_assessment": _jsonable(
            report.operational_assessment if report is not None else None
        ),
        "executive_summary": None if report is None else report.executive_summary,
        "executive_conclusions": _jsonable(
            [] if report is None else report.executive_conclusions
        ),
        "priority_actions": _jsonable([] if report is None else report.priority_actions),
        "metrics_analysed": list(result.metrics_analysed),
    }


def _prompt_messages(result) -> list[dict[str, str]]:
    snapshot = build_deterministic_analysis_snapshot(result)
    request = NarrativeRequestBuilder().build(snapshot)
    artifact = PromptArtifactBuilder().build(request)
    return OpenAIPromptFormatter().format(artifact), artifact


def _privacy_hits(prompt_text: str, names: set[str]) -> list[str]:
    lowered = prompt_text.lower()
    return sorted(name for name in names if name.lower() in lowered)


def _usage(response) -> dict:
    usage = getattr(response, "usage", None)
    details = getattr(usage, "completion_tokens_details", None) if usage else None
    choice = response.choices[0]
    return {
        "returned_model": getattr(response, "model", None),
        "finish_reason": getattr(choice, "finish_reason", None),
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "reasoning_tokens": (
            getattr(details, "reasoning_tokens", None) if details is not None else None
        ),
    }


class _RecordingCompletions:
    def __init__(self, inner) -> None:
        self._inner = inner
        self.calls: list[dict] = []

    def create(self, **kwargs):
        started = time.perf_counter()
        params = {key: value for key, value in kwargs.items() if key != "messages"}
        try:
            response = self._inner.create(**kwargs)
        except Exception as exc:
            self.calls.append(
                {
                    "params": params,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            raise
        self.calls.append(
            {
                "params": params,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                **_usage(response),
            }
        )
        return response


def _comparison_client(model_name: str) -> tuple[OpenAIClient, _RecordingCompletions]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAIClient(model_name=model_name, timeout_seconds=30, max_retries=0)
    raw = OpenAI(api_key=api_key, max_retries=0)
    recorder = _RecordingCompletions(raw.chat.completions)

    class _Chat:
        completions = recorder

    class _Shim:
        chat = _Chat()

    client._client = _Shim()
    return client, recorder


def _sections(parsed) -> list[dict[str, str]]:
    return [{"title": section.title, "content": section.content} for section in parsed.sections]


def _deterministic_narrative(artifact) -> dict:
    response = DeterministicNarrativeGenerator().generate(artifact)
    return {
        "generator_type": response.generator_type,
        "sections": _sections(response),
        "limitations": response.limitations,
        "fallback_status": "deterministic_control",
    }


def _run_model(model_name: str, messages: list[dict[str, str]]) -> dict:
    client, recorder = _comparison_client(model_name)
    started = time.perf_counter()
    outcome = {
        "requested_model": model_name,
        "fallback_status": "not_applied",
        "counted_as_successful_model_generation": False,
    }
    try:
        raw_text = client.complete(messages, temperature=0.0)
    except Exception as exc:
        outcome.update(
            {
                "classification": "transport_or_api_failure",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "api_calls": recorder.calls,
            }
        )
        return outcome

    outcome["latency_ms"] = int((time.perf_counter() - started) * 1000)
    outcome["api_calls"] = recorder.calls
    outcome["raw_response"] = raw_text
    try:
        parsed = OpenAINarrativeResponseParser().parse(raw_text)
    except NarrativeGenerationError as exc:
        outcome.update(
            {
                "classification": "labelled_response_parsing_failure",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        return outcome

    outcome.update(
        {
            "classification": "successful_openai_narrative",
            "counted_as_successful_model_generation": True,
            "sections": _sections(parsed),
            "limitations": parsed.limitations,
        }
    )
    return outcome


def prepare() -> dict:
    frame = pd.read_csv(DATASET_PATH)
    profile = DatasetProfiler().profile_dataframe("manufacturing_demo", frame)
    supervisor_names = {
        str(value).strip()
        for value in frame["supervisor"].dropna().unique()
        if str(value).strip()
    }
    scenarios = []
    blocked = False
    for scenario_id, question in SCENARIOS:
        first = run_analysis(
            question,
            frame,
            profile,
            narrative_config=NarrativeRuntimeConfig.disabled(),
        )
        second = run_analysis(
            question,
            frame,
            profile,
            narrative_config=NarrativeRuntimeConfig.disabled(),
        )
        record = {
            "id": scenario_id,
            "question": question,
            "clarification": _jsonable(first.clarification),
            "deterministic_results_identical": _fingerprint(first) == _fingerprint(second),
            "control": _fingerprint(first),
        }
        if first.clarification is not None or first.report is None:
            record["prompt_safe"] = False
            record["privacy_hits"] = []
            record["blocked_reason"] = "deterministic analysis requested clarification"
            blocked = True
            scenarios.append(record)
            continue
        messages, artifact = _prompt_messages(first)
        prompt_text = "\n".join(message["content"] for message in messages)
        hits = _privacy_hits(prompt_text, supervisor_names)
        record["messages"] = messages
        record["privacy_hits"] = hits
        record["prompt_safe"] = not hits
        record["deterministic_narrative"] = _deterministic_narrative(artifact)
        if hits:
            blocked = True
            record["blocked_reason"] = "prompt contains supervisor names"
        scenarios.append(record)
    return {
        "dataset": str(DATASET_PATH),
        "supervisor_names_present_in_source": sorted(supervisor_names),
        "planned_model_calls": PLANNED_MODEL_CALLS,
        "prompts_safe_for_transmission": not blocked and all(
            item.get("prompt_safe") for item in scenarios
        ),
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    _load_local_env()
    prepared = prepare()
    if args.live:
        if not prepared["prompts_safe_for_transmission"]:
            prepared["live_executed"] = False
            prepared["live_blocked"] = True
        else:
            executed_calls = 0
            for scenario in prepared["scenarios"]:
                scenario["models"] = {}
                for model_name in MODELS:
                    if executed_calls >= PLANNED_MODEL_CALLS:
                        raise RuntimeError("Refusing to exceed the planned six model calls")
                    scenario["models"][model_name] = _run_model(model_name, scenario["messages"])
                    outcome = scenario["models"][model_name]
                    executed_calls += len(outcome["api_calls"])
                    error_text = f"{outcome.get('error_type', '')} {outcome.get('error', '')}".lower()
                    if outcome["classification"] == "transport_or_api_failure" and (
                        "authentication" in error_text
                        or "api key" in error_text
                        or "401" in error_text
                    ):
                        prepared["stopped_reason"] = outcome.get("error")
                        prepared["live_executed"] = True
                        prepared["actual_api_calls"] = executed_calls
                        OUTPUT_PATH.write_text(json.dumps(prepared, indent=2), encoding="utf-8")
                        print(f"stopped after authentication failure: {outcome.get('error_type')}")
                        return 1
            prepared["live_executed"] = True
            prepared["actual_api_calls"] = executed_calls
    OUTPUT_PATH.write_text(json.dumps(prepared, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    print(f"prompts_safe={prepared['prompts_safe_for_transmission']}")
    for scenario in prepared["scenarios"]:
        control = scenario["control"]
        print(
            f"{scenario['id']}: routes={control['routes']} "
            f"clarification={scenario['clarification'] is not None} "
            f"identical={scenario['deterministic_results_identical']} "
            f"privacy_hits={scenario['privacy_hits']}"
        )
        if args.live and "models" in scenario:
            for model_name, outcome in scenario["models"].items():
                print(
                    f"  {model_name}: {outcome['classification']} "
                    f"calls={len(outcome['api_calls'])}"
                )
    return 0 if prepared["prompts_safe_for_transmission"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
