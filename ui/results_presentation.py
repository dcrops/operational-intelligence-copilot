"""Results panel typography, spacing, and zone styling."""

from __future__ import annotations

import html
import re
from typing import Callable

import streamlit as st

from ui.branding import CRC_PRIMARY_COLOR, CRC_TEXT_MUTED, inject_shell_styles
from ui.metric_presentation import humanise_metric_name
from ui.models import AnalysisResult

ZONE_EXECUTIVE = "executive"
ZONE_INVESTIGATION = "investigation"
ZONE_AUDIT = "audit"

INVESTIGATION_ACCENT = "#D97706"
AUDIT_ACCENT = "#94A3B8"

_BULLET_LINE_PATTERN = re.compile(r"^\s*(?:[-•*]|\d+\.)\s+")

_RESULTS_STYLES = f"""
<style>
.oic-results-metadata {{
    margin: 0.1rem 0 0.75rem 0;
    padding: 0.45rem 0.7rem;
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 0.4rem;
    background: rgba(15, 23, 42, 0.12);
}}
.oic-results-metadata-status {{
    color: {CRC_TEXT_MUTED};
    font-size: 0.65rem;
    font-weight: 650;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin: 0 0 0.35rem 0;
    opacity: 0.9;
}}
.oic-metadata-grid {{
    display: grid;
    grid-template-columns: 6.5rem 1fr;
    gap: 0.18rem 0.6rem;
    font-size: 0.8rem;
    line-height: 1.38;
}}
.oic-metadata-label {{
    color: {CRC_TEXT_MUTED};
    font-weight: 550;
    font-size: 0.76rem;
}}
.oic-metadata-value {{
    color: #CBD5E1;
    font-weight: 450;
}}

.oic-section-heading.oic-zone-executive {{
    border-left: 3px solid {CRC_PRIMARY_COLOR};
    padding-left: 0.75rem;
    margin-top: 0.35rem;
}}
.oic-section-heading.oic-zone-investigation {{
    border-left: 3px solid {INVESTIGATION_ACCENT};
    padding-left: 0.75rem;
}}
.oic-section-heading.oic-zone-audit {{
    border-left: 3px solid {AUDIT_ACCENT};
    padding-left: 0.75rem;
}}
.oic-section-heading.oic-tier-1 h4 {{
    font-size: 1.28rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}}
.oic-section-heading.oic-zone-executive.oic-tier-2 {{
    margin-top: 0.7rem;
    margin-bottom: 0.2rem;
}}
.oic-section-heading.oic-tier-2 h5 {{
    font-size: 1.02rem;
    font-weight: 650;
    margin-bottom: 0.25rem;
}}
.oic-variant-hero {{
    border-left: 4px solid {CRC_PRIMARY_COLOR};
    padding-left: 0.85rem;
    margin: 0.45rem 0 1.5rem 0;
}}
.oic-section-heading.oic-variant-hero h4 {{
    font-size: 1.4rem;
    font-weight: 750;
    margin-bottom: 0.55rem;
}}
.oic-hero-card {{
    padding: 1.6rem 1.7rem;
    border: 1px solid rgba(124, 255, 58, 0.42);
    border-radius: 0.9rem;
    background: linear-gradient(
        135deg,
        rgba(46, 125, 50, 0.22),
        rgba(15, 23, 42, 0.58)
    );
    box-shadow: 0 6px 28px rgba(0, 0, 0, 0.22);
}}
.oic-hero-card p {{
    font-size: 1.3rem;
    line-height: 1.72;
    margin: 0;
    color: #F8FAFC;
    font-weight: 500;
}}

.oic-assessment-banner {{
    border-radius: 0.65rem;
    padding: 1rem 1.15rem 0.95rem;
    margin: 0;
    background-color: rgba(148, 163, 184, 0.08);
}}
.oic-assessment-label {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: {CRC_TEXT_MUTED};
    margin-bottom: 0.4rem;
}}
.oic-assessment-level {{
    font-size: 1.42rem;
    font-weight: 850;
    line-height: 1.25;
    letter-spacing: 0.015em;
    margin-bottom: 0.7rem;
}}
.oic-assessment-headline {{
    font-size: 0.93rem;
    line-height: 1.58;
    color: #CBD5E1;
    padding-top: 0.55rem;
    border-top: 1px solid rgba(148, 163, 184, 0.16);
}}

.oic-executive-summary-body {{
    display: flex;
    flex-direction: column;
}}
.oic-executive-spacer-sm {{
    height: 0.55rem;
}}
.oic-executive-spacer-md {{
    height: 0.9rem;
}}
.oic-executive-spacer-lg {{
    height: 1.2rem;
}}

.oic-action-list {{
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    margin: 0.45rem 0 0.2rem 0;
}}
.oic-action-item {{
    display: grid;
    grid-template-columns: 1.75rem 1fr;
    gap: 0.6rem;
    align-items: start;
    line-height: 1.58;
    padding: 0.6rem 0.7rem 0.6rem 0.45rem;
    border-left: 2px solid rgba(124, 255, 58, 0.38);
    background: rgba(15, 23, 42, 0.28);
    border-radius: 0.4rem;
}}
.oic-action-number {{
    color: {CRC_PRIMARY_COLOR};
    font-weight: 750;
    font-size: 0.95rem;
}}
.oic-action-text {{
    color: #F1F5F9;
}}

.oic-overview-list {{
    margin: 0.15rem 0 0.25rem 0;
    padding-left: 1.1rem;
    line-height: 1.65;
}}

.oic-reasoning-block {{
    margin: 0.75rem 0 0.35rem 0;
}}

.oic-evidence-panel {{
    margin: 0.35rem 0 0.75rem 0;
}}
.oic-evidence-title {{
    font-size: 0.92rem;
    font-weight: 650;
    margin-bottom: 0.55rem;
    color: #E2E8F0;
}}
.oic-evidence-field {{
    display: grid;
    grid-template-columns: 9.5rem 1fr;
    gap: 0.65rem;
    padding: 0.28rem 0;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    font-size: 0.88rem;
    line-height: 1.45;
}}
.oic-evidence-label {{
    color: {CRC_TEXT_MUTED};
    font-weight: 600;
}}
.oic-evidence-value {{
    color: #E2E8F0;
}}

.oic-audit-verification {{
    margin-top: 0.85rem;
    padding-top: 0.35rem;
    border-top: 1px solid rgba(148, 163, 184, 0.18);
}}
</style>
"""


def inject_results_styles() -> None:
    """Inject CRC-aligned results presentation styles once per run."""
    inject_shell_styles()
    st.markdown(_RESULTS_STYLES, unsafe_allow_html=True)


def render_metadata_header(
    *,
    status: str,
    rows: tuple[tuple[str, str], ...],
) -> None:
    row_html = "".join(
        f'<div class="oic-metadata-label">{html.escape(label)}</div>'
        f'<div class="oic-metadata-value">{html.escape(value)}</div>'
        for label, value in rows
    )
    st.markdown(
        f"""
<div class="oic-results-metadata">
  <div class="oic-results-metadata-status">{html.escape(status)}</div>
  <div class="oic-metadata-grid">{row_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def open_section_heading(*, zone: str, tier: int = 1, variant: str | None = None) -> None:
    variant_class = f" oic-variant-{variant}" if variant else ""
    st.markdown(
        f'<div class="oic-section-heading oic-zone-{zone} oic-tier-{tier}{variant_class}">',
        unsafe_allow_html=True,
    )


def close_section_heading() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_level2_heading(title: str, *, zone: str = ZONE_EXECUTIVE) -> None:
    st.markdown(
        f'<div class="oic-section-heading oic-zone-{zone} oic-tier-2">',
        unsafe_allow_html=True,
    )
    st.markdown(f"##### {title}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_executive_spacer(size: str = "md") -> None:
    """Insert vertical rhythm spacing inside the Executive Summary."""
    if size not in {"sm", "md", "lg"}:
        size = "md"
    st.markdown(f'<div class="oic-executive-spacer-{size}"></div>', unsafe_allow_html=True)


def render_hero_body(text: str) -> None:
    st.markdown(
        f'<div class="oic-hero-card"><p>{html.escape(text)}</p></div>',
        unsafe_allow_html=True,
    )


def render_labelled_field(label: str, value: object) -> None:
    st.markdown(
        f'<div class="oic-evidence-field">'
        f'<span class="oic-evidence-label">{html.escape(label)}</span>'
        f'<span class="oic-evidence-value">{html.escape(str(value))}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_numbered_items(lines: list[str]) -> None:
    items = "".join(
        f'<div class="oic-action-item">'
        f'<span class="oic-action-number">{index}.</span>'
        f'<span class="oic-action-text">{html.escape(_strip_bullet_prefix(line))}</span>'
        f"</div>"
        for index, line in enumerate(lines, start=1)
    )
    st.markdown(f'<div class="oic-action-list">{items}</div>', unsafe_allow_html=True)


def render_overview_bullets(bullets: list[str]) -> None:
    items = "".join(f"<li>{html.escape(bullet)}</li>" for bullet in bullets)
    st.markdown(f'<ul class="oic-overview-list">{items}</ul>', unsafe_allow_html=True)


def _strip_bullet_prefix(line: str) -> str:
    return _BULLET_LINE_PATTERN.sub("", line.strip()).strip()


def split_action_lines(content: str, *, limit: int) -> tuple[list[str], list[str]]:
    lines = [line for line in content.splitlines() if line.strip()]
    bullet_lines = [line for line in lines if _BULLET_LINE_PATTERN.match(line)]
    if len(bullet_lines) >= 2:
        source_lines = bullet_lines
    else:
        source_lines = lines
    return source_lines[:limit], source_lines[limit:]


def format_investigation_overview_bullets(result: AnalysisResult) -> list[str]:
    """Business-first overview bullets for Investigation (tools omitted; see Audit)."""
    from ui.executive_reasoning_presentation import format_analysis_overview

    overview = format_analysis_overview(
        findings=result.findings,
        routes=result.routes,
        report=result.report,
    )
    bullets: list[str] = []
    for bullet in overview.bullets:
        if bullet.endswith(" executed"):
            continue
        if "analytical finding" in bullet:
            findings_count = len(result.findings)
            finding_word = "finding" if findings_count == 1 else "findings"
            bullets.append(f"{findings_count} {finding_word}")
            continue
        bullets.append(bullet)

    metric_names: list[str] = []
    seen: set[str] = set()
    for metric in result.metrics_analysed or []:
        if metric not in seen:
            metric_names.append(humanise_metric_name(metric))
            seen.add(metric)
    if not metric_names:
        for finding in result.findings:
            for item in finding.evidence:
                if item.metric_name and item.metric_name not in seen:
                    metric_names.append(humanise_metric_name(item.metric_name))
                    seen.add(item.metric_name)

    if metric_names and not any(bullet.startswith("Primary metrics affected:") for bullet in bullets):
        bullets.append(f"Primary metrics affected: {', '.join(metric_names[:4])}")

    return bullets


def render_collapsible_group(
    label: str,
    render_body: Callable[[], None],
    *,
    expanded: bool = False,
    zone: str = ZONE_INVESTIGATION,
) -> None:
    """Render a disclosure group collapsed by default."""
    st.markdown(f'<div class="oic-disclosure oic-zone-{zone}">', unsafe_allow_html=True)
    with st.expander(label, expanded=expanded):
        render_body()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("")


def render_section(
    title: str,
    render_body: Callable[[], None],
    *,
    bordered: bool = True,
    zone: str = ZONE_EXECUTIVE,
    tier: int = 1,
    variant: str | None = None,
) -> None:
    open_section_heading(zone=zone, tier=tier, variant=variant)
    st.markdown(f"#### {title}")
    close_section_heading()
    if bordered:
        with st.container(border=True):
            render_body()
    else:
        render_body()
    st.markdown("")


def render_subsection(
    title: str,
    render_body: Callable[[], None],
    *,
    bordered: bool = True,
    zone: str = ZONE_AUDIT,
) -> None:
    render_level2_heading(title, zone=zone)
    if bordered:
        with st.container(border=True):
            render_body()
    else:
        render_body()
    st.markdown("")
