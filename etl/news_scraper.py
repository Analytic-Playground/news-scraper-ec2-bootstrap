# scraper for news articles to aggregate banned items and highlights
import os
import sys
import time
from dotenv import load_dotenv
import boto3
import json
import socket # package for email retrieval timeout
socket.setdefaulttimeout(60)
import signal # package for python operation timeouts

# data manipulation
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--full-refresh', action='store_true', help='Pull full Gmail history instead of last 3 days')
args = parser.parse_args()

# email packages
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_DIR = os.path.join(BASE_DIR, "env")
TOKEN_PATH = os.path.join(ENV_DIR, "token.json")
creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
service = build("gmail", "v1", credentials=creds)

# web scraping
from urllib.parse import unquote, urlparse, parse_qs
from bs4 import BeautifulSoup
import requests

# graphs
# import plotly.express as px
import us

# organize later
import re
import base64
from urllib.parse import unquote, urlparse, parse_qs

# -----------------------
# Project setup
# -----------------------
print(f"[START] ETL script started at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
sys.stdout.flush()
# Import ban_config properly
sys.path.append(os.path.join(BASE_DIR))
from config.ban_config import state_patterns, keywords
from config.news_scraper_functions import extract_state, extract_datasource, clean_headline, COMPILED_PATTERNS, extract_target_generic, find_keyword_targets, choose_target, safe_get_plain
# imports for Gmail cutoff
from datetime import datetime, timedelta, timezone
# connect to email server and initial pull of messages and emails

def fetch_gmail_messages(full_refresh=False):
    all_messages = []
    page_token = None
    
    if full_refresh:
        query = 'subject:"Google Alert - ban"'
        print("Mode: FULL REFRESH - pulling complete Gmail history")
    else:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y/%m/%d")
        query = f'subject:"Google Alert - ban" after:{cutoff}'
        print(f"Mode: INCREMENTAL - pulling from {cutoff}")

    while True:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=500,
            pageToken=page_token
        ).execute()
        all_messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return all_messages

all_messages = fetch_gmail_messages(full_refresh=args.full_refresh)

print(f"Total messages found: {len(all_messages)}")

# unpack messages
# -----------------------
# Pre-compile patterns
# -----------------------
results_pattern = re.compile(
    r"(\d+\s+new results for \[Bans\])",
    re.IGNORECASE
)

split_pattern = re.compile(
    r"(.*?)(?:\r\n\r\n|$)",
    re.DOTALL
)

line_pattern = re.compile(
    r"(.*?)(?:\r\n|$)",
    re.DOTALL
)

# -----------------------
# Helper: fetch + decode Gmail message
# -----------------------
def get_plain_text_and_date(service, msg_id):
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    parts = payload.get("parts", [])

    # Extract Date header
    alert_date = None
    for h in headers:
        if h["name"].lower() == "date":
            alert_date = h["value"]
            break

    # Extract plain text body
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part["body"].get("data")
            if data:
                return (
                    alert_date,
                    base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="ignore"
                    )
                )

    return alert_date, None


# -----------------------
# Iterate through Gmail messages
# -----------------------
container = {
    "alert_date": [],
    "headlines": [],
    "article_links": [],
}

for m in all_messages:
    alert_date, plain_text = get_plain_text_and_date(service, m["id"])
    if not plain_text:
        continue

    # Optional debug: how many results Google reports
    match = results_pattern.search(plain_text)
    if match:
        print("Found:", match.group(1))

    # Split alert into blocks
    matches = [
        g.group(1).strip()
        for g in split_pattern.finditer(plain_text)
        if g.group(1).strip()
    ]

    # Guard against malformed alerts
    if len(matches) < 5:
        continue

    matches = matches[1:-3]

    for item in matches:
        sub_groups = [
            g.group(1).strip()
            for g in line_pattern.finditer(item)
            if g.group(1).strip()
        ]

        if not sub_groups:
            continue

        container["alert_date"].append(alert_date)
        container["headlines"].append(sub_groups[0])

        url_match = re.search(r"<(https.*?)>", sub_groups[-1])
        if url_match:
            google_url = unquote(url_match.group(1))
            parsed = urlparse(google_url)
            qs = parse_qs(parsed.query)
            container["article_links"].append(
                qs.get("url", [""])[0] or "no url found (1)."
            )
        else:
            container["article_links"].append("no url found (2).")

print('finished unpacking emails into dictionary.')
print('converting into df and organizing..')
# call cleaning and organizing functions
df = pd.DataFrame(data=container)
df["state"] = df["headlines"].apply(extract_state)
df["datasource"] = df["article_links"].apply(extract_datasource)
df["target"] = df["headlines"].apply(choose_target)
df = df[['alert_date', 'state', 'target', 'headlines', 'datasource', 'article_links']].sort_values(by=['state', 'target']).drop_duplicates(subset=['article_links']).reset_index(drop=True)
df['alert_date'] = pd.to_datetime(df['alert_date'], utc=True)


# --- S3 JSON export ---
print("Uploading JSON to S3...")
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
# S3 cleanup for full refreshes only
if args.full_refresh:
    print("Full refresh: clearing existing S3 data...")
    try:
        s3.delete_object(
            Bucket="krieger-technologies.com",
            Key="news_data/public_news_detail_table.json"
        )
        print("Existing S3 data cleared.")
    except Exception as e:
        print(f"Nothing to clear or error: {e}")

# -- MERGE WITH EXISTING S3 DATA --
print("downloading existing detail JSON from S3 for merge...")
try:
    existing_obj = s3.get_object(
            Bucket="krieger-technologies.com",
            Key="news_data/public_news_detail_table.json"
            )
    existing_records = json.loads(existing_obj["Body"].read().decode("utf-8"))
    df_existing = pd.DataFrame(existing_records)
    print(f"Existing records loaded: {len(df_existing)}")
except Exception as e:
    print(f"No existing data found or error loading - starting fresh: {e}")
    df_existing = pd.DataFrame()
# Convert DataFrame dates to ISO format
# 1 drop "National / Unknown"
df_filtered = df[df["state"] != "National / Unknown"]
# 2 drop headlines that are parsed wrong and begin with an https tag
df_filtered = df_filtered[~df_filtered["headlines"].str.startswith("<https", na=False)]
df_filtered["state_abbrev"] = df_filtered["state"].apply(lambda x: us.states.lookup(x).abbr if us.states.lookup(x) else None)
df_filtered['alert_date'] = df_filtered['alert_date'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# --- APPEND TO EXISTING DATA ---
if not df_existing.empty:
    df_filtered = pd.concat([df_existing, df_filtered], ignore_index=True)
    df_filtered = df_filtered.drop_duplicates(subset=["article_links"]).reset_index(drop=True)
    print(f"Merged record count after dedup: {len(df_filtered)}")
else:
    print("No existing data to merge - using new records only")
# --- DETAIL DATASET (row-level, authoritative) ---
df_filtered = df_filtered.where(pd.notnull(df_filtered), None)
detail_payload = (
    df_filtered[
        [
            "alert_date",
            "state",
            "state_abbrev",
            "target",
            "headlines",
            "datasource",
            "article_links",
        ]
    ]
    .sort_values(["alert_date", "state", "target"])
    .to_dict(orient="records")
)

resp_detail = s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/public_news_detail_table.json",
    Body=json.dumps(detail_payload, indent=2),
    ContentType="application/json",
)
print(
    "DETAIL PUT:",
    resp_detail.get("ResponseMetadata", {}).get("HTTPStatusCode"),
    "ETag:",
    resp_detail.get("ETag"),
)
# Build aggregated dataset for histogram
summary_df = (
    df_filtered.groupby("target")
    .agg(
        count_of_news_articles=("target", "count"),
        states=("state", lambda x: ", ".join(sorted(set(x))))
    )
    .reset_index()
    .sort_values("count_of_news_articles", ascending=False)
    .head(10)
)

json_payload = summary_df.to_dict(orient="records")

resp_bar = s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/public_news_data_bar_chart.json",
    Body=json.dumps(json_payload, indent=2),
    ContentType="application/json",
)
print(
    "BAR PUT:",
    resp_bar.get("ResponseMetadata", {}).get("HTTPStatusCode"),
    "ETag:",
    resp_bar.get("ETag"),
)
# export last time run timestamp
metadata = {
    "last_updated_utc": datetime.now(timezone.utc).isoformat(),
    "record_count": len(df),
    "source": "email_scraper_v4"
}

resp_meta = s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/last_run_timestamp.json",
    Body=json.dumps(metadata, indent=2),
    ContentType="application/json",
    CacheControl="no-cache, no-store, must-revalidate",
)
print(
    "META PUT:",
    resp_meta.get("ResponseMetadata", {}).get("HTTPStatusCode"),
    "ETag:",
    resp_meta.get("ETag"),
)
print("ETL reached end of script")
sys.exit(0)
print("public_news_data.json uploaded")
