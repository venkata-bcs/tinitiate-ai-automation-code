"""
Theme catalog the Theme Decision Maker agent chooses from.
The chosen theme becomes the Streamlit theme (.streamlit/config.toml) and CSS (lib/theme.py)
of the generated website.
"""

THEMES = {
    "corporate-blue": {
        "description": "Clean and professional. Suits finance, consulting, B2B and corporate services.",
        "keywords": ["professional", "trustworthy", "corporate", "finance", "consulting", "formal"],
        "mode": "light",
        "colors": {
            "primary": "#1d4ed8", "primary-contrast": "#ffffff", "secondary": "#0f172a",
            "accent": "#f59e0b", "bg": "#f8fafc", "surface": "#ffffff",
            "text": "#0f172a", "muted": "#475569", "border": "#e2e8f0",
            "header-bg": "#0f172a", "header-text": "#ffffff",
        },
        "fonts": {"heading": "Merriweather", "body": "Inter"},
        "radius": "6px",
    },
    "tech-violet": {
        "description": "Modern and energetic with blue-violet gradients. Suits tech, SaaS, education and startups.",
        "keywords": ["modern", "tech", "energetic", "innovative", "education", "startup", "blue", "purple"],
        "mode": "light",
        "colors": {
            "primary": "#4f46e5", "primary-contrast": "#ffffff", "secondary": "#7c3aed",
            "accent": "#06b6d4", "bg": "#f5f7ff", "surface": "#ffffff",
            "text": "#111827", "muted": "#4b5563", "border": "#e0e7ff",
            "header-bg": "#1e1b4b", "header-text": "#ffffff",
        },
        "fonts": {"heading": "Poppins", "body": "Inter"},
        "radius": "12px",
    },
    "midnight-dark": {
        "description": "Dark, bold and high contrast. Suits gaming, developer tools, AI and nightlife.",
        "keywords": ["dark", "bold", "gaming", "developer", "futuristic", "night", "edgy"],
        "mode": "dark",
        "colors": {
            "primary": "#22d3ee", "primary-contrast": "#0b1120", "secondary": "#a78bfa",
            "accent": "#f472b6", "bg": "#0b1120", "surface": "#111827",
            "text": "#e5e7eb", "muted": "#9ca3af", "border": "#1f2937",
            "header-bg": "#030712", "header-text": "#f9fafb",
        },
        "fonts": {"heading": "Space Grotesk", "body": "Inter"},
        "radius": "10px",
    },
    "warm-earthy": {
        "description": "Warm, cosy and natural. Suits restaurants, cafes, food, bakeries and handicrafts.",
        "keywords": ["warm", "cosy", "food", "restaurant", "organic", "rustic", "family"],
        "mode": "light",
        "colors": {
            "primary": "#b45309", "primary-contrast": "#ffffff", "secondary": "#78350f",
            "accent": "#15803d", "bg": "#fffbf5", "surface": "#ffffff",
            "text": "#292524", "muted": "#57534e", "border": "#f5e6d3",
            "header-bg": "#451a03", "header-text": "#fff7ed",
        },
        "fonts": {"heading": "Playfair Display", "body": "Lato"},
        "radius": "8px",
    },
    "fresh-green": {
        "description": "Calm, healthy and eco-friendly. Suits healthcare, wellness, agriculture and NGOs.",
        "keywords": ["calm", "health", "wellness", "eco", "nature", "green", "ngo", "clinic"],
        "mode": "light",
        "colors": {
            "primary": "#047857", "primary-contrast": "#ffffff", "secondary": "#065f46",
            "accent": "#0ea5e9", "bg": "#f6fdf9", "surface": "#ffffff",
            "text": "#14231c", "muted": "#4b5d54", "border": "#d1fae5",
            "header-bg": "#064e3b", "header-text": "#ecfdf5",
        },
        "fonts": {"heading": "Nunito", "body": "Nunito Sans"},
        "radius": "14px",
    },
    "playful-bright": {
        "description": "Fun, colourful and friendly. Suits kids, events, toys and hobby clubs.",
        "keywords": ["fun", "playful", "kids", "colourful", "events", "friendly", "pink"],
        "mode": "light",
        "colors": {
            "primary": "#db2777", "primary-contrast": "#ffffff", "secondary": "#7c3aed",
            "accent": "#facc15", "bg": "#fffaf0", "surface": "#ffffff",
            "text": "#1f2937", "muted": "#6b7280", "border": "#fde68a",
            "header-bg": "#ffffff", "header-text": "#1f2937",
        },
        "fonts": {"heading": "Fredoka", "body": "Nunito"},
        "radius": "18px",
    },
    "minimal-mono": {
        "description": "Minimal black and white with lots of space. Suits portfolios, architecture, luxury and fashion.",
        "keywords": ["minimal", "elegant", "luxury", "portfolio", "fashion", "architecture", "simple"],
        "mode": "light",
        "colors": {
            "primary": "#111111", "primary-contrast": "#ffffff", "secondary": "#404040",
            "accent": "#b91c1c", "bg": "#ffffff", "surface": "#fafafa",
            "text": "#111111", "muted": "#525252", "border": "#e5e5e5",
            "header-bg": "#ffffff", "header-text": "#111111",
        },
        "fonts": {"heading": "DM Serif Display", "body": "DM Sans"},
        "radius": "0px",
    },
}


def catalog_for_prompt():
    """Short text listing of the themes for the LLM (no colour codes needed to decide)."""
    return "\n".join(
        f"- {tid}: {t['description']} Mode: {t['mode']}. Keywords: {', '.join(t['keywords'])}."
        for tid, t in THEMES.items()
    )
