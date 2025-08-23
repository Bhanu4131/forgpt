import pandas as pd

def convert_temp_to_candles(temp_file, output_file, symbol="NIFTY"):
    # Load broker's temp.csv
    df = pd.read_csv(temp_file)

    # Detect and parse datetime (adjust column names if needed)
    # Example: if your temp.csv has 'Date' and 'Time' columns separately:
    if "Date" in df.columns and "Time" in df.columns:
        df["start_time"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    elif "Date" in df.columns:
        df["start_time"] = pd.to_datetime(df["Date"])
    else:
        raise ValueError("CSV does not have Date/Time columns I can parse.")

    # Keep only required columns and rename them
    # Adjust based on actual temp.csv headers
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close"
    })

    # Select only needed columns
    df = df[["start_time", "open", "high", "low", "close"]]

    # Convert start_time to string in ISO format
    df["start_time"] = df["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Save to candles_NIFTY.csv
    output_path = f"candles_{symbol}.csv"
    df.to_csv(output_path, index=False)

    print(f"✅ Converted {len(df)} candles to {output_path}")

# Example usage:
convert_temp_to_candles("temp.csv", "candles_NIFTY.csv", symbol="NIFTY")
