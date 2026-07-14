# 07 — Etsy Strategy

> **Status:** Draft for team review. Terminology, tiers, citation keys, and rulings follow [00 — Evidence Foundation](00-evidence-foundation.md) exactly; product names follow 00 §8 verbatim; all listing copy below passes 00 §10.
> **Scope:** Everything commercial about the Etsy channel — role, lineup, pricing, bundles, shop structure, images, listing template (with one fully worked listing), SEO, FAQs, delivery, reviews, and support. File and folder structure inside the downloads follows [04 — Information Architecture](04-information-architecture.md) §D.

**Executive summary.** Etsy is our discovery engine, not our home: buyers already search it for ADHD planners and budget templates, and we meet them there with a short, clearly differentiated ladder of products — four minis, two core systems, one flagship, one bundle — priced at a handful of legible price points ([IyengarLepper-2000] applied to our own shelf). Two things make this strategy unusual and both are deliberate. First, honesty as positioning: every listing carries an Evidence Notes section and image stating, in plain language, what is tested (the CBT-derived workflows inside), what is not (this template, any template, against a spreadsheet), and that nothing here is a treatment. Second, ethics as mechanics: our buyers are the population with documented impulsive-buying vulnerability [Bangma-2019] [Einarsson-2024], so we run no fake urgency, no inflated compare-at prices, one cross-sell per touchpoint, a standing "sleep on it" invitation, and a 30-day friction-free refund. One hard rule governs every keyword list in this file: **we never state Etsy search volumes, conversion rates, or revenue projections — all keywords are hypotheses to be validated with Etsy's own search bar and Search Analytics after launch.**

---

## A. The role of Etsy in the ecosystem

### A.1 What Etsy is for: discovery

Etsy is a search marketplace with existing buyer intent for exactly our categories (digital planners, budget templates, Notion templates, ADHD-specific organization tools). We treat it as a **discovery channel with built-in distribution**: it finds strangers who are already looking, handles payment and delivery, and lends early trust through reviews. It is the top of our ecosystem funnel (02 — Product Ecosystem), not the business itself.

What Etsy is explicitly **not** for: relationship ownership (Etsy owns the buyer relationship), recurring revenue (no subscriptions — Anchor Lab lives off-Etsy), or the free tier (Etsy has no free listings — the First Action Kit is delivered off-Etsy via email opt-in).

### A.2 Email capture: consent-first, value-first

Etsy's seller policy prohibits adding buyers to a marketing list without their consent, and we would not want to anyway. The capture mechanism is inside the product, not the transaction:

- The download's `0-START-HERE` PDF and the in-template START HERE page offer the **First Action Kit** and a short onboarding email course as an *optional, clearly labeled* opt-in ("get the free setup course by email — or don't; the PDF covers everything").
- The pitch for opting in is service ("we walk you through setup in three short emails"), never gated content: **everything the buyer paid for works without giving us an email address.**
- No pre-checked boxes, no "enter email to unlock," no dark patterns. One-click unsubscribe is stated at the point of opt-in.

> **Evidence:** T2 for the onboarding-course mechanism ([Selaskowski-2022] mobile homework transfer; [LivingSMART-2015] coached structuring beats self-serve) · **Confidence:** Moderate · **Rationale:** the email course is our only channel for the follow-up and practice-loop support the evidence says matters (Law 6), and consent-first is the only version of it compatible with our ethics and Etsy policy · **Expected outcome:** a meaningful share of buyers opt in and reach first use; the list becomes the platform-independence hedge (§A.4) · **Downside:** consent-first capture converts far fewer addresses than gating would; we accept that permanently · **Difficulty:** Low · **Priority:** High

### A.3 Fee and margin honesty

Planning numbers, stated so nobody discovers them in month three. **Verify all of these against Etsy's current published fee schedule before launch; they change.** As of writing, for a US shop: listing fee $0.20 per listing per 4 months; transaction fee 6.5% of the order total; payment processing approximately 3% + $0.25; Offsite Ads fee 15% on attributed orders (12% once trailing-12-month revenue passes Etsy's threshold) — mandatory participation below that threshold; currency conversion 2.5% where applicable. Etsy generally collects and remits VAT/sales tax on digital items in many jurisdictions on our behalf (verify per jurisdiction).

Worked arithmetic on our own hypothetical price (this is fee math, not a revenue projection): on a $39 Anchor Money System sale — transaction $2.54 + processing ~$1.42 + listing $0.20 ≈ **$34.8 net (~89%)**; if the order arrives via an Offsite Ad, subtract a further $5.85 → **~$29.0 net (~74%)**. Margins on digital goods remain excellent; the real costs are acquisition and support time.

### A.4 Platform dependence: the risks, said plainly

| Risk | Reality | Mitigation |
|---|---|---|
| Algorithm/search changes | Rankings can drop without notice or appeal | Email list from day one (§A.2); content channels (11); landing page (09) |
| Fee increases | Etsy has raised fees before; we price with headroom | Ladder priced on value, not at margin edge (§C) |
| Suspension/lockout | Accounts get suspended, sometimes in error; funds can be held | Off-Etsy delivery capability kept warm (09 landing page + payment processor); backups of all listings/assets |
| Copycats | Digital templates are trivially copied and undercut | Our moat is the evidence honesty layer, the voice, updates, and support — things a copied file does not carry |
| Review dependence | Early listings live or die on first reviews | §K: ethical review generation timed to the first win |
| Category policy drift | Rules for digital/AI-assisted goods keep evolving | Quarterly policy review; nothing in our listings depends on gray areas |

**Decision:** Etsy launches the ecosystem and remains a permanent storefront, but every buyer is invited (consensually) into channels we own, and by Phase 2 (02 — Product Ecosystem) the landing page must be able to carry the catalog alone if Etsy vanished tomorrow.

> **Evidence:** design rationale (T3); platform risk is business judgment, not clinical evidence · **Confidence:** High (that the risks exist), Low (on timing) · **Rationale:** single-channel dependence is the commercial version of the fragility we design against for users · **Expected outcome:** no single point of failure for distribution by Phase 2 · **Downside:** running parallel channels costs listing-maintenance time · **Difficulty:** Medium · **Priority:** High

---

## B. The lineup on Etsy, mapped to the product ladder

The canonical ladder (02 — Product Ecosystem) and its Etsy expression. The First Action Kit (free) and Anchor Lab ($8/mo membership) are off-Etsy by design; the Anchor App is future SaaS and never an Etsy listing.

| Rung | Product | Etsy price | Listing(s) | Notes |
|---|---|---|---|---|
| Mini | Daily Board Lite | $9 | 1 | Same build as the free First Action Kit tier (08 §J); $9 on Etsy because Etsy has no free listings |
| Mini | Weekly Reset Kit | $12 | 1 | Printable + Notion editions in one listing (same ritual, two formats) |
| Mini | Anchor Routines | $15 | 1 | Momentum, never streaks |
| Mini | Anchor Home Base | $15 | 1 | Shared household checklists + chore recurrence |
| Core | Anchor Planner | $34 | 1 | The Anchor Daily Board + The Weekly Reset + Comeback Mode as a standalone planner |
| Core | Anchor Money System | $39 | 2 | **Separate listings for the Notion edition and the Google Sheets edition** (distinct search intent; fewer variation decisions per listing) |
| Flagship | Anchor Life OS | $79 | 1 | The full six-database workspace (08) |
| Bundle | Everything Bundle | $119 | 1 | Every product above, both Money editions, all printables |

Per-product recommendation blocks:

**Daily Board Lite ($9).** The lowest-risk first purchase: The Inbox + a trimmed Tasks database + the Anchor Daily Board (Now / Next / Later) + capture button + a one-page reset checklist.
> **Evidence:** T1 for the task-list/decomposition core it carries ([Safren-2010], [Matsumoto-2024]); the Lite packaging itself is untested (T3) · **Confidence:** Moderate · **Rationale:** a $9 working sample of the core loop is the cheapest honest way for a skeptical buyer to test whether our approach fits their brain · **Expected outcome:** first-purchase entry point; upgrade path to Anchor Planner / Anchor Life OS · **Downside:** cannibalizes some Anchor Planner sales; acceptable, because a fitting $9 purchase beats a regretted $34 one · **Difficulty:** Low · **Priority:** High

**Weekly Reset Kit ($12).** The Weekly Reset as a printable pad + a minimal Notion page: the 5-step, 15-minute ritual with timeboxes.
> **Evidence:** T1 for review rituals as package components ([Solanto-2010] homework-completion correlation, [Safren-2010], [NICE-NG87] regular follow-up); the standalone kit format is T3 · **Confidence:** Moderate · **Rationale:** the ritual is our most defensible single artifact and the strongest leading indicator we can measure (00 §11 metric 5) · **Expected outcome:** buyers run a weekly review with a physical or digital scaffold · **Downside:** a ritual sold without the surrounding system may be used twice and dropped — the kit's own Comeback page addresses restart, but we do not pretend a PDF fixes adherence · **Difficulty:** Low · **Priority:** Medium

**Anchor Routines ($15).** Routine cards with weekly-frequency momentum, anchor cues ("after coffee"), and no streaks anywhere.
> **Evidence:** T2 ([Gollwitzer-2006] if-then cues d = 0.65; [Lally-2010] one miss ≠ failure; [Singh-2024] 2–5 months, morning/self-selected stronger); anti-streak design constraint from [KimCastelli-2021] · **Confidence:** Moderate · **Rationale:** externalized cues plus miss-tolerant metrics is the evidence-consistent version of a habit tracker · **Expected outcome:** routines survive missed days (momentum resumes instead of resetting) · **Downside:** buyers conditioned by streak apps may initially read "no streaks" as a missing feature; the Evidence Notes image explains why · **Difficulty:** Low · **Priority:** Medium

**Anchor Home Base ($15).** Household chores on cadence with rooms, a "ready, not overdue" model, and shared visibility.
> **Evidence:** T2/consensus ([UKAAN-2021] environmental structuring); cadence/forgiveness design from [Lally-2010]; packaging untested (T3) · **Confidence:** Low · **Rationale:** shared external structure moves household load out of working memory and out of arguments · **Expected outcome:** recurring chores get done on cadence without a household manager holding the list in their head · **Downside:** weakest evidence rung on the ladder; labeled accordingly · **Difficulty:** Low · **Priority:** Medium

**Anchor Planner ($34).** The daily/weekly planning core: Anchor Daily Board, The Inbox, task decomposition templates, The Weekly Reset, Comeback Mode.
> **Evidence:** T1 for the package it implements ([Safren-2010], [Solanto-2010], [Matsumoto-2024] organizational strategies OR 2.03); digital delivery of same ingredients T1 ([attexis-2026], [Kenter-2023]); this product as shipped is untested until Part 14 measurement · **Confidence:** Moderate · **Rationale:** this is the calendar/task-list spine the trials actually used, translated · **Expected outcome:** committed-≤3 daily planning plus a weekly review habit (metrics 4–5) · **Downside:** the planner category is Etsy's most crowded; differentiation rests on the honesty layer and Comeback Mode · **Difficulty:** Medium · **Priority:** High

**Anchor Money System ($39, two editions).** Stepwise paycheck/bill workflow + financial dashboard; Notion edition and Google Sheets edition sold as separate listings.
> **Evidence:** problem T1-documented ([Bangma-2019], [Barkley-2008], [Swedish-Registry], [Einarsson-2024]); solution unproven — no budgeting tool has outcome trials (00 §4D ruling); workflow scaffolds borrow T1 components ([Safren-2010] structure, [Gollwitzer-2006] cues) · **Confidence:** Moderate (need), Low (our effect) · **Rationale:** externalize bills, dates, and payday decisions so working memory never carries them (Law 1, Law 5) · **Expected outcome:** bills visible ≥7 days ahead; a repeatable payday routine (metrics 1–3) · **Downside:** we must sell a money product while stating no money outcome is proven — the Evidence Notes section carries that weight on every listing · **Difficulty:** Medium · **Priority:** High (this is the front door, §E)

**Anchor Life OS ($79).** The flagship six-database Notion workspace (08 — Notion Strategy).
> **Evidence:** T1 package translation ([Safren-2010], [Solanto-2010], [attexis-2026]); architecture choices T2/T3 per 04 · **Confidence:** Moderate · **Rationale:** one integrated system beats four disconnected ones for maintenance burden — fewer places to check is itself decision reduction (Law 3) · **Expected outcome:** the core workflows in one workspace; highest-LTV single purchase · **Downside:** big systems invite big setup stalls; the 2-minute START HERE wizard (08 §L) exists precisely for this · **Difficulty:** High · **Priority:** High

**Everything Bundle ($119).** Everything above, both Money editions, all printables.
> **Evidence:** commercial packaging (T3); bundle-overlap disclosure is an ethics requirement, not a nicety ([Bangma-2019] impulsive buying) · **Confidence:** Moderate · **Rationale:** one honest "just give me all of it" option, clearly cheaper than the sum ($203 → $119), with the overlap stated (Anchor Life OS already contains Daily Board, Weekly Reset, Routines, and Home systems) · **Expected outcome:** the natural landing spot for high-intent buyers; fewer multi-order support tangles · **Downside:** a $119 impulse purchase is exactly the failure mode our audience is vulnerable to — mitigated by §D's cooling-off mechanics and the 30-day refund · **Difficulty:** Low · **Priority:** Medium

---

## C. Pricing

### C.1 The ladder and its logic

Four price bands, few and clearly differentiated: **$9–15 minis · $34–39 core · $79 flagship · $119 bundle.** The choice-overload evidence we apply to users' screens applies to our own shelf: more differentiated-but-similar options produce more browsing and fewer decisions [IyengarLepper-2000]. So:

- **One price per rung meaning.** A buyer can reconstruct the ladder from prices alone: single ritual < single system < everything-planner < whole life < all of it.
- **Both Anchor Money System editions cost the same $39.** Choosing Notion vs Google Sheets should be a platform preference, never a value calculation.
- **No $X.99 theater.** Whole-dollar prices read calmer and more honest; this is brand voice expressed numerically (design rationale, untested).
- **Prices include the support cost of doing refunds properly** (§L). We priced headroom in rather than nickel-and-diming later.

### C.2 No fake anchoring

We never set an inflated "original" price so a strikethrough can flatter the real one. If an item has never sold at $59, it does not get a $59 compare-at. Etsy's sale mechanics display strikethroughs automatically during genuine sales — that is acceptable because it is true.

### C.3 Sale policy: real, rare, calendar-honest

- **2–4 sales per year maximum**: launch week, ADHD Awareness Month (October), New Year, and optionally one mid-year. Real discounts (15–25%) on real prices.
- Announced in advance to the email list; no surprise "24 hours only" theater, no countdown language in our copy, no "only 3 left" (a lie for digital goods, and illegal-adjacent in several jurisdictions).
- Rationale is ethical, not just aesthetic: steeper delay discounting and impulsive buying are documented in our audience [DelayDiscounting-Meta] [Bangma-2019] [Einarsson-2024]. Urgency mechanics would work — that is exactly why they are banned (00 §10).

> **Evidence:** T2 [IyengarLepper-2000] for few-differentiated-options; problem evidence [Bangma-2019], [Einarsson-2024], [DelayDiscounting-Meta] motivating the anti-urgency stance; specific price points are untested hypotheses (T3) · **Confidence:** Moderate · **Rationale:** a legible ladder converts by reducing the buyer's decision load; honesty about sales protects the exact population we serve · **Expected outcome:** buyers self-select the right rung; low regret-refund rate on sale purchases · **Downside:** we leave short-term revenue on the table versus urgency tactics, and price tests are slow without fake anchors · **Difficulty:** Low · **Priority:** High

---

## D. Bundles, upsells, cross-sells — and the cooling-off element

### D.1 Where cross-sells appear (one per touchpoint, never a wall)

| Touchpoint | What appears | Limit |
|---|---|---|
| Listing description | One "goes well with" line naming at most one other product + the Everything Bundle by exact listing name (Etsy surfaces same-shop items automatically; we do not paste link salads) | 1 named product |
| Post-purchase thank-you message (Etsy) | Thank you, START HERE pointer, support promise. **No upsell at all** — the moment after an impulse-prone purchase is not when we sell | 0 |
| Package-insert PDF ("What's next", inside the download) | The ladder shown honestly with overlap disclosure, one suggestion based on what they bought, the free First Action Kit / email course opt-in, and Anchor Lab mentioned once | 1 suggestion |
| Email course (if opted in) | Products mentioned only after the first-win email, only once per sequence | 1 per sequence |

### D.2 Ethical limits, stated as rules

Our buyers include people with documented impulsive-buying vulnerability and weaker gratification deferral [Bangma-2019] [Einarsson-2024]. Therefore: no time-limited bundle pressure; no "customers also bought" mimicry inside our own inserts; no upsell in the first 24 hours post-purchase; overlap between products always disclosed next to any bundle mention ("Anchor Life OS already includes most of the minis — do not buy both unless you want the standalone editions"); and every cross-sell sits within one screen's distance of the refund promise.

### D.3 The deliberate friction element: "Sleep on it" + the upgrade guarantee

Two mechanics that *remove* the rational pressure to buy now:

1. **The "sleep on it" line** appears verbatim in every listing, above the license line: *"Not sure yet? Favorite this listing and sleep on it. It will still be here tomorrow, at the same price."*
2. **The 30-day upgrade guarantee** appears in every mini and core listing's FAQ: *"If you buy any smaller Anchor product and upgrade to the Everything Bundle within 30 days, message us and we will refund what you already paid, off the bundle."* (Mechanically: a partial refund on the bundle order.) This deletes the fear that buying small now means overpaying later — the usual engine of impulse-upgrading.

> **Evidence:** T3 — deliberate friction/cool-down is experimental per 00 §6 ruling, mechanism-consistent with [DelayDiscounting-Meta] (immediacy pull) and problem evidence [Bangma-2019], [Einarsson-2024]; untested in ADHD as a commerce pattern · **Confidence:** Low · **Rationale:** if immediacy is the exploit, removing time pressure is the countermeasure — we make waiting costless and say so · **Expected outcome:** fewer regret purchases and refunds; trust that compounds into reviews and referrals · **Downside:** measurably lower same-session conversion and average order value; we accept this on purpose and will report it in Part 14 metrics rather than quietly reverse it · **Difficulty:** Low · **Priority:** High

---

## E. Shop structure and the front door

### E.1 Sections (few, plain, buyer-language)

Five shop sections, mirroring the ladder rather than our internal taxonomy: **Start Here** (Daily Board Lite, Weekly Reset Kit) · **Money** (both Anchor Money System editions) · **Planning & Daily** (Anchor Planner, Anchor Life OS) · **Routines & Home** (Anchor Routines, Anchor Home Base) · **Bundles** (Everything Bundle). Twenty sections are allowed; five is the point (Law 3).

### E.2 The front door: Anchor Money System

One listing gets the deepest SEO, image, and iteration investment: **Anchor Money System (Notion edition)**. Reasons: money searches carry the clearest pain and intent; the financial problem is our best-documented need [Bangma-2019] [Swedish-Registry] [Barkley-2008]; and the honesty positioning ("no budget tool is proven — here is what is") differentiates hardest exactly where competitors overclaim hardest. Daily Board Lite is the designated low-risk first purchase; featured listings order: Anchor Money System (Notion), Anchor Life OS, Everything Bundle, Daily Board Lite.

Shop announcement (one line, standing): *"Evidence-honest ADHD organization systems: we label what is tested, what is experimental, and we never promise outcomes. Start with the $9 Daily Board Lite if you are skeptical — that is what it is for."*

> **Evidence:** front-door choice is commercial judgment (T3) resting on problem evidence [Bangma-2019], [Swedish-Registry]; section minimalism T2 [IyengarLepper-2000] · **Confidence:** Low · **Rationale:** concentrate ranking effort where pain, intent, and our differentiation align · **Expected outcome:** one listing achieves ranking traction and tows the shop · **Downside:** if money-keyword competition proves brutal, the front door may need to become Anchor Planner — revisit after 90 days of Etsy Search Analytics · **Difficulty:** Low · **Priority:** High

---

## F. Product images: the 10-image sequence

Every listing uses the same 10-slot sequence plus the video slot. Our images must themselves pass the ADHD-friendly bar (06 — ADHD Design Checklist): one idea per image, large type, high contrast.

| # | Image | Content spec |
|---|---|---|
| 1 | Promise + who it's for | One headline (≤10 words, no outcome claim), one subline ("for adults with ADHD — no diagnosis needed"), one clean product visual. This is the search-results thumbnail: legible at 300 px |
| 2 | What's included | The complete contents as a visual checklist (≤7 items; if more, group) |
| 3 | Workflow: Anchor Daily Board | Real screenshot: Now / Next / Later, one next action visible |
| 4 | Workflow: capture → The Inbox | The zero-friction capture moment, phone-sized frame |
| 5 | Workflow: The Weekly Reset | The 5 steps with timeboxes; "15 minutes, once a week" |
| 6 | Workflow: Comeback Mode | The restart screen; caption "for when you disappear for two weeks — no guilt, no starting over" (product-specific slots 3–6 may swap in money views: next-14-days bills, Paycheck day checklist) |
| 7 | **Evidence Notes** | Plain-language tier labels: "Built on methods tested in randomized trials with adults with ADHD (the workflows). This template itself: not clinically tested. No template of any brand is. Not a treatment." This image is our differentiator and is never omitted or buried below slot 7 |
| 8 | Setup in 2 minutes | Three numbered steps: duplicate → follow START HERE → first win. Screenshot of the wizard |
| 9 | FAQ / compatibility | Free Notion plan works · phone + desktop · instant download · works without email signup |
| 10 | Guarantee + support | 30-day refund, friction-free · real-human support · free updates to this edition |
| Video | 15–30 s screen recording | The first win in real time: capture a thought, see it on the Anchor Daily Board. No music-driven hype cuts; calm pace |

**Readability specs (all images):** minimum text size ≥ 1/10 of image height for headlines, ≥ 1/20 for body; ≤ 12 words per image outside checklists; contrast ratio ≥ 4.5:1; one message per image; consistent template across the shop (same grid, palette, and type per 05 — UX Specification); real screenshots only — no mockups showing states the product cannot produce; export ≥ 2000 px on the short side and compose for Etsy's square search crop.

**Alt-text spec (every image, no exceptions):** one or two sentences, ≤ 200 characters; literal description first ("Screenshot of a Notion board with three columns labeled Now, Next, Later"), then at most one natural keyword phrase ("from an ADHD planner template"); never a keyword list. Examples — image 3: *"Notion task board with columns Now, Next and Later; the Now column holds a single task card with its two-minute first action."* Image 7: *"Text slide titled Evidence Notes explaining which parts of this ADHD template are research-based and which are experimental."*

> **Evidence:** T3 for image order and text-size rules (design rationale; no ADHD trials on listing imagery); T2 borrowed mechanism: fewer, clearer options and one-idea-per-screen ([IyengarLepper-2000]); the Evidence Notes slot implements 00 §10 mandatory disclosure · **Confidence:** Low · **Rationale:** the listing is the first screen of the product; if a buyer cannot parse our images, they will not parse our workspace · **Expected outcome:** buyers arrive pre-onboarded (they have already seen the Daily Board, Reset, and Comeback) and pre-informed (tier labels) · **Downside:** honest slide 7 may depress conversion versus competitors' "clinically proven" claims; that trade is the brand · **Difficulty:** Low · **Priority:** High

---

## G. Listing structure template — and one fully worked example

### G.1 Title formula

`[Buyer search phrase] for [platform] | [Product name] | [2–3 honest capability phrases] for [audience] | Digital Download` — ≤ 140 characters, front-load the highest-intent phrase, zero claims, readable aloud without embarrassment.

### G.2 Tag strategy (all 13, every listing)

Each tag ≤ 20 characters (Etsy's limit). Mix: 3–4 head-adjacent phrases (also present in title), 5–6 long-tail variants, 2 audience/format tags, 1–2 rotating seasonal or test tags (§H.4). Multi-word phrases beat single words; no tag wasted on words Etsy attributes already cover (color, occasion).

### G.3 Description skeleton

1. **First 160 characters = the promise**, complete and honest (this is the search snippet).
2. What this is (2–3 sentences, plain).
3. What's inside (bulleted, ≤ 10 bullets).
4. How it works (3 numbered steps).
5. **Evidence Notes** (plain-language tier disclosure — the §10 block, always under this exact heading).
6. FAQ (the 5 most decision-relevant from §I).
7. Delivery, refunds, license.
8. The "sleep on it" line (§D.3).

### G.4 Worked example: Anchor Money System (Notion edition)

**Title (134 characters):**

```
ADHD Budget Template for Notion | Anchor Money System | Paycheck Routine, Bill Tracker & Money Dashboard for Adults | Digital Download
```

**13 tags (all ≤ 20 characters):**

```
adhd budget template · notion budget · adhd money planner · bill tracker adhd ·
adhd planner adults · notion template adhd · paycheck budget · money dashboard ·
executive function · adhd budget planner · bill pay checklist · adult adhd tools ·
finance template
```

**Attributes:** Digital download · Craft type: templates (fill all applicable attribute fields; attributes are free search surface).

**Full description:**

```
A calm, step-by-step money system for adults with ADHD: see every bill in one
place, run a short paycheck routine, and restart without shame after a bad month.

WHAT THIS IS
Anchor Money System is a Notion template (a Google Sheets edition is available
in a separate listing) that externalizes the money admin your working memory
keeps dropping: which bills exist, what is on autopay, what is due in the next
two weeks, and exactly what to do on payday. You do not have to become a
spreadsheet person. You follow one short checklist at a time.

WHAT'S INSIDE
- Bills & Money Events database: every bill, subscription, and paycheck with
  amount, due date, autopay flag, and a days-until-due countdown
- Next 14 Days view: one glance, no digging
- Paycheck day checklist: a fixed-order routine you repeat every payday
  (confirm deposit, pay what is due before next paycheck, move one pre-decided
  savings transfer, set your spending number)
- Subscription audit view with monthly-equivalent costs, so quiet money leaks
  become visible
- The Weekly Reset money glance: a 2-minute step inside a 15-minute weekly review
- Comeback Mode: a one-page restart for after a skipped month. No guilt, no
  starting over
- START HERE guide: first win in about 2 minutes, sample data pre-filled so you
  can see it working, then clear the samples with one click
- Video walkthrough (about 10 minutes)

HOW IT WORKS
1. Duplicate the template to your Notion account (the free plan is enough - we
   show you how, about 2 minutes)
2. Add your real bills in one 10-minute sitting, or explore with the sample
   data first
3. On payday, open the Paycheck day checklist and follow it top to bottom

EVIDENCE NOTES (the honest part - please read)
- The workflows inside (structured checklists, task breakdown, a weekly review
  ritual) are built on organization and planning methods tested in randomized
  trials with adults with ADHD.
- This specific template has not been clinically tested. No planner or budget
  tool of any brand has been proven better than a plain spreadsheet in a
  head-to-head trial. Anyone who implies otherwise is marketing at you.
- Research clearly documents that adults with ADHD face real, measurable money
  challenges. Research has not yet proven that any tool fixes them. We label
  every feature honestly, and we are measuring our own products.
- We promise a calmer system, not an outcome. No savings or debt results are
  guaranteed.

FAQ
Is this therapy or a medical product? No. This is a self-help organization
tool. It does not diagnose or treat ADHD, and it does not replace diagnosis,
medication, or therapy.
Do I need an ADHD diagnosis to use it? No. If bills keep surprising you, this
was built for the way your weeks actually go.
Do I need to pay for Notion? No. The free personal plan is enough.
What if I have bought planners before and stopped using them? So has nearly
everyone we build for - research on digital self-help programs shows most
people do not finish them. That is why this system is built around a
15-minute weekly reset, a 2-minute first step, and a shame-free restart page.
What if it is not for me? 30-day refund, no questions asked. Message us and we
will sort it, and you can keep the download.

DELIVERY, REFUNDS, LICENSE
Instant digital download: one PDF containing your template link, the START
HERE guide, and the video walkthrough. Nothing ships. 30-day refund policy as
above. License: personal and household use - please do not resell or
redistribute.

Not sure yet? Favorite this listing and sleep on it. It will still be here
tomorrow, at the same price.
```

> **Evidence:** copy implements 00 §10 (allowed T1 phrasing, mandatory disclosure, no outcome promises); abandonment honesty grounded in [Kenter-2023] (29% module completion) without quoting stats at buyers; structure T3 design rationale · **Confidence:** Moderate · **Rationale:** the listing does the Evidence Notes work before purchase so no buyer can feel bait-and-switched after · **Expected outcome:** lower refund and negative-review rates; reviews referencing honesty · **Downside:** longer copy than category norm; the honest FAQ names our own category's failure mode out loud · **Difficulty:** Low · **Priority:** High

---

## H. SEO and keywords

### H.1 The hard rule, restated

**Every keyword below is a hypothesis, not a fact.** We do not know its search volume, click-through, or conversion, and this document will not pretend to. Validation loop after launch: Etsy search-bar autocomplete (what Etsy suggests is what gets typed) → Etsy Search Analytics (which queries actually delivered visits/orders to *our* listings) → quarterly tag rotation, changing 1–2 tags per listing at a time so cause stays readable.

### H.2 Long-tail keyword families (hypotheses to validate)

| Family | Example phrases | Maps to | Notes |
|---|---|---|---|
| ADHD money | adhd budget template, adhd budget planner, adhd money management, bill tracker adhd, paycheck budget | Anchor Money System | Front-door family; clearest pain-to-product fit |
| ADHD planner | adhd planner, adult adhd planner, adhd digital planner, adhd daily planner, adhd planner notion | Anchor Planner, Anchor Life OS | Crowded; differentiation carried by images 1 and 7 |
| Notion generic | notion template, notion budget template, notion life os, notion dashboard | Anchor Life OS, Money (Notion) | High competition, weaker intent fit; secondary tags only |
| Executive function | executive function planner, executive dysfunction planner, adhd brain dump, brain dump template | Anchor Planner, Daily Board Lite | "Brain dump" maps directly to The Inbox; use it |
| Routines & home | adhd routine planner, habit tracker adhd, adhd cleaning checklist, cleaning schedule adhd | Anchor Routines, Anchor Home Base | "Habit tracker" is fine as a search phrase; the product page then explains momentum-not-streaks |
| Community language | dopamine menu, body doubling, doom pile | Content only (see H.3) | Traffic-rich, ethics-sensitive |

### H.3 When a popular term conflicts with our ethics: the "dopamine menu" ruling

"Dopamine menu" is beloved community shorthand for a pre-decided list of quick, rewarding activities. Two problems: the term smuggles in a neuro-claim ("this manipulates dopamine") that sits next to our banned vocabulary ("dopamine hack," neuroscience-as-halo, 00 §10), and no product of ours contains a tested artifact by that name (the underlying idea — pre-decided low-friction options — is mechanism-plausible at best, T3).

**Ruling:** we do not name products after it and do not put it in product tags to harvest its traffic — that would be keyword-stuffing a claim we refuse to make. We address it where honesty has room to breathe: educational content (11 — Content Strategy; a piece explaining what the community means by it, what the evidence actually says, and how a pre-decided options list maps to implementation intentions [Gollwitzer-2006], labeled T2/T3). If we ever ship such an artifact inside Anchor Routines, it ships under a plain name ("Quick wins menu"), labeled experimental in Evidence Notes — and only then may the tag be tested. Same test applies to future community terms: **borrow the language only where we ship the honest version of the thing.**

### H.4 Buyer-intent mapping and seasonal moments

Intent mapping: problem-aware searches ("adhd can't pay bills on time" — mostly off-Etsy, content's job) → solution-aware ("adhd budget template" — Etsy's sweet spot, front door) → product-aware ("anchor money system notion" — brand searches, protect with consistent naming). Etsy effort concentrates on solution-aware phrases; content (11) catches problem-aware and refers in.

| Moment | Window | What we do | What we refuse |
|---|---|---|---|
| New Year | Dec 26 – Jan 15 | Seasonal tags ("2027 planner adhd"), one real sale, copy theme "new year, same brain, kinder system" | "New year new you" shame framing; resolution-failure fear copy |
| ADHD Awareness Month | October | Education-forward content push, Evidence Notes featured in images/copy, one real sale, awareness framing | Claiming charity affiliation we do not have; awareness-washing |
| Back-to-school | Aug 15 – Sep 15 | Rotate tags toward "college adhd planner" where honest — the coached-college evidence exists ([ACCESS-2021], college students, d = 0.39–1.21) | Marketing to parents of children (we are adults-only, 01 — Product Vision) |
| Tax season (US) | Feb – Apr | Money-system content tie-ins ("find every subscription before tax time") | Any implication of tax or financial advice |

All seasonal activity inherits §C.3: pre-announced, real discounts, no countdowns, no scarcity.

> **Evidence:** keyword families are untested hypotheses (T3 commercial); seasonal-ethics constraints implement 00 §10; college framing bounded by [ACCESS-2021] · **Confidence:** Low · **Rationale:** search phrases are the one place buyer language and our honesty rules can collide, so the collision rule is written down · **Expected outcome:** tag set converges on measured winners within 2–3 rotation cycles · **Downside:** refusing "dopamine menu" style tags cedes real traffic to less scrupulous shops; we will measure what it costs and keep receipts · **Difficulty:** Low · **Priority:** Medium

---

## I. The shared FAQ blocks

Exact reusable copy. Each listing carries the 5 most relevant; the full set lives in the support macros (§L) and on the landing page (09).

**Is this therapy or a medical product?**
No. This is a self-help organization tool. It does not diagnose or treat ADHD, and it does not replace diagnosis, medication, or therapy. If you are struggling, a clinician is the right first stop — this can sit alongside whatever care looks like for you.

**Do I need an ADHD diagnosis to use it?**
No. Nothing here checks your paperwork. If bills, tasks, and time keep slipping, it was built for the way your weeks actually go.

**Do I need to pay for Notion?**
No. The free personal Notion plan is enough. You will duplicate the template into your own workspace, so your data stays yours — we never see it.

**Which edition should I pick, Notion or Google Sheets?**
Pick the tool you already open. The workflows are identical; only the container differs. If you have never used either, Notion is the richer experience and the walkthrough assumes no prior knowledge.

**Is this a printable?**
The Weekly Reset Kit includes a printable edition. Everything else is a digital workspace template; printables are noted per listing.

**What if I have bought planners before and stopped using them?**
So has nearly everyone we build for — research on digital self-help programs shows most people do not finish them. That is why the first step takes 2 minutes, the weekly ritual takes 15, and there is a shame-free restart page (we call it Comeback Mode) instead of a graveyard of guilt.

**How do I get the files?**
Instant download after purchase: one PDF containing your template link, the START HERE guide, and the video walkthrough. Etsy also keeps your files in your account under Purchases, so you can re-download anytime — including future updates.

**Do I get updates?**
Yes. Updates to your edition are free: re-download from your Etsy Purchases page. The template's Changelog page explains what changed and how to bring updates into an existing setup.

**Can I share it with my partner or household?**
Yes — the license covers personal and household use. Please do not resell, redistribute, or post the template publicly.

**What is your refund policy?**
30 days, friction-free, no questions required. Message us "refund please" and it is done. You can even keep the download — we would rather lose a sale than have you feel trapped.

---

## J. Digital delivery and onboarding: designing against "bought but never opened"

### J.1 The failure mode is documented, so we design for it

Our audience's known pattern is not "buys the wrong thing" — it is "buys the right thing and never opens it." In the best digital-intervention trial conditions, only 29% of participants completed all modules [Kenter-2023], and engagement in a well-liked monitoring app declined within three months without moving the primary outcome [FOCUS-2023]. A purchased ZIP has none of a trial's supports. Every delivery decision below exists to shorten the distance from download to first win.

### J.2 What is inside the download

One door, not a pile (04 §D naming rules: numbered prefixes, no "Misc"):

- **`0-START-HERE.pdf`** — the only file a buyer must open. Page 1 contains exactly one action: the template link with "duplicate this — 2 minutes." Page 2: the 2-minute first win. Page 3: the optional email course opt-in + video walkthrough link. Page 4: Evidence Notes (tier labels, plain language) + support and refund promise + license.
- Product files as applicable (printable PDFs for kit items; the Google Sheets edition ships its copy link the same way).
- **`Evidence-Notes.pdf`** — the honesty layer as a standalone, shareable one-pager.

Where Etsy's file caps force a choice, everything routes through the single START-HERE PDF rather than shipping five loose files: one file means zero "which file do I open" decisions (Law 3).

### J.3 The onboarding path (first win ≤ 2 minutes)

1. Purchase → Etsy's thank-you message: warm, one pointer ("open 0-START-HERE.pdf — your first win takes 2 minutes"), no upsell (§D.1).
2. START-HERE page 1 → duplicate template. Page 2 → first win: capture one real thought into The Inbox and see it on the Anchor Daily Board (08 §L specifies the in-template wizard, sample data, and one-click sample clearing).
3. Optional email course (10 — Email Marketing owns the copy): day 0 deliver + first win; day 2 one pre-decided action ("add your three real bills — 10 minutes"); day 7 The Weekly Reset invitation; day 14 a no-shame Comeback nudge for the silent. Each email = one cue → one pre-decided small action (Law 5, [Gollwitzer-2006]) — because reminder blasts alone demonstrably do not move adherence ([Nordby-2022]).
4. The product itself carries the rest: the wizard, the ritual, Comeback Mode.

> **Evidence:** T1/T2 for the mechanism mix (structured first steps [Safren-2010]; cue→pre-decided action [Gollwitzer-2006] under the [Nordby-2022] constraint; defaults/pre-fills [Jachimowicz-2019]); the abandonment problem itself is documented ([Kenter-2023], [FOCUS-2023]); this specific delivery design is untested (T3) · **Confidence:** Moderate · **Rationale:** the purchase is the moment of maximum motivation and minimum structure; the single-door PDF and 2-minute win spend that motivation before it evaporates · **Expected outcome:** measurably higher opened-and-duplicated rate (Part 14 voluntary panel), fewer "never opened it" refunds · **Downside:** one-door delivery irritates the minority who want raw files immediately; page 1 links them straight through · **Difficulty:** Medium · **Priority:** High

---

## K. Review generation — ethical and Etsy-compliant

- **Never incentivized.** No discounts, freebies, entries, or upgrades for reviews (Etsy policy and our own). No review gating ("happy? review us / unhappy? email us" filtering is manipulative and banned).
- **Timed to the first win, not the purchase.** A review request at purchase asks people to review their optimism. Ours rides the day-7 email, after The Weekly Reset invitation: *"If the first week helped even a little, a review helps another brain like yours find this. If it has not helped yet, reply instead — we would rather fix it than be rated."* One ask per buyer, ever; buyers who never opt into email are never chased (the in-template START HERE final step carries the same single soft ask).
- **Negative reviews: validate, fix, update.** Public seller response within 48 hours, one message: name what is true in the complaint ("you are right that step 3 was confusing"), state the fix and its version ("clarified in v2026.08 — re-download from Purchases"), offer the refund plainly. Never defensive, never clinical, never a debate. Review themes feed the changelog (14 — Continuous Improvement); a complaint that recurs twice is a product bug, not a customer problem.

> **Evidence:** T3 (commercial design rationale); the first-win timing borrows the honest logic of Law 10 — rate the function, not the unboxing · **Confidence:** Low · **Rationale:** reviews earned after real use select for durable satisfaction and describe the product accurately to the next buyer · **Expected outcome:** slower review accumulation, higher review truthfulness; public repair behavior becomes marketing · **Downside:** competitors gathering day-1 excitement reviews will out-pace our count early · **Difficulty:** Low · **Priority:** Medium

---

## L. Customer support and refunds

### L.1 Canned responses that never shame

Support macros ship with the shop from day one. House rules: no "as clearly stated in the listing," no "did you read the instructions," no exclamation-point cheer over someone's frustration. Four core macros, verbatim:

**"I can't open / find the file."**
*"Happy to help — this trips up more people than you would think, and it is not just you. On the Etsy app or site, go to You → Purchases and look for the Download button next to your order. Open the file called 0-START-HERE — it is the only one you need. If the button is not showing or anything else is odd, tell me what device you are on and I will sort it from my end."*

**"This is not working for me / I'm overwhelmed by it."**
*"Thank you for telling me — genuinely. Two options, both fine: if you want to try the smallest possible version, do just page 2 of the START HERE guide (2 minutes) and ignore absolutely everything else for a week. If you are done with it, say the word 'refund' and I will process it today, no questions and no hard feelings. Tools have to fit brains, not the other way around."*

**"I accidentally bought twice / bought the wrong edition."**
*"Easily fixed — I have refunded the duplicate (you will see it within a few days, depending on your bank). Keep whichever edition suits you. If you meant to grab the other edition, tell me and I will make sure you are set up with the right one."*

**"Refund please."**
*"Done — processed today, and you are welcome to keep the download. If you ever feel like telling me what did not fit, one line helps me build better, but it is truly optional. Take care."*

### L.2 Refund policy: 30 days, friction-free

Etsy digital-goods norms allow "no refunds"; we do the opposite, prominently. **Policy: any reason, 30 days, no questions required, keep the files.**

Rationale, in order: (1) we sell to a population with documented impulsive buying [Bangma-2019] [Einarsson-2024] — a friction-free exit is the ethical backstop for every purchase our anti-urgency design did not prevent; (2) risk-reversal honestly earned — we refuse outcome promises (00 §10), so the guarantee is the only "proof" we will sell with; (3) commercially sane — digital marginal cost is zero, and a granted refund converts a likely 1-star review into a survivable goodbye; (4) it keeps us honest — refund reasons are Part 14 telemetry we cannot get anywhere else.

Abuse: expected, small, tolerated. If serial-refund patterns appear, we handle the pattern quietly (per-account limits), never by adding friction for everyone.

> **Evidence:** T3 commercial design; ethical grounding in problem evidence [Bangma-2019], [Einarsson-2024]; no trial evidence exists on refund-policy effects in this population and we will not imply any · **Confidence:** Moderate · **Rationale:** the refund policy is the purchase-side expression of Comeback Mode — leaving must be as shame-free as lapsing · **Expected outcome:** higher trust-to-purchase conversion among skeptics; refund rate becomes a product-quality metric we publish to ourselves (Part 14) · **Downside:** measurably more refunds than a no-refunds shop; margin already accounts for it (§C.1) · **Difficulty:** Low · **Priority:** High

---

*Previous: [06 — ADHD Design Checklist](06-adhd-design-checklist.md) · Next: [08 — Notion Strategy](08-notion-strategy.md) · Full index in [README](README.md).*
