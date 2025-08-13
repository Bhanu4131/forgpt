# converter_add_ist_offset.py
import csv
import pandas as pd
from pathlib import Path
from datetime import timedelta
from dateutil import parser

INPUT_FILE = Path("temp.csv")
OUTPUT_FILE = Path("candles_NIFTY.csv")

# Time offset for IST
IST_OFFSET = timedelta(hours=5, minutes=30)

def convert_file():
    df = pd.read_csv(INPUT_FILE, sep=None, engine="python")

    results = []
    skipped = 0

    for i, row in df.iterrows():
        try:
            # Try multiple possible datetime column names
            raw_date = row.get("Date") or row.get("start_time") or row[0]

            # Parse and shift by IST offset
            dt_utc = parser.parse(str(raw_date))
            dt_ist = dt_utc + IST_OFFSET

            # Format datetime as ISO without timezone
            start_time = dt_ist.strftime("%Y-%m-%dT%H:%M:%S")

            o = float(row["Open"])
            h = float(row["High"])
            l = float(row["Low"])
            c = float(row["Close"])

            results.append({
                "start_time": start_time,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            })

        except Exception as e:
            skipped += 1
            continue

    # Write output
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["start_time", "open", "high", "low", "close"])
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Wrote {len(results)} rows. Skipped {skipped} bad rows.")

if __name__ == "__main__":
    convert_file()
