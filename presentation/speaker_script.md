# IntraStack CRM Platform — Speaker Script
### Meeting with Stefan & Luan
### Estimated Duration: 15–20 minutes + Q&A

---

## 🎤 OPENING — Slide 0 (Title)
**⏱ ~30 seconds**

> "Hi Stefan, Luan — thank you for the time. Tonight I'll walk you through our execution plan for the Odoo CRM platform. I'll cover: what's already done, our Phase 1 plan, who owns what, the timeline, and risks. This should take about 15 minutes, then I'd love your feedback."

---

## 📌 Slide 1 — Platform Status
**⏱ ~1–2 minutes**

> "Before I get into the plan — the infrastructure is already live. Odoo 17 is deployed on Docker, SSL is active, everyone has access."

> "The key mindset: this is not just a CRM — it's our full revenue-to-delivery control tower. Every module connects — from leads through delivery to invoicing."

**Key points to hit:**
- 5 infrastructure tasks already DONE (show the green checkmarks)
- Platform vision: Revenue + Staffing + Delivery
- Flow: Leads → Deals → Staffing → Delivery → Invoicing → Renewals

---

## 📌 Slide 2 — Team & Ownership
**⏱ ~1–2 minutes**

> "Three engineers full-time. I own the core CRM configuration — pipelines, automation, sales engine, and dashboard. Arian handles contacts and project delivery, and covers Asia timezone. Rishit handles custom fields and timesheets."

> "PM and BA support from Auspicious and Luan. Everyone has clear ownership — no overlap, no gaps."

**Key points to hit:**
- Steve = Pipelines, Automation, Sales, Dashboard (core)
- Arian = Contacts, Projects, timezone coverage
- Rishit = Custom fields, Timesheets, technical
- Everyone full-time on project

---

## 📌 Slide 3 — Phase 1 Scope
**⏱ ~2 minutes**

> "Phase 1 is pure no-code Odoo configuration. Nine deliverables across 4 weeks."

> "Week 1 is foundation — pipelines, fields, contacts. Week 2 — automation and project templates. Week 3 — sales engine and dashboard. Week 4 — training and UAT."

> "Everything is mapped directly from the CRM Platform document you provided."

**Key points to hit:**
- 9 deliverables total
- Color-coded by week (blue=W1, green=W2, orange=W3, red=W4)
- Each card shows owner + target week
- This is ALL no-code — no development needed for Phase 1

---

## 📌 Slide 4 — 4 Revenue Pipelines
**⏱ ~1–2 minutes**

> "As defined in your platform document — four independent pipelines."

> "Staffing for fast revenue. Consulting for high margin. Subcontracting for partner network. Managed Services for recurring MRR."

> "Each pipeline is its own Sales Team in Odoo with dedicated Kanban stages. No mixing, no confusion. Total 26 stages."

**Key points to hit:**
- P1 Staffing = 8 stages (fast cash flow)
- P2 Consulting = 7 stages (highest margin)
- P3 Subcontracting = 5 stages (MSP/primes)
- P4 Managed Services = 6 stages (recurring MRR)
- Each = separate Sales Team in Odoo

---

## 📌 Slide 5 — Automation & Operating Rules
**⏱ ~2 minutes**

> "Since we're on Community Edition, we don't have enterprise automation. We use Odoo's Activity system instead — four rules that keep the team accountable."

> "R1: new lead → qualify in 24 hours. R2: new requirement → submit 5 candidates in 48 hours. R3: discovery stage → prep checklist. R4: no activity for 5 days → re-engage alert."

> "And four non-negotiable operating rules from your platform document. These are enforced from day one. No exceptions."

> **⚠️ PAUSE HERE and ask:** "One thing I want to confirm: the automation triggers at 5 days, but the operating rule says 7 days — should we align these? My recommendation: use 5 days for the automation alert, and 7 days for management escalation."

**Key points to hit:**
- Community Edition workaround using Activities system
- 4 automation rules (R1–R4)
- 4 non-negotiable rules (everything in CRM, no external tracking, 4 mandatory fields, no stale deals)
- ASK about the 5-day vs 7-day discrepancy

---

## 📌 Slide 6 — Sprint Timeline
**⏱ ~2 minutes**

> "Four weekly sprints. Each week has a clear focus and parallel workstreams for all three engineers."

> "Week 1: foundation. Week 2: automation. Week 3: sales and dashboard. Week 4: training and UAT."

> "We target Phase 1 sign-off at end of Week 4 — that's when we do a live demo for you and Luan."

> "Phase 2 starts Month 2 with development-level work: email automation, AI lead scoring, ATS integration. I want to scope Phase 2 priorities with you after Phase 1 is complete."

**Key points to hit:**
- Color-coded tasks: purple=Steve, blue=Arian, green=Rishit
- Week 4 row is highlighted (green border) = sign-off milestone
- Phase 2 row is dashed = scoped after Phase 1 sign-off
- 5 Phase 2 items listed at high level

---

## 📌 Slide 7 — Acceptance Criteria
**⏱ ~1–2 minutes**

> "Eleven acceptance criteria — all must pass before we call Phase 1 done."

> "This gives you a clear, measurable checklist to evaluate our delivery. No ambiguity."

> "At the sign-off meeting in Week 4, we'll walk through each item live in the system."

**Key points to hit:**
- 11 specific pass/fail items
- Don't read all 11 — just highlight the key ones:
  - 4 pipelines live ✓
  - 6 custom fields required ✓
  - R1–R4 automation tested ✓
  - CEO dashboard 7 views ✓
  - 5+ test deals end-to-end ✓
- Bottom note: ALL must pass

**💡 TIP:** This is where Stefan is most likely to ask questions. Pause and let him react.

---

## 📌 Slide 8 — Risks & Mitigation
**⏱ ~1–2 minutes**

> "Four key risks identified upfront."

> "The biggest: scope creep — three phases in three months is aggressive. My recommendation: let's nail Phase 1 first, then scope Phase 2 with clear priorities."

> "Second: our VPS is at 83% swap usage with no production load yet. I'd recommend upgrading RAM before go-live to avoid performance issues."

> "Learning curve is medium risk — I lead all configuration, and we do daily async standups to keep everyone aligned."

**Key points to hit:**
- Scope creep = HIGH — be honest about this
- VPS memory = HIGH — actionable recommendation
- Learning curve = MEDIUM — mitigated by Steve leading
- Timezone = LOW — Arian covers overlap

---

## 📌 Slide 9 — Communication Plan
**⏱ ~1 minute**

> "Communication is structured at every level."

> "Daily async standups on Telegram. Weekly Friday demos with the full team. Bi-weekly written reports to you and Luan."

> "You'll have full visibility. And the Phase 1 sign-off is a live demo — you'll see everything working in the system."

**Key points to hit:**
- 4 communication channels
- Highlight the sign-off card (green border)
- Emphasis: "You'll never be in the dark"

---

## 📌 Slide 10 — Decisions Needed
**⏱ ~2 minutes**

> "Before I close — two items I need your decision on."

> "**First:** the stale deal threshold. Your platform document mentions both 5 days and 7 days in different sections. My recommendation: use 5 days for the automation alert, and 7 days for management escalation. What do you think?"

*[WAIT for response]*

> "**Second:** our VPS is already at 83% swap usage with no production load. I strongly recommend upgrading RAM before we go live. Should I proceed with researching upgrade options?"

*[WAIT for response]*

**Key points to hit:**
- These are the ONLY two things you need from them tonight
- Have a recommendation ready for each (you do)
- Let them decide — shows you respect their authority

---

## 🎤 CLOSING — Slide 11
**⏱ ~30 seconds**

> "To wrap up: infrastructure is ready, the team has clear ownership, Phase 1 is 9 deliverables in 4 weekly sprints with 11 measurable acceptance criteria. Risks are identified with mitigation plans."

> "I'm confident we can deliver Phase 1 on time."

> "I'm open to any questions or feedback you have. Thank you."

---

## 📋 Q&A CHEAT SHEET — If They Ask...

| Question | Your Answer |
|----------|-------------|
| **"What's the cost?"** | "Zero license cost — Odoo Community is free. Only cost is VPS hosting, approximately $X/month." |
| **"Why not Odoo Enterprise?"** | "Community covers all Phase 1 needs. We evaluate Enterprise in Phase 3 if we need advanced analytics or automation." |
| **"What if we fall behind?"** | "Week 4 has a buffer — training can overlap UAT. Worst case, we push sign-off 1 week. Phase 2 start is flexible." |
| **"Who's the single point of failure?"** | "I'm the primary config owner, but Arian is co-lead and can cover. All work is documented in Odoo itself." |
| **"What about data migration?"** | "No legacy CRM system to migrate from. We start clean. Any existing contacts can be CSV-imported." |
| **"When do we see results?"** | "End of Week 1 you'll see 4 live pipelines. End of Week 3 you'll see the CEO dashboard with test data." |
| **"What do you need from us?"** | "Two things: confirm the stale deal threshold (5 vs 7 days), and approve VPS RAM upgrade if needed." |
| **"Can we add more features to Phase 1?"** | "I'd recommend keeping Phase 1 lean to hit our timeline. We can add items to Phase 2 scope." |
| **"How do we track progress?"** | "Bi-weekly written reports plus weekly Friday demos. You'll see progress live every week." |

---

## 💡 PRESENTATION TIPS

1. **Don't read the slides** — use this script as a guide, speak naturally
2. **Pause after Slide 7** (Acceptance Criteria) — Stefan is most likely to ask questions there
3. **Slide 10 is your power move** — asking for their input shows confidence and respect
4. **If asked about Phase 2 details**, say: *"I have a high-level scope — happy to deep-dive in a follow-up session"*
5. **End strong** — the closing should feel decisive, not trailing off
6. **Keep total time under 20 minutes** — leave room for Q&A
7. **Press N in the browser** to see speaker notes on-screen during presentation (only you can see the bottom panel)
8. **Press F** to go fullscreen during the meeting
