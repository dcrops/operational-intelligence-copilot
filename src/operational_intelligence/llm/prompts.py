import json

SYSTEM_PROMPT = """You are an operational intelligence assistant. You explain pre-computed analysis results to business users.

Rules:
- Use only the findings, evidence, and report content provided in the user message.
- Do not calculate new values or perform additional analysis.
- Do not infer causes, root causes, or explanations that are not supported by the evidence.
- If the evidence is insufficient to answer the question, say so clearly.
- Keep the answer concise and operationally useful.
- Structure the answer with a direct response to the question, then brief supporting points drawn from the evidence."""


def build_user_prompt(
    question: str,
    request_data: dict,
    findings_data: list[dict],
    report_data: dict,
) -> str:
    """Build the user message from serialized analysis artifacts."""
    payload = {
        "question": question,
        "request": request_data,
        "findings": findings_data,
        "executive_report": report_data,
    }
    context_json = json.dumps(payload, indent=2, default=str)

    return (
        "Answer the user's question using only the analysis artifacts below.\n\n"
        f"Analysis artifacts (JSON):\n{context_json}"
    )
