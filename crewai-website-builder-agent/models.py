"""
Structured data passed between the agents. Each agent answers with JSON that is
validated against one of these models.
"""
import re
from typing import Literal

from pydantic import BaseModel, Field


# ---------- Requirements Analyst output ----------
class Link(BaseModel):
    label: str
    route: str = Field(description="Route path, e.g. / or /courses or /contact")


class Page(BaseModel):
    name: str = Field(description="Page title shown in navigation, e.g. 'About Us'")
    component: str = Field(description="PascalCase page name, e.g. 'AboutUs'")
    route: str = Field(description="Route path. Home page must be '/'")
    purpose: str
    sections: list[str] = Field(description="Content sections the page must contain, each copied word for word "
                                            "from the spec with ALL its details (items, names, counts, prices)")

    @property
    def file(self) -> str:
        """Streamlit page file, e.g. AboutUs -> pages/about_us.py"""
        return "pages/" + re.sub(r"(?<!^)(?=[A-Z])", "_", self.component).lower() + ".py"

    @property
    def url_path(self) -> str:
        return self.route.strip("/")


class HeaderSpec(BaseModel):
    logo_text: str
    nav: list[Link]
    cta_label: str | None = Field(default=None, description="Highlighted button text, if any")
    cta_route: str | None = None


class FooterSpec(BaseModel):
    copyright: str
    links: list[Link]
    contact_info: list[str] = Field(default_factory=list, description="Address, email, phone lines")
    social: list[str] = Field(default_factory=list, description="Social network names")


class FormField(BaseModel):
    name: str = Field(description="snake_case field key, used as CSV column, e.g. full_name")
    label: str
    type: Literal["text", "email", "tel", "textarea", "select"]
    required: bool
    options: list[str] = Field(default_factory=list, description="Options for select fields")


class ContactSpec(BaseModel):
    name: str = "Contact Us"
    route: str = "/contact"
    intro: str
    fields: list[FormField]
    success_message: str = Field(description="The actual thank-you sentence shown to the visitor")

    @property
    def file(self) -> str:
        return "pages/contact.py"

    @property
    def url_path(self) -> str:
        return self.route.strip("/")


class ThemeInputs(BaseModel):
    audience: str
    industry: str
    mood: str
    color_preference: str
    other_notes: str = ""


class SiteSpec(BaseModel):
    site_name: str
    description: str
    pages: list[Page] = Field(description="All content pages EXCEPT the Contact Us page")
    header: HeaderSpec
    footer: FooterSpec
    contact: ContactSpec
    theme_inputs: ThemeInputs


# ---------- Theme Decision Maker output ----------
class ThemeScore(BaseModel):
    theme_id: str
    score: int = Field(ge=1, le=10)
    reason: str


class ThemeDecision(BaseModel):
    scores: list[ThemeScore] = Field(description="A score for every theme in the catalog")
    theme_id: str = Field(description="The chosen theme id; must exist in the catalog")
    reasoning: str = Field(description="Why this theme best matches the theme inputs")


# ---------- Developer output (parsed from FILE blocks, not JSON) ----------
class GeneratedFile(BaseModel):
    path: str
    content: str


class DeveloperOutput(BaseModel):
    files: list[GeneratedFile]


# ---------- Testing Agent output ----------
class TestReport(BaseModel):
    section_checks: list[str] = Field(default_factory=list,
                                      description="One line per requirement: FOUND (evidence) or MISSING")
    passed: bool = Field(description="True only if there are no functional defects")
    issues: list[str] = Field(default_factory=list, description="Functional defects found, each with the file name")
    fix_instructions: str = Field(default="", description="Concrete instructions for the developer to fix the issues")
