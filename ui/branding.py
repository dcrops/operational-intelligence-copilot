"""CRC brand constants and shell styling for portfolio applications."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BRAND_ORG_NAME = "CHASE RISK & COMPLIANCE"
APP_TITLE = "Operational Intelligence Copilot"
SIDEBAR_PLATFORM_NAME = "Operational Intelligence Platform"
APP_SUBTITLE = (
    "Transform operational data into trusted executive decisions through "
    "deterministic analytics, transparent reasoning, and AI-assisted executive guidance."
)

CAPABILITY_BADGES: tuple[str, ...] = (
    "Evidence-Based Analytics",
    "Executive Reasoning",
    "Evidence Transparency",
    "AI Executive Advisor",
)

CRC_LOGO_PATH = PROJECT_ROOT / "assets" / "images" / "crc-logo.png"

SIDEBAR_LOGO_WIDTH = 70
HERO_LOGO_WIDTH = 170

CRC_PRIMARY_COLOR = "#7CFF3A"
CRC_PRIMARY_DARK = "#2E7D32"
CRC_TEXT_MUTED = "#B0BEC5"

SHELL_LAYOUT_TOP_PADDING = "0.85rem"

SHELL_STYLES = f"""
<style>
section.main > div.block-container {{
    padding-top: {SHELL_LAYOUT_TOP_PADDING};
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding-top: {SHELL_LAYOUT_TOP_PADDING};
}}

.oic-sidebar-branding-shell {{
    text-align: center;
    padding: 0.05rem 0 0.3rem 0;
}}
.oic-sidebar-logo {{
    width: {SIDEBAR_LOGO_WIDTH}px;
    height: auto;
    display: block;
    margin: 0 auto 0.18rem auto;
}}
.oic-sidebar-brand {{
    text-align: center;
    padding: 0;
}}
.oic-sidebar-org {{
    color: {CRC_PRIMARY_COLOR};
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0.22rem 0 0.12rem 0;
}}
.oic-sidebar-platform {{
    color: {CRC_TEXT_MUTED};
    font-size: 0.8rem;
    line-height: 1.35;
    margin: 0;
}}

.oic-app-hero-shell {{
    margin-top: 0;
}}
.oic-hero-card {{
    padding: 2.1rem 2.4rem;
    border: 1px solid rgba(124, 255, 58, 0.28);
    border-radius: 1rem;
    background:
        radial-gradient(circle at top left, rgba(124, 255, 58, 0.18), transparent 34%),
        linear-gradient(135deg, rgba(46, 125, 50, 0.22), rgba(5, 18, 20, 0.88));
}}
.oic-hero-grid {{
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 2rem;
    align-items: center;
}}
.oic-hero-brand {{
    color: {CRC_PRIMARY_COLOR};
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin: 0 0 0.45rem 0;
}}
.oic-hero-title {{
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 0.8rem 0;
}}
.oic-hero-subtitle {{
    color: #DDE6E8;
    font-size: 1.02rem;
    line-height: 1.55;
    margin: 0 0 1.35rem 0;
    max-width: 58rem;
}}
.oic-hero-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
}}
.oic-hero-badge {{
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border: 1px solid rgba(124, 255, 58, 0.65);
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    color: {CRC_PRIMARY_COLOR};
    background-color: rgba(46, 125, 50, 0.16);
    white-space: nowrap;
}}

@media (max-width: 900px) {{
    .oic-hero-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
"""


def capability_badges_html() -> str:
    badges = "".join(
        f'<span class="oic-hero-badge">✓ {label}</span>' for label in CAPABILITY_BADGES
    )
    return f'<div class="oic-hero-badges">{badges}</div>'


def inject_shell_styles() -> None:
    import streamlit as st

    st.markdown(SHELL_STYLES, unsafe_allow_html=True)