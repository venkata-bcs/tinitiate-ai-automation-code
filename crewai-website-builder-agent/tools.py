"""
Automated test suite whose results the Testing Agent reviews:
  compile  - every generated Python file has valid syntax
  render   - every page runs without errors (Streamlit AppTest) and links to every other page
  contact  - the Contact Us form saves a valid submission to the CSV and rejects an invalid one

The tests run website/tests/check_site.py in a separate Python process, so every round tests
the latest files. Results are recorded in RESULTS so the flow's router can trust real test
outcomes, not just the agent's opinion.
"""
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

from models import SiteSpec
from scaffold import allowed_paths

WEBSITE_DIR: Path = Path()
SPEC: SiteSpec | None = None
RESULTS: dict[str, bool] = {}   # check name -> passed (reset before each test round)
OUTPUTS: dict[str, str] = {}    # check name -> last output text


def configure(website_dir: Path, spec: SiteSpec):
    global WEBSITE_DIR, SPEC
    WEBSITE_DIR, SPEC = website_dir, spec
    RESULTS.clear()
    OUTPUTS.clear()


def _record(name, ok, output):
    RESULTS[name], OUTPUTS[name] = ok, output
    return output


def _run_site_test(mode):
    """Run tests/check_site.py <mode> and return its parsed RESULTS json (or an error string)."""
    env = {**os.environ, "CONTACTS_CSV": "data/contacts.test.csv", "PYTHONUTF8": "1"}
    result = subprocess.run([sys.executable, "tests/check_site.py", mode], cwd=WEBSITE_DIR, env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    line = next((l for l in result.stdout.splitlines() if l.startswith("RESULTS ")), None)
    if not line:
        return None, (result.stdout + result.stderr)[-3000:]
    return json.loads(line[len("RESULTS "):]), None


# ---------------------------------------------------------------- checks
INTERNAL_HTML_LINK = re.compile(r"""href\s*=\s*["'](?!https?:|mailto:|tel:|#)""")
PAGE_LINK_IN_FSTRING = re.compile(r"\{\s*st\.page_link\(")


def check_compile() -> str:
    """Syntax check, plus code patterns that break navigation in Streamlit."""
    problems = []
    for rel in sorted(allowed_paths(SPEC)):
        path = WEBSITE_DIR / rel
        if not path.exists():
            problems.append(f"{rel} is missing")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            problems.append(f"{rel}: {e.msg.strip()}")
            continue
        code = path.read_text(encoding="utf-8")
        if INTERNAL_HTML_LINK.search(code):
            problems.append(f"{rel}: uses an HTML <a href> link to an internal page - use st.page_link instead")
        if PAGE_LINK_IN_FSTRING.search(code):
            problems.append(f"{rel}: calls st.page_link inside an f-string/HTML - st.page_link returns None and "
                            "draws its own link; call it as a separate statement")
    return _record("compile", not problems, "COMPILE PASSED" if not problems
                   else "COMPILE FAILED:\n" + "\n".join(problems))


def check_render() -> str:
    """Run app.py and every page; verify no errors and that the header/footer link to every page."""
    result, error = _run_site_test("render")
    if error:
        return _record("render", False, "RENDER TEST FAILED TO RUN:\n" + error)

    problems, layout = [], result["layout"]
    if not layout["ok"]:
        problems.append(f"app.py (header/footer in components/layout.py) raised an error:\n{layout['error']}")
    names = {p.url_path: p.name for p in SPEC.pages} | {SPEC.contact.url_path: SPEC.contact.name}
    missing = set(names) - {link["url_path"] for link in layout["links"]}
    cta = SPEC.header.cta_label
    if layout["ok"] and cta:
        cta_path = (SPEC.header.cta_route or SPEC.contact.route).strip("/")
        if not any(cta.lower() in link["label"].lower() and link["url_path"] == cta_path
                   for link in layout["links"]):
            problems.append(f"components/layout.py: the '{cta}' button must be an st.page_link to /{cta_path} "
                            "inside st.container(key=\"header_cta\")")
    if layout["ok"] and missing:
        problems.append("components/layout.py: header/footer has no st.page_link to "
                        f"{sorted(names[m] for m in missing)}")
    for page in result["pages"]:
        if not page["ok"]:
            problems.append(f"{page['file']} raised an error:\n{page['error']}")

    summary = [f"{p['file']}\n  headings: {' | '.join(p['headings'])}\n  page text: "
               + " | ".join(p["texts"])[:1800] for p in result["pages"] if p["ok"]]
    links = ", ".join(f"{link['label']} -> /{link['url_path']}" for link in layout["links"])
    status = "RENDER TEST PASSED for all pages" if not problems else "RENDER TEST FAILED:\n" + "\n".join(problems)
    return _record("render", not problems, status
                   + f"\n\nHeader + footer (same on every page)\n  links: {links}"
                   + f"\n  text: {' | '.join(layout['texts'])[:800]}"
                   + "\n\nRendered content of each page:\n" + "\n".join(summary))


def check_contact() -> str:
    """Fill in and submit the Contact Us form; verify the CSV row and required-field validation."""
    result, error = _run_site_test("contact")
    if error:
        return _record("contact", False, "CONTACT TEST FAILED TO RUN:\n" + error)
    if result["ok"]:
        return _record("contact", True, "CONTACT FORM PASSED (valid submission saved to CSV with a thank-you "
                                        f"message {result['success_messages']}; missing required field rejected)")
    return _record("contact", False, "CONTACT FORM FAILED (src: pages/contact.py):\n" + "\n".join(result["problems"]))


CHECKS = {"compile": check_compile, "render": check_render, "contact": check_contact}
