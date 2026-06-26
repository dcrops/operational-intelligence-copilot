"""Branded application shell — hero and shared CRC presentation."""

from __future__ import annotations

import streamlit as st

from ui.branding import (
    APP_SUBTITLE,
    APP_TITLE,
    BRAND_ORG_NAME,
    CRC_LOGO_PATH,
    HERO_LOGO_WIDTH,
    SIDEBAR_PLATFORM_NAME,
    capability_badges_html,
    inject_shell_styles,
)


def render_sidebar_branding() -> None:
    """Render compact CRC branding at the top of the sidebar."""
    inject_shell_styles()

    logo_html = ""
    if CRC_LOGO_PATH.is_file():
        import base64

        encoded = base64.b64encode(CRC_LOGO_PATH.read_bytes()).decode("utf-8")
        logo_html = (
            f'<img class="oic-sidebar-logo" src="data:image/png;base64,{encoded}" '
            f'alt="CRC logo" />'
        )

    st.sidebar.markdown(
        f"""
<div class="oic-sidebar-branding-shell">
  {logo_html}
  <div class="oic-sidebar-brand">
    <p class="oic-sidebar-org">{BRAND_ORG_NAME}</p>
    <p class="oic-sidebar-platform">{SIDEBAR_PLATFORM_NAME}</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()


def render_app_hero() -> None:
    """Render the CRC-branded hero card at the top of the main page."""
    inject_shell_styles()

    logo_html = ""
    if CRC_LOGO_PATH.is_file():
        import base64

        encoded = base64.b64encode(CRC_LOGO_PATH.read_bytes()).decode("utf-8")
        logo_html = (
            f'<img src="data:image/png;base64,{encoded}" '
            f'width="{HERO_LOGO_WIDTH}" alt="CRC logo" />'
        )

    st.markdown(
        f"""
<div class="oic-app-hero-shell">
  <div class="oic-hero-card">
    <div class="oic-hero-grid">
      <div>{logo_html}</div>
      <div>
        <p class="oic-hero-brand">{BRAND_ORG_NAME}</p>
        <p class="oic-hero-title">{APP_TITLE}</p>
        <p class="oic-hero-subtitle">{APP_SUBTITLE}</p>
        {capability_badges_html()}
      </div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("")