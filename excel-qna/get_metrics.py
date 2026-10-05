"""
Get Metrics - Non AI approach
(c) Venkata Bhattaram

Reads the sales Excel file using a hardcoded schema and computes:
  * Number of Products
  * Total Sales in Rs. by Product      (Price x Sales)
  * Total Sales in Rs. across all Products

Usage:
    python get_metrics.py
"""
from pathlib import Path

import openpyxl

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "settings.config"
DEFAULT_EXCEL_FILE = Path(__file__).resolve().parent / "sales-data.xlsx"

# Hardcoded schema of the sales sheet
SHEET_NAME = "Sales Data"
COL_PRODUCT = "Product-Name"
COL_PRICE = "Price"
COL_SALES = "Sales"


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


def get_excel_path(config):
    excel = config.get("EXCEL_FILE")
    if not excel:
        return DEFAULT_EXCEL_FILE
    path = Path(excel)
    return path if path.is_absolute() else ROOT_DIR / path


def read_sales(excel_path):
    """Return list of dicts: {product, price, sales} using the fixed schema."""
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    ws = wb[SHEET_NAME]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() for h in next(rows)]
    idx_product = header.index(COL_PRODUCT)
    idx_price = header.index(COL_PRICE)
    idx_sales = header.index(COL_SALES)

    records = []
    for row in rows:
        if row[idx_product] is None:
            continue
        records.append({
            "product": str(row[idx_product]).strip(),
            "price": float(row[idx_price] or 0),
            "sales": float(row[idx_sales] or 0),
        })
    wb.close()
    return records


def get_metrics(records):
    sales_by_product = {}
    for r in records:
        sales_by_product[r["product"]] = sales_by_product.get(r["product"], 0) + r["price"] * r["sales"]
    return {
        "number_of_products": len(sales_by_product),
        "total_sales_by_product": sales_by_product,
        "total_sales_all_products": sum(sales_by_product.values()),
    }


def print_metrics(metrics):
    print(f"Number of Products : {metrics['number_of_products']}")
    print("Total Sales in Rs. by Product:")
    for product, total in metrics["total_sales_by_product"].items():
        print(f"    {product:<12} Rs. {total:>14,.2f}")
    print(f"Total Sales in Rs. across all Products : Rs. {metrics['total_sales_all_products']:,.2f}")


def main():
    excel_path = get_excel_path(load_config())
    print(f"Reading: {excel_path}\n")
    print_metrics(get_metrics(read_sales(excel_path)))


if __name__ == "__main__":
    main()
