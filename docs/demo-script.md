# Demo Script — RAG Support Agent (60 seconds, terminal-based)

Screen layout: Terminal (left/top) + Slack `#support-escalations` (right/bottom). Screen-record with audio. Do ONE dry run first to confirm both branches still fire correctly, then record for real — don't stop mid-take, just redo the whole thing if something breaks.

Have these two commands ready to paste (swap in your real webhook URL), so you're not typing live:

```
curl -X POST YOUR_WEBHOOK_URL -H "Content-Type: application/json" -d '{"message":"How do I add a teammate?","conversation_id":"demo-1","customer_email":"test@acme.com"}'
```

```
curl -X POST YOUR_WEBHOOK_URL -H "Content-Type: application/json" -d '{"message":"I was double-charged, can I get a refund?","conversation_id":"demo-2","customer_email":"test@acme.com"}'
```

---

**0:00–0:07 — Opening (talk to camera or voiceover over terminal)**
> "This is a support agent that answers the easy questions from your docs — and refuses the ones it shouldn't touch. Watch both."

**0:07–0:25 — Clip A: the win (auto-answered)**
- Paste the first curl command, hit enter.
- Let the JSON response fill the terminal — point the cursor at `"decision":"answer"` and the actual answer text.
> "Safe, well-documented question — answered instantly, grounded in the docs. No human touched this."

**0:25–0:50 — Clip B: the judgment (refused + escalated)**
- Paste the second curl command, hit enter.
- Point at `"decision":"escalate"` and the fact that `"answer"` is empty/null — nothing went to the customer.
- Cut immediately to Slack — show the escalation message: reason, confidence score, and the drafted reply waiting for a human.
> "Billing question — it refuses to answer on its own, even though the refund policy is in its knowledge base. Instead it drafts a reply and hands it to a human to verify the actual charge first."

**0:50–1:00 — Closing**
> "Deflects the safe majority, escalates the rest with the reply already drafted, never fabricates a policy. Same pattern drops into any support stack — happy to walk you through it."

---

### Recording notes
- Increase your terminal font size before recording — JSON needs to be readable on video.
- Silent-trim the gap between hitting enter and the response appearing so it feels instant.
- Export at 1080p.
