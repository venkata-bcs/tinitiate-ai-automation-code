"""
Simple Agent - a CrewAI crew that runs ONCE (no agentic loop)
(c) Venkata Bhattaram

    Agent 1   Topic Creator      -> picks a topic            (printed in the terminal)
    Agent 2.0 Text Writer        -> writes an article        } these two run
    Agent 2.1 Visual Designer    -> image prompt + workflow  } in PARALLEL
    Agent 3   Content Validator  -> spelling, grammar and accuracy check

Everything the agents produce is saved in output/<date_time>_<topic>/

Usage:
    python simple_agent.py                                   # default subject
    python simple_agent.py "Generative AI in healthcare"     # your own subject
    python simple_agent.py "Cyber security" --no-image       # skip the image generation
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
if hasattr(sys.stdout, "reconfigure"):          # CrewAI logs emojis; Windows consoles need UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402

# Workaround: CrewAI adds a "cache_breakpoint" key to messages that Groq (via LiteLLM) rejects
_format_messages = LLM._format_messages_for_provider
LLM._format_messages_for_provider = lambda self, messages: _format_messages(
    self, [{k: v for k, v in m.items() if k != "cache_breakpoint"} for m in messages or []])

HERE = Path(__file__).resolve().parent
SETTINGS_FILE = HERE.parent / "settings.config"
OUTPUT_DIR = HERE / "output"
GROQ_MODEL = "groq/openai/gpt-oss-120b"
IMAGE_API = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"


def load_settings():
    """Read KEY=VALUE lines from ../settings.config."""
    settings = {}
    if SETTINGS_FILE.exists():
        for line in SETTINGS_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip().strip("'\"")
    return settings


# ------------------------------------------------------------------ progress messages
START = time.time()


def field(text, name):
    """Get the value after 'NAME:' in an agent's answer (ignores Markdown bold like **NAME:**)."""
    match = re.search(rf"\**{name}\**\s*:\**\s*(.+)", text)
    return match.group(1).strip(" *") if match else ""


def show_topic(output):
    """Task callback: prints the topic as soon as Agent 1 finishes."""
    print("\n" + "=" * 70)
    print(f"  {field(output.raw, 'TOPIC') or output.raw.strip()}")
    print(f"  {field(output.raw, 'WHY')}")
    print("=" * 70)
    print(f"[{time.time() - START:5.1f}s] Agent 1 done. Agents 2.0 and 2.1 now start in parallel ...", flush=True)


def show_done(output):
    """Task callback: shows when each agent finishes (2.0 and 2.1 finish close together = parallel)."""
    print(f"[{time.time() - START:5.1f}s] {output.agent} done", flush=True)


# ------------------------------------------------------------------ the agents
def build_crew(llm, subject):
    topic_creator = Agent(
        role="Topic Creator",
        goal=f"Pick one specific, interesting topic about: {subject}",
        backstory="You are a content strategist who finds topics readers actually want to learn about.",
        llm=llm, verbose=False,
    )
    text_writer = Agent(
        role="Text Content Writer",
        goal="Write a clear, accurate and engaging article on the given topic",
        backstory="You are a technical writer who explains complex ideas in simple words.",
        llm=llm, verbose=False,
    )
    visual_designer = Agent(
        role="Image and Workflow Designer",
        goal="Design a cover image and a step-by-step workflow diagram for the topic",
        backstory="You are a visual designer who turns ideas into images and simple diagrams.",
        llm=llm, verbose=False,
    )
    validator = Agent(
        role="Content Validator",
        goal="Find every spelling, grammar and factual accuracy issue in the content",
        backstory="You are a strict editor and fact-checker. You list real problems and suggest fixes.",
        llm=llm, verbose=False,
    )

    # ---- Task 1: runs first; the callback prints the topic as soon as it is ready
    topic_task = Task(
        description=f"Choose ONE specific topic about '{subject}' for a short article for beginners.",
        expected_output="Exactly two lines:\nTOPIC: <the topic title>\nWHY: <one sentence on why it is interesting>",
        agent=topic_creator,
        callback=show_topic,
    )

    # ---- Tasks 2.0 and 2.1: async_execution=True makes them run at the same time.
    #      Both get the topic through context=[topic_task].
    text_task = Task(
        description="Write an article of about 400 words on the TOPIC from the previous step. "
                    "Use a title, an introduction, 3 short sections with headings and a conclusion.",
        expected_output="The article in Markdown.",
        agent=text_writer,
        context=[topic_task],
        async_execution=True,
        callback=show_done,
    )
    visual_task = Task(
        description="For the TOPIC from the previous step create:\n"
                    "1. A detailed prompt for an AI image generator for the article's cover image "
                    "(style, subject, colours; no text in the image).\n"
                    "2. A workflow diagram with 5-7 steps that explains the topic, as Mermaid flowchart code.\n"
                    "3. A one-sentence caption.",
        expected_output="Exactly this format:\n"
                        "IMAGE PROMPT: <one paragraph>\n"
                        "CAPTION: <one sentence>\n"
                        "WORKFLOW:\n```mermaid\nflowchart TD\n  ...\n```",
        agent=visual_designer,
        context=[topic_task],
        async_execution=True,
        callback=show_done,
    )

    # ---- Task 3: waits for BOTH parallel tasks (context) and then validates their output
    validate_task = Task(
        description="Validate the article and the image/workflow content from the previous steps. Check:\n"
                    "- spelling mistakes\n- grammar mistakes\n- factual accuracy (claims that are wrong or "
                    "misleading)\n- whether the workflow diagram matches the article.\n"
                    "Quote each problem and give the correction.",
        expected_output="A Markdown report with the sections: Spelling, Grammar, Accuracy, Workflow, "
                        "then a line 'Score: <1-10>/10' and a final line 'VERDICT: PASS' or "
                        "'VERDICT: NEEDS FIXES'.",
        agent=validator,
        context=[text_task, visual_task],
        callback=show_done,
    )

    crew = Crew(
        agents=[topic_creator, text_writer, visual_designer, validator],
        tasks=[topic_task, text_task, visual_task, validate_task],
        process=Process.sequential,   # tasks run in list order; async tasks run side by side
        verbose=False,
    )
    return crew, (topic_task, text_task, visual_task, validate_task)


# ------------------------------------------------------------------ helpers
def generate_image(api_key, prompt, target):
    """Turn the Visual Designer's prompt into a real image (FLUX.1-dev on NVIDIA)."""
    payload = {"prompt": prompt[:2000], "width": 1344, "height": 768, "steps": 30, "seed": 0}
    request = urllib.request.Request(IMAGE_API, data=json.dumps(payload).encode(), headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        artifact = json.load(response)["artifacts"][0]
    target.write_bytes(base64.b64decode(artifact["base64"]))


def main():
    global START
    parser = argparse.ArgumentParser(description="Run the simple 4-agent CrewAI crew once")
    parser.add_argument("subject", nargs="?", default="AI automation for small businesses")
    parser.add_argument("--no-image", action="store_true", help="do not generate the cover image")
    args = parser.parse_args()

    settings = load_settings()
    if not settings.get("GROQ_API_KEY"):
        sys.exit(f"GROQ_API_KEY not found in {SETTINGS_FILE}")
    os.environ["GROQ_API_KEY"] = settings["GROQ_API_KEY"]
    # num_retries: LiteLLM waits and retries when Groq's free plan rate-limits us
    llm = LLM(model=GROQ_MODEL, api_key=settings["GROQ_API_KEY"], temperature=0.4, num_retries=5)

    START = time.time()
    print(f"Subject: {args.subject}\nAgent 1 is choosing a topic ...", flush=True)
    crew, (topic_task, text_task, visual_task, validate_task) = build_crew(llm, args.subject)
    crew.kickoff()
    print(f"All agents finished. Total time: {time.time() - START:.0f}s", flush=True)

    # ---- Save everything in output/<date_time>_<topic>/
    topic = field(topic_task.output.raw, "TOPIC") or args.subject
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50]
    run_dir = OUTPUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}"
    run_dir.mkdir(parents=True)

    visual = visual_task.output.raw
    (run_dir / "1_topic.md").write_text(f"# Topic\n\n{topic_task.output.raw.strip()}\n", encoding="utf-8")
    (run_dir / "2.0_article.md").write_text(text_task.output.raw.strip() + "\n", encoding="utf-8")
    (run_dir / "2.1_image_and_workflow.md").write_text(visual.strip() + "\n", encoding="utf-8")
    (run_dir / "3_validation_report.md").write_text(validate_task.output.raw.strip() + "\n", encoding="utf-8")

    image_note = "skipped (--no-image)"
    if not args.no_image:
        prompt, nvidia_key = field(visual, "IMAGE PROMPT"), settings.get("NVDIA_API_KEY")
        if not prompt or not nvidia_key:
            image_note = "skipped (no image prompt or no NVDIA_API_KEY in settings.config)"
        else:
            print("Generating the cover image from Agent 2.1's prompt ...", flush=True)
            try:
                generate_image(nvidia_key, prompt, run_dir / "2.1_cover_image.jpg")
                image_note = "2.1_cover_image.jpg"
            except (urllib.error.URLError, KeyError, TimeoutError) as e:
                image_note = f"failed ({e})"

    verdict = field(validate_task.output.raw, "VERDICT") or "see report"
    print(f"\nValidation verdict: {verdict}")
    print(f"Output folder     : {run_dir}")
    for f in sorted(run_dir.iterdir()):
        print(f"   {f.name}")
    print(f"Cover image       : {image_note}")


if __name__ == "__main__":
    main()
