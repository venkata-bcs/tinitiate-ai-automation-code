# Create a Simple Agent

## Agent 1 - Create Topic
## Agent 2.0 - Create Text Content  On that Topic
## Agent 2.1 - Create Image / Workflow Content On that Topic
## Agent 3 - Valiadate Content and Check for issues, spell checks, grammer and accuracy

* Create a CrewAI using kes from "C:\work\GIT-CODE\git-venkata-bcs\tinitiate-ai-automation-code\settings.config"

#  This is not an Agentic Loop, Run Once to kick off these agents inorder

---

## How it runs

```
Agent 1  Topic Creator ─────────► topic is printed in the terminal
            │
            ├──► Agent 2.0  Text Writer      ┐  run in PARALLEL
            └──► Agent 2.1  Visual Designer  ┘  (async_execution=True)
                          │
                          ▼
Agent 3  Content Validator ─────► spelling, grammar, accuracy, workflow check
                          │
                          ▼
               output/<date_time>_<topic>/
```

- `Process.sequential` runs the tasks in order: Topic, then 2.0 + 2.1, then Validator.
- Tasks 2.0 and 2.1 have `async_execution=True`, so they run **at the same time**. Both get the topic
  through `context=[topic_task]`.
- The Validator has `context=[text_task, visual_task]`, so it **waits for both** before it starts.
- Each agent runs once. There is no loop and nothing is sent back for fixing.

## Output

The topic is printed in the terminal, with the time each agent finished:

```
======================================================================
  How Generative AI is Transforming Medical Imaging Diagnosis
======================================================================
[  0.9s] Agent 1 done. Agents 2.0 and 2.1 now start in parallel ...
[  2.4s] Image and Workflow Designer done
[  2.9s] Text Content Writer done
[  8.2s] Content Validator done
```

Everything else goes to `output/<date_time>_<topic>/`:

| File | Created by |
|---|---|
| `1_topic.md` | Agent 1: topic and why it is interesting |
| `2.0_article.md` | Agent 2.0: the article (Markdown) |
| `2.1_image_and_workflow.md` | Agent 2.1: image prompt, caption and a Mermaid workflow diagram |
| `2.1_cover_image.jpg` | The image generated from Agent 2.1's prompt (FLUX on NVIDIA) |
| `3_validation_report.md` | Agent 3: spelling, grammar, accuracy and workflow issues, a score and a verdict |

> Tip: to see the Mermaid diagram in VS Code, install the *Markdown Preview Mermaid Support* extension
> and open the preview (Ctrl + Shift + V).

## Setup (once)

Needs **Python 3.13** (CrewAI does not support 3.14 yet).

```powershell
cd simple-agent
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Keys are read from `../settings.config`:

```
OPENROUTER_API_KEY=sk-or-... # required - the LLM for all 4 agents
NVDIA_API_KEY=nvapi-...     # optional - only for the cover image
```

## Run

```powershell
python simple_agent.py                                  # default subject
python simple_agent.py "Generative AI in healthcare"    # your own subject
python simple_agent.py "Cyber security" --no-image      # skip the cover image
```

A run takes about 10-30 seconds.