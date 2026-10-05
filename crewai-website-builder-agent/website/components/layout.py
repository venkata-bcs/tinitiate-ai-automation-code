import streamlit as st
from lib.theme import COLORS
from lib.storage import save_contact  # Imported per contract (not used here)

# ----------------------------------------------------------------------
# Page catalogue – shared by header and footer
# ----------------------------------------------------------------------
ALL_PAGES = [
    {"name": "Home", "file": "pages/home.py"},
    {"name": "Courses", "file": "pages/courses.py"},
    {"name": "About Us", "file": "pages/about_us.py"},
    {"name": "Contact Us", "file": "pages/contact.py"},
]

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
def render_header() -> None:
    """Render the site header with logo, navigation links and CTA."""
    with st.container(key="site_header"):
        # Layout: logo | navigation | CTA
        col_logo, col_nav, col_cta = st.columns([1, 3, 1])

        # --------------------------------------------------------------
        # Logo
        # --------------------------------------------------------------
        with col_logo:
            st.markdown(
                f"<span style='font-weight: bold; color:{COLORS['primary-contrast']}'>"
                "Tinitiate AI Academy"
                "</span>",
                unsafe_allow_html=True,
            )

        # --------------------------------------------------------------
        # Navigation links (one per page)
        # --------------------------------------------------------------
        with col_nav:
            # Evenly distribute the links across a row
            nav_cols = st.columns(len(ALL_PAGES))
            for idx, page in enumerate(ALL_PAGES):
                with nav_cols[idx]:
                    st.page_link(page["file"], label=page["name"])

        # --------------------------------------------------------------
        # Call‑to‑action button
        # --------------------------------------------------------------
        with col_cta:
            with st.container(key="header_cta"):
                st.page_link(
                    "pages/contact.py",
                    label="Enroll Now",
                    icon="🚀",
                )

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
def render_footer() -> None:
    """Render the site footer with copyright, quick links, contact info and socials."""
    with st.container(key="site_footer"):
        # --------------------------------------------------------------
        # Copyright line – centred, using muted colour
        # --------------------------------------------------------------
        st.markdown(
            f"<div class='muted' style='text-align:center; color:{COLORS['muted']}'>"
            "(c) Tinitiate AI Academy"
            "</div>",
            unsafe_allow_html=True,
        )

        # --------------------------------------------------------------
        # Footer body – three columns
        # --------------------------------------------------------------
        col_links, col_contact, col_social = st.columns([2, 2, 1])

        # ------------------------------
        # Quick links (all pages)
        # ------------------------------
        with col_links:
            st.markdown("<strong>Quick Links</strong>", unsafe_allow_html=True)
            for page in ALL_PAGES:
                st.page_link(page["file"], label=page["name"])

        # ------------------------------
        # Contact information
        # ------------------------------
        with col_contact:
            st.markdown("<strong>Contact</strong>", unsafe_allow_html=True)
            st.markdown("- Hyderabad, Telangana, India")
            st.markdown("- info@tinitiate.example")

        # ------------------------------
        # Social network names (styled as badges)
        # ------------------------------
        with col_social:
            st.markdown("<strong>Follow Us</strong>", unsafe_allow_html=True)
            for network in ["LinkedIn", "YouTube", "GitHub"]:
                st.markdown(
                    f"<span class='badge' style='margin-right:4px;'>{network}</span>",
                    unsafe_allow_html=True,
                )
