# CrewAI Website Builder Agent
> (c) Venkata Bhattaram

You describe a website in plain English in [`to-do.md`](to-do.md). A team ("crew") of AI agents then
builds that website for you with **Streamlit**, a Python library for making web pages. The site includes
a **Contact Us** form that saves every message to a CSV file you can open in Excel.

The crew has four AI agents:

| Agent | What it does |
|---|---|
| **Requirements Analyst** | Reads `to-do.md` and turns it into a precise list of pages, header, footer and form fields |
| **Theme Decision Maker** | Scores 7 ready-made colour themes against your *Theme Inputs* and picks the best one |
| **Developer** | Writes the Python/Streamlit code for the header, footer and every page |
| **Testing Agent** | Checks the test results against `to-do.md`; anything missing or broken is sent back to the Developer to fix |

No web development experience is needed. You only edit `to-do.md` and run two commands.

---

## What you need

- A Windows 10/11 computer (Mac and Linux commands are also shown)
- An internet connection
- **Python 3.13**. CrewAI does not work with Python 3.14 yet, so install 3.13 even if you already
  have 3.14. Both can be installed side by side.
- A free **Groq API key**, which lets the agents use an AI model, and optionally a free **Google Gemini API key** as a backup (step 5 shows how to get them)
- Optional but recommended: [Visual Studio Code](https://code.visualstudio.com/) to edit files

---

## Setup (do this once)

### Step 1 - Install Python 3.13

1. Go to <https://www.python.org/downloads/> and download the latest **Python 3.13.x** Windows installer (64-bit).
2. Run it. On the first screen, **tick "Add python.exe to PATH"**, then click **Install Now**.
3. Open a new terminal (press `Win`, type `PowerShell`, press Enter) and check that it worked:

   ```powershell
   py -3.13 --version
   ```

   You should see `Python 3.13.x`.

> On Mac, install Python 3.13 from python.org too, then use `python3.13` wherever this guide says `py -3.13`.

### Step 2 - Open a terminal in this folder

In VS Code:

1. Choose **File > Open Folder...** and open the `tinitiate-ai-automation-code` folder.
2. Choose **Terminal > New Terminal**.
3. Go into this project's folder:

   ```powershell
   cd crewai-website-builder-agent
   ```

### Step 3 - Create a virtual environment

A *virtual environment* is a private folder (`.venv`) where this project's Python packages are installed.
It keeps them separate from the rest of your computer.

```powershell
py -3.13 -m venv .venv
```

Now **activate** it. You must do this every time you open a new terminal for this project:

```powershell
.venv\Scripts\Activate.ps1          # PowerShell (the VS Code default)
.venv\Scripts\activate.bat          # Command Prompt (cmd)
source .venv/bin/activate           # Mac / Linux
```

When it is active, your prompt starts with **`(.venv)`**. Check that it is using the right Python:

```powershell
python --version                    # must say Python 3.13.x
```

### Step 4 - Install the packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs **CrewAI** (the agent framework) and **Streamlit** (the website framework). It can take
a few minutes.

### Step 5 - Add your API keys

The agents use **Groq** first. If Groq is busy (rate limited) or fails, they automatically switch to
**Google Gemini** for that step. Only the Groq key is required; the Google key is an optional backup
that makes builds faster.

1. **Groq key (required):** create a free account at <https://console.groq.com>, open
   <https://console.groq.com/keys>, click **Create API Key** and copy it (it starts with `gsk_`).
2. **Google key (optional backup):** open <https://aistudio.google.com/apikey> with your Google
   account, click **Create API key** and copy it (it starts with `AIza`).
3. Create a file called **`settings.config`**, either in this folder or in the repository root
   (`tinitiate-ai-automation-code/settings.config`, which the other projects in this repo also use).
   Put your keys in it, one per line:

   ```
   GROQ_API_KEY=gsk_your_key_here
   GOOGLE_API_KEY=AIza_your_key_here
   ```

When you build (step 7), the first lines tell you which providers will be used:

```
Main LLM    : groq (groq/openai/gpt-oss-120b)
Fallback LLM: google (gemini/gemini-2.5-flash)
```

If it says `Fallback LLM: google NOT available - ...`, the Google key does not work yet (see
Troubleshooting). The build still runs using Groq only.

> Keep your keys secret. `settings.config` is listed in `.gitignore` so it is never committed to Git.

Setup is done.

---

## Build and run the website

### Step 6 - Describe your website in `to-do.md`

Open [`to-do.md`](to-do.md). It already contains an example website (a training institute). Change
anything you like; the headings tell the agents what each part is:

| Section | What to write |
|---|---|
| **Site** | Website name and a one-line description |
| **Pages** | Each page and what it should contain (be specific: names, counts, prices) |
| **Header** / **Footer** | Logo text, links, button, address, social networks |
| **Contact Us** | The form fields, and which ones are required |
| **Theme Inputs** | Audience, industry, mood and colours you like or dislike; used to pick the theme |

### Step 7 - Let the agents build it

Make sure the virtual environment is active (`(.venv)` in the prompt), then run:

```powershell
python build_website.py
```

You will see the four steps run one after another:

```
1/4  Requirements Analyst: reading to-do.md
2/4  Theme Decision Maker: choosing a theme
3/4  Developer: writing pages (round 1)
4/4  Testing Agent: testing round 1
...
Website build PASSED after 1 round(s)
```

- A build usually takes **5-10 minutes**. The free Groq plan limits how fast requests can be sent,
  so messages like `rate limited by the LLM provider, retrying in 20s` are normal. Just wait.
- If the Testing Agent finds a problem, you will see `Developer: fixing pages (round 2)`. The crew
  fixes it by itself (up to 2 extra rounds).
- Add `--quiet` to hide the agents' detailed thinking: `python build_website.py --quiet`

The finished website is in the **`website`** folder. A summary is in **`reports/BUILD_REPORT.md`**,
including which theme was chosen and why.

### Step 8 - Run the website

```powershell
cd website
streamlit run app.py
```

Your browser opens the website at <http://localhost:8501>. Click through the pages and try the
**Contact Us** form. To stop the website, click the terminal and press **Ctrl + C**. Then run
`cd ..` to go back to the project folder.

### Step 9 - See the contact form submissions

Every message sent through the Contact Us form is added as a row to:

```
website/data/contacts.csv
```

Open it with Excel or VS Code. The file is created when the first message is sent.

---

## Coming back later

Each time you open a new terminal:

```powershell
cd crewai-website-builder-agent
.venv\Scripts\Activate.ps1
```

Then run `python build_website.py` to rebuild after editing `to-do.md`, or
`cd website` and `streamlit run app.py` to run the site.

---

## How it works

```
to-do.md
   |
   v
1. Requirements Analyst --> structured spec (pages, header, footer, form fields, theme inputs)
   |
   v
2. Theme Decision Maker --> scores every theme in themes.py, picks the best fit
   |
   v
   Scaffold (no AI) ------> app.py, page navigation, theme, contact form storage, tests
   |
   v
3. Developer -------------> components/layout.py (header + footer) and one file per page
   |          ^
   v          | fix  (only the files with problems, up to 2 times)
4. Testing Agent ---------> runs the automated tests, then checks every item of to-do.md
   |
   v passed
   website/  +  reports/BUILD_REPORT.md
```

- The steps are connected with a **CrewAI Flow** (`@start`, `@listen`, `@router` in `build_website.py`).
  The router sends the work back to the Developer when the Testing Agent finds a problem.
- The parts that must always work, such as page navigation and saving the contact form to CSV, are
  written by normal Python code (`scaffold.py`), not by the AI.
- The automated tests (`tools.py`) use Streamlit's built-in `AppTest` to run the website without a
  browser. They check that every page loads without errors, that the header links to every page, and
  that submitting the contact form really adds a row to the CSV. The Testing Agent can never mark the
  website as passed if one of these tests fails.

### Project files

| File / folder | What it is |
|---|---|
| `to-do.md` | **Your input**: the website description |
| `build_website.py` | The agents, their tasks and the flow; run this to build the site |
| `models.py` | The data each agent must return (checked automatically) |
| `themes.py` | The 7 colour themes the Theme Decision Maker chooses from |
| `scaffold.py` | Writes the fixed parts of the website (app, theme, CSV storage, tests) |
| `tools.py` | The automated tests the Testing Agent reviews |
| `website/` | **The generated website** |
| `website/app.py` | Website entry point (`streamlit run app.py`) |
| `website/pages/` | One Python file per page, written by the Developer agent |
| `website/components/layout.py` | Header and footer, written by the Developer agent |
| `website/data/contacts.csv` | Contact form submissions |
| `website/tests/check_site.py` | Site tests; run `python tests/check_site.py render` inside `website` |
| `reports/` | What each agent decided: spec, theme scores, test reports, `BUILD_REPORT.md` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'py' is not recognized` or `'python' is not recognized` | Python is not installed or not on PATH. Re-run the installer, choose **Modify**, and tick **Add Python to environment variables**. Then open a new terminal. |
| `running scripts is disabled on this system` when activating | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once in PowerShell, or use Command Prompt and `.venv\Scripts\activate.bat`. |
| `An Application Control policy has blocked this file` | Windows Smart App Control is blocking an unsigned `python.exe` (this happens with virtual environments made by tools like `uv`). Delete the `.venv` folder and create it again with `py -3.13 -m venv .venv` as in step 3. |
| `ModuleNotFoundError: No module named 'crewai'` | The virtual environment is not active. Activate it (step 3) and check for `(.venv)` in the prompt. |
| `pip install` fails for crewai | You are probably on Python 3.14. Inside the activated environment, `python --version` must show 3.13. If not, delete `.venv` and redo step 3 with `py -3.13`. |
| `Cannot use groq: GROQ_API_KEY is not in settings.config` | Create `settings.config` as in step 5 and check the spelling of `GROQ_API_KEY`. |
| `Invalid API Key` | The key was copied incorrectly or deleted. Create a new one at <https://console.groq.com/keys>. |
| `Fallback LLM: google NOT available - the key is not allowed to use the Gemini API` | The Google key belongs to a Google Cloud project where the Gemini API is off, or the key is restricted. The easiest fix is to create a new key at <https://aistudio.google.com/apikey>. Alternatively, in Google Cloud Console enable the **Generative Language API** for the project and allow it under the key's **API restrictions**. |
| `groq: rate limit -> switching to google for this step` | Normal: Groq's free plan is busy, so this step uses Google instead. |
| `all providers rate limited, retrying ...` | Normal on free plans. The builder waits and continues on its own. |
| `Website build FAILED` | Open `reports/BUILD_REPORT.md` to see what is still wrong, then run `python build_website.py` again. AI output varies from run to run. Being more specific in `to-do.md` also helps. |
| `Port 8501 is already in use` | Another website is still running. Stop it with Ctrl + C, or run `streamlit run app.py --server.port 8502`. |

### Choosing the AI providers

```powershell
python build_website.py                              # Groq first, Google as backup (default)
python build_website.py --fallback none              # Groq only
python build_website.py --llm google --fallback groq # Google first, Groq as backup
python build_website.py --llm nvidia                 # NVIDIA first (NVDIA_API_KEY from build.nvidia.com)
```
