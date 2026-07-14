# Build Runbook — RAG Support Agent Demo

Goal: two recordable moments — (1) a routine how-to question that gets **auto-answered from the docs with a citation**, and (2) a **billing/refund question that the agent refuses to answer**, drafts, and escalates to a human Slack queue. Budget: ~1–2 focused sessions. Cost: free-tier / trial credits.

---

## Phase 0 — Accounts (~20 min)

- [ ] **AICredits** ([aicredits.in](https://aicredits.in)) — INR-billed OpenAI-compatible gateway, used in place of a direct OpenAI key. Sign up, top up ₹50 via UPI, create an API key (starts `sk-...`, shown once — save it). Used only for the 3 chat nodes (classifier + answer/draft generation), model `openai/gpt-4o-mini` — confirmed working via the AICredits Playground.
- [ ] **Google AI Studio** ([aistudio.google.com/apikey](https://aistudio.google.com/apikey)) — free, no card, separate key from AICredits. Used only for embeddings (`gemini-embedding-001`, 3072 dims), since AICredits doesn't currently offer a working embedding model despite what their docs claim.
- [ ] (If you later get a direct OpenAI key for a real client, point the chat Base URL back at `https://api.openai.com/v1` and the embeddings node at `https://api.openai.com/v1/embeddings` with `text-embedding-3-small`, and resize the Supabase column to 1536.)
- [ ] **Supabase** — free project. You'll enable the `pgvector` extension and create a `documents` table. The workflow queries it directly with the native **Postgres** node (no RPC needed), so grab your DB connection details from Project Settings → Database.
- [ ] **n8n** — n8n Cloud free trial, or self-host with `npx n8n` locally (free).
- [ ] **Slack** — a workspace with one channel (e.g. `#support-escalations`) and a Slack app/bot token so you can add a **Slack credential** in n8n. This is the human queue.

> **Note on node types:** the workflow uses n8n's *native* OpenAI, Postgres (Supabase), and Slack nodes — so the canvas shows recognizable branded nodes, not a row of identical HTTP nodes. The only HTTP node is **OpenAI · Embed Query** (n8n has no main-flow node that returns a raw embedding vector). Credentials are set once in n8n's credential manager rather than pasted inline.

---

## Phase 1 — Seed the knowledge base (~30 min)

1. In Supabase SQL editor, enable pgvector and create the store:
   ```sql
   create extension if not exists vector;
   create table documents (
     id bigserial primary key,
     title text,
     content text,
     embedding vector(3072)
   );
   ```
   No match function needed — the **Supabase · Vector Match** node runs the pgvector similarity query directly and returns a `similarity` score per row.
2. Write **8–12 short sample docs** for a fake SaaS product (call it e.g. "Beacon Analytics"). Cover: password reset, exporting data, adding a teammate, API/webhooks, supported integrations — **and at least one billing/refund policy doc** (so the protected-topic path has something to draft from).
3. Embed each doc (`gemini-embedding-001` via Google AI Studio, 3072 dims) and insert into `documents`. A tiny script or a one-off n8n run both work.

✅ At this point you have a searchable knowledge base with a deliberate mix of safe how-tos and a protected billing topic.

---

## Phase 2 — Import & wire the workflow (~30 min)

1. Import `rag-n8n-workflow.json` into n8n (Workflows → Import from File).
2. Attach credentials in the nodes (see the **Setup Notes** sticky in the canvas):
   - **OpenAI account** → the 3 OpenAI nodes (Classify / Generate / Draft). Set **Base URL** to `https://api.aicredits.in/v1` and the API key to your AICredits key. Model fields are already set to `openai/gpt-4o-mini`.
   - **HTTP Header Auth** credential (`Authorization = Bearer <GOOGLE_API_KEY>` — your separate Google AI Studio key) → **OpenAI · Embed Query**. URL is already set to `https://generativelanguage.googleapis.com/v1beta/openai/embeddings`.
   - **Supabase Postgres** credential → **Supabase · Vector Match** (host/db/user/pass from Supabase → Project Settings → Database).
   - **Slack account** credential → **Slack · Post to Human Queue**; set the channel (e.g. `#support-escalations`).
3. In the demo you'll show the auto-answer in n8n's execution output / webhook response; wiring the reply back into a real helpdesk (Intercom/Zendesk) is the live-client step.
4. Copy the **Incoming Ticket (Webhook)** Production URL — that's where a real ticket source would POST. For the demo you'll POST to it yourself.
5. Set the workflow **Active**.

---

## Phase 3 — Test both paths (~30 min)

Send test tickets to the webhook (curl, Postman, or an n8n manual trigger). Payload shape:
```json
{ "message": "How do I export my data to CSV?", "conversation_id": "demo-1", "customer_email": "test@acme.com" }
```

- [ ] **Deflection path:** ask a clean how-to ("how do I add a teammate?"). Confirm the **Answer or Escalate?** node goes down the *answer* branch, the generated reply is grounded and cites a source, and the response shows `decision: answer`.
- [ ] **Protected-topic path:** ask "I was double-charged last month, can I get a refund?" Confirm it goes down the *escalate* branch, **nothing is sent to the customer**, and a message lands in your Slack channel with the reason (`protected_topic:refund`), the confidence score, and a drafted reply.
- [ ] **Low-confidence path (bonus):** ask something not in your docs ("do you integrate with SAP?"). Confirm it escalates with `low_confidence:…` — the agent refuses to guess.

If the refund question gets auto-answered, your classifier or protected list is off — fix before recording. That gate holding is the entire demo.

---

## Phase 4 — Record the demo (~20 min)

Use `rag-loom-demo-script.md` for the exact questions and shots. Two clips:
- **Clip A (the win):** how-to question → auto-answered → show the grounded reply + citation.
- **Clip B (the judgment):** refund question → show it NOT answering → cut to Slack showing the escalation with the drafted reply and confidence score.

Trim to ~60–90 seconds. Clip B is the one that closes buyers.

---

## Common gotchas
- **Everything escalates:** your `THRESHOLD` (0.78 in the Gate node) may be too high for your embedding model. Log `topSim` from the Gate output and tune.
- **Refund question gets auto-answered:** the classifier returned `protected: false`. Check the Classify Topic node output; tighten the category list.
- **Empty sources:** confirm docs were actually embedded and inserted, and that the embedding dims (3072, for `gemini-embedding-001`) match the column.
- **Slack message doesn't fire:** verify the Incoming Webhook URL and that the escalate branch is actually being hit.
- **Keep test volume low** — you're on trial credits; a handful of calls proves every path.
