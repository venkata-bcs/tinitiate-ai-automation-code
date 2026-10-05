"""
Simple Agent Loop - an agentic research loop with a human in the loop
(c) Venkata Bhattaram

Each round of the loop:
    1. Researcher agent   researches the current topic (it remembers earlier rounds)
    2. Strategist agent   proposes 3 directions for the next research
    3. HUMAN              approves the next direction with Yes / No
                          (No -> the next proposal is offered; all No -> asked whether to stop)
When the human stops (or --max-rounds is reached):
    4. Reporter agent     writes a final report that connects all rounds

Everything is saved in output/<date_time>_<topic>/

Usage:
    python research_loop.py                                    # asks for the starting question
    python research_loop.py "How do AI agents use tools?"
    python research_loop.py "Solar energy in India" --max-rounds 3
"""
import argparse
import os
import re
import sys
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


def load_settings():
    """Read KEY=VALUE lines from ../settings.config."""
    settings = {}
    if SETTINGS_FILE.exists():
        for line in SETTINGS_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip().strip("'\"")
    return settings


def slugify(text, length=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:length] or "research"


# ------------------------------------------------------------------ human in the loop
def ask_yes_no(question):
    """Keep asking until the human answers yes/y or no/n."""
    while True:
        try:
            answer = input(f"\n👤 {question} (Yes/No): ").strip().lower()
        except EOFError:                       # no keyboard input available: treat as No
            print("No")
            return False
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("   Please type Yes or No.")


def choose_next_direction(directions):
    """Offer the proposed directions one at a time. Returns the chosen one, or None to stop."""
    while True:
        for i, (title, reason) in enumerate(directions, 1):
            print(f"\n🧭 Proposal {i} of {len(directions)}: {title}\n   Why: {reason}")
            if ask_yes_no("Research this next?"):
                return title
        if ask_yes_no("You declined all proposals. Stop the research and write the final report?"):
            return None
        print("\nOK, here are the proposals again.")


# ------------------------------------------------------------------ the agents
def create_agents(llm):
    researcher = Agent(
        role="Researcher",
        goal="Research a topic thoroughly and explain the findings clearly and accurately",
        backstory="You are an experienced research analyst. You state facts carefully, mention "
                  "uncertainty when you are not sure, and build on what was already researched.",
        llm=llm, verbose=False,
    )
    strategist = Agent(
        role="Research Strategist",
        goal="Decide where the research should go next to answer the original question best",
        backstory="You plan research projects. You spot gaps and open questions and suggest the most "
                  "valuable next step, without repeating topics that were already covered.",
        llm=llm, verbose=False,
    )
    reporter = Agent(
        role="Report Writer",
        goal="Combine all research rounds into one clear final report",
        backstory="You write concise reports for busy readers, with a clear conclusion.",
        llm=llm, verbose=False,
    )
    return researcher, strategist, reporter


def run_round(researcher, strategist, question, topic, history):
    """One loop iteration: research the topic, then propose the next directions."""
    memory = "\n".join(f"- Round {i}: {t} -> {s}" for i, (t, s, _) in enumerate(history, 1)) or "- (none yet)"
    research_task = Task(
        description=f"Original research question: {question}\n"
                    f"Research done so far:\n{memory}\n\n"
                    f"Now research this topic: {topic}\n"
                    "Build on the earlier rounds and do not repeat them.",
        expected_output="Markdown that starts with the line 'SUMMARY: <2 sentences>', followed by the "
                        "sections '## Key findings' (4-6 bullet points), '## Details' (2 short paragraphs) "
                        "and '## Open questions' (2-3 bullet points).",
        agent=researcher,
    )
    next_task = Task(
        description=f"Original research question: {question}\n"
                    f"Topics already researched: {[t for t, _, _ in history] + [topic]}\n\n"
                    "Using the latest findings, propose the 3 best directions for the NEXT research round, "
                    "best first. Each must be a new, specific topic that brings us closer to answering the "
                    "original question. Write each topic as a short, plain-English question or subject of at "
                    "most 12 words (e.g. 'How do agents choose between many tools?') - not a project plan.",
        expected_output="Exactly three lines:\n"
                        "NEXT 1: <topic, max 12 words> | <one short sentence on why>\n"
                        "NEXT 2: <topic, max 12 words> | <one short sentence on why>\n"
                        "NEXT 3: <topic, max 12 words> | <one short sentence on why>",
        agent=strategist,
        context=[research_task],
    )
    Crew(agents=[researcher, strategist], tasks=[research_task, next_task],
         process=Process.sequential, verbose=False).kickoff()

    findings = research_task.output.raw.strip()
    match = re.search(r"\**SUMMARY\**\s*:\**\s*(.+)", findings)
    summary = match.group(1).strip(" *") if match else findings[:300]
    directions = re.findall(r"NEXT\s*\d\s*\**\s*:\**\s*(.+?)\s*\|\s*(.+)", next_task.output.raw)
    return findings, summary, [(t.strip(" *"), r.strip(" *")) for t, r in directions[:3]]


def write_final_report(reporter, question, history):
    rounds = "\n\n".join(f"### Round {i}: {t}\n{f}" for i, (t, _, f) in enumerate(history, 1))
    task = Task(
        description=f"Original research question: {question}\n\nAll research rounds:\n{rounds}\n\n"
                    "Write the final report that answers the original question using these rounds.",
        expected_output="Markdown with: a title, '## Answer' (one paragraph), '## What we learned' "
                        "(one bullet per round), '## Conclusion' and '## Suggested further research'.",
        agent=reporter,
    )
    Crew(agents=[reporter], tasks=[task], verbose=False).kickoff()
    return task.output.raw.strip()


# ------------------------------------------------------------------ the loop
def main():
    parser = argparse.ArgumentParser(description="Agentic research loop with a human in the loop")
    parser.add_argument("question", nargs="?", help="the research question to start with")
    parser.add_argument("--max-rounds", type=int, default=5, help="safety limit for the loop (default 5)")
    args = parser.parse_args()

    settings = load_settings()
    if not settings.get("GROQ_API_KEY"):
        sys.exit(f"GROQ_API_KEY not found in {SETTINGS_FILE}")
    os.environ["GROQ_API_KEY"] = settings["GROQ_API_KEY"]
    llm = LLM(model=GROQ_MODEL, api_key=settings["GROQ_API_KEY"], temperature=0.4, num_retries=5)
    researcher, strategist, reporter = create_agents(llm)

    question = args.question or input("👤 What do you want to research? ").strip()
    if not question:
        sys.exit("No research question given.")
    run_dir = OUTPUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slugify(question)}"
    run_dir.mkdir(parents=True)
    log = [f"# Research log\n\nQuestion: {question}\n"]

    history = []          # [(topic, summary, findings)] - the loop's memory
    topic = question      # round 1 researches the question itself
    while True:
        round_no = len(history) + 1
        print(f"\n{'=' * 70}\n🔎 Round {round_no}: {topic}\n{'=' * 70}\nResearching ...", flush=True)
        findings, summary, directions = run_round(researcher, strategist, question, topic, history)
        history.append((topic, summary, findings))

        out_file = run_dir / f"round_{round_no}_{slugify(topic, 30)}.md"
        out_file.write_text(f"# Round {round_no}: {topic}\n\n{findings}\n", encoding="utf-8")
        print(f"\n📝 {summary}\n   Full findings: {out_file.name}")
        log.append(f"## Round {round_no}: {topic}\n- Summary: {summary}")

        if round_no >= args.max_rounds:
            print(f"\n⏹  Reached the limit of {args.max_rounds} rounds.")
            log.append(f"- Stopped: reached --max-rounds {args.max_rounds}")
            break
        if not directions:
            print("\n⚠️  The strategist did not propose a next direction.")
            log.append("- Stopped: no next direction proposed")
            break

        log.append("- Proposed next: " + "; ".join(t for t, _ in directions))
        chosen = choose_next_direction(directions)    # <-- the human decides
        if chosen is None:
            log.append("- Human decision: STOP")
            break
        log.append(f"- Human decision: continue with '{chosen}'")
        topic = chosen

    print(f"\n{'=' * 70}\n📄 Writing the final report from {len(history)} round(s) ...", flush=True)
    report = write_final_report(reporter, question, history)
    (run_dir / "final_report.md").write_text(report + "\n", encoding="utf-8")
    (run_dir / "research_log.md").write_text("\n".join(log) + "\n", encoding="utf-8")

    print(f"\n✅ Done. Output folder: {run_dir}")
    for f in sorted(run_dir.iterdir()):
        print(f"   {f.name}")


if __name__ == "__main__":
    main()
