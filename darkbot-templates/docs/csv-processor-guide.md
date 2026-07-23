# CSV Processor: Transform and Aggregate Without Pandas

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Pandas is 50MB. For simple CSV transformations — filtering, renaming, grouping, deduplication — the stdlib `csv` module is enough. This template wraps it in a fluent API.

## Usage

```python
from darkbot_templates.templates.csv_processor import CSVProcessor

# Load
processor = CSVProcessor.from_file("orders.csv")

# Chain transformations
result = (
    processor
    .filter(lambda row: row["status"] == "completed")
    .rename({"customer_id": "cust_id", "order_total": "amount"})
    .add_column("amount_eur", lambda row: float(row["amount"]) * 0.92)
    .sort_by("amount", descending=True)
)

# Write
result.to_file("processed_orders.csv")

# Or export to JSON
result.to_json("processed_orders.json")
```

## Filtering

```python
# By predicate
high_value = processor.filter(lambda r: float(r["amount"]) > 1000)

# By column value
completed = processor.filter_by("status", "completed")

# Negate
cancelled = processor.filter_by("status", "cancelled", negate=True)
```

## Column Operations

```python
# Rename
processor.rename({"old_name": "new_name", "id": "order_id"})

# Select only specific columns
processor.select_columns(["order_id", "customer", "amount"])

# Drop columns
processor.drop_columns(["internal_id", "temp_field"])

# Add computed column
processor.add_column("tax", lambda r: float(r["amount"]) * 0.20)

# Type conversion
processor.convert_types({"amount": float, "quantity": int, "active": bool})
```

## Aggregation

```python
# Group by + sum
revenue = processor.group_by("customer", agg={"amount": "sum"})
# [{"customer": "Alice", "amount_sum": 4500.0}, {"customer": "Bob", "amount_sum": 2300.0}]

# Group by + count
order_counts = processor.group_by("status", agg={"order_id": "count"})
# [{"status": "completed", "order_id_count": 150}, {"status": "pending", "order_id_count": 30}]

# Group by + average
avg_order = processor.group_by("customer", agg={"amount": "avg"})
```

## Deduplication

```python
# Remove duplicate rows by key column
unique = processor.deduplicate(key_column="order_id")
```

## Streaming Large Files

```python
# Process row-by-row without loading entire file into memory
for row in CSVProcessor.stream("huge_file.csv"):
    process(row)
```

## Join Two CSVs

```python
orders = CSVProcessor.from_file("orders.csv")
customers = CSVProcessor.from_file("customers.csv")

joined = orders.join(customers, left_key="customer_id", right_key="id")
# Each order row now has customer columns merged in
```

## Export Formats

```python
processor.to_file("output.csv")           # CSV
processor.to_json("output.json")           # JSON array
processor.to_tsv("output.tsv")            # Tab-separated
processor.to_dict_list()                   # Python list of dicts
```

## Freelance Earnings Tracker

```python
earnings = CSVProcessor.from_file("earnings.csv")
# columns: date, platform, amount, currency, status

monthly = (
    earnings
    .filter_by("status", "paid")
    .add_column("amount_usd", lambda r: convert(r["amount"], r["currency"]))
    .group_by("platform", agg={"amount_usd": "sum"})
    .sort_by("amount_usd_sum", descending=True)
)

monthly.to_file("earnings_by_platform.csv")
```

## Testing

```bash
pytest tests/test_log_csv.py -k csv -v
```

## References

- [Python csv module](https://docs.python.org/3/library/csv.html)
- [Pandas Alternative](https://saturncloud.io/blog/should-you-use-pandas-or-csv-module/) — when stdlib is enough

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
