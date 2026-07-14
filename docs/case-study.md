# RAG Support Agent with Confidence Gating + Escalation — B2B SaaS

**An AI support agent that answers your customers from your own docs — but only when it's sure. On billing, refunds, account, and anything it can't ground in a source, it refuses to guess: it drafts a reply and hands the ticket to a human.**

> _Built for B2B SaaS teams drowning in repetitive tier-1 tickets who've been burned by chatbots that confidently make things up. It deflects the easy majority and escalates the rest with the answer already drafted — so a human approves in seconds instead of starting from scratch._

**Who it's for:** B2B SaaS companies with a help center / docs and a support queue (Intercom, Zendesk, Freshdesk, or a website widget).
**What it replaces:** support reps re-answering the same how-to questions all day, and the fear of a bot inventing a refund policy that doesn't exist.
**The guardrail that makes it safe:** it never auto-answers billing, refund, cancellation, or account-security questions — and never answers anything it can't cite from your knowledge base.

---

## The Problem

Every B2B SaaS support queue is the same shape. Somewhere around 60% of it is repetitive tier-1 volume: "how do I reset my password," "where do I export my data," "does your API support webhooks," "how do I add a teammate." These questions are already answered in the docs. A human re-typing those answers all day is expensive and slow, and it buries the tickets that actually need a person.

So teams reach for a chatbot. And then they get burned. The generic support bot's failure mode isn't that it can't answer the easy 60% — it's that it answers the *hard* 10% with total confidence and gets it wrong. It quotes a refund window that doesn't exist. It tells a customer their data is deletable when it isn't. It invents an API limit. On a how-to question, a wrong answer is an annoyance. On a billing, refund, cancellation, or security question, a wrong answer is a chargeback, a compliance problem, or a churned account — and a screenshot on X.

That's the real reason support leaders don't trust automation: not "will it deflect tickets," but "what happens on the questions where being wrong is expensive." A bot that's right 90% of the time sounds great until you realize the 10% it's wrong on is exactly the 10% you couldn't afford to get wrong.

The result is that most SaaS teams either don't deploy a bot at all, or deploy one and quietly turn it off after the first bad incident. The deflection they were promised never materializes, and the reps are still re-answering password resets.

---

## What It Does

When a customer message comes in — from a website widget, a helpdesk (Intercom/Zendesk/Freshdesk), or email — the agent:

- **Retrieves** the most relevant passages from the company's own knowledge base (help center, docs, policies) using semantic search, and scores how well the question is actually covered.
- **Classifies** the question's topic — is this a routine how-to, or does it touch billing, refunds, cancellation, account access, security, or legal?
- **Decides whether it's allowed to answer.** Two conditions must *both* be true to auto-respond: retrieval confidence is high enough, and the topic is not in the protected set. If either fails, it does not send.
- **Auto-answers the safe, well-covered questions** — grounded strictly in the retrieved passages, with a citation/source link, in the company's tone. No source, no answer.
- **Escalates everything else with the work already done.** For low-confidence or protected-topic questions, it does *not* reply to the customer. Instead it drafts a suggested response, attaches the retrieved sources and its confidence score, and drops it into a human queue (Slack or the helpdesk) for a rep to approve, edit, or discard.
- **Logs** every interaction — question, retrieved sources, confidence, topic, decision (answered / escalated), and outcome — so the deflection rate and the escalation reasons are measurable.

A typical deflection: a customer asks "how do I export my account data to CSV?" The agent retrieves the exact docs section, scores it high-confidence, sees it's a routine how-to, and replies in seconds with the steps and a link to the doc. No human touched it.

A typical escalation: a customer asks "can I get a refund for last month — I was double-charged?" Even though the billing policy is in the docs, this is a protected topic. The agent does **not** answer. It drafts "Here's what our policy says about double-charge refunds… [draft], sources: [billing-policy], confidence: high" and posts it to the support Slack for a human to verify the actual charge and send. The customer waits a few minutes for a correct human answer instead of getting an instant wrong one.

---

## Architecture & Decision Logic

The point of this build isn't "it can do RAG." Plenty of bots can retrieve and generate. The point is that it makes an explicit, defensible decision about **when it's allowed to speak** — and deliberately stays silent when the cost of being wrong is high.

**Trigger → orchestration.** An inbound message (widget, helpdesk webhook, or email) fires an n8n workflow. n8n is the brain: it drives retrieval, applies the gate, routes the decision, and syncs out. The LLM and vector database are components n8n calls — they don't make the routing decision, the workflow does.

**Retrieval + confidence scoring.** The question is embedded and run against a vector database (Supabase pgvector or Pinecone) holding the chunked, embedded knowledge base. The search returns the top passages with similarity scores. "Confidence" here isn't the LLM's self-reported vibe — it's grounded signal: the top-match similarity and how many passages clear a relevance threshold. If nothing clears the bar, the system treats the question as *undocumented* and refuses to answer from thin air.

**Topic classification (the second gate).** Independently of confidence, the question is classified against a protected set: billing, refunds, cancellation, account access/security, and legal/contractual. This is deliberately a *separate* gate from confidence — because a question can be perfectly well-documented and still be one the business never wants auto-answered. High confidence does not buy a pass on a refund question.

**The gate (the part that proves judgment).** The system auto-responds **only if** `confidence ≥ threshold AND topic ∉ protected`. Everything else is escalated, not answered:

- **Low confidence / undocumented** → it doesn't guess. It escalates with "no confident source found," so a human answers and the gap gets added to the docs.
- **Protected topic** → it never auto-sends, even at high confidence. It drafts and escalates so a human with account context verifies before anything goes out.
- **Well-covered + routine** → it answers, cited.

This is the "knows what it doesn't know" design a support leader actually needs to see before they'll trust automation on their queue. The bot is trusted with volume; humans stay in charge of anything expensive-to-get-wrong.

**Human-in-the-loop draft.** Escalation is not a dead end that dumps a raw ticket on a rep. The agent still does the work — it drafts the answer and attaches sources and score — so the human's job is *verify and send*, not *start from scratch*. That's what keeps the escalated 40% cheap to handle instead of just shifting the cost.

**The demo-to-live swap point.** In the portfolio build, the knowledge base is a seeded sample doc set, the "incoming ticket" is a mock webhook, and escalations post to a test Slack channel. For a real client, three things swap in with no change to the core logic: (1) their actual docs/help center (re-indexed into the vector DB), (2) their real ticket source (Intercom/Zendesk/Freshdesk/widget), and (3) their real escalation destination. The confidence threshold and the protected-topic list are config the client tunes — not hard-coded. Clean seams, so a demo becomes a deployment in days.

---

## Projected Outcomes

_These figures are illustrative targets based on published RAG-support benchmarks, not results from a live client deployment — this build is being finished now. They're framed the way I'd model ROI for a real SaaS team, and I'll replace them with actual queue data as the system goes live._

- **~60% of tier-1 tickets deflected** — the repetitive, well-documented how-to volume answered instantly, 24/7, without a rep.
- **Zero wrong answers on billing, refunds, cancellation, and account/security** — by design, because those never auto-send. Published agentic-support case studies report hallucinated-policy rates under 0.5% precisely because of gating like this.
- **Faster resolution on escalations, not just deflections** — reps approve a pre-drafted, source-backed reply instead of researching from scratch, so even the 40% that reaches a human is faster.
- **A self-documenting gap list** — every "no confident source" escalation is a flag for a missing or unclear doc, so the knowledge base (and the deflection rate) improves over time.
- **Every interaction logged and measurable** — deflection rate, escalation reasons, and confidence distribution are reportable from day one.

The headline claim I'd put on a proposal: **"Most support bots hallucinate on the 10% of questions that matter most. This one deflects the easy 60% and escalates the rest with a draft reply — so it's never confidently wrong on a refund."**

---

## Adapting to Your Business

The architecture is SaaS-support-specific in its knowledge base and protected topics, but the pattern — retrieve, score confidence, gate on topic, answer-or-escalate-with-a-draft — transfers cleanly to any support context where being *confidently wrong* is worse than being slow:

- **E-commerce:** auto-answers sizing, shipping, and product questions; refuses to confirm refunds, order changes, or address edits and escalates those with a drafted reply.
- **Fintech / financial services:** answers general product and how-to questions; never touches account balances, transactions, or anything regulated — routes to a licensed/authorized human.
- **Healthcare / dental:** answers logistics (hours, insurance accepted, how to book); escalates anything clinical, every time.

In each case the swap is the knowledge base and the protected-topic list — the retrieval, confidence gate, and human-in-the-loop escalation backbone stay the same.

---

## How It's Built

Stack: n8n (orchestration + gating) · Vector DB — Supabase pgvector or Pinecone (retrieval) · OpenAI or Claude (embeddings + grounded generation) · Slack / helpdesk (human escalation queue)

- **n8n** orchestrates everything and owns the decision: it embeds the query, calls the vector search, computes the confidence + topic gate, and routes to either the auto-answer branch or the draft-and-escalate branch. Self-hostable, so there's no per-workflow platform lock-in. The gate logic lives here, in the open, not buried inside a black-box bot.
- **The vector database** (Supabase pgvector on the free tier, or Pinecone) holds the chunked, embedded knowledge base and returns passages with similarity scores — the raw signal the confidence gate runs on.
- **The LLM** (OpenAI or Claude) does two narrow jobs: embed the query, and generate an answer *strictly grounded* in retrieved passages with citations. It is explicitly not trusted to decide whether to answer — that's the workflow's job.
- **Slack / the helpdesk** is the human-in-the-loop destination: escalations arrive as a drafted reply plus sources and confidence, ready to approve and send.

The whole system is built to be importable and configurable: the n8n workflow exports as a JSON file a client can drop into their own instance, and the confidence threshold, protected-topic list, and knowledge-base source are parameters — not hard-coded — so it adapts to a specific team without touching the core logic.
