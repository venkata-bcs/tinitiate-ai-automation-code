"""
GenAI Image Builder
(c) Venkata Bhattaram

Reads an image prompt file (Image Type, Image Size, Image Description),
generates the image with FLUX.1-dev on NVIDIA NIM and saves it to ./output.

The API key is read from ../settings.config (NVDIA_API_KEY).

Usage:
    python image_builder.py
    python image_builder.py my_prompt.txt
    python image_builder.py my_prompt.txt --seed 42 --steps 30
"""
import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE.parent / "settings.config"
DEFAULT_PROMPT_FILE = HERE / "image_prompt.txt"
OUTPUT_DIR = HERE / "output"

API_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
API_KEY_NAME = "NVDIA_API_KEY"

# FLUX.1-dev on NVIDIA accepts 768..1344 in steps of 64
MIN_SIDE, MAX_SIDE, SIDE_STEP = 768, 1344, 64

PROMPT_FIELDS = {
    "image type": "type",
    "image size": "size",
    "image description": "description",
}


def load_config(path=CONFIG_FILE):
    """Parse KEY=VALUE lines from settings.config."""
    config = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip("'\"")
    return config


def read_prompt_file(path):
    """Parse 'Key: value' fields; lines without a known key continue the previous field."""
    fields, current = {}, None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() in PROMPT_FIELDS:
            current = PROMPT_FIELDS[key.strip().lower()]
            fields[current] = value.strip()
        elif current:
            fields[current] = f"{fields[current]} {line}".strip()

    missing = [k for k, v in PROMPT_FIELDS.items() if not fields.get(v)]
    if missing:
        sys.exit(f"Prompt file {path} is missing: {', '.join(missing)}")
    return fields


def parse_size(size_text):
    """'1024x768' -> (1024, 768), snapped to the sizes the model supports."""
    match = re.fullmatch(r"\s*(\d+)\s*[xX*]\s*(\d+)\s*", size_text)
    if not match:
        sys.exit(f"Invalid Image Size '{size_text}', expected WIDTHxHEIGHT e.g. 1024x768")

    def snap(n):
        return min(MAX_SIDE, max(MIN_SIDE, round(n / SIDE_STEP) * SIDE_STEP))

    requested = (int(match.group(1)), int(match.group(2)))
    width, height = snap(requested[0]), snap(requested[1])
    if (width, height) != requested:
        print(f"Note: size {requested[0]}x{requested[1]} adjusted to {width}x{height} "
              f"(supported {MIN_SIDE}-{MAX_SIDE}, multiples of {SIDE_STEP})")
    return width, height


def build_prompt(fields):
    return f"{fields['type']}. {fields['description']}"


def generate_image(api_key, prompt, width, height, steps, seed):
    payload = {"prompt": prompt, "width": width, "height": height, "steps": steps, "seed": seed}
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            body = json.load(response)
    except urllib.error.HTTPError as e:
        sys.exit(f"Image request failed ({e.code}): {e.read().decode('utf-8', 'replace')}")

    artifact = body["artifacts"][0]
    if artifact.get("finishReason") != "SUCCESS":
        sys.exit(f"Image generation did not succeed: {artifact.get('finishReason')}")
    return base64.b64decode(artifact["base64"])


def main():
    parser = argparse.ArgumentParser(description="Generate an image from a prompt file")
    parser.add_argument("prompt_file", nargs="?", default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--steps", type=int, default=30, help="diffusion steps (5-50)")
    parser.add_argument("--seed", type=int, default=0, help="0 = random")
    args = parser.parse_args()

    api_key = load_config().get(API_KEY_NAME)
    if not api_key:
        sys.exit(f"{API_KEY_NAME} not found in settings.config")

    fields = read_prompt_file(args.prompt_file)
    width, height = parse_size(fields["size"])
    prompt = build_prompt(fields)

    print(f"Prompt file : {args.prompt_file}")
    print(f"Image Type  : {fields['type']}")
    print(f"Image Size  : {width}x{height}")
    print(f"Prompt      : {prompt}\n")
    print("Generating image ...")

    image = generate_image(api_key, prompt, width, height, args.steps, args.seed)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_file = OUTPUT_DIR / f"{Path(args.prompt_file).stem}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    out_file.write_bytes(image)
    print(f"Saved       : {out_file}")


if __name__ == "__main__":
    main()
