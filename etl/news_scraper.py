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

# connection for RDS db
import psycopg2
from psycopg2.extras import execute_values

# data manipulation
import pandas as pd
import re
from datetime import datetime, timedelta, timezone

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
import plotly.express as px
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

# connect to email server and initial pull of messages
# initialize connection to server
all_messages = []
page_token = None

while True:
    response = service.users().messages().list(
        userId="me",
        q='subject:"Google Alert - ban"',
        maxResults=500,
        pageToken=page_token
    ).execute()

    all_messages.extend(response.get("messages", []))
    page_token = response.get("nextPageToken")

    if not page_token:
        break

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

# set up connection to db
# print('connecting to db and updating...')
# user = os.getenv("DB_USER")
# password = os.getenv("DB_PASS")
# host = os.getenv("DB_HOST")
# database = os.getenv("DB_NAME")
# port = int(os.getenv("DB_PORT"))
# conn = psycopg2.connect(
#    host=host,
#    database=database,
#    user=user,
#    password=password,
#    port=port
#)

# conn.autocommit = True
# cur = conn.cursor()

# Prepare the insert statement
# insert_query = """
# INSERT INTO etl_news (alert_date, state, target, headlines, datasource, article_links)
# VALUES %s
# ON CONFLICT (article_links) DO NOTHING;  -- avoid duplicates
# """

# Convert DataFrame to list of tuples
# data_tuples = list(df.itertuples(index=False, name=None))

# Execute bulk insert
# execute_values(cur, insert_query, data_tuples)

# cur.close()
# conn.close()

# print(f"{len(df)} rows inserted into etl_news!")


# --- S3 JSON export ---
print("Uploading JSON to S3...")
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
# Convert DataFrame dates to ISO format
# print('full dataframe shape:',df.shape)
# 1 drop "National / Unknown"
df_filtered = df[df["state"] != "National / Unknown"]
# print('filtered out national/unknown:',df_filtered.shape)
# 2 drop headlines that begin with "<https"
df_filtered = df_filtered[~df_filtered["headlines"].str.startswith("<https", na=False)]
# df_to_json = df_filtered.copy()
df_filtered['alert_date'] = df_filtered['alert_date'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
# print('final datframe shape:', df_filtered.shape)
# --- DETAIL DATASET (row-level, authoritative) ---
detail_payload = (
    df_filtered[
        [
            "alert_date",
            "state",
            "target",
            "headlines",
            "datasource",
            "article_links",
        ]
    ]
    .sort_values(["alert_date", "state", "target"])
    .to_dict(orient="records")
)

s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/public_news_detail_table.json",
    Body=json.dumps(detail_payload, indent=2),
    ContentType="application/json",
)

# Build aggregated dataset for frontend
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

s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/public_news_data_bar_chart.json",
    Body=json.dumps(json_payload, indent=2),
    ContentType="application/json",
)
# export last time run timestamp
metadata = {
    "last_updated_utc": datetime.now(timezone.utc).isoformat(),
    "record_count": len(df),
    "source": "email_scraper_v4"
}

s3.put_object(
    Bucket="krieger-technologies.com",
    Key="news_data/last_run_timestamp.json",
    Body=json.dumps(metadata, indent=2),
    ContentType="application/json",
    CacheControl="no-cache, no-store, must-revalidate",
)
print("ETL reached end of script")
sys.exit(0)
print("✅ public_news_data.json uploaded")
