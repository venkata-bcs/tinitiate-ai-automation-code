# Website Spec

Edit this file and run `python build_website.py` to (re)build the website.

## Technology
- Framework: Streamlit (Python) - the whole website is built with Streamlit, no HTML/JavaScript project
- Run with: `streamlit run app.py` inside the `website` folder
- Contact Us submissions are stored in a CSV file: `website/data/contacts.csv`

## Site
- Site Name: Tinitiate AI Academy
- Description: A training institute that teaches Generative AI, AI Agents and Automation to working professionals and students in India.

## Pages
1. Home
   - Hero banner with a headline, a short pitch and a "Explore Courses" button
   - Three highlights: Hands-on Labs, Industry Mentors, Placement Support
   - Testimonials from 3 students
2. Courses
   - Course cards: GenAI Foundations, AI Agents with CrewAI & LangGraph, Python Automation, Prompt Engineering
   - Each card shows duration, mode (Online / Classroom) and fee in Rs.
3. About Us
   - Our story, mission and vision
   - Team section with 3 trainers (name, role, one-line bio)
4. Contact Us
   - See the Contact Us section below

## Header
- Logo text: Tinitiate AI Academy
- Navigation links to all pages
- A highlighted "Enroll Now" button that goes to Contact Us

## Footer
- Copyright line: (c) Tinitiate AI Academy
- Quick links to all pages
- Address: Hyderabad, Telangana, India
- Email: info@tinitiate.example
- Social: LinkedIn, YouTube, GitHub

## Contact Us
- Short intro text inviting visitors to ask about courses
- Form fields:
  - Full Name (required)
  - Email (required)
  - Phone (optional)
  - Course Interested In (dropdown with the course names, required)
  - Message (required, multi-line)
- Show a thank-you message after submitting
- Submitted data is saved to `data/contacts.csv`

## Theme Inputs
(The Theme Decision Maker agent picks a theme using these.)
- Audience: Working professionals and college students
- Industry: Technology education
- Mood: Modern, trustworthy, energetic
- Colour preference: Blues or purples, avoid pastel pinks
- Dark or light: Either, but text must be easy to read
