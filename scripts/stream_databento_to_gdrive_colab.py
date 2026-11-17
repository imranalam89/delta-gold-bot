"""
Syndicate Alpha — Direct Databento MBP-10 to Google Drive Streamer (via Google Colab)
-------------------------------------------------------------------------------------
Run this script inside a FREE Google Colab notebook (https://colab.research.google.com).
It mounts your personal Google Drive (where your Gemini Pro / Google One 2TB storage lives)
and downloads Databento COMEX Gold (GC.v.0) MBP-10 data directly from Databento's servers
into your Google Drive folder — using 0 bytes of your PC disk and 0 home internet!

In Google Colab, first run:
    !pip install databento
"""

import os
from datetime import datetime, timedelta
import databento as db

# 1. Mount Google Drive inside Google Colab
try:
    from google.colab import drive
    drive.mount("/content/drive")
    GDRIVE_BASE_DIR = "/content/drive/MyDrive/Syndicate_Alpha_Gold_MBP10"
except ImportError:
    # Fallback if testing path locally via Google Drive for Desktop (Stream Mode)
    GDRIVE_BASE_DIR = "G:/My Drive/Syndicate_Alpha_Gold_MBP10"

os.makedirs(GDRIVE_BASE_DIR, exist_ok=True)

# 2. Configuration
DATABENTO_API_KEY = "YOUR_DATABENTO_API_KEY"  # Paste your Databento key here
DATASET = "GLBX.MDP3"                         # CME Globex
SYMBOL = "GC.v.0"                             # Continuous Front-Month Gold by Volume
STYPE_IN = "continuous"
SCHEMA = "mbp-10"                             # 10-Level L2 Order Book Depth

START_DATE = "2026-05-01"
END_DATE = "2026-11-01"


def generate_weekly_windows(start_str: str, end_str: str):
    curr = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    while curr < end:
        nxt = min(curr + timedelta(days=7), end)
        yield curr.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        curr = nxt


def download_directly_to_google_drive():
    client = db.Historical(key=DATABENTO_API_KEY)

    # Check exact cost against your $125 credit BEFORE downloading anything
    cost_usd = client.metadata.get_cost(
        dataset=DATASET,
        symbols=[SYMBOL],
        stype_in=STYPE_IN,
        schema=SCHEMA,
        start=START_DATE,
        end=END_DATE,
    )
    billable_bytes = client.metadata.get_billable_size(
        dataset=DATASET,
        symbols=[SYMBOL],
        stype_in=STYPE_IN,
        schema=SCHEMA,
        start=START_DATE,
        end=END_DATE,
    )
    print(f"==================================================")
    print(f"Total Uncompressed Size : {billable_bytes / (1024**3):.2f} GB")
    print(f"Estimated Credit Cost   : ${cost_usd:.2f} USD (out of $125)")
    print(f"Target Google Drive Dir : {GDRIVE_BASE_DIR}")
    print(f"==================================================")

    if cost_usd > 125.0:
        raise ValueError(f"ABORTED: Cost (${cost_usd:.2f}) exceeds $125 credit!")

    # Stream week-by-week directly into Google Drive
    for w_start, w_end in generate_weekly_windows(START_DATE, END_DATE):
        file_name = f"GC_v0_mbp10_{w_start}_to_{w_end}.dbn.zst"
        file_path = os.path.join(GDRIVE_BASE_DIR, file_name)

        if os.path.exists(file_path):
            print(f"[SKIP] Already in Google Drive: {file_name}")
            continue

        print(f"[DOWNLOADING TO GOOGLE DRIVE] {w_start} -> {w_end} ...")
        client.timeseries.get_range(
            dataset=DATASET,
            symbols=[SYMBOL],
            stype_in=STYPE_IN,
            schema=SCHEMA,
            start=w_start,
            end=w_end,
            path=file_path,  # Streams straight into your mounted Google Drive!
        )
        size_mb = os.path.getsize(file_path) / (1024 ** 2)
        print(f"[SAVED] {file_name} ({size_mb:.1f} MB compressed in Google Drive)")

    print("\nSUCCESS! All MBP-10 Gold data is now inside your Google Drive!")


if __name__ == "__main__":
    download_directly_to_google_drive()
