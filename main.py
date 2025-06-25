import imapclient
import ssl
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
import time
import json
import requests

# Load environment variables from .env file
load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

IMAP_SERVER = 'imap.naver.com'
IMAP_PORT = 993

TIME_WINDOW_HOURS = 1
MAX_RETRIES = 5
RETRY_DELAY = 5
POLL_INTERVAL_SECONDS = 30
PROCESSED_UIDS_FILE = 'processed_uids.json'

# Disable SSL verification (for testing purposes)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def load_processed_uids():
    if os.path.exists(PROCESSED_UIDS_FILE):
        with open(PROCESSED_UIDS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_processed_uids(uids):
    with open(PROCESSED_UIDS_FILE, 'w') as f:
        json.dump(uids, f)

def is_uid_processed(uid, processed_uids):
    return uid in processed_uids

def add_processed_uid(uid, processed_uids):
    if uid not in processed_uids:
        processed_uids.append(uid)
        save_processed_uids(processed_uids)

def send_to_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] Discord webhook URL not set.")
        return
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        response.raise_for_status()
        print("[INFO] Sent to Discord.")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send to Discord: {e}")

def fetch_emails(client):
    print(f"[INFO] Polling inbox at {datetime.now().isoformat()}")
    try:
        processed_uids = load_processed_uids()
        client.select_folder('INBOX', readonly=True)

        # Get all emails from Netflix within the last TIME_WINDOW_HOURS
        since_date = (datetime.now() - timedelta(hours=TIME_WINDOW_HOURS)).strftime('%d-%b-%Y')
        messages = client.search(['FROM', 'info@account.netflix.com', 'SINCE', since_date])

        korea_tz = pytz.timezone('Asia/Seoul')
        now_kst = datetime.now(korea_tz)

        if messages:
            print(f"[INFO] Found {len(messages)} messages from Netflix.")
            for msg_id in messages:
                print(f"[INFO] Checking UID: {msg_id}")
                if is_uid_processed(str(msg_id), processed_uids):
                    print("[SKIP] Already processed.")
                    continue

                raw_msg = client.fetch([msg_id], ['BODY[]', 'FLAGS'])
                msg = email.message_from_bytes(raw_msg[msg_id][b'BODY[]'])

                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')

                sent_time = parsedate_to_datetime(msg['Date']).astimezone(korea_tz)
                print(f"[INFO] Sent at {sent_time.isoformat()} / Now: {now_kst.isoformat()}")

                if now_kst - sent_time > timedelta(hours=TIME_WINDOW_HOURS):
                    print("[SKIP] Older than time window.")
                    continue

                # Extract plain text body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body += part.get_payload(decode=True).decode(charset, errors='ignore')
                            except Exception as e:
                                print(f"[WARN] Failed decoding part: {e}")
                else:
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        body = msg.get_payload(decode=True).decode(charset, errors='ignore')
                    except Exception as e:
                        print(f"[WARN] Failed decoding body: {e}")

                if "코드" in subject or "code" in subject or "코드" in body or "code" in body:
                    match = re.search(r'https?://[^\s\]]+', body)
                    if match:
                        first_link = match.group(0)
                        message = f"넷플릭스 코드 [{sent_time.isoformat()}]\n{first_link}"
                        send_to_discord(message)
                        add_processed_uid(str(msg_id), processed_uids)
                    else:
                        print("[WARN] Code email found, but no link detected.")
                else:
                    print("[INFO] Email skipped (no 'code' keyword).")
        else:
            print("[INFO] No new email from Netflix.")
    except Exception as e:
        print(f"[ERROR] While fetching emails: {e}")
        raise

def connect_to_imap():
    retry_count = 0
    print("[BOOT] Script started and connecting to IMAP...")
    send_to_discord("📡 Netflix code listener started.")
    while retry_count < MAX_RETRIES:
        try:
            client = imapclient.IMAPClient(IMAP_SERVER, ssl=True, ssl_context=ssl_context)
            client.login(EMAIL, PASSWORD)
            print("[AUTH] Logged in to IMAP.")
            while True:
                fetch_emails(client)
                time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            retry_count += 1
            print(f"[FAIL] Attempt {retry_count}/{MAX_RETRIES} failed: {e}")
            if retry_count < MAX_RETRIES:
                print(f"[RETRY] Waiting {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("[FATAL] Max retries reached. Exiting.")
                break

if __name__ == "__main__":
    connect_to_imap()
