"""
Syndicate Alpha — Direct Databento MBP-10 to Google Cloud Storage (GCS) Streamer
--------------------------------------------------------------------------------
Streams CME COMEX Gold Futures (GC.v.0 - Volume-based continuous front month)
MBP-10 (10-level Level 2 order book depth) directly into a Google Cloud Storage
bucket (`gs://...`) in compressed `.dbn.zst` chunks without storing files on
your local PC hard drive.

Run this in Google Cloud Shell (shell.cloud.google.com) or Google Colab so the
traffic flows 100% cloud-to-cloud at datacenter speeds.
"""

import os
from datetime import datetime, timedelta
import databento as db
from google.cloud import storage

# =====================================================================
# 1. CONFIGURATION
# =====================================================================
DATABENTO_API_KEY = os.environ.get("DATABENTO_API_KEY", "YOUR_DATABENTO_API_KEY")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "syndicate-alpha-gold-mbp10")
GCS_FOLDER_PREFIX = "comex_gc_mbp10"

# CME Globex dataset & Continuous Front-Month Gold Symbol (saves 90% cost vs all expirations)
DATASET = "GLBX.MDP3"
SYMBOL = "GC.v.0"        # Continuous contract rolled by highest daily volume
STYPE_IN = "continuous"
SCHEMA = "mbp-10"        # 10 levels of Level 2 Market-By-Price book depth

# Date range (Example: 6 months of high-precision L2 data)
START_DATE = "2026-05-01"
END_DATE = "2026-11-01"


def check_cost_first(client: db.Historical) -> float:
    """Checks the exact GB size and US Dollar cost before downloading a single byte."""
    print(f"Checking billable size and cost for {SYMBOL} ({SCHEMA}) from {START_DATE} to {END_DATE}...")
    
    billable_bytes = client.metadata.get_billable_size(
        dataset=DATASET,
        symbols=[SYMBOL],
        stype_in=STYPE_IN,
        schema=SCHEMA,
        start=START_DATE,
        end=END_DATE,
    )
    cost_usd = client.metadata.get_cost(
        dataset=DATASET,
        symbols=[SYMBOL],
        stype_in=STYPE_IN,
        schema=SCHEMA,
        start=START_DATE,
        end=END_DATE,
    )
    billable_gb = billable_bytes / (1024 ** 3)
    print(f"--------------------------------------------------")
    print(f"Estimated Uncompressed Billable Size : {billable_gb:.2f} GB")
    print(f"Estimated Databento Credit Cost      : ${cost_usd:.2f} USD (out of your $125 credit)")
    print(f"--------------------------------------------------")
    return cost_usd


def generate_weekly_windows(start_str: str, end_str: str):
    """Splits the date range into 7-day chunks so streams stay small in RAM."""
    curr = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    while curr < end:
        nxt = min(curr + timedelta(days=7), end)
        yield curr.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        curr = nxt


def stream_databento_to_gcs():
    db_client = db.Historical(key=DATABENTO_API_KEY)
    
    # Step 1: Always verify cost against your $125 credit before streaming
    cost = check_cost_first(db_client)
    if cost > 125.0:
        raise ValueError(f"STOP! Estimated cost (${cost:.2f}) exceeds $125 free credit. Shorten date range.")

    # Step 2: Connect to Google Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    # Step 3: Stream week-by-week directly into GCS bucket
    for chunk_start, chunk_end in generate_weekly_windows(START_DATE, END_DATE):
        blob_name = f"{GCS_FOLDER_PREFIX}/GC_v0_mbp10_{chunk_start}_to_{chunk_end}.dbn.zst"
        blob = bucket.blob(blob_name)

        if blob.exists():
            print(f"[SKIP] {blob_name} already exists in gs://{GCS_BUCKET_NAME}/")
            continue

        print(f"[STREAMING] {chunk_start} -> {chunk_end} directly to gs://{GCS_BUCKET_NAME}/{blob_name} ...")

        # Request compressed DBN stream from Databento and pipe straight to GCS write stream
        data_store = db_client.timeseries.get_range(
            dataset=DATASET,
            symbols=[SYMBOL],
            stype_in=STYPE_IN,
            schema=SCHEMA,
            start=chunk_start,
            end=chunk_end,
        )

        # Open a direct cloud write stream (never touches local disk)
        with blob.open("wb", content_type="application/zstd") as gcs_stream:
            data_store.to_file(gcs_stream)

        print(f"[DONE] Saved gs://{GCS_BUCKET_NAME}/{blob_name}")

    print("\nAll MBP-10 Gold chunks successfully streamed to Google Cloud Storage!")


if __name__ == "__main__":
    stream_databento_to_gcs()
