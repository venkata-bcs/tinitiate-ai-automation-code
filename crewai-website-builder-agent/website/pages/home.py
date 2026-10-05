import streamlit as st
from lib.theme import COLORS
from lib.storage import save_contact  # Imported per contract (not used on this page)

# ----------------------------------------------------------------------
# Home Page – Tinitiate AI Academy
# ----------------------------------------------------------------------
# 1️⃣ Hero banner with headline, pitch and a navigation button
# 2️⃣ Three highlight cards
# 3️⃣ Student testimonials
# ----------------------------------------------------------------------


# -------------------------------------------------
# 1️⃣ Hero banner
# -------------------------------------------------
hero_html = f"""
<div class="hero" style="padding: 4rem 1rem; text-align: center;">
    <h1 style="margin-bottom: 0.5rem; color: {COLORS['primary-contrast']};">
        Welcome to Tinitiate AI Academy
    </h1>
    <p style="font-size: 1.2rem; color: {COLORS['text']}; max-width: 800px; margin: 0 auto;">
        Empowering professionals and students across India with hands‑on Generative AI,
        AI Agents, and Automation training. Learn from industry mentors, build real‑world
        projects, and accelerate your career.
    </p>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

# Button that navigates to the Courses page
st.page_link(
    "pages/courses.py",
    label="Explore Courses",
    icon="🚀",
    help="Browse all our AI courses",
    width="content",
)

st.write("---")  # visual separator


# -------------------------------------------------
# 2️⃣ Highlights – Hands‑on Labs, Industry Mentors, Placement Support
# -------------------------------------------------
st.header("Why Choose Tinitiate AI Academy?")

highlight_data = [
    {
        "title": "Hands‑on Labs",
        "emoji": "🧪",
        "desc": "Live labs with real datasets and cloud resources – you code, test, and iterate instantly.",
    },
    {
        "title": "Industry Mentors",
        "emoji": "👩‍🏫",
        "desc": "Learn directly from AI engineers at leading tech firms who guide you through every step.",
    },
    {
        "title": "Placement Support",
        "emoji": "💼",
        "desc": "Resume reviews, interview prep, and job referrals to help you land your dream AI role.",
    },
]

cols = st.columns(3, gap="large")
for col, item in zip(cols, highlight_data):
    with col:
        card_html = f"""
        <div class="card" style="padding: 1.5rem; border-radius: 0.75rem; background: {COLORS['surface']};
            box-shadow: 0 2px 6px rgba(0,0,0,0.1); text-align: center;">
            <div style="font-size: 2rem;">{item['emoji']}</div>
            <h3 style="margin-top: 0.5rem; color: {COLORS['primary']};">{item['title']}</h3>
            <p class="muted" style="color: {COLORS['muted']};">{item['desc']}</p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

st.write("---")


# -------------------------------------------------
# 3️⃣ Testimonials
# -------------------------------------------------
st.header("What Our Students Say")

testimonials = [
    {
        "name": "Riya Sharma",
        "role": "Data Analyst, Bangalore",
        "quote": "The GenAI Foundations course gave me the confidence to build production‑grade models. The mentors were always there to help!",
        "emoji": "🌟",
    },
    {
        "name": "Amit Patel",
        "role": "Software Engineer, Hyderabad",
        "quote": "Hands‑on labs were the best part – I built an AI agent that automated my daily reporting tasks.",
        "emoji": "🚀",
    },
    {
        "name": "Sneha Rao",
        "role": "Recent Graduate, Chennai",
        "quote": "Placement support opened doors I never imagined. I landed a role as an AI Engineer within weeks of graduating.",
        "emoji": "💼",
    },
]

cols = st.columns(3, gap="large")
for col, t in zip(cols, testimonials):
    with col:
        testimonial_html = f"""
        <div class="card" style="padding: 1.5rem; border-radius: 0.75rem; background: {COLORS['surface']};
            box-shadow: 0 2px 6px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column;
            justify-content: space-between;">
            <p class="muted" style="font-style: italic; color: {COLORS['text']};">
                {t['emoji']} “{t['quote']}”
            </p>
            <div style="margin-top: 1rem;">
                <strong style="color: {COLORS['primary']};">{t['name']}</strong><br/>
                <span class="muted" style="color: {COLORS['muted']};">{t['role']}</span>
            </div>
        </div>
        """
        st.markdown(testimonial_html, unsafe_allow_html=True)

st.write("---")
