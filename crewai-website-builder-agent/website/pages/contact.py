import streamlit as st
from lib.storage import save_contact
from lib.theme import COLORS  # Imported as per contract, can be used for custom styling if needed

# ----------------------------------------------------------------------
# Page Title & Introduction
# ----------------------------------------------------------------------
st.title("Contact Us")

intro_text = (
    "Have questions about our AI courses or want to learn more? "
    "Fill out the form below and we'll get back to you promptly."
)
st.markdown(intro_text)

# ----------------------------------------------------------------------
# Contact Form
# ----------------------------------------------------------------------
with st.form("contact_form", clear_on_submit=True):
    # Full Name (required)
    full_name = st.text_input("Full Name *", key="full_name")

    # Email (required)
    email = st.text_input("Email *", key="email")

    # Phone (optional)
    phone = st.text_input("Phone", key="phone")

    # Course Interested In (required select)
    course_options = [
        "GenAI Foundations",
        "AI Agents with CrewAI & LangGraph",
        "Python Automation",
        "Prompt Engineering",
    ]
    course_interested_in = st.selectbox(
        "Course Interested In *",
        options=course_options,
        index=None,
        placeholder="Choose...",
        key="course_interested_in",
    )

    # Message (required)
    message = st.text_area("Message *", key="message")

    # Submit button
    submitted = st.form_submit_button("Send Message")

# ----------------------------------------------------------------------
# Handle Submission
# ----------------------------------------------------------------------
if submitted:
    # Gather values into a dict matching the expected field names
    values = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "course_interested_in": course_interested_in,
        "message": message,
    }

    # Save the contact information using the provided storage helper
    error = save_contact(values)

    if error:
        st.error(error)
    else:
        st.success("Thank you for contacting us. We will respond shortly.")
