# Image Builder - Code Explainer

> (c) Venkata Bhattaram

## 1. Objective

Generate an image with **Generative AI** from a plain-text prompt file. There is no coding needed to
change the image; you only edit the prompt file.

You describe the image in `image_prompt.txt` (**type**, **size** and **description**). The script
`image_builder.py` reads it, sends it to the **FLUX.1-dev** image model hosted on **NVIDIA NIM**, and
saves the returned picture as a `.jpg` in the `output/` folder.

```mermaid
flowchart LR
    A["✍️ You describe the image<br/>image_prompt.txt"] --> B["⚙️ image_builder.py<br/>reads, validates, builds the prompt"]
    B --> C["🧠 FLUX.1-dev model<br/>on NVIDIA NIM (cloud)"]
    C --> D["🖼️ Picture saved<br/>output/image_prompt_DATE_TIME.jpg"]
```

---

## 2. Files involved

| File / folder | Type | What it does |
|---|---|---|
| `image-builder/image_prompt.txt` | **Input** (you edit it) | Describes the image: `Image Type`, `Image Size`, `Image Description` |
| `settings.config` (repository root) | **Input** (secret) | Holds the API key line `NVDIA_API_KEY=nvapi-...` |
| `image-builder/image_builder.py` | **Code** | The whole program: reads the inputs, calls the AI model, saves the image |
| NVIDIA NIM - FLUX.1-dev | **External service** | The AI model that turns the text prompt into a picture |
| `image-builder/output/` | **Output** | Every generated image, named `<prompt file name>_<YYYYMMDD_HHMMSS>.jpg` |

### Architecture

```mermaid
flowchart TB
    subgraph REPO["📁 tinitiate-ai-automation-code"]
        CFG[("settings.config<br/>NVDIA_API_KEY")]
        subgraph IB["📁 image-builder"]
            PROMPT[/"image_prompt.txt<br/>Image Type / Size / Description"/]
            CODE["image_builder.py"]
            OUT[("output/<br/>*.jpg images")]
        end
    end
    subgraph CLOUD["☁️ NVIDIA NIM cloud"]
        API["FLUX.1-dev image model<br/>ai.api.nvidia.com"]
    end

    CFG -- "API key" --> CODE
    PROMPT -- "prompt fields" --> CODE
    CODE -- "HTTPS POST: prompt, width, height, steps, seed" --> API
    API -- "JSON: base64-encoded JPEG" --> CODE
    CODE -- "writes .jpg" --> OUT
```

---

## 3. Data flow diagram

The diagram follows the classic data flow notation:
- **Rectangles** are external entities.
- **Rounded boxes** are processes (functions in `image_builder.py`).
- **Cylinders** are data stores.
- **Arrow labels** are the data that moves.

```mermaid
flowchart LR
    USER["👤 User"]
    NVIDIA["☁️ NVIDIA NIM<br/>FLUX.1-dev"]

    D1[("settings.config")]
    D2[("image_prompt.txt")]
    D3[("output/ folder")]

    P1(["1. load_config()"])
    P2(["2. read_prompt_file()"])
    P3(["3. parse_size()"])
    P4(["4. build_prompt()"])
    P5(["5. generate_image()"])
    P6(["6. save image<br/>in main()"])

    USER -- "runs command<br/>+ optional --steps / --seed" --> P2
    USER -- "edits" --> D2
    D1 -- "KEY=VALUE lines" --> P1
    D2 -- "Key: value lines" --> P2
    P2 -- "size text '1344x768'" --> P3
    P2 -- "type + description" --> P4
    P1 -- "API key" --> P5
    P3 -- "width, height<br/>(snapped to 768-1344)" --> P5
    P4 -- "prompt text" --> P5
    P5 -- "JSON request" --> NVIDIA
    NVIDIA -- "JSON with base64 image" --> P5
    P5 -- "image bytes" --> P6
    P6 -- "image_prompt_DATE_TIME.jpg" --> D3
    P6 -- "prints file path" --> USER
```

---

## 4. The code, function by function

`image_builder.py` has one job per function. `main()` calls them in order.

| # | Function | Input | Output | What it does |
|---|---|---|---|---|
| 1 | `load_config()` | `settings.config` | dictionary of keys | Reads every `KEY=VALUE` line, skips `#` comments, removes surrounding quotes from values |
| 2 | `read_prompt_file()` | `image_prompt.txt` | `{type, size, description}` | Reads `Key: value` lines. A line without a known key **continues** the previous field, so the description can span several lines. Stops with an error if a field is missing |
| 3 | `parse_size()` | `"1344x768"` | `(1344, 768)` | Checks the `WIDTHxHEIGHT` format and **snaps** each side to what FLUX accepts: 768 to 1344, in multiples of 64. Prints a note if it had to adjust |
| 4 | `build_prompt()` | type + description | one prompt string | Joins them: `"Anime Image. People in a fair"` |
| 5 | `generate_image()` | key, prompt, size, steps, seed | image bytes | Sends an HTTPS POST to NVIDIA, checks `finishReason == SUCCESS`, and decodes the base64 JPEG |
| 6 | `main()` | command-line arguments | `.jpg` file | Runs steps 1-5, prints progress, creates `output/` and saves the file with a timestamp |

### Important constants (top of the file)

| Constant | Value | Meaning |
|---|---|---|
| `CONFIG_FILE` | `../settings.config` | Where the API key is read from |
| `DEFAULT_PROMPT_FILE` | `image_prompt.txt` | Used when no prompt file is given on the command line |
| `OUTPUT_DIR` | `output/` | Where images are saved |
| `API_URL` | `https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev` | The FLUX.1-dev endpoint |
| `MIN_SIDE, MAX_SIDE, SIDE_STEP` | `768, 1344, 64` | Allowed image sizes |

### How the prompt file is read

Example `image_prompt.txt`:

```text
# comment lines are ignored
Image Type: Anime Image
Image Size: 1344x768
Image Description:
    People in a fair
```

```mermaid
flowchart TD
    S(["Read next line"]) --> E{"Empty or<br/>starts with # ?"}
    E -- "yes" --> S
    E -- "no" --> K{"Starts with a known key?<br/>Image Type / Image Size /<br/>Image Description"}
    K -- "yes" --> N["Start that field<br/>with the text after ':'"]
    K -- "no" --> C{"Inside a field?"}
    C -- "yes" --> A["Append the line to the<br/>current field (multi-line text)"]
    C -- "no" --> S
    N --> S
    A --> S
    S -- "end of file" --> M{"All 3 fields<br/>filled?"}
    M -- "yes" --> R(["Return type, size, description"])
    M -- "no" --> X(["❌ Exit: 'Prompt file is missing ...'"])
```

### How the size is snapped

`round(n / 64) * 64`, then clamped between 768 and 1344:

| You write | Width x Height used | Why |
|---|---|---|
| `1344x768` | 1344 x 768 | Already valid |
| `1920x1080` | 1344 x 1088 | 1920 is above the maximum of 1344; 1080 rounds to 1088 |
| `500x500` | 768 x 768 | Below the minimum of 768 |

---

## 5. How to run

The script uses **only the Python standard library**, so there is nothing to install. Any Python 3.10
or newer works.

1. Put your NVIDIA key in `settings.config` at the repository root. Get one from
   <https://build.nvidia.com>.

   ```text
   NVDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
   ```

2. Describe your image in `image-builder/image_prompt.txt`.
3. Run:

   ```powershell
   cd image-builder
   python image_builder.py                                # uses image_prompt.txt
   python image_builder.py my_prompt.txt                  # use another prompt file
   python image_builder.py --seed 42 --steps 30           # repeatable result, more detail
   ```

| Option | Default | Meaning |
|---|---|---|
| `prompt_file` | `image_prompt.txt` | Which prompt file to read |
| `--steps` | `30` | Diffusion steps (5-50). More steps give more detail but are slower |
| `--seed` | `0` | `0` gives a random image each time; any other number gives the same image again for the same prompt |

Example terminal output:

```text
Prompt file : C:\...\image-builder\image_prompt.txt
Image Type  : Anime Image
Image Size  : 1344x768
Prompt      : Anime Image. People in a fair

Generating image ...
Saved       : C:\...\image-builder\output\image_prompt_20260930_052546.jpg
```

---

## 6. Code execution flow

What happens, step by step, when you run `python image_builder.py`:

```mermaid
flowchart TD
    START(["▶ python image_builder.py"]) --> ARGS["main(): read command-line options<br/>prompt_file, --steps, --seed"]
    ARGS --> CFG["load_config()<br/>read settings.config"]
    CFG --> KEY{"NVDIA_API_KEY<br/>found?"}
    KEY -- "no" --> E1(["❌ Exit: key not found"])
    KEY -- "yes" --> READ["read_prompt_file()<br/>get type, size, description"]
    READ --> FIELDS{"All 3 fields<br/>present?"}
    FIELDS -- "no" --> E2(["❌ Exit: prompt file is missing ..."])
    FIELDS -- "yes" --> SIZE["parse_size()<br/>'1344x768' to 1344, 768"]
    SIZE --> VALID{"WIDTHxHEIGHT<br/>format OK?"}
    VALID -- "no" --> E3(["❌ Exit: invalid Image Size"])
    VALID -- "yes" --> SNAP["snap to 768-1344,<br/>multiples of 64"]
    SNAP --> BUILD["build_prompt()<br/>'type. description'"]
    BUILD --> PRINT["print prompt details"]
    PRINT --> CALL["generate_image()<br/>HTTPS POST to NVIDIA FLUX.1-dev"]
    CALL --> HTTP{"HTTP 200?"}
    HTTP -- "no" --> E4(["❌ Exit: image request failed + error"])
    HTTP -- "yes" --> OK{"finishReason<br/>= SUCCESS?"}
    OK -- "no" --> E5(["❌ Exit: generation did not succeed<br/>e.g. content filtered"])
    OK -- "yes" --> DECODE["base64-decode the image"]
    DECODE --> SAVE["create output/ if needed<br/>save image_prompt_DATE_TIME.jpg"]
    SAVE --> DONE(["✅ print 'Saved : path'"])
```

### The same flow as a sequence of messages

```mermaid
sequenceDiagram
    actor User
    participant Script as image_builder.py
    participant Config as settings.config
    participant Prompt as image_prompt.txt
    participant NVIDIA as NVIDIA NIM FLUX.1-dev
    participant Output as output/ folder

    User->>Script: python image_builder.py [--seed] [--steps]
    Script->>Config: load_config()
    Config-->>Script: NVDIA_API_KEY
    Script->>Prompt: read_prompt_file()
    Prompt-->>Script: type, size, description
    Script->>Script: parse_size() + build_prompt()
    Script->>NVIDIA: POST prompt, width, height, steps, seed
    Note over NVIDIA: the model generates the image<br/>(about 5-30 seconds)
    NVIDIA-->>Script: JSON artifacts - base64 image + finishReason SUCCESS
    Script->>Script: base64 decode
    Script->>Output: write image_prompt_YYYYMMDD_HHMMSS.jpg
    Script-->>User: Saved : output/...jpg
```

---

## 7. Errors you may see

| Message | Cause | Fix |
|---|---|---|
| `NVDIA_API_KEY not found in settings.config` | Key missing or misspelled | Add `NVDIA_API_KEY=...` to the repository-root `settings.config` (note the spelling `NVDIA`) |
| `Prompt file ... is missing: image size` | A field is empty or misspelled in the prompt file | Check the three `Key:` names |
| `Invalid Image Size '...'` | Size not written as `WIDTHxHEIGHT` | Use a format like `1024x768` |
| `Image request failed (401)` / `(403)` | Invalid or expired key, or no access to the model | Create a new key at <https://build.nvidia.com> |
| `Image generation did not succeed: CONTENT_FILTERED` | The prompt was blocked by the safety filter | Change the description |
| `Note: size ... adjusted to ...` | Not an error: the size was snapped to a supported value | Nothing to do |

> **Viewing the diagrams:** GitHub shows them automatically. In VS Code, install the
> *Markdown Preview Mermaid Support* extension, then open the preview with **Ctrl + Shift + V**.
