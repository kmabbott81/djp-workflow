# 09 — Landing Page

> **Status:** Draft for team review · **Owner:** Copywriter / Email Strategist / Behavioral Economist · **Depends on:** [00 — Evidence Foundation](00-evidence-foundation.md) (§3 tiers, §4 registry, §5 gaps, §7 Ten Laws, §8 vocabulary, §10 marketing rules, §11 metrics) · **Conversion goals:** Primary = **First Action Kit** email opt-in. Secondary = **Anchor Money System** purchase.

**Executive summary.** This document delivers the complete Anchor landing page: final copy for every section, a design annotation before each section (layout, hierarchy, decision load), an annotated wireframe, and the compliance rationale for each strategy-level choice. The page is built to demonstrate the product's own design laws — one primary call to action repeated down the page, minimal navigation, generous whitespace, at most three visible product choices, and evidence presented with tier labels and honest caveats (including the admission that no planner, ours included, has beaten a spreadsheet in a head-to-head trial). Every study referenced in customer-facing copy is written in plain language and annotated with its registry key in an inline HTML comment so reviewers can trace every claim to §4 of the foundation.

---

## 1. Page strategy

### 1.1 Conversion logic

- **Primary conversion:** the free **First Action Kit** (email opt-in). Low commitment, immediate first win, feeds the welcome sequence in [10 — Email Marketing](10-email-marketing.md).
- **Secondary conversion:** **Anchor Money System** purchase — offered quietly, once, in the products section. Never in the hero, never in a popup.
- **One primary CTA, repeated.** The same button ("Get the free First Action Kit") appears in the hero, after the evidence section, after How It Works, and after the FAQ. No competing CTAs above the products section.
- **The page is the demo.** A visitor with ADHD should experience Laws 2, 3, and 4 while reading: one next action per screen, few decisions, everything scannable in an F-pattern skim.

> **Evidence:** T2 [IyengarLepper-2000] [Jachimowicz-2019]; governance Law 10 · **Confidence:** Moderate · **Rationale:** fewer choices and a single default action raise follow-through in general populations; a distractible visitor should never have to decide *which* button matters. · **Expected outcome:** higher opt-in completion; lower pogo-sticking between competing CTAs. · **Downside:** a single funnel entry may cost some direct-to-purchase sales; we accept this for list quality. · **Difficulty:** Low · **Priority:** High

### 1.2 Honesty as positioning

The ADHD app market has 109 apps and zero proof [Pasarelu-2020]. Our differentiation is not a bigger claim — it is the *smallest defensible claim, stated plainly*, plus Evidence Notes. The page says out loud what competitors hide: the evidence supports the strategy class, not any specific template; nobody has run the head-to-head trial (§5.1); and we measure function, not engagement.

> **Evidence:** Governance (§5, §10); trust rationale is design judgment, untested · **Confidence:** Moderate · **Rationale:** in a market of inflated claims, verifiable honesty is the only positioning a skeptical, burned audience cannot dismiss. · **Expected outcome:** higher trust among research-literate visitors; more replies and fewer refunds. · **Downside:** weaker copy "punch" than competitors' claims; some visitors want certainty and will bounce. · **Difficulty:** Low · **Priority:** High

### 1.3 Copy standards for this page

1. Reading level ≈ grade 7. Short sentences. Short paragraphs (1–3 lines).
2. Every study reference in customer copy: plain language + inline `<!-- [key] -->` comment mapping to §4.
3. §10 pass required: no "clinically proven [product]," no outcome promises, no urgency theater, no shame hooks. Not-a-treatment disclosure appears in the hero area *and* the footer.
4. §8 vocabulary used verbatim: First Action Kit, The Inbox, Anchor Daily Board, The Weekly Reset, Comeback Mode, Anchor Money System, Anchor Life OS, Anchor Lab, Evidence Notes.
5. The financial-distress evidence is presented with care. **Rule (binding):** the suicide association in [Swedish-Registry] **never appears in sales copy** — not on this page, not in ads, not in cart emails. It may appear only in long-form educational content that leads with support resources.

### 1.4 Reading this document

Design annotations appear as indented blockquotes (**> Design annotation**). Everything under a "**Copy**" marker is verbatim page copy. Prices shown are illustrative placeholders within the approved ladder bands (final numbers come from the pricing doc).

---

## 2. Annotated wireframe (section order)

```
┌────────────────────────────────────────────────────────────┐
│ 0. Micro-nav: logo · Evidence · Products · [CTA button]    │  minimal, sticky
├────────────────────────────────────────────────────────────┤
│ 1. HERO: headline, subhead, ONE CTA, trust microcopy,      │  1 decision
│    product visual (Anchor Daily Board screenshot)          │
├────────────────────────────────────────────────────────────┤
│ 2. PROBLEM: planner graveyard + the ADHD tax (gentle)      │  0 decisions
├────────────────────────────────────────────────────────────┤
│ 3. WHY PLANNERS FAIL YOU: the mechanism story +            │  0 decisions
│    the head-to-head honesty box                            │
├────────────────────────────────────────────────────────────┤
│ 4. EVIDENCE: "What the research actually shows"            │  0–1 decisions
│    6 study cards w/ tier labels · link to evidence page    │
│    → CTA band #2                                           │
├────────────────────────────────────────────────────────────┤
│ 5. WHAT ANCHOR IS DESIGNED TO CHANGE (benefits as          │  0 decisions
│    measurable design goals, §11 metrics)                   │
├────────────────────────────────────────────────────────────┤
│ 6. HOW IT WORKS: Capture → Today → Weekly Reset            │  0 decisions
│    + Comeback Mode callout → CTA band #3                   │
├────────────────────────────────────────────────────────────┤
│ 7. PRODUCTS: 3 visible tiers (Free kit · Money System ·    │  ≤3 decisions
│    Life OS) + quiet "see all kits" disclosure              │
├────────────────────────────────────────────────────────────┤
│ 8. TESTIMONIALS: 3 [PLACEHOLDER] blocks (hidden at launch) │  0 decisions
├────────────────────────────────────────────────────────────┤
│ 9. GUARANTEE: 30-day friction-free refund                  │  0 decisions
├────────────────────────────────────────────────────────────┤
│ 10. FAQ: 10 questions, accordion → CTA band #4 (final)     │  0–1 decisions
├────────────────────────────────────────────────────────────┤
│ 11. FOOTER: full disclosure block, crisis-resources        │
│     pointer, contact, privacy, unsubscribe promise         │
└────────────────────────────────────────────────────────────┘
```

**Whitespace and decision-load rules:** max content width ~680 px for text; min 96 px vertical padding between sections; one idea per viewport on desktop. Total interactive choices above the products section: the CTA, the evidence-page link, and nav. Nothing else is clickable.

**Mobile-order note:** section order is unchanged on mobile (the argument *is* the order). Adaptations: micro-nav collapses to logo + CTA button only; the hero visual moves below the CTA; evidence cards become an accordion (first card open, five collapsed); tier cards stack with the free kit first; FAQ is fully collapsed; a slim sticky bottom bar with the single CTA appears after 50% scroll and hides when the products section is in view (so it never competes with the purchase buttons). No popups, no exit-intent modals, ever.

**Objection-to-section map** (internal; personas in §4 below): every persona's top objection must be answered *on the page*, not just in FAQ. The map in §4 is the QA checklist for that.

---

## 3. The page, section by section

### 3.0 Micro-nav

> **Design annotation:** sticky, 56 px, three text links maximum plus the CTA button. No dropdowns, no mega-menu (Law 3: reduce decisions). Logo scrolls to top. "Evidence" anchors to section 4 — putting evidence in the nav is itself a trust signal.

**Copy:** `Anchor` · `Evidence` · `Products` · `[ Get the free First Action Kit ]`

---

### 3.1 Hero (a)

> **Design annotation:** one viewport. Left: headline (max 9 words), subhead (2 short sentences), one button, one line of trust microcopy, one line of disclosure microcopy. Right (below on mobile): product visual. Nothing else. Zero secondary links. The visitor's single decision: take the kit or keep scrolling.

**Headline candidates:**

1. **"A planner that expects you to miss days."** *(chosen)*
2. "You don't need more willpower. You need a place to put things."
3. "Your memory shouldn't have to live in your head."

**Rationale for #1:** it leads with the market's real, evidence-documented failure point — abandonment, the central design bottleneck (only 29% finished all modules in one strong digital trial <!-- [Kenter-2023] -->; engagement decayed in another <!-- [FOCUS-2023] -->). It promises a *design property we fully control* (forgiveness, Law 7 [Lally-2010]) rather than an outcome we can't promise (§10). And it disarms the #1 objection ("I'll quit this too") in the first second. Candidates 2 and 3 test well as Law 1/Law 4 framings; keep them for A/B rotation — all three are §10-clean.

> **Evidence:** T2 [Lally-2010] [KimCastelli-2021]; abandonment evidence [Kenter-2023] [FOCUS-2023] · **Confidence:** Moderate · **Rationale:** forgiveness-first positioning matches the strongest documented pain and makes no outcome claim. · **Expected outcome:** higher opt-in among planner-abandoners; lower "this is more hype" bounce. · **Downside:** less aspirational than competitor copy; may underperform with first-time planner buyers. · **Difficulty:** Low · **Priority:** High

**Copy:**

# A planner that expects you to miss days.

Anchor is a set of simple systems — planner, money, routines — designed around organization and planning strategies tested in randomized trials with adults with ADHD. <!-- [Safren-2010] [Solanto-2010] [attexis-2026] -->

Missed days don't reset anything. Comeback Mode is built in.

**[ Get the free First Action Kit ]**

*A 2-minute first win, then one short, useful email a week. Unsubscribe in one click, no guilt trip.*

*Anchor is a self-help organization tool — not therapy, not a treatment for ADHD, and not a replacement for diagnosis, medication, or professional care.*

**Hero visual description:** a calm, real screenshot of the **Anchor Daily Board** on a laptop with a phone beside it. Visible: "Today" with **Now / Next / Later** columns, exactly three committed tasks, the single next action highlighted, and a small, friendly **Comeback Mode** button in the corner. Muted two-color palette, big type, obvious whitespace — deliberately *boring-calm*, the visual opposite of dashboard clutter. No charts, no badges, no streaks (there are none in the product). Alt text: "Anchor Daily Board showing three tasks under Now, Next, and Later, with one next action highlighted."

---

### 3.2 Problem section (b)

> **Design annotation:** validation, not pain-poking. Short lines, generous spacing, second person. The ADHD-tax figures are presented as *shared reality* ("this is common and documented"), never as fear. Per §1.3 rule, the [Swedish-Registry] suicide association does not appear here or anywhere in sales copy; the registry study is used only for its "money problems compound over time" finding, stated gently. No red colors, no alarm icons.

**Copy:**

## If you've abandoned five planners, you're in the right place.

The notebook from January. The app with the streak you lost in March. The spreadsheet you built at 1am and never opened again.

That's not a character flaw. That's a pattern — and it has a mechanism.

Then there's what the ADHD community calls the **ADHD tax**: the late fees, the expired groceries, the subscription you meant to cancel, the rush shipping because it's due tomorrow.

It's not just you, and it's not in your head:

- In case-control research, adults with ADHD report **more debt, less saving, and more impulse buying** than comparison adults. <!-- [Bangma-2019] -->
- In a 27-year longitudinal study, adults with ADHD saved about **3–4% of income; the comparison group saved about 11%**. <!-- [Barkley-2008] -->
- A population study of millions of adults' credit records found that money problems linked to ADHD tend to **build up over the years, not fade** — starting from a level playing field in early adulthood. <!-- [Swedish-Registry] -->

None of this means you're doomed. It means the usual advice — "just be more disciplined" — was never aimed at the real problem.

---

### 3.3 "Why planners fail you" (c)

> **Design annotation:** the intellectual heart of the page: a mechanism story in three beats, then the honesty box. The honesty box is visually distinct (bordered, headed "What no planner company tells you") — it should look like a label, not a banner ad. This section carries the page's credibility; do not compress it.

**Copy:**

## Why planners keep failing you

Most planners are built on a hidden assumption: **that you'll remember to look at them.**

They assume the remembering, the starting, and the deciding all work fine — and just need a prettier container. For ADHD brains, *those are exactly the parts that struggle.* Remembering to act at the right moment (researchers call it prospective memory), getting started, and choosing the next thing.

Here's the part that surprises people: **knowing what to do was never your problem.** In a review of 201 studies, financial education explained about **0.1%** of actual money behavior — and what little it changed faded within months. <!-- [Fernandes-2014] --> Knowledge isn't the bottleneck. Follow-through is.

So Anchor doesn't try to teach you discipline. It's built to *hold things for you*:

- **Capture** everything the moment it appears, so your head doesn't have to hold it.
- **Cue** you toward one small action you already decided on — not a vague nag.
- **One next action** on every screen. Never a wall of undone things.

**What no planner company tells you**

> No planner — including ours — has ever been tested head-to-head against a plain spreadsheet in a clinical trial. Not one such trial exists. <!-- §5 of our evidence foundation -->
>
> The trials that do exist tested *structured skills programs* (calendars, task lists, task breakdown, weekly review), live and digital. Those worked. Anchor is built from those ingredients — that's an honest design bet, not a proven product.
>
> Why tell you this? Because you've been burned by confident claims before. We'd rather earn a smaller promise than sell a bigger one. Every feature in Anchor carries an evidence label. We call them **Evidence Notes**.

---

### 3.4 Evidence section: "What the research actually shows" (d)

> **Design annotation:** six cards, two rows of three (accordion on mobile, first card open). Each card = plain-language study line, a one-line honest takeaway, and a tier chip using §3 language. Chips are neutral-colored — tier labels are information, not badges. Below the grid: one link to the public evidence page and CTA band #2. This section exists to *earn* the CTA, so the CTA band directly follows it.

**Copy:**

## What the research actually shows

Short version: structured skills systems are well supported. Specific apps and templates — anyone's — are not. Here's the honest picture.

**Card 1 — Organization skills, taught as a system, work.**
In a randomized trial with 88 adults with ADHD, a 12-week program teaching time management, organization, and planning beat supportive therapy — on blinded ratings. People who did the between-session practice improved most. <!-- [Solanto-2010] -->
*Takeaway: the skills Anchor scaffolds are the best-tested part of this whole field.*
`Tier: Clinically supported (T1) — for the program, not any product.`

**Card 2 — A calendar plus one task list is the tested core.**
In a randomized trial with 86 adults already on medication, 12 sessions built around a calendar-and-task-list system, task breakdown, and "write it down, come back to it" beat relaxation training — 67% responded versus 33%. <!-- [Safren-2010] -->
*Takeaway: the boring tools, used consistently, are the active ingredient.*
`Tier: Clinically supported (T1) — package and named components.`

**Card 3 — Digital delivery can carry those ingredients.**
A 337-person randomized trial of a fully self-guided digital CBT program (2026) found a large improvement in ADHD symptoms at 3 months versus usual care, still present at 6 months. Caveats we won't hide: outcomes were self-reported, and the study had a sponsor conflict. <!-- [attexis-2026] -->
*Takeaway: self-guided digital tools can work — with honest caveats attached.*
`Tier: Clinically supported (T1) — digital package.`

**Card 4 — The real enemy is abandonment.**
In a 120-person trial of a self-guided online ADHD program, symptoms improved — but **only 29% of people finished every module**. <!-- [Kenter-2023] -->
*Takeaway: starting isn't the hard part. That's why Anchor is designed around lapses, not against them.*
`Tier: Clinically supported (T1) — with the adherence warning we build for.`

**Card 5 — The components that carry weight are unglamorous.**
A component-level analysis across CBT trials for ADHD found **organizational strategies** and **problem-solving (breaking tasks down)** were the elements linked to better response. <!-- [Matsumoto-2024] -->
*Takeaway: not colors, not gamification — task breakdown and organization routines.*
`Tier: Clinically supported (T1) — component-level, interpreted with care.`

**Card 6 — Offloading memory to the outside world works.**
A meta-analysis (general population, not ADHD-specific) found that moving intentions out of your head into external reminders reliably improves follow-through — most of all for *remembering to do things later*, the exact thing ADHD makes hard. <!-- [Offloading-2025] -->
*Takeaway: the "external brain" idea is solid science — tested broadly, not yet in ADHD-specific trials.*
`Tier: Moderately supported (T2) — indirect for ADHD, and we say so.`

**Below the cards:**

Want the whole picture, including the studies that *don't* flatter us — null results on reminders, brain training, and chatbots?

→ **Read the public Evidence Notes page.** Every claim, every tier label, every caveat.

> **CTA band #2 — Copy:**
> **Start with the free First Action Kit.**
> One page, one 2-minute action, no setup.
> **[ Get the free First Action Kit ]**

---

### 3.5 Benefits as design goals (e)

> **Design annotation:** this is the §10-safe replacement for a classic "benefits" section. Frame: *what Anchor is designed to change, and how we check ourselves* — the §11 functional metrics in plain words. Each row = design goal + how it's measured. The explicit "we measure, we don't promise" line does double duty as compliance and differentiation. No checkmark-icon promises, no before/after imagery.

**Copy:**

## What Anchor is designed to change

Not vibes. Not "productivity." Specific, checkable things. These are **design goals we measure with volunteer users — not promised results.**

| Designed to change | How we check ourselves |
|---|---|
| Bills paid on time | On-time bills out of total, self-logged by volunteers |
| Late fees and overdrafts | Count per month, self-logged |
| Savings transfers that actually happen | Planned vs. completed |
| Tasks finished without the overwhelm | Done vs. committed on the Anchor Daily Board — with commitments capped at 3 a day *by design* |
| A weekly 15-minute reset that survives real life | Share of weeks with a completed Weekly Reset |
| Coming back after you disappear for a while | Our signature number: how many people return within 14 days of a week-plus lapse |

If we ever prove these in a proper trial, we'll say so loudly. Until then, you get honesty: the design is evidence-informed; the results are yours to test — with a 30-day guarantee so testing is free.

---

### 3.6 How it works (f)

> **Design annotation:** three numbered steps, one line of copy each plus 2–3 supporting lines; horizontal on desktop, stacked on mobile. Each step names the §8 workflow it maps to. The Comeback Mode callout sits directly beneath in a soft-colored box — it is the emotional payoff of the hero promise. CTA band #3 follows.

**Copy:**

## How Anchor works

**1. Capture — get it out of your head.**
Everything goes into **The Inbox** the second it appears. No folders, no tags, no filing decisions. Capture now, organize later — or never.

**2. Today — see only what matters now.**
The **Anchor Daily Board** shows Now / Next / Later and **one next action**. You commit to 3 things a day, maximum. The rest waits quietly where you put it.

**3. Reset — 15 guided minutes a week.**
**The Weekly Reset** is a short checklist ritual: clear the Inbox, pick the week's few priorities, done. In the research, the people who kept a review habit like this were the ones who improved. <!-- [Solanto-2010] -->

**⟲ And when you disappear for two weeks?**

**Comeback Mode.** One screen, one button. It archives the backlog, resets Today to zero, and asks you for exactly one next action. No guilt screen, no broken streak — there are no streaks. Missing days is in the plan, because that's how real habits form: in a habit-formation study, missing a single day made no real difference in the long run. <!-- [Lally-2010] -->

> **CTA band #3 — Copy:**
> **Try the 2-minute version first. Free.**
> **[ Get the free First Action Kit ]**

---

### 3.7 Products (g)

> **Design annotation:** exactly **three visible choices** — free kit, core money product (secondary conversion), flagship. The full ladder (four minis at $9–19, Everything Bundle, Anchor Lab membership) lives behind one quiet text link ("See all the small kits"), keeping first-glance choice count at 3. Middle card (Anchor Money System) gets subtle visual emphasis as the default paid pick. Each paid card carries its own Evidence Notes line and the guarantee. Purchase buttons appear here and nowhere else on the page.

> **Evidence:** T2 [IyengarLepper-2000] [Jachimowicz-2019] · **Confidence:** Moderate · **Rationale:** in the classic field experiment, 6 choices sold to 30% of stoppers vs. 3% with 24 choices — choice overload is real, and our audience is selected for decision fatigue; a highlighted default further lowers decision cost. · **Expected outcome:** less pricing-page paralysis; more completed checkouts among ready buyers. · **Downside:** minis get less discovery; bundle upsell deferred to email/receipt flows. · **Difficulty:** Low · **Priority:** High

**Copy:**

## Start free. Add pieces only if they earn it.

**First Action Kit — Free**
One page. One 2-minute action. The capture habit that everything else builds on.
Plus one short, useful email a week (**The External Brain**). Leave anytime, one click.
**[ Get the free kit ]**

**Anchor Money System — $39** *(most people start here)*
The ADHD money workflow: a stepwise paycheck-and-bills routine plus a simple dashboard. Notion and spreadsheet editions included.
Built around cue → one pre-decided action (like: payday → move one amount). Designed against the ADHD tax; honest that **no budgeting tool — ours included — has proven financial outcomes in ADHD trials yet**. Evidence Notes inside.
30-day friction-free guarantee.
**[ Get the Money System ]**

**Anchor Life OS — $79**
The full external brain: planner, money, routines, and home base in one connected Notion system. The Inbox, Anchor Daily Board, The Weekly Reset, and Comeback Mode throughout.
30-day friction-free guarantee.
**[ Get Anchor Life OS ]**

*Want something smaller? See all the small kits ($9–19: Weekly Reset Kit, Daily Board Lite, Anchor Routines, Anchor Home Base), the Everything Bundle, and the Anchor Lab membership ($8/mo) →*

---

### 3.8 Testimonials (h)

> **Design annotation:** three quote cards, name + first-initial + context, no stock photos. **This section ships hidden** until three real, written-permission quotes exist. Never fabricate, never paraphrase, never use "as seen on" theater. Each card is paired with the typicality disclaimer, which renders on-page (small but legible, adjacent to the quotes — not buried in the footer).

**Copy (structure only — all three are placeholders):**

## What people tell us

> [PLACEHOLDER — Real customer quote #1, verbatim, with written permission on file. Selection rule: an ordinary-experience quote (e.g., "the Weekly Reset finally stuck"), not a best-case outlier. No financial-outcome claims unless the customer's own logged data supports them and the quote still carries the disclaimer.]
> — [First name L., context, e.g., "diagnosed at 34"]

> [PLACEHOLDER — Real customer quote #2, verbatim, permissioned. Prefer a Comeback Mode story: abandoned it, came back, still using it.]
> — [First name L., context]

> [PLACEHOLDER — Real customer quote #3, verbatim, permissioned. Prefer a money-workflow quote about *behavior* ("bills have a day now"), not results ("saved $X") .]
> — [First name L., context]

**On-page compliance note (renders with the quotes):**
*These are individual experiences shared with permission — not typical results, and not a promise of yours. Anchor is a self-help organization tool, not a treatment. We don't pay for testimonials, and we edit only for length.*

---

### 3.9 Guarantee (k)

> **Design annotation:** plain box, no badge clip-art. The guarantee is stated as policy *and* as philosophy — it exists partly because our audience is more vulnerable to impulse purchases, and we'd rather absorb that risk than exploit it. That reasoning is written on the page; saying it is the trust move.

> **Evidence:** T2/T3 rationale from problem evidence [Einarsson-2024] [DelayDiscounting-Meta] · **Confidence:** Moderate · **Rationale:** adults with ADHD show more impulse buying and steeper delay discounting; a friction-free refund converts an exploitable trait into a protected one, aligning incentives with Law 10. · **Expected outcome:** lower purchase anxiety, higher long-run trust; refund rate is a quality signal we track, not suppress. · **Downside:** some refund abuse; accepted as cost of honesty. · **Difficulty:** Low · **Priority:** High

**Copy:**

## The 30-day friction-free guarantee

Buy anything. Use it, or don't manage to — we know how that goes, and it's covered either way.

Within 30 days, one email gets you a full refund. No form, no exit interview, no "quick call." You even keep the free kit.

Why so easy? Because ADHD brains are more prone to impulse purchases — that's documented, not a stereotype. <!-- [Einarsson-2024] --> Most companies profit from that. We'd rather you keep your money than keep a product you don't use. If that costs us some refunds, it's the right cost.

---

### 3.10 FAQ (i)

> **Design annotation:** accordion, all collapsed by default (mobile and desktop), one open at a time. Order = trust questions first, logistics last. Questions are written the way people actually ask them, including the hard ones. CTA band #4 (final) follows the FAQ.

**Copy:**

## Honest questions, honest answers

**Is this therapy or a treatment for ADHD?**
No. Anchor products are self-help organization tools — not medical devices, not therapy, not treatment. They don't diagnose anything and they don't replace medication, therapy, or a clinician's advice. Many people use tools like these *alongside* professional care.

**Do I need an ADHD diagnosis to use this?**
No. Anchor is designed around adult-ADHD research, but it's just a set of organization systems. If you struggle with follow-through, you're welcome here — diagnosed, self-suspecting, or neither. Nothing in Anchor tells you whether you have ADHD.

**What if I abandon it like everything else?**
We assume you will, at some point — the best study on this found only 29% of people finished a well-made program. <!-- [Kenter-2023] --> So lapsing is designed for: no streaks to lose, momentum counted weekly instead, and **Comeback Mode** to restart in one tap. In habit research, missing a day didn't derail people; quitting after the *guilt* did. <!-- [Lally-2010] --> And if it truly doesn't fit: 30 days, full refund, one email.

**Why should I trust you? Every ADHD app says it's science-based.**
A systematic review found **109 ADHD apps — none with proof of effectiveness**. <!-- [Pasarelu-2020] --> We can't claim proof either, so we do the next honest thing: every feature carries an **Evidence Notes** label (clinically supported / moderately supported / experimental), and we publish what we *refuse* to claim — no "clinically proven," no "rewires your brain," no "guaranteed savings," no "21-day habit." If a claim of ours can't be traced to a study, we call it a design bet.

**Has Anchor itself been tested in a trial?**
No — and neither has any planner or budgeting template on the market, against a spreadsheet or anything else. Anchor is *built from* components tested in randomized trials with adults with ADHD <!-- [Safren-2010] [Solanto-2010] [Matsumoto-2024] -->, and we run voluntary outcome tracking with users who opt in. When we have product-level results, we'll publish them — favorable or not.

**Do I need Notion? Does it cost extra?**
Most Anchor systems run on Notion's **free plan** (phone, tablet, desktop). The Anchor Money System also includes a **spreadsheet edition** (Google Sheets / Excel) if Notion isn't your thing. Setup guides assume zero Notion experience.

**How long does setup take? I've died in setup before.**
The First Action Kit: about 2 minutes. Paid systems: one guided evening, with everything pre-filled with sensible defaults — you change things later, only if you want. Defaults doing the work is a design principle here, not laziness. <!-- [Jachimowicz-2019] -->

**Does this work with medication? Without it?**
It's independent of medication — it's an organization system, not a health intervention. For what it's worth, the skills research includes trials with medicated adults <!-- [Safren-2010] --> and unmedicated ones. Medication decisions belong with you and your clinician; we make no claims there.

**Is my data private?**
Yes, structurally: templates live in *your* Notion workspace or *your* spreadsheet. We never see your tasks, your accounts, or your numbers. Outcome tracking is opt-in, self-reported, and anonymized.

**Is there an app?**
Not yet. Today Anchor is templates + guides, honestly priced for what they are. A standalone app (bank feeds, smart cues) is on the long-term roadmap — we won't sell it before it exists.

> **CTA band #4 (final) — Copy:**
> **Your head was never meant to be the filing cabinet.**
> Start with the free First Action Kit: one page, one 2-minute win.
> **[ Get the free First Action Kit ]**

---

### 3.11 Objection handling mapped to personas (j)

> **Design annotation (internal QA, not a rendered section):** the page must answer each persona's core objection *in body copy*, with FAQ as backup. Persona labels below are working names — sync with the persona doc before publication. This table is the pre-launch checklist.

| Persona (working name) | Core objection | Answered where | The load-bearing line |
|---|---|---|---|
| **The Serial Restarter** (bought 5+ planners, expects to fail) | "I'll abandon this too, and it'll be my fault again." | Hero; §3.6 Comeback callout; FAQ #3 | "A planner that expects you to miss days." |
| **The Skeptical Researcher** (late-diagnosed, reads studies, allergic to hype) | "Templates are snake oil with a neuroscience sticker." | §3.3 honesty box; §3.4 cards; FAQ #4–5 | "No planner — including ours — has ever been tested head-to-head against a spreadsheet." |
| **The Money-Stressed Avoider** (unopened bank app, ADHD-tax bleed) | "Budget tools just make me feel worse about myself." | §3.2 (validation, gentle stats); §3.7 Money System card | "The usual advice — 'just be more disciplined' — was never aimed at the real problem." |
| **The Overloaded Professional/Parent** (no bandwidth for another system) | "I don't have the time or energy to set this up." | §3.6 steps; FAQ #7 | "About 2 minutes… one guided evening, everything pre-filled." |
| **The Impulse Buyer** (buys tonight, regrets Friday) | (Unvoiced — needs protection, not persuasion) | §3.9 guarantee; no urgency anywhere on page | "We'd rather you keep your money than keep a product you don't use." |

---

### 3.12 Footer disclosure block (l)

> **Design annotation:** full-width, quiet, genuinely legible (min 14 px, real contrast — the disclosure is content, not decoration). Four short blocks: what Anchor is/isn't; evidence honesty; support resources; housekeeping. The crisis pointer is a standing element of the footer — calm, brief, and always present, because some of our visitors arrive in financial distress.

**Copy:**

**What Anchor is — and isn't.** Anchor products are self-help organization tools. They are **not** medical devices, therapy, or treatment for ADHD or any condition, and they are **not** a substitute for diagnosis, medication, therapy, or financial advice from qualified professionals. If ADHD is making life heavy, a clinician is the right first stop — these tools can sit alongside that care, not replace it.

**About our evidence claims.** Anchor is designed around strategies tested in randomized trials with adults with ADHD. Anchor itself has not been trial-tested, and no similar product has either. Every feature's evidence level is published on our Evidence Notes page — including the experimental ones and the studies that found nulls.

**If things feel heavy right now.** Money stress and ADHD can pile up. If you're struggling, you deserve real support, not a template: talk to someone you trust, a clinician, or a free helpline — **findahelpline.com** lists free, confidential lines worldwide (in the US, call or text **988**). Nonprofit credit-counseling services offer free first sessions for debt stress.

**Housekeeping.** 30-day friction-free refunds · Contact: [support email] · Privacy: we don't see your data; templates live in your accounts · Emails: one useful email a week, one-click unsubscribe, honored instantly · [Company name, physical address] · © [year]

---

## 4. Pre-publication compliance pass (§10 self-audit)

| Check | Status |
|---|---|
| No "clinically proven [product]" anywhere | Pass — closest phrasing is "designed around strategies tested in randomized trials," §10-allowed |
| No outcome promises (symptoms, money, habits) | Pass — benefits framed as measured design goals (§3.5); guarantee promises a *refund*, not results |
| No urgency/scarcity theater | Pass — no countdowns, no "3 left," no exit popups; guarantee invites slower decisions |
| No shame hooks | Pass — problem section validates; "not a character flaw" framing throughout |
| Not-a-treatment disclosure | Pass — hero microcopy + FAQ #1 + footer block |
| Suicide association excluded from sales copy | Pass — [Swedish-Registry] used only for the compounding finding; rule documented in §1.3 |
| Testimonials placeholder-only, typicality note adjacent | Pass — §3.8; section hidden until permissioned quotes exist |
| T2/T3 claims labeled indirect/experimental in adjacent copy | Pass — card 6 says "not ADHD-specific"; Money System card admits unproven financial outcomes |
| Every study reference traceable to §4 registry | Pass — inline `<!-- [key] -->` annotations throughout |
| Reading level ≈ grade 7, scannable | Pass — short sentences; headers carry the argument; tables/cards over paragraphs |

---

*Previous: [08 — Notion Strategy](08-notion-strategy.md) · Next: [10 — Email Marketing](10-email-marketing.md) · Full index in [README](README.md).*
