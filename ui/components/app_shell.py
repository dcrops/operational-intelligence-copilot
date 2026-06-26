"""Branded application shell — hero and shared CRC presentation."""

from __future__ import annotations

import streamlit as st

from ui.branding import (
    APP_SUBTITLE,
    APP_TITLE,
    BRAND_ORG_NAME,
    CRC_LOGO_PATH,
    HERO_LOGO_WIDTH,
    SIDEBAR_LOGO_WIDTH,
    SIDEBAR_PLATFORM_NAME,
    capability_badges_html,
    inject_shell_styles,
)


def render_sidebar_branding() -> None:
    """Render compact CRC branding at the top of the sidebar."""
    inject_shell_styles()

    if CRC_LOGO_PATH.is_file():
        _, logo_col, _ = st.sidebar.columns([1.4, 1, 1.4])
        with logo_col:
            st.image(str(CRC_LOGO_PATH), width=SIDEBAR_LOGO_WIDTH)

    st.sidebar.markdown(
        f"""
<div class="oic-sidebar-brand">
  <p class="oic-sidebar-org">{BRAND_ORG_NAME}</p>
  <p class="oic-sidebar-platform">{SIDEBAR_PLATFORM_NAME}</p>
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
""",
        unsafe_allow_html=True,
    )

    st.markdown("")