"""
Seed the Supabase `documents` table for the RAG Support Agent demo.

Run this yourself, locally — do not share your DB password or API keys
with anyone, including in chat. Set them as environment variables before running:

  export SUPABASE_DB_PASSWORD="your-db-password"
  export GOOGLE_API_KEY="your-google-ai-studio-key"
  python3 seed_documents.py

Note: embeddings are generated via Google AI Studio (gemini-embedding-001),
NOT AICredits — AICredits doesn't currently offer a working embeddings model
despite what their docs claim. AICredits is still used for the chat nodes in
the n8n workflow itself; this script only needs the Google key.
"""

import os
import sys
import json
import requests
import psycopg2

# ---- Connection details (from your Session Pooler string) ----
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres.iqmzqklstbqvroxtbabb"
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/openai/embeddings"
EMBED_MODEL = "gemini-embedding-001"  # text-only Gemini embedding model, default 3072 dims
EMBED_DIMS = 3072

if not DB_PASSWORD or not GOOGLE_API_KEY:
    print("Missing SUPABASE_DB_PASSWORD or GOOGLE_API_KEY env vars.")
    print("Set them first, e.g.:")
    print('  export SUPABASE_DB_PASSWORD="your-db-password"')
    print('  export GOOGLE_API_KEY="your-google-ai-studio-key"')
    sys.exit(1)

# ---- Sample knowledge base: fake SaaS product "Beacon Analytics" ----
DOCS = [
    {
        "title": "Resetting your password",
        "content": "To reset your Beacon Analytics password, go to the login page and click "
                    "'Forgot password'. Enter the email associated with your account and we'll "
                    "send a reset link valid for 30 minutes. If you don't receive the email, "
                    "check your spam folder or contact support to confirm your account email is correct.",
    },
    {
        "title": "Exporting your data to CSV",
        "content": "You can export any dashboard or report to CSV by clicking the 'Export' button "
                    "in the top-right corner of the report view and selecting CSV format. Exports "
                    "include all filtered data currently shown on screen. Large exports (over 100,000 "
                    "rows) are emailed to you as a download link instead of downloading directly.",
    },
    {
        "title": "Adding a teammate to your workspace",
        "content": "Workspace admins can invite teammates from Settings > Team > Invite Member. "
                    "Enter their email and choose a role: Admin, Editor, or Viewer. Editors can create "
                    "and edit dashboards; Viewers have read-only access. Invited teammates count toward "
                    "your plan's seat limit.",
    },
    {
        "title": "Connecting the API and webhooks",
        "content": "Beacon Analytics exposes a REST API for programmatic access to your reporting data. "
                    "Generate an API key from Settings > Developer > API Keys. Webhooks can be configured "
                    "under Settings > Developer > Webhooks to receive real-time notifications when a report "
                    "is updated or a scheduled export completes.",
    },
    {
        "title": "Supported integrations",
        "content": "Beacon Analytics integrates natively with Slack, Google Sheets, and Zapier. Slack "
                    "integration lets you post scheduled report summaries to any channel. Google Sheets "
                    "sync keeps a live copy of your dashboard data in a spreadsheet. Zapier support lets "
                    "you connect Beacon Analytics to 5,000+ other apps without code.",
    },
    {
        "title": "Understanding your billing cycle and invoices",
        "content": "Beacon Analytics bills monthly on the date you first subscribed. Invoices are sent by "
                    "email and available under Settings > Billing > Invoice History. Plan upgrades are "
                    "prorated for the remainder of the current billing cycle; downgrades take effect at the "
                    "start of the next cycle.",
    },
    {
        "title": "Refund policy",
        "content": "Beacon Analytics offers refunds within 14 days of a new subscription purchase if you "
                    "have not exceeded 1,000 API calls or created more than 3 dashboards. Refund requests "
                    "must be submitted via Settings > Billing > Request Refund or by contacting support. "
                    "Refunds are processed to the original payment method within 5-10 business days. "
                    "Refunds are not available for renewal charges after the initial 14-day window.",
    },
    {
        "title": "Cancelling your subscription",
        "content": "You can cancel your subscription anytime from Settings > Billing > Cancel Subscription. "
                    "Cancellation takes effect at the end of your current billing period; you retain access "
                    "until then. Cancelling does not automatically delete your data — exported reports and "
                    "raw data remain available for 30 days after cancellation, after which they are permanently deleted.",
    },
    {
        "title": "Two-factor authentication setup",
        "content": "Enable two-factor authentication (2FA) under Settings > Security > Two-Factor Authentication. "
                    "Beacon Analytics supports authenticator apps (Google Authenticator, Authy) via QR code setup. "
                    "SMS-based 2FA is not currently supported. If you lose access to your authenticator app, "
                    "contact support with your account email to verify identity and reset 2FA.",
    },
    {
        "title": "Rate limits and API usage quotas",
        "content": "The Beacon Analytics API allows 100 requests per minute on the Starter plan and 1,000 "
                    "requests per minute on the Growth plan. Exceeding the limit returns a 429 status code. "
                    "Monthly API call quotas are visible under Settings > Developer > Usage. Contact sales "
                    "for custom rate limits on Enterprise plans.",
    },
]


def get_embedding(text: str) -> list:
    resp = requests.post(
        EMBED_URL,
        headers={
            "Authorization": f"Bearer {GOOGLE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": text},
        timeout=30,
    )
    if not resp.ok:
        print(f"\nAICredits returned {resp.status_code}. Response body:")
        print(resp.text)
        print()
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def main():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )
    conn.autocommit = True
    cur = conn.cursor()

    print(f"Connected. Seeding {len(DOCS)} documents...")

    for doc in DOCS:
        embedding = get_embedding(doc["content"])
        if len(embedding) != EMBED_DIMS:
            print(f"WARNING: embedding for '{doc['title']}' has {len(embedding)} dims, expected {EMBED_DIMS}")
        cur.execute(
            "INSERT INTO documents (title, content, embedding) VALUES (%s, %s, %s::vector)",
            (doc["title"], doc["content"], json.dumps(embedding)),
        )
        print(f"  inserted: {doc['title']}")

    cur.execute("SELECT count(*) FROM documents")
    count = cur.fetchone()[0]
    print(f"\nDone. documents table now has {count} rows.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
