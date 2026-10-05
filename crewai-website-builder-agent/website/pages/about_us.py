import streamlit as st
from lib.theme import COLORS
from lib.storage import save_contact  # Imported per contract; not used on this page.

# ----------------------------------------------------------------------
# Hero banner
# ----------------------------------------------------------------------
hero_html = f'''
<div class="hero" style="
    background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
    padding: 3rem;
    border-radius: 0.5rem;
    color: {COLORS["primary-contrast"]};
    text-align: center;
">
    <h1 style="margin: 0; font-size: 2.5rem;">About Tinitiate AI Academy</h1>
    <p style="margin-top: 0.5rem; font-size: 1.2rem;">
        Empowering professionals and students with cutting‑edge Generative AI, AI Agents and Automation skills.
    </p>
</div>
'''
st.markdown(hero_html, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Our story, mission and vision
# ----------------------------------------------------------------------
st.header("Our story, mission and vision")

st.subheader("Our Story")
st.write(
    """
    Founded in 2022, Tinitiate AI Academy began as a small group of AI enthusiasts "
    "who wanted to make advanced AI concepts accessible to anyone with a passion for learning.
    Based in Hyderabad, we quickly grew into a full‑fledged training institute,
    partnering with industry leaders to bring real‑world projects into the classroom.
    """
)

st.subheader("Mission")
st.write(
    """
    **To democratise Generative AI education** by offering hands‑on, mentor‑driven courses "
    "that bridge the gap between theory and production‑ready solutions.
    """
)

st.subheader("Vision")
st.write(
    """
    **A future where every professional and student in India can confidently build, "
    "deploy, and innovate with AI agents and automation tools**, driving the next wave of digital transformation.
    """
)

# ----------------------------------------------------------------------
# Team section
# ----------------------------------------------------------------------
st.header("Meet Our Trainers")

trainers = [
    {
        "name": "Dr. Ananya Rao",
        "role": "Lead AI Engineer",
        "bio": "10+ years building AI products; passionate about teaching Generative AI."
    },
    {
        "name": "Rohit Verma",
        "role": "Automation Specialist",
        "bio": "Automation guru who has streamlined workflows for Fortune 500 firms."
    },
    {
        "name": "Sneha Patel",
        "role": "Prompt Engineering Mentor",
        "bio": "Creative technologist turning prompts into powerful AI experiences."
    },
]

cols = st.columns(len(trainers))
for col, trainer in zip(cols, trainers):
    with col:
        with st.container(border=True):
            # Card title
            st.subheader(trainer["name"])
            # Role badge
            badge_html = f'''
            <span class="badge" style="
                background-color: {COLORS["accent"]};
                color: {COLORS["primary-contrast"]};
                padding: 0.2rem 0.5rem;
                border-radius: 0.3rem;
                font-size: 0.85rem;
            ">{trainer["role"]}</span>
            '''
            st.markdown(badge_html, unsafe_allow_html=True)
            # Bio
            st.write(trainer["bio"])

# ----------------------------------------------------------------------
# Call‑to‑action
# ----------------------------------------------------------------------
st.markdown("---")
st.write("Ready to start your AI journey? Reach out to us and we’ll help you pick the perfect course.")
st.page_link("pages/contact.py", label="Contact Us", icon="✉️")
