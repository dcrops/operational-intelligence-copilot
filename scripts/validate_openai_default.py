"""One-call production smoke test for the gpt-6-luna default.

Uses the production narrative factory and the manufacturing variance question.
OIC_OPENAI_MODEL is removed before resolution. Retries are disabled only on
the client instance created for this smoke test.

    .venv\\Scripts\\python.exe scripts\\validate_openai_default.py
    .venv\\Scripts\\python.exe scripts\\validate_openai_default.py --live
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

from src.operational_intelligence.llm.fallback_narrative_generator import (
    FallbackNarrativeGenerator,
)
from src.operational_intelligence.llm.narrative_builder import NarrativeRequestBuilder
from src.operational_intelligence.llm.narrative_config import (
    DEFAULT_OPENAI_MODEL,
    NarrativeRuntimeConfig,
    get_openai_provider_config,
)
from src.operational_intelligence.llm.narrative_factory import resolve_narrative
from src.operational_intelligence.llm.narrative_governance import ADVISOR_SECTION_TITLES
from src.operational_intelligence.llm.openai_client import OpenAIClient
from src.operational_intelligence.llm.openai_prompt_formatter import OpenAIPromptFormatter
from src.operational_intelligence.llm.prompt_artifact_builder import PromptArtifactBuilder
from src.operational_intelligence.profiling import DatasetProfiler
from ui.analysis_service import run_analysis
from ui.narrative_service import build_deterministic_analysis_snapshot

DATASET_PATH = PROJECT_ROOT / "data" / "sample" / "manufacturing_demo.csv"
QUESTION = "Which production line has the highest defects?"
OUTPUT_PATH = Path(os.environ.get("TEMP", ".")) / "oic_default_smoke.json"


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
        usage = getattr(response, "usage", None)
        details = getattr(usage, "completion_tokens_details", None) if usage else None
        choice = response.choices[0]
        self.calls.append(
            {
                "params": params,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "returned_model": getattr(response, "model", None),
                "finish_reason": getattr(choice, "finish_reason", None),
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "reasoning_tokens": (
                    getattr(details, "reasoning_tokens", None) if details is not None else None
                ),
            }
        )
        return response


def _prepare() -> dict:
    model_was_set = "OIC_OPENAI_MODEL" in os.environ
    os.environ.pop("OIC_OPENAI_MODEL", None)
    os.environ["OIC_NARRATIVE_ENABLED"] = "true"
    os.environ["OIC_NARRATIVE_PROVIDER"] = "openai"
    frame = pd.read_csv(DATASET_PATH)
    profile = DatasetProfiler().profile_dataframe("manufacturing_demo", frame)
    result = run_analysis(
        QUESTION,
        frame,
        profile,
        narrative_config=NarrativeRuntimeConfig.disabled(),
    )
    names = {
        str(value).strip()
        for value in frame["supervisor"].dropna().unique()
        if str(value).strip()
    }
    snapshot = build_deterministic_analysis_snapshot(result)
    request = NarrativeRequestBuilder().build(snapshot)
    artifact = PromptArtifactBuilder().build(request)
    messages = OpenAIPromptFormatter().format(artifact)
    prompt_text = "\n".join(message["content"] for message in messages)
    hits = sorted(name for name in names if name.lower() in prompt_text.lower())
    config = NarrativeRuntimeConfig.from_environment()
    return {
        "question": QUESTION,
        "oic_openai_model_was_set_before_unset": model_was_set,
        "oic_openai_model_after_unset": os.environ.get("OIC_OPENAI_MODEL"),
        "runtime_provider": config.provider,
        "resolved_default_model": get_openai_provider_config().model,
        "expected_default_model": DEFAULT_OPENAI_MODEL,
        "direct_answer": result.direct_answer,
        "routes": list(result.routes),
        "messages": messages,
        "privacy_hits": hits,
        "prompt_safe": not hits and result.report is not None and result.clarification is None,
        "artifact": artifact,
        "config": config,
    }


def _run_live(prepared: dict) -> dict:
    resolution = resolve_narrative(prepared["config"])
    generator = resolution.generator
    if not isinstance(generator, FallbackNarrativeGenerator):
        raise RuntimeError("Production factory did not return the fallback wrapper")
    client = generator._primary._llm_client
    if not isinstance(client, OpenAIClient):
        raise RuntimeError("Production factory did not build an OpenAIClient")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    raw = OpenAI(api_key=api_key, max_retries=0)
    recorder = _RecordingCompletions(raw.chat.completions)

    class _Chat:
        completions = recorder

    class _Shim:
        chat = _Chat()

    client._max_retries = 0
    client._client = _Shim()
    started = time.perf_counter()
    response = generator.generate(prepared["artifact"])
    return {
        "selected_model": client._model_name,
        "returned_narrative_model": response.model,
        "generator_type": response.generator_type,
        "fallback_applied": "deterministic fallback applied" in response.limitations.lower()
        or response.generator_type != "openai",
        "section_titles": [section.title for section in response.sections],
        "sections": [
            {"title": section.title, "content": section.content} for section in response.sections
        ],
        "limitations": response.limitations,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "api_calls": recorder.calls,
        "expected_section_count": len(ADVISOR_SECTION_TITLES),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    _load_local_env()
    prepared = _prepare()
    record = {
        key: value
        for key, value in prepared.items()
        if key not in {"artifact", "config"}
    }
    if args.live:
        if not prepared["prompt_safe"]:
            record["live_executed"] = False
            OUTPUT_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")
            print("blocked before transmission")
            return 2
        record["live"] = _run_live(prepared)
        record["live_executed"] = True
    OUTPUT_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    print(
        f"model={record['resolved_default_model']} "
        f"provider={record['runtime_provider']} "
        f"safe={record['prompt_safe']} "
        f"direct={record['direct_answer']}"
    )
    if "live" in record:
        live = record["live"]
        print(
            f"live generator={live['generator_type']} "
            f"selected={live['selected_model']} "
            f"narrative_model={live['returned_narrative_model']} "
            f"calls={len(live['api_calls'])} "
            f"fallback={live['fallback_applied']} "
            f"sections={live['section_titles']}"
        )
    return 0 if record["prompt_safe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
