import streamlit as st
from lib.theme import COLORS

# ----------------------------------------------------------------------
# Courses Page
# ----------------------------------------------------------------------
# Hero banner
st.markdown(
    """
    <div class="hero" style="padding: 2rem 1rem; text-align: center;">
        <h1 style="margin-bottom: 0.5rem;">Courses at Tinitiate AI Academy</h1>
        <p style="margin: 0; font-size: 1.1rem;">
            Cutting‑edge AI training for professionals and students across India.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Section heading
st.header("Our Courses")

# ----------------------------------------------------------------------
# Course data
# ----------------------------------------------------------------------
courses = [
    {
        "name": "GenAI Foundations",
        "duration": "6 weeks",
        "mode": "Online",
        "fee": 15000,
    },
    {
        "name": "AI Agents with CrewAI & LangGraph",
        "duration": "8 weeks",
        "mode": "Classroom",
        "fee": 25000,
    },
    {
        "name": "Python Automation",
        "duration": "4 weeks",
        "mode": "Online",
        "fee": 12000,
    },
    {
        "name": "Prompt Engineering",
        "duration": "3 weeks",
        "mode": "Online",
        "fee": 10000,
    },
]

# ----------------------------------------------------------------------
# Render cards (2 columns per row)
# ----------------------------------------------------------------------
cols = st.columns(2, gap="large")
for idx, course in enumerate(courses):
    col = cols[idx % 2]
    with col:
        with st.container(border=True):
            # Course title
            st.subheader(course["name"])

            # Mode badge
            badge_html = f'''
                <span class="badge"
                      style="
                        background:{COLORS["primary"]};
                        color:{COLORS["primary-contrast"]};
                        padding:4px 8px;
                        border-radius:4px;
                        font-size:0.85rem;
                        ">
                    {course["mode"]}
                </span>
            '''
            st.markdown(badge_html, unsafe_allow_html=True)

            # Details (duration & fee)
            details_html = f'''
                <p class="muted" style="margin-top:0.5rem;">
                    <strong>Duration:</strong> {course["duration"]}<br>
                    <strong>Fee:</strong> ₹{course["fee"]:,}
                </p>
            '''
            st.markdown(details_html, unsafe_allow_html=True)

            # Enroll button – links to Contact Us page
            st.page_link(
                "pages/contact.py",
                label="Enroll Now",
                icon="🧭",
                help=f"Enroll in {course['name']}",
                width="content",
            )
