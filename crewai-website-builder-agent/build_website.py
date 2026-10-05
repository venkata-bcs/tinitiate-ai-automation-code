"""
CrewAI Website Builder Agent
(c) Venkata Bhattaram

Reads the website spec from to-do.md and builds a Streamlit website into ./website
using a crew of AI agents:

  1. Requirements Analyst  - turns to-do.md into a structured SiteSpec
  2. Theme Decision Maker  - scores every theme in themes.py and picks the best fit
  3. Developer             - writes the header, footer and pages (Streamlit / Python)
  4. Testing Agent         - reviews the automated test results against to-do.md;
                             defects are sent back to the Developer (max 2 fix rounds)

The Contact Us form saves each submission to website/data/contacts.csv.

Usage:
    python build_website.py                 # Groq (GROQ_API_KEY)
    python build_website.py --llm nvidia    # NVIDIA NIM (NVDIA_API_KEY)
    python build_website.py --quiet         # hide the agents' step-by-step logs
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
if hasattr(sys.stdout, "reconfigure"):          # CrewAI logs emojis; Windows consoles need UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from crewai import LLM, Agent, Crew, Task                      # noqa: E402
from crewai.flow.flow import Flow, listen, or_, router, start  # noqa: E402
from pydantic import BaseModel, PrivateAttr, ValidationError   # noqa: E402

import tools                                                    # noqa: E402
from models import DeveloperOutput, GeneratedFile, SiteSpec, TestReport, ThemeDecision  # noqa: E402
from scaffold import allowed_paths, normalize_spec, write_scaffold  # noqa: E402
from themes import THEMES, catalog_for_prompt                   # noqa: E402

# Workaround: CrewAI marks messages with a "cache_breakpoint" key for prompt caching and its native
# providers strip it, but the LiteLLM path (used for Groq / NVIDIA) sends it on and Groq rejects it.
_format_messages = LLM._format_messages_for_provider
LLM._format_messages_for_provider = lambda self, messages: _format_messages(
    self, [{k: v for k, v in m.items() if k != "cache_breakpoint"} for m in messages or []])

HERE = Path(__file__).resolve().parent
CONFIG_FILES = [HERE / "settings.config", HERE.parent / "settings.config"]
WEBSITE_DIR = HERE / "website"
REPORTS_DIR = HERE / "reports"

LLM_PROVIDERS = {
    "groq": {"model": "groq/openai/gpt-oss-120b", "key": "GROQ_API_KEY", "env": "GROQ_API_KEY"},
    "google": {"model": "gemini/gemini-2.5-flash", "key": "GOOGLE_API_KEY", "env": "GEMINI_API_KEY"},
    "nvidia": {"model": "nvidia_nim/nvidia/nemotron-3-super-120b-a12b", "key": "NVDIA_API_KEY",
               "env": "NVIDIA_NIM_API_KEY"},
}


def classify_llm_error(error: Exception) -> str:
    """Sort an LLM failure into: rate_limit, auth, bad_tool_call, guardrail or other."""
    message = str(error).lower()
    if any(s in message for s in ("rate limit", "ratelimit", "resource_exhausted", "quota", " 429")):
        return "rate_limit"
    if any(s in message for s in ("invalid_api_key", "invalid api key", "permission_denied", "api key not valid",
                                  "api_key_service_blocked", "unauthorized", "authentication", " 401", " 403")):
        return "auth"
    if "tool_use_failed" in message:
        return "bad_tool_call"
    if "guardrail" in message:
        return "guardrail"
    return "other"


def make_llm(provider_name: str, config: dict, model: str | None = None):
    """Create the LLM for a provider, or return (None, reason) if its key is missing."""
    provider = LLM_PROVIDERS[provider_name]
    api_key = config.get(provider["key"])
    if not api_key:
        return None, f"{provider['key']} is not in settings.config"
    os.environ[provider["env"]] = api_key   # CrewAI's LiteLLM path reads the key from the environment
    try:
        llm = LLM(model=model or provider["model"], api_key=api_key, temperature=0.2, max_tokens=16000)
    except ImportError as e:
        return None, str(e)
    return llm, None


def check_llm(llm) -> str | None:
    """Send a tiny request to verify a key works. Returns an error summary, or None if OK."""
    try:
        llm.call("Reply with the word OK.")
        return None
    except Exception as e:  # noqa: BLE001
        message = str(e)
        if "not been used in project" in message or "SERVICE_BLOCKED" in message or "PERMISSION_DENIED" in message:
            return ("the key is not allowed to use the Gemini API. In Google Cloud Console enable the "
                    "'Generative Language API' for the key's project and allow it in the key's API restrictions, "
                    "or create a new key at https://aistudio.google.com/apikey")
        return message[:200]


def load_config():
    """Read KEY=VALUE lines from settings.config (this folder first, then the repo root)."""
    for path in CONFIG_FILES:
        if path.exists():
            config = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip("'\"")
            return config
    return {}


def save_report(name, data):
    REPORTS_DIR.mkdir(exist_ok=True)
    text = data.model_dump_json(indent=2) if isinstance(data, BaseModel) else json.dumps(data, indent=2)
    (REPORTS_DIR / name).write_text(text, encoding="utf-8")


def banner(text):
    print(f"\n{'=' * 70}\n  {text}\n{'=' * 70}", flush=True)


# ====================================================================== agents
def create_agents(llm, verbose):
    common = {"llm": llm, "verbose": verbose, "allow_delegation": False}
    return {
        "analyst": Agent(
            role="Requirements Analyst",
            goal="Convert a plain-text website spec into a complete, precise structured site specification",
            backstory="You are a business analyst who has scoped hundreds of small business websites. "
                      "You never drop a requirement and you never invent pages that were not asked for.",
            **common,
        ),
        "theme_maker": Agent(
            role="Theme Decision Maker",
            goal="Pick the single best visual theme from the catalog for the client's audience, industry and mood",
            backstory="You are a brand designer. You compare every option against the client's inputs, "
                      "respect their colour likes and dislikes, and justify your decision clearly.",
            **common,
        ),
        "developer": Agent(
            role="Senior Python Streamlit Developer",
            goal="Write clean, working Streamlit pages that implement the site spec exactly",
            backstory="You build polished multi-page Streamlit websites and follow the project contract "
                      "strictly so the site runs and passes QA the first time.",
            **common,
        ),
        "tester": Agent(
            role="QA Testing Agent",
            goal="Find every functional defect in the generated website",
            backstory="You are a meticulous QA engineer. You study the automated test results (compile, page "
                      "render and contact form tests) and check every requirement of the spec against them. "
                      "You only report real functional problems and give the developer exact fix instructions.",
            **common,
        ),
    }


# ====================================================================== output parsing & checks
# Agents answer in plain text; we parse and validate it ourselves. This works with every LLM provider
# (some models, e.g. gpt-oss on Groq, do not reliably use the tool call CrewAI's output_pydantic relies on).
def parse_json_model(raw: str, model: type[BaseModel]):
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return model.model_validate_json(raw[start:end + 1])


def clean_path(path):
    return path.strip().replace("\\", "/").removeprefix("./").removeprefix("website/")


FILE_BLOCK = re.compile(r"FILE:\s*`?([\w./-]+)`?\s*\n```[\w-]*\n(.*?)\n```", re.S)


def parse_files(raw: str) -> DeveloperOutput:
    """Developer answers with 'FILE: path' + a fenced code block per file (no JSON escaping of code)."""
    files = [GeneratedFile(path=clean_path(p), content=c.strip() + "\n") for p, c in FILE_BLOCK.findall(raw)]
    if not files:
        raise ValueError("no 'FILE: <path>' + ``` code block found")
    return DeveloperOutput(files=files)


def check_theme(decision: ThemeDecision):
    if decision.theme_id not in THEMES:
        return f"theme_id must be exactly one of: {', '.join(THEMES)}"
    return None


def make_files_check(files: list[str], all_required: bool):
    expected = set(files)

    def check(result: DeveloperOutput):
        paths = {f.path for f in result.files}
        if paths - expected:
            return f"Only return these files: {sorted(expected)}. Not allowed: {sorted(paths - expected)}"
        if all_required and expected - paths:
            return f"Missing files: {sorted(expected - paths)}. Return every file with complete content."
        for f in result.files:
            try:
                compile(f.content, f.path, "exec")
            except SyntaxError as e:
                return f"{f.path} has a Python syntax error on line {e.lineno}: {e.msg}. Fix it."
            if "set_page_config" in f.content:
                return f"{f.path} must not call st.set_page_config (app.py already does)."
        return None

    return check


def json_format(model: type[BaseModel]):
    return ("ONLY a JSON object (no markdown, no commentary) matching this JSON schema:\n"
            + json.dumps(model.model_json_schema()))


FILES_FORMAT = ("Each file as a line 'FILE: <path>' followed by a fenced code block with the complete file "
                "content, e.g.\nFILE: pages/home.py\n```python\n...\n```")


def work_units(spec: SiteSpec):
    """Split the developer's work into small tasks (keeps each LLM request small).
    Returns (name, files, spec details for that unit, unit-specific rules)."""
    all_pages = [{"name": p.name, "file": p.file} for p in spec.pages] + \
                [{"name": spec.contact.name, "file": spec.contact.file}]
    units = [(
        "Header and Footer",
        ["components/layout.py"],
        {"site_name": spec.site_name, "header": spec.header.model_dump(), "footer": spec.footer.model_dump(),
         "all_pages": all_pages},
        "- components/layout.py defines `render_header()` and `render_footer()` and runs no Streamlit code "
        "at import time.\n"
        "- render_header(): everything inside `with st.container(key=\"site_header\"):`. Use st.columns to "
        "show the logo text (bold st.markdown), one st.page_link per page for EVERY page in all_pages, and the "
        "CTA as an st.page_link placed inside `with st.container(key=\"header_cta\"):` (it is styled as a "
        "highlighted button).\n"
        "- render_footer(): everything inside `with st.container(key=\"site_footer\"):` with the copyright, "
        "an st.page_link to EVERY page in all_pages, the contact info lines and the social network names.",
    )]
    for p in spec.pages:
        units.append((
            f"{p.name} page", [p.file],
            {"site_name": spec.site_name, "description": spec.description, "page": p.model_dump(),
             "all_pages": all_pages},
            f"- {p.file}: a plain script. Start with the page title (st.title, or a hero banner with "
            "st.markdown('<div class=\"hero\"><h1>...</h1><p>...</p></div>', unsafe_allow_html=True)). Implement "
            "EVERY section in page.sections with an st.header or st.subheader heading. Show cards with "
            "st.columns + st.container(border=True). Buttons that go to another page must be st.page_link.",
        ))
    units.append((
        "Contact Us page", [spec.contact.file],
        {"site_name": spec.site_name, "contact": spec.contact.model_dump()},
        "- pages/contact.py: `from lib.storage import save_contact`. Show st.title and the intro text, then "
        "`with st.form(\"contact_form\", clear_on_submit=True):` with ONE widget per field in contact.fields, "
        "each with key=\"<field name>\" exactly: st.text_input for text/email/tel, st.text_area for textarea, "
        "st.selectbox(label, options, index=None, placeholder=\"Choose...\") for select. Add ' *' to the "
        "labels of required fields. End the form with `submitted = st.form_submit_button(\"Send Message\")`.\n"
        "- After the form: `if submitted:` build a dict {field name: widget value} for every field, call "
        "`error = save_contact(values)` (it validates and appends to data/contacts.csv - never write files "
        "yourself); if error: st.error(error) else st.success(contact.success_message).",
    ))
    return units


# ====================================================================== flow
class BuildState(BaseModel):
    spec: SiteSpec | None = None
    theme: ThemeDecision | None = None
    attempt: int = 0
    feedback: str = ""
    report: TestReport | None = None
    status: str = ""


class WebsiteBuilderFlow(Flow[BuildState]):
    # Flow is a pydantic model, so run settings are declared as private attributes
    # No flow memory needed: it would load LanceDB/pyarrow, whose DLLs Windows Smart App Control can block
    _skip_auto_memory: bool = PrivateAttr(default=True)
    _spec_file: Path = PrivateAttr()
    _max_rounds: int = PrivateAttr()
    _providers: list = PrivateAttr()   # [(provider name, agents)] in order of preference
    _verbose: bool = PrivateAttr()

    def __init__(self, spec_file: Path, llms: list, max_fix_rounds: int, verbose: bool):
        """llms: [(provider name, LLM)] - the first is used first, the next ones are fallbacks."""
        super().__init__()
        self._spec_file = spec_file
        self._max_rounds = max_fix_rounds + 1
        self._providers = [(name, create_agents(llm, verbose)) for name, llm in llms]
        self._verbose = verbose

    def spec_text(self):
        return self._spec_file.read_text(encoding="utf-8")

    def run_task(self, agent_key, parse, check=None, max_waits=8, **task_args):
        """Run one task with one agent and return its parsed output.

        A guardrail parses/validates the answer (the agent retries with the error if invalid).
        Each task starts with the first provider (Groq); if it is rate limited or fails, the task
        switches to the fallback provider (Google). If every provider is rate limited we wait and retry.
        """
        def guardrail(output):
            try:
                result = parse(output.raw)
            except (ValueError, ValidationError) as e:
                return False, f"Your answer could not be parsed ({str(e)[:400]}). Follow the output format exactly."
            error = check(result) if check else None
            return (False, error) if error else (True, output)

        provider, waits = 0, 0
        while True:
            name, agents = self._providers[provider]
            task = Task(agent=agents[agent_key], guardrail=guardrail, guardrail_max_retries=3, **task_args)
            try:
                crew_output = Crew(agents=[agents[agent_key]], tasks=[task], verbose=self._verbose).kickoff()
                return parse(crew_output.raw)
            except Exception as e:  # noqa: BLE001
                kind = classify_llm_error(e)
                if kind == "bad_tool_call" and waits < max_waits:   # model called a tool that doesn't exist
                    waits += 1
                    print(f"   {name}: model made an invalid tool call, retrying ...", flush=True)
                    time.sleep(5)
                    continue
                if kind in ("rate_limit", "auth", "guardrail") and provider + 1 < len(self._providers):
                    provider += 1
                    print(f"   {name}: {kind.replace('_', ' ')} -> switching to {self._providers[provider][0]} "
                          "for this step", flush=True)
                    continue
                if kind == "auth" and provider > 0:              # a fallback key stopped working: drop it
                    print(f"   {name} key failed ({str(e)[:150]}); continuing without it", flush=True)
                    self._providers = self._providers[:provider]
                    provider = 0
                    continue
                if kind == "rate_limit" and waits < max_waits:  # every provider is rate limited: wait
                    wait = 20 + 10 * waits
                    waits += 1
                    print(f"   all providers rate limited, retrying with {self._providers[0][0]} in {wait}s ...",
                          flush=True)
                    time.sleep(wait)
                    provider = 0
                    continue
                raise

    # ---- 1. Requirements Analyst
    @start()
    def analyze_requirements(self):
        banner("1/4  Requirements Analyst: reading " + self._spec_file.name)
        self.state.spec = normalize_spec(self.run_task(
            "analyst",
            description=(
                "Read this website spec and convert it into a SiteSpec.\n"
                "Rules:\n"
                "- `pages` contains every page EXCEPT Contact Us (Contact Us goes in `contact`).\n"
                "- The home page route is '/'; other routes are short lowercase paths like '/courses'. "
                "Contact Us route is '/contact'.\n"
                "- Header nav and footer links must include every page AND Contact Us.\n"
                "- Copy every section of every page word for word with all its details (names, counts, "
                "prices, lists) - the developer only sees what you write.\n"
                "- Contact form field names are snake_case. Use type 'select' with options for dropdowns and "
                "'textarea' for multi-line text. success_message is the actual thank-you sentence to show.\n\n"
                f"SPEC (to-do.md):\n{self.spec_text()}"
            ),
            expected_output=json_format(SiteSpec),
            parse=lambda raw: parse_json_model(raw, SiteSpec),
        ))
        save_report("1-site-spec.json", self.state.spec)
        print(f"Pages: {[p.name for p in self.state.spec.pages] + [self.state.spec.contact.name]}")

    # ---- 2. Theme Decision Maker
    @listen(analyze_requirements)
    def decide_theme(self):
        banner("2/4  Theme Decision Maker: choosing a theme")
        spec = self.state.spec
        self.state.theme = self.run_task(
            "theme_maker",
            description=(
                "Choose a theme for this website.\n\n"
                f"Website: {spec.site_name} - {spec.description}\n"
                f"Theme inputs:\n{spec.theme_inputs.model_dump_json()}\n\n"
                f"Theme catalog:\n{catalog_for_prompt()}\n\n"
                "Score EVERY theme from 1 to 10 against the audience, industry, mood and colour preference "
                "(a theme using a colour the client wants to avoid must score low). "
                "Choose the highest scoring theme and explain the decision."
            ),
            expected_output=json_format(ThemeDecision),
            parse=lambda raw: parse_json_model(raw, ThemeDecision),
            check=check_theme,
        )
        save_report("2-theme-decision.json", self.state.theme)
        print(f"Theme: {self.state.theme.theme_id}\nWhy  : {self.state.theme.reasoning}")

    # ---- Fixed scaffold (no AI): app.py, navigation, theme, contact storage, tests
    @listen(decide_theme)
    def scaffold_site(self):
        banner("Scaffold: writing app.py, theme, contact storage and tests (no AI)")
        write_scaffold(self.state.spec, self.state.theme.theme_id, WEBSITE_DIR)

    # ---- 3. Developer (runs again after each failed test round)
    @listen(or_(scaffold_site, "fix"))
    def develop(self):
        self.state.attempt += 1
        spec, theme_id = self.state.spec, self.state.theme.theme_id
        first = self.state.attempt == 1
        banner(f"3/4  Developer: {'writing' if first else 'fixing'} pages (round {self.state.attempt})")

        page_files = ", ".join(f"{p['name']} = \"{p['file']}\"" for p in
                               [{"name": p.name, "file": p.file} for p in spec.pages]
                               + [{"name": spec.contact.name, "file": spec.contact.file}])
        contract = (
            "PROJECT CONTRACT (the rest of the project already exists - do not change it):\n"
            "- Python 3.13 + Streamlit. Only import streamlit, the Python standard library and the project "
            "modules lib.theme (COLORS dict) and lib.storage (save_contact).\n"
            "- app.py already calls st.set_page_config, applies the theme CSS, calls render_header(), runs "
            "the current page, then calls render_footer(). Page files are plain scripts run top to bottom: "
            "do NOT call st.set_page_config, do NOT render the header/footer, no `if __name__` block.\n"
            f"- Links to pages: st.page_link(<file>, label=...) with these files: {page_files}. "
            "Never use HTML <a href> for internal links, and never put st.page_link inside an f-string or HTML "
            "(it returns None and draws its own link) - call it as its own statement, e.g. inside st.columns. "
            "Its only arguments are: st.page_link(page, label=..., icon=..., help=..., disabled=..., "
            "width=\"content\"|\"stretch\") - there is NO `type` or `key` argument.\n"
            f"- Theme '{theme_id}' ({THEMES[theme_id]['mode']} mode) is already applied. For custom HTML use "
            "st.markdown(html, unsafe_allow_html=True) with the CSS classes hero (gradient banner), card, muted "
            f"and badge. lib.theme.COLORS has the keys: {', '.join(THEMES[theme_id]['colors'])}.\n"
            "- No external images or files (emoji are fine). Write real, friendly content - no lorem ipsum.\n"
        )

        units = work_units(spec)
        if not first:   # only rework the files the QA feedback points at
            hits = [u for u in units if any(f in self.state.feedback for f in u[1])]
            units = hits or units

        for name, files, details, rules in units:
            print(f"-> {name}", flush=True)
            description = (
                f"{'Write' if first else 'Fix'} the {name} of the website.\n\n{contract}\nFILE RULES:\n{rules}\n\n"
                f"SPEC DETAILS:\n{json.dumps(details)}\n\n"
                "ORIGINAL SPEC (to-do.md - the source of truth: use every item, name, count and price it gives "
                f"for this part of the site):\n{self.spec_text()}\n"
            )
            if first:
                description += f"\nReturn these files with complete content: {files}"
            else:
                current = "\n\n".join(f"--- {f} ---\n{(WEBSITE_DIR / f).read_text(encoding='utf-8')}"
                                      for f in files if (WEBSITE_DIR / f).exists())
                description += (f"\nQA FEEDBACK (fix everything that concerns these files):\n{self.state.feedback}\n\n"
                                f"CURRENT FILES:\n{current}\n\n"
                                f"Return the corrected files (only from {files}) with complete content.")
            result = self.run_task(
                "developer",
                description=description,
                expected_output=FILES_FORMAT,
                parse=parse_files,
                check=make_files_check(files, all_required=first),
            )
            for f in result.files:
                target = WEBSITE_DIR / f.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f.content, encoding="utf-8")
                print(f"   wrote {f.path}", flush=True)

    # ---- 4. Testing Agent -> decides: passed / fix / failed
    @router(develop)
    def test(self):
        banner(f"4/4  Testing Agent: testing round {self.state.attempt}")
        spec = self.state.spec

        # Run the automated test suite first, then the agent reviews the evidence in ONE LLM call.
        # (A tool-calling loop resends every tool output on each step, which blows through small
        # tokens-per-minute limits such as Groq's free tier.)
        tools.configure(WEBSITE_DIR, spec)
        for name, check in tools.CHECKS.items():
            print(f"   running {name} test ...", flush=True)
            check()
        evidence = "\n\n".join(f"=== {name} test ===\n{tools.OUTPUTS[name]}" for name in tools.CHECKS)

        report = self.run_task(
            "tester",
            description=(
                "Review the automated test results of the generated Streamlit website and decide if it is done.\n"
                "1. Any failed compile, render or contact test is an issue; explain the cause and the fix.\n"
                "2. The render test shows the header/footer links and text and the headings and visible text "
                "of every page. For EVERY requirement in the ORIGINAL SPEC below (each bullet under Pages, "
                "Header, Footer and Contact Us), add a line to section_checks: '<page>: <requirement> -> FOUND "
                "(<evidence>)' or '-> MISSING'. A requirement that names specific items or a count (e.g. 'Three "
                "highlights: A, B, C', 'Testimonials from 3 students', course names, fees) is only FOUND if "
                "exactly those items appear. Every MISSING requirement is an issue.\n"
                "3. The thank-you message and the CSV saving only happen after submitting the form; the contact "
                "test submits the form, so its result is the evidence for them.\n\n"
                "Report only FUNCTIONAL defects (errors, missing links, pages, sections, items or form fields, "
                "contact form not saving). Ignore wording and cosmetic preferences. Name the file (e.g. "
                "pages/home.py or components/layout.py) in every issue. passed=true only if every test passed "
                "and there are no functional defects.\n\n"
                "PAGE FILES: " + ", ".join(f"{p.name} -> {p.file}" for p in spec.pages)
                + f", {spec.contact.name} -> {spec.contact.file}, header/footer -> components/layout.py\n\n"
                f"ORIGINAL SPEC (to-do.md):\n{self.spec_text()}\n\n"
                f"AUTOMATED TEST RESULTS:\n{evidence}"
            ),
            expected_output=json_format(TestReport),
            parse=lambda raw: parse_json_model(raw, TestReport),
        )

        # Never trust the agent alone: the real test results override its verdict
        failed_checks = [name for name, ok in tools.RESULTS.items() if not ok]
        if not failed_checks and not report.passed and not report.issues:
            report.passed = True     # agent said failed but gave no reason and all checks pass
        if failed_checks and report.passed:
            report.passed = False
            report.issues.append(f"Automated tests failed: {failed_checks}")
        self.state.report = report
        save_report(f"3-test-report-round{self.state.attempt}.json", report)

        print(f"Tests: {tools.RESULTS}  |  Agent verdict: {'PASSED' if report.passed else 'FAILED'}")
        for issue in report.issues:
            print(f"  - {issue}")

        if report.passed:
            return "passed"
        if self.state.attempt >= self._max_rounds:
            return "failed"
        self.state.feedback = "\n".join(
            ["Issues:"] + [f"- {i}" for i in report.issues]
            + [f"\nFix instructions:\n{report.fix_instructions}"]
            + [f"\n{tools.OUTPUTS[name]}" for name in failed_checks]
        )
        return "fix"

    @listen(or_("passed", "failed"))
    def finish(self):
        self.state.status = "PASSED" if self.state.report.passed else "FAILED"
        write_build_report(self.state)
        banner(f"Website build {self.state.status} after {self.state.attempt} round(s)")
        print(f"Website : {WEBSITE_DIR}")
        print(f"Reports : {REPORTS_DIR}")
        print("Run it  : cd website   then   streamlit run app.py")


def write_build_report(state: BuildState):
    spec, theme, report = state.spec, state.theme, state.report
    scores = "\n".join(f"| {s.theme_id} | {s.score} | {s.reason} |"
                       for s in sorted(theme.scores, key=lambda s: -s.score))
    lines = [
        f"# Build Report - {spec.site_name}",
        f"Built: {datetime.now():%Y-%m-%d %H:%M}  |  Status: **{state.status}**  |  Rounds: {state.attempt}",
        "",
        "## Pages",
        *[f"- {p.name}: `website/{p.file}`" for p in spec.pages],
        f"- {spec.contact.name}: `website/{spec.contact.file}` -> saves to `website/data/contacts.csv`",
        "",
        f"## Theme decision: `{theme.theme_id}`",
        theme.reasoning,
        "",
        "| Theme | Score | Reason |", "|---|---|---|", scores,
        "",
        "## Final test results",
        *[f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in tools.RESULTS.items()],
        *([f"- Open issue: {i}" for i in report.issues] if not report.passed else []),
        "",
        "## Testing Agent requirement checks",
        *[f"- {c}" for c in report.section_checks],
    ]
    (REPORTS_DIR / "BUILD_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a Streamlit website from to-do.md with a CrewAI crew")
    parser.add_argument("--spec", default=HERE / "to-do.md", type=Path, help="website spec file")
    parser.add_argument("--llm", choices=LLM_PROVIDERS, default="groq", help="main LLM provider (default groq)")
    parser.add_argument("--fallback", choices=[*LLM_PROVIDERS, "none"], default="google",
                        help="provider used when the main one is rate limited or fails (default google)")
    parser.add_argument("--model", help="override the main provider's model name")
    parser.add_argument("--max-fix-rounds", type=int, default=2)
    parser.add_argument("--quiet", action="store_true", help="hide the agents' step-by-step logs")
    args = parser.parse_args()

    config = load_config()
    llm, error = make_llm(args.llm, config, args.model)
    if not llm:
        sys.exit(f"Cannot use {args.llm}: {error}. Add a line  {LLM_PROVIDERS[args.llm]['key']}=your-key  to "
                 f"settings.config (in this folder or {HERE.parent}). See README.md, step 5.")
    llms = [(args.llm, llm)]
    print(f"Main LLM    : {args.llm} ({args.model or LLM_PROVIDERS[args.llm]['model']})")

    if args.fallback not in ("none", args.llm):
        fallback, error = make_llm(args.fallback, config)
        error = error or check_llm(fallback)
        if error:
            print(f"Fallback LLM: {args.fallback} NOT available - {error}")
        else:
            llms.append((args.fallback, fallback))
            print(f"Fallback LLM: {args.fallback} ({LLM_PROVIDERS[args.fallback]['model']})")

    flow = WebsiteBuilderFlow(args.spec.resolve(), llms, args.max_fix_rounds, verbose=not args.quiet)
    flow.kickoff()
    sys.exit(0 if flow.state.status == "PASSED" else 1)


if __name__ == "__main__":
    main()
