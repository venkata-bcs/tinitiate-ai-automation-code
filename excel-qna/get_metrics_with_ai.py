"""
Get Metrics - AI approach
(c) Venkata Bhattaram

Reads the sales Excel file (no hardcoded schema), sends the sheet contents to
an LLM and asks it to answer:
  * Number of Products
  * Total Sales in Rs. by Product
  * Total Sales in Rs. across all Products

API keys are read from ../settings.config. Supported providers (OpenAI-compatible):
    groq        -> GROQ_API_KEY        (default)
    openrouter  -> OPENROUTER_API_KEY

Usage:
    python get_metrics_with_ai.py
    python get_metrics_with_ai.py --provider openrouter
    python get_metrics_with_ai.py --model qwen/qwen3.8-27b
"""
import argparse
import csv
import io
import json
import sys
import urllib.error
import urllib.request

import openpyxl

from get_metrics import get_excel_path, load_config

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": "GROQ_API_KEY",
        "model": "openai/gpt-oss-120b",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": "OPENROUTER_API_KEY",
        "model": "meta-llama/llama-3.3-70b-instruct",
    },
}

QUESTIONS = [
    "Number of Products",
    "Total Sales in Rs. by Product",
    "Total Sales in Rs. across all Products",
]

SYSTEM_PROMPT = (
    "You are a precise data analyst. You are given spreadsheet data as CSV. "
    "Sales in Rs. for a row = Price x Sales (Sales is the quantity sold). "
    "Compute carefully and reply with JSON only, no markdown, in this format: "
    '{"number_of_products": <int>, '
    '"total_sales_by_product": {"<product>": <number>, ...}, '
    '"total_sales_all_products": <number>}'
)


def excel_to_csv(excel_path):
    """Dump every sheet of the workbook as CSV text, without assuming a schema."""
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    out = io.StringIO()
    for ws in wb.worksheets:
        out.write(f"# Sheet: {ws.title}\n")
        writer = csv.writer(out, lineterminator="\n")
        for row in ws.iter_rows(values_only=True):
            if any(v is not None for v in row):
                writer.writerow(["" if v is None else v for v in row])
    wb.close()
    return out.getvalue()


def ask_llm(provider, api_key, model, data_csv):
    user_prompt = (
        "Spreadsheet data:\n" + data_csv + "\n\nAnswer these questions:\n"
        + "\n".join(f"- {q}" for q in QUESTIONS)
    )
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        PROVIDERS[provider]["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "tinitiate-excel-qna/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.load(response)
    except urllib.error.HTTPError as e:
        sys.exit(f"LLM request failed ({e.code}): {e.read().decode('utf-8', 'replace')}")
    return body["choices"][0]["message"]["content"]


def parse_json(text):
    """Extract the JSON object from the model reply (tolerates ```json fences)."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON in LLM reply:\n{text}")
    return json.loads(text[start:end + 1])


def main():
    parser = argparse.ArgumentParser(description="Get sales metrics from Excel using an LLM")
    parser.add_argument("--provider", choices=PROVIDERS, default="groq")
    parser.add_argument("--model", help="override the provider's default model")
    args = parser.parse_args()

    config = load_config()
    provider = PROVIDERS[args.provider]
    api_key = config.get(provider["key"])
    if not api_key:
        sys.exit(f"{provider['key']} not found in settings.config")
    model = args.model or provider["model"]

    excel_path = get_excel_path(config)
    print(f"Reading: {excel_path}")
    print(f"Asking : {args.provider} / {model}\n")

    reply = ask_llm(args.provider, api_key, model, excel_to_csv(excel_path))
    metrics = parse_json(reply)

    print(f"Number of Products : {metrics['number_of_products']}")
    print("Total Sales in Rs. by Product:")
    for product, total in metrics["total_sales_by_product"].items():
        print(f"    {product:<12} Rs. {float(total):>14,.2f}")
    print(f"Total Sales in Rs. across all Products : Rs. {float(metrics['total_sales_all_products']):,.2f}")


if __name__ == "__main__":
    main()
