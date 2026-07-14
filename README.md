# RAG Support Agent with Confidence Gating + Escalation — B2B SaaS

**An AI support agent that answers customers from your own docs — but only when it's sure. On billing, refunds, account, or anything it can't ground in a source, it refuses to guess: it drafts a reply and hands the ticket to a human.**

Built for B2B SaaS teams drowning in repetitive tier-1 tickets who've been burned by chatbots that confidently make things up.

`n8n` `Supabase pgvector / Pinecone` `OpenAI or Claude` `Slack`

---

## The problem

~60% of a typical SaaS support queue is repetitive, already-documented tier-1 volume. Teams deploy a chatbot to handle it — and get burned, because the bot's failure mode isn't the easy 60%, it's the *hard* 10%. It quotes a refund window that doesn't exist, or confirms something it shouldn't. On a how-to question a wrong answer is an annoyance; on billing or account security it's a chargeback or a churned account.

## What it does

- Retrieves the most relevant passages from the company's knowledge base and scores how well the question is actually covered
- Classifies the topic: routine how-to, or billing/refunds/cancellation/account/security/legal
- **Auto-answers only if both hold:** retrieval confidence clears the threshold **and** the topic isn't in the protected set
- Auto-answers safe, well-covered questions — grounded strictly in retrieved passages, with a citation
- Escalates everything else **with the work already done**: drafts a suggested reply, attaches sources + confidence score, drops it in a human queue (Slack/helpdesk) to approve, edit, or discard
- Logs every interaction — question, sources, confidence, topic, decision, outcome

## Architecture

```
Inbound message (widget / helpdesk / email)
        │
        ▼
   n8n trigger ──► embed query ──► vector search (top passages + similarity scores)
        │
        ▼
   Gate 1: confidence ≥ threshold?  ──NO──► escalate: "no confident source found"
        │ YES
        ▼
   Gate 2: topic ∈ {billing, refunds, cancellation, account, security, legal}?
        │
        ├─ YES (protected) ──► draft answer + sources + confidence ──► Slack human queue
        │                       (never auto-sent, even at high confidence)
        │
        └─ NO ──► auto-answer, grounded + cited, sent directly to customer
```

**Both gates must pass to auto-respond.** Confidence alone doesn't buy a pass on a refund question — that's the second, independent gate, and it's the part that proves this isn't just "a bot that does RAG."

## Mock vs. live

| | Demo (this repo) | Client deployment |
|---|---|---|
| Knowledge base | Seeded sample docs (`scripts/seed_documents.py`) | Client's real docs/help center, re-indexed |
| Ticket source | Mock webhook | Real Intercom/Zendesk/Freshdesk/widget |
| Escalation destination | Test Slack channel | Client's real support Slack/queue |
| Confidence threshold + protected-topic list | Sample config | Config the client tunes |

No change to the retrieval → gate → answer-or-escalate logic — only the endpoints and config swap.

## Projected outcome

*Modeled from published RAG-support benchmarks — this build is pre-deployment, figures will be replaced with real queue data as it goes live.*

~60% of tier-1 tickets deflected · zero auto-sent answers on billing/refunds/cancellation/account-security by design · faster resolution even on escalations (rep approves a pre-drafted, source-backed reply instead of researching from scratch) · every "no confident source" escalation doubles as a documented gap in the knowledge base.

## What's in this repo

```
workflow/n8n-workflow.json    importable n8n workflow (retrieval + both gates)
scripts/seed_documents.py     seeds the sample knowledge base into the vector DB
docs/case-study.md            full problem → architecture → outcome writeup
docs/system-prompt.md         grounded-generation system prompt (citation-only, no guessing)
docs/build-runbook.md         step-by-step setup/deploy instructions
docs/demo-script.md           walkthrough script used for the recorded demo
```

## Adapting this pattern

The retrieve → score confidence → gate on topic → answer-or-escalate-with-a-draft pattern transfers to any support context where being confidently wrong is worse than being slow — e-commerce (never auto-confirm refunds/order changes), fintech (never touch balances or regulated topics), healthcare/dental (escalate anything clinical, every time).

---

Built by Surabhi Deb as part of an AI automation portfolio. [See the full project index](https://github.com/YOUR-USERNAME) for related builds (voice lead qualification, speed-to-lead systems, financial reporting automation).

## License

MIT — see [LICENSE](LICENSE).
