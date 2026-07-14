# 14 — Continuous Improvement System

**Executive summary.** The evidence base under this blueprint is young, package-level, and moving — the field's own umbrella review rates its quality as low, with roughly 30% of its included reviews reporting adverse effects [LopezCampos-2025], and the strongest trials are recent and unreplicated at component level. So this ecosystem ships with a maintenance system for its *claims*, not just its templates: a quarterly literature scan with explicit registry-entry criteria, a re-grading workflow that can promote a T3 to T2 or demote a T2 to T4 with full changelog and downstream propagation, product versioning with free updates and Notion migration notes, a feature-retirement process, a privacy-respecting measurement panel (templates never spy), an ADHD-adjusted user-testing protocol, a staged pathway toward the preregistered RCT all four source reviews call for, ethics rules for future app analytics, a clinical-partnership pathway, and an annual public State of the Evidence report. The through-line: we promised to label evidence honestly; this document is how the labels stay true over time.

---

## 1. Reading new literature: the quarterly evidence scan

**Cadence.** Monthly: skim saved database alerts (~15 minutes; flag, don't analyze). Quarterly: formal screen and a 90-minute review meeting with registry decisions. Annually: deep re-read of the whole registry feeding the State of the Evidence report (§10).

**Where we look.** PubMed/MEDLINE, PsycINFO, and the Cochrane Library for published evidence; ClinicalTrials.gov and equivalent international registries for preregistrations (these feed a watchlist of results to expect, e.g., any registered body-doubling trial); PROSPERO for systematic-review protocols; citation alerts on the foundation §4 anchor studies so follow-ups and corrections surface automatically.

**Standing queries** (adapt syntax per database):

- **Q1 — core interventions:** ("ADHD" OR "attention deficit hyperactivity disorder") AND (adult*) AND (randomized OR randomised OR "controlled trial" OR "meta-analysis") AND (digital OR app OR smartphone OR internet OR web-based) AND ("executive function" OR "time management" OR organization OR organisation OR planning)
- **Q2 — money:** ("ADHD") AND (adult*) AND (financial OR money OR debt OR spending OR budgeting OR "delay discounting")
- **Q3 — T2 anchor refresh (meta-analyses only):** "implementation intentions"; "cognitive offloading"; "habit formation"; "choice overload"; "default effect"
- **Q4 — T3 watchlist:** "body doubling"; ADHD "visual timer"; ADHD adult gamification; ADHD chatbot OR "conversational agent" OR "AI coach"

**What qualifies for the registry** (a candidate must clear all six):

1. **Population:** adults ≥18. Diagnosed ADHD preferred; self-report samples enter with an explicit caveat, exactly as [Kenter-2023] carries one.
2. **Design:** RCT, systematic review, or meta-analysis for any *intervention* claim. Longitudinal, registry, and case-control studies qualify for *problem* evidence. HCI, survey, and qualitative work enters at T3 ceiling.
3. **Outcomes:** functional or validated symptom measures. Engagement-only outcomes never qualify a study as intervention evidence — the [FOCUS-2023] lesson (adopted and liked, primary outcome null).
4. **Peer-reviewed.** Preprints may enter flagged "provisional — preprint," re-checked the following quarter, and may not upgrade any tier while provisional.
5. **Extractable effects:** effect sizes with confidence intervals reported or computable.
6. **Conflicts recorded:** sponsor involvement noted in the registry entry, as we did for [attexis-2026].

Child-only studies cap at T3 (the [Hallez-2024] precedent). Vendor blogs, app-store copy, and press releases never qualify — that is the [Pasarelu-2020] swamp we exist to stay out of.

**Who reviews.** The evidence lead screens titles/abstracts and drafts registry entries; a second reader verifies extraction and tier; disagreements resolve to the conservative reading (foundation prime directive); the advisory clinicians (§9) are consulted on clinical interpretation. Every quarter logs counts — found, screened, added, excluded and why — even when the answer is "nothing new," because "we looked and found nothing" is itself a finding worth recording.

**Quarterly scan log template:**

```
Quarter:            2026-Q3
Queries run:        Q1–Q4 (dates per database)
Hits / screened:    412 / 37 full-text
Added to registry:  1 ([NewKey-YYYY], T2, §4E) — or "none"
Watchlist changes:  +1 registered body-doubling RCT (results est. 2027)
Excluded, notable:  2 child-only RCTs (T3 ceiling rule); 1 vendor white paper
Reviewers:          [evidence lead] / [second reader]; disagreements: 0
```

---

## 2. Updating the evidence foundation: re-grading workflow

Tiers move on evidence, in both directions. All changes land in `00-evidence-foundation.md` through this workflow — never by silent edit.

**Promotion and demotion rules:**

| Move | Trigger | Worked example |
|---|---|---|
| T3 → T2 | One adequately powered adult-ADHD RCT with functional outcomes supports the feature | The body-doubling case: today it is T3, community-endorsed, no RCTs [BodyDoubling-HCI]. If a preregistered adult-ADHD RCT with objective task-completion outcomes reports benefit, body doubling is re-graded T2 with confidence Low ("single study") and the foundation §6 conflict ruling is updated |
| T2 → T1 | The component is isolated in adult-ADHD RCT(s) or component-level meta-analysis (the [Matsumoto-2024] standard) | If-then cues would move from [Gollwitzer-2006]-based T2 to T1 only after an adult-ADHD trial isolates them |
| T2 → T4 | Adult-ADHD trials return null/negative for the mechanism *as deployed* | The precedent already in the registry: generic reminders sit at T4 standalone because direct trials were null ([Nordby-2022], [FOCUS-2023]) despite positive indirect SMS evidence [SMS-Meta-2023] |
| T1 confidence revision | New meta shrinks effects (e.g., stronger active-control comparisons, per [Knouse-2017] and [Nasri-2023]) | Tier may hold while confidence drops and copy softens; the change is still logged and propagated |

Single positive studies promote **one tier maximum**. T1 requires the tier definition in foundation §3 to be met on its face — no enthusiasm shortcuts. New citation keys enter foundation §4 in the registry's format (key, study, finding, tier) via §1's qualification bar.

**Changelog rules for `00-evidence-foundation.md`:**

- Append-only, dated changelog section; entries never rewritten after publication.
- Each entry: date · foundation version · what changed (key added / tier changed, shown as old → new / ruling changed) · why, in one sentence with the triggering key · downstream documents affected.
- Two-person sign-off (evidence lead + second reader), same as registry entry.
- Tier changes also update the foundation §6 conflict table when they resolve or create a divergence.

Example entry:

```
### 2027-03-14 — foundation v1.2
- Added [Hypothetical-2027] to §4E: preregistered adult-ADHD RCT of scheduled
  co-working, task completion improved (details in entry).
- Re-graded: body doubling T3 → T2 (single study; confidence Low).
- §6 ruling "Body doubling" updated; divergence with source reviews resolved.
- Downstream: Parts 06 (item keys), 13 (§2 phrasing, Evidence Notes), product
  copy sweep opened (30-day clock).
Signed: [evidence lead], [second reader]
```

**Downstream product-update triggers** (the clock starts at changelog publication):

| Event | Required action | Deadline |
|---|---|---|
| Any tier change | Update every Evidence Note citing the key | 14 days |
| Any tier change | Sweep marketing surfaces; demotions handled as Part 13 §7 Class B corrections | 30 days |
| Demotion to T4 | Open a feature-retirement review (§4) | 30 days |
| Promotion | Copy may strengthen only after Part 13 §7 re-review; roadmap consideration for deeper investment | Next release |
| New problem-evidence key | Content/editorial review for accuracy opportunities | Next quarter |

---

## 3. Product version control

**Semver for templates and spreadsheets — MAJOR.MINOR.PATCH:**

- **MAJOR — the workflow changes.** Users must relearn or restructure something: Weekly Reset steps change, the Money System paycheck flow is resequenced, a database schema is reorganized.
- **MINOR — a new optional module.** Added capability, off by default, ignorable forever: an Anchor Routines board added to Anchor Life OS, an optional debt-snowball view in the Money System.
- **PATCH — copy and fixes.** Wording, formula bugs, broken links, Evidence Note updates after §2 events.

**Changelogs shipped to buyers.** Every release ships a plain-language changelog with exactly three fields: *What changed* · *Why* (including "the evidence moved" when that is the reason, with the key) · *What you need to do* (usually "nothing"). No internal jargon, no tier codes without their plain-language gloss.

Example (Anchor Money System v2.1.0):

```
What changed:      A new optional "debt snapshot" view. Off by default.
Why:               Lab-panel members asked to see balances and next payments
                   in one place; it passed the Part 06 review in June.
What you need to do: Nothing. If you want it: Settings → add view →
                   Debt snapshot (about 2 minutes, steps below).
```

**Free updates policy.** All updates to a purchased product — including MAJOR — are free for the life of that product line. Charging for evidence-driven corrections would bill the people who trusted us for our own learning. A genuinely different product is sold as a different product; an upgrade toll on the same promise is not.

**Migration notes for Notion duplicates.** A duplicated Notion template is the user's own snapshot; it cannot auto-update, and it should not (see §5 — no code reaching into user copies). Therefore every MINOR and MAJOR ships with: a "What's new" page inside the template; a step-numbered migration note of ten minutes or less ("add this property, drag this view, paste this block"); and an explicit "keep what you have" path — skipping an upgrade never breaks an old copy. This is Law 7 applied to versioning: a user three versions behind is a user in good standing. Spreadsheet editions follow the same pattern with a fresh download plus a copy-in-your-data block.

---

## 4. Feature retirement

Features leave the ecosystem the way they entered: on evidence and observed behavior.

**Criteria** (any one opens a retirement review; two make retirement the default):

1. Evidence demoted to T4 in §2.
2. Panel data (§5) shows an abandonment spike, refund pattern, or harm reports attributable to the feature.
3. User testing (§6) repeatedly shows overwhelm or checklist failures (Part 06) traceable to the feature.
4. Maintenance burden is crowding out the core workflows the evidence actually supports.

**Process:**

1. **Review memo:** the evidence, the data, the options (fix, simplify, retire), one page.
2. **Decision logged** with the §2 changelog if evidence-driven.
3. **Sunset comms:** buyer email plus an in-template deprecation note, in plain language, stating the real reason — "the evidence didn't hold up; here's what we changed" is a complete sentence and we use it.
4. **Grace period:** 90 days with the feature marked deprecated, functional, and non-punitive.
5. **Removal from new sales and current templates.** Existing user copies keep working untouched — we never reach into them.
6. **Recorded** in the annual State of the Evidence report (§10).

**Sunset email skeleton:**

```
Subject: We're retiring [feature] — here's the honest why

We built [feature] labeled experimental. The evidence has moved: [one plain
sentence + key, e.g., "a randomized trial found no benefit"]. So we're
retiring it rather than keeping it because it looks good on a listing.

Your copy keeps working — nothing breaks, nothing to do. From [date], new
versions won't include it. What we recommend instead: [one alternative].
Full reasoning: this year's State of the Evidence report.
```

**Tone rule:** a retirement announcement gets the same care as a launch. Publicly removing something because the evidence moved is the cheapest credibility we will ever buy — and it is also simply the deal we offered.

---

## 5. Evidence monitoring dashboard (privacy first)

The foundation §11 canonical metrics, made real — with the instrumentation honesty stated up front: **templates can't and shouldn't spy.** Notion templates, spreadsheets, and printables ship with no pixels, no scripts, no hidden telemetry of any kind. In most cases that is technically infeasible anyway; in all cases it would be wrong for a product whose core promise is being safe to think inside. Every number below comes from people who chose to tell us.

**Data sources (all opt-in, all revocable):**

1. **Monthly check-in survey:** ~2 minutes, the same 8 questions every month, one-tap answers, sent by email to subscribers who opted in.
2. **Anchor Lab panel:** consented, compensated members completing a deeper quarterly survey and occasional interviews; also the recruiting pool for §6 testing.
3. **Self-score card:** an optional in-template month card users fill for themselves and may paste into the survey if they wish — self-tracking first, research contribution second.

**Metric → instrument map (targets from foundation §11):**

| §11 metric | Instrument | Cadence | Benchmark / target |
|---|---|---|---|
| Bill-payment timeliness (on-time / total) | Check-in survey self-log | Monthly | Establish baseline year 1 |
| Late fees + overdrafts count | Check-in survey self-log | Monthly | Directional decline |
| Savings-transfer completion (planned vs executed) | Check-in survey | Monthly | Establish baseline |
| Daily Board task completion (done / committed ≤3) | Self-score card + survey | Monthly | Establish baseline |
| Weekly Reset completion | Survey + panel | Monthly | ≥50% of active weeks |
| Retention at weeks 4 / 12 / 26 | Panel | Quarterly | >40% using any core workflow at week 12 — vs the field's 29% full-completion benchmark [Kenter-2023] and month-3 engagement decay [FOCUS-2023] |
| **Comeback Rate** (return within 14 days after a ≥7-day lapse) | Panel | Quarterly | Signature metric — report from year 1 |
| QoL / functioning self-check (AAQoL/WSAS-style spirit, framed as self-tracking) | Quarterly panel survey | Quarterly | Directional; QoL evidence is mixed ([Cochrane-2018] vs [attexis-2026]) and we say so |

**Privacy and honesty rules:** aggregate-only reporting with small cells suppressed (n<10); raw responses retained no longer than 24 months; deletion on request; data never sold or shared for advertising. And the statistical honesty: an opt-in panel self-selects toward engaged users, so all numbers are directional, benchmarked with that bias named, and **never** quoted in marketing as outcome claims (Part 13 §3).

> **Evidence:** Governance implementing Law 10; benchmarks from T1-package adherence data [Kenter-2023], [FOCUS-2023]; check-in survey format is design rationale (no direct evidence that surveys don't distort) · **Confidence:** Moderate · **Rationale:** without consented functional measurement we cannot know whether the ecosystem works, and the field's history is engagement mistaken for benefit. · **Expected outcome:** a truthful, updating picture of bill timeliness, task completion, retention, and Comeback Rate against published benchmarks. · **Downside:** self-selected, self-reported data overstates success; low response rates may leave metrics underpowered. · **Difficulty:** Medium · **Priority:** High

---

## 6. User testing

**Per-release protocol (every MAJOR and MINOR):** 5–8 moderated sessions. The 5-to-8 figure is standard usability practice for surfacing major issues — industry craft knowledge, not clinical evidence, and we label it that way.

**ADHD-specific adjustments:**

- **Shorter sessions:** 30–45 minutes maximum, with an offered break; attention is the constraint we design for, so it is also the constraint we test within.
- **Real-task testing:** participants use their own actual tasks and bills (with privacy protections), or a realistic dummy set if they prefer — toy data hides real overwhelm.
- **Fair, immediate compensation:** paid same-day, no gift-card mazes.
- **Forgiving logistics (Law 7 applied to research ops):** pre-decided session time with a same-day one-tap reminder (Law 5 applied to ourselves); no-shows carry zero penalty and one-tap rebooking.
- **Recruiting beyond superfans:** mix of new and returning users, medicated and unmedicated, across ages and genders, from Anchor Lab plus outside channels — a panel of devotees cannot fail a test.
- **Plain-language consent and debrief**, recording optional.

**Core task set, every round:**

1. First run → first value (target: within one session, matching checklist item I1).
2. Capture five things while mid-task (items C1–C3).
3. Plan tomorrow on the Anchor Daily Board.
4. Complete The Weekly Reset unassisted.
5. **Lapse simulation — mandatory:** "It's been two weeks since you opened this. Open it and do whatever you'd naturally do." Pass = the participant lands in Comeback Mode and restarts with zero manual cleanup (checklist items R1/R2 observed in the wild, not just in review).

**Measures:** task success, time-to-first-value, single-question ease rating, self-reported overwhelm, first place their eyes went. Findings feed Part 06 checklist revisions, §4 retirement reviews, and release go/no-go.

**Quarterly unmoderated pulse:** a 5-task remote test (always including capture and the lapse simulation) between releases.

> **Evidence:** Protocol is design rationale plus governance; the lapse-simulation emphasis derives from abandonment being the documented bottleneck ([Kenter-2023], [FOCUS-2023], [KimCastelli-2021] decay) · **Confidence:** Moderate · **Rationale:** the failure mode that kills these tools appears at re-entry after a lapse, so testing must simulate the lapse, not just the honeymoon. · **Expected outcome:** overwhelm and recovery failures caught before ship; Comeback Mode validated against real behavior. · **Downside:** small samples miss issues; lab lapses are gentler than real ones. · **Difficulty:** Medium · **Priority:** High

---

## 7. RCT opportunities: the study we owe the field

All four source reviews converge on the same missing study, and the foundation states it twice (§2, §5): **no trial has ever compared an ADHD-specific planning/budgeting system against the spreadsheet and planner baseline it claims to beat.** Our positioning inherits that gap. The plan is to close it rather than talk around it.

**Target design (built with academic partners, not alone):**

- **Preregistered randomized controlled trial** in adults with confirmed ADHD.
- **Comparator:** an *active* baseline — a clean conventional spreadsheet/planner with equal onboarding attention — because waitlist controls flatter interventions ([Inflow-2026] used waitlist; [Knouse-2017] found smaller effects against active controls; [Nasri-2023] found iCBT no better than active relaxation).
- **Intervention:** the Anchor system as actually sold (Anchor Money System + Anchor Daily Board + The Weekly Reset), warts included.
- **Primary outcomes (objective, functional):** bill-payment timeliness (on-time / total) and task completion rate.
- **Secondary outcomes:** overdrafts and late fees, savings-transfer completion, retention and Comeback Rate, cognitive load and stress (validated self-report instruments selected with partners), quality of life and functional impairment in the AAQoL/WSAS spirit — answering the core-outcome call in [NimmoSmith-2020] and probing the functional-impairment gap [Inflow-2026] left open — plus adverse effects including compulsive-use signals [LopezCampos-2025].
- **Duration:** 12 weeks with a 6-month follow-up, aimed at the durability blind spot (foundation §5.5).

**Staged pathway:**

1. **Stage 1 — single-arm pilot, n≈20** (Anchor Lab volunteers, distinct consent): feasibility, instrument validation, adherence and harm signals. Pilot data supports design decisions only — it never appears in marketing (Part 13 §3), because a single-arm pilot cannot support an efficacy claim.
2. **Stage 2 — university partnership:** independent principal investigator, blinded outcome assessment where feasible, analysis plan owned by the academic team. We mirror the sponsor-conflict caveat we recorded on [attexis-2026] by keeping our hands off the analysis: we supply product access, instrumentation help, and funding contributions — not conclusions.
3. **Stage 3 — the preregistered RCT:** registered before first enrollment, primary outcomes locked, sample size powered by the partner statistician using §4B digital-package effects (d ≈ 0.4–0.85) as priors — which implies hundreds of participants, not dozens.

**Funding notes:** investigator-initiated grants through the partner university, ADHD research foundations, and small-business innovation research programs; our own contribution ring-fenced so publication is never contingent on results.

**Publish regardless of result.** That commitment is preregistered too. A null result re-grades our own tiers (§2), softens our own copy (Part 13 §7), and gets a featured section in the State of the Evidence report — not a burial. If our system cannot beat a clean spreadsheet, adults with ADHD deserve to know it, and so do we.

> **Evidence:** The gap is documented at T-consensus (foundation §2, §5.1); the design choices import T1-trial lessons ([Nasri-2023], [Inflow-2026], [Knouse-2017], [NimmoSmith-2020]) · **Confidence:** High that the study is needed; unknowable for the result — that is the point · **Rationale:** every superiority-flavored inference in this blueprint is mechanism-based until this trial exists. · **Expected outcome:** the first head-to-head evidence for or against an ADHD-specific system vs a spreadsheet baseline; honest re-grading either way. · **Downside:** expensive, slow, and it may show our product is no better than a spreadsheet — a result we have publicly pre-committed to publishing. · **Difficulty:** High · **Priority:** Medium (staged: pilot is near-term, RCT is a multi-year commitment)

---

## 8. Behavioral analytics ethics (future Anchor App)

The only tier of the ecosystem with real telemetry is the future Anchor App, and it inherits Law 10 wholesale: **measure function, not engagement.**

- **Metrics we build:** the §11 list — bills paid on time, tasks completed, Weekly Reset completion, retention, Comeback Rate, self-rated functioning.
- **Metrics we refuse:** DAU, session length, notification open rates, streak length. Time-in-app should trend *down* per unit of life managed; a rising session count is investigated as a possible harm, not celebrated as growth.
- **Experiments allowed:** A/B tests whose success metric is a §11 functional metric or an abandonment/recovery improvement (e.g., two Comeback Mode entry designs compared on Comeback Rate). Marketing-copy experiments follow Part 13 and score on qualified, refund-free outcomes — never raw clicks.
- **Experiments banned:** anything optimizing time-in-app, notification volume or opens, purchase impulsivity, or variable-reward mechanics. No engagement-maximizing experiment is ever "just a test" — with this audience it is a harm vector ([LopezCampos-2025]: adverse effects concentrated in compulsive-engagement formats; [DelayDiscounting-Meta]: heightened immediacy sensitivity).
- **Adverse-effect watch:** monitor for compulsive patterns — rapidly rising daily sessions, late-night checking spirals, panel-reported anxiety about the app. Response ladder: calm in-app de-escalation ("you're done for today" states), optional session caps, direct outreach for panel members, and design rollback if a feature is implicated. Never a win-back campaign aimed at someone the data says is overusing.
- **Consent defaults:** analytics **off by default** — opt-in at onboarding with granular, plain-language scopes; one-tap opt-out later; local-first storage where feasible; self-serve export and deletion; no third-party ad trackers; no data sales, ever.
- **Lapse communications:** one action-shaped return email after a long lapse ("one button archives your backlog — here it is"), then silence is respected. Guilt is not a re-engagement channel (Law 7).

---

## 9. Clinical partnership pathway

**Advisory clinicians.** A standing advisory relationship with at least one adult-ADHD psychiatrist or clinical psychologist and one occupational therapist — the OT consensus base [UKAAN-2021] and guideline framing [NICE-NG87] are the professional anchors for our workflow claims. Roles: sanity-check clinical adjacency in content, support Part 13 §7 claim review, help design §6 testing and §7 research, and triage any §8 adverse signals. Advisors are credited, compensated, and free to disagree in writing.

**The wellness / digital-therapeutic boundary.** The decision rule, applied before any new claim ships:

| If the claim says… | Lane | Requirement |
|---|---|---|
| "Organizes your bills, plans, tasks; holds your reminders; structures your week" | Wellness / self-help organization tool (current lane) | Part 13 rules; the mandatory disclosure block |
| "Reduces ADHD symptoms," "improves attention," "treats, mitigates, or helps manage ADHD" | Digital-therapeutic territory | Clinical trial evidence on our product **and** a regulatory strategy (medical-device-style pathway) **and** counsel plus regulatory-affairs review — before the claim is drafted, not after |

We stay in the wellness lane until evidence and regulatory clearance justify crossing — marketing enthusiasm is never a crossing criterion. Even a positive §7 RCT does not by itself authorize treatment language; it authorizes accurate research statements, reviewed under Part 13, while the regulatory question gets professional advice. (Good-practice framing, not legal advice; counsel review recommended, per Part 13 §8.)

**Crisis-adjacent content.** Anything touching debt crisis or despair follows Part 13 §5's signposting rule and is reviewed by the advisors — the [Swedish-Registry] association between financial distress and suicide risk is the standing reason this content class gets clinician eyes.

---

## 10. The annual "State of the Evidence" report

Once a year, publicly, we publish what moved — with a pre-committed outline so no section can quietly disappear in a bad year:

1. **Registry changes:** keys added, tiers re-graded (old → new), rulings changed, and why.
2. **Our numbers:** the §5 dashboard versus targets — including the misses, with the self-selection bias restated every single year.
3. **Features retired** and the evidence or data that retired them.
4. **Corrections issued:** Class A and B counts from Part 13 §7, with the material ones summarized.
5. **Research progress:** which §7 stage we are in, honestly.
6. **What we got wrong:** named, in plain language.
7. **Open questions** we intend to chase next year.

**Rules:** published every year even when unflattering; plain language; contains no marketing claims and passes Part 13 §7 review like everything else; drafted by the evidence lead, reviewed by the §9 advisors, released in Q1 for the prior year. The report is the ecosystem's public heartbeat — proof that "we label every feature's evidence level" is a practice, not a slogan.

---

*Previous: [13 — Ethical Marketing Framework](13-ethical-marketing-framework.md) · Canonical rules: [00 — Evidence Foundation](00-evidence-foundation.md) · Full index in [README](README.md).*
