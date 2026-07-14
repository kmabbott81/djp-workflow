# 06 — ADHD Design Checklist

**Executive summary.** This is the ship gate. Before any screen, Notion page, spreadsheet tab, printable, email, or listing goes out, a reviewer walks it through the questions below. Every item is a yes/no question tied to one of the Ten Design Laws in [00 — Evidence Foundation](00-evidence-foundation.md) §7 and a citation key from §4 — because the central, evidence-documented failure mode of tools for adults with ADHD is not that they lack features but that people abandon them ([Kenter-2023]: only 29% finished all modules; [FOCUS-2023]: engagement decayed and outcomes stayed null). Most abandonment drivers — decision overload, unclear first actions, working-memory taxes, punitive lapse handling, dishonest promises — are visible in an artifact *before* it ships. This checklist makes them reviewable.

---

## 1. How to use this checklist

**What it applies to.** Every user-facing artifact: app/Notion screens and views, spreadsheet tabs, printables, onboarding sequences, emails, Etsy/listing pages, and in-product copy. For non-screen artifacts, read "screen" as the visible unit: the fold of an email, the tab of a spreadsheet, the page of a printable, the first screenful of a listing.

**When.** Before first ship; after any MAJOR or MINOR version change (Part 14 versioning); whenever marketing copy on the artifact changes. PATCH-level copy fixes may be self-reviewed.

**Who.** A reviewer who did not build the artifact, wherever team size allows. The builder answers first; the reviewer verifies. Disagreements resolve conservatively (the stricter reading wins), per the foundation's prime directive.

**How to score.**

1. Answer every item **Pass / Fail / N-A**. N-A requires a one-line justification in the ship log (e.g., "email has no capture surface").
2. **[MUST] items: any single failure blocks ship.** No waivers. Fix it or don't ship it.
3. **[SHOULD] items: two or more failures block ship.** Exactly one failure may ship with a logged fix and a target date (next PATCH or MINOR).
4. Record in the ship log: artifact, version, date, reviewer, failures, N-A justifications, and any logged fix.
5. Count things literally. "Count the decisions" means: open the artifact as a new user and tally every point where the user must choose, name, configure, or recall something. Estimates in your head don't count; tallies do.

**How to count (so two reviewers get the same number):**

- **Decisions:** every point where the user must choose, name, configure, or recall something before proceeding. A default accepted without noticing = 0. A confirmation dialog = 1. A blank field with no suggestion = 1 decision plus 1 recall.
- **Elements above the fold:** each card, button, form field, header, navigation item, and badge counts as 1. A tight repeating list (e.g., task rows) counts as 1 element, plus 1 for each distinct interactive control inside a row.
- **Interactions (capture):** each tap, click, or focus change counts; typing the captured content itself counts as one interaction regardless of length.
- **First-action timing:** measured from opening the artifact in a new-user state, *including* reading time. If the user must read three paragraphs to find the action, the paragraphs are on the clock.

**On the numeric thresholds.** The *directions* below are evidence-anchored (fewer choices, smaller first actions, external memory, forgiveness). The specific numbers — ≤7 elements, ≤2 interactions, ≤2 minutes, ≤3 committed tasks — are house rules that make the laws reviewable. No study validates the numbers themselves; we state that plainly (no direct evidence) and hold them anyway, because an unreviewable rule ("keep it simple") protects no one.

**Ship log entry template:**

```
Artifact / version:      Anchor Daily Board v1.0 (Notion edition)
Date / reviewer:         2026-07-14 / [name, not the builder]
MUST results:            15 pass / 0 fail
SHOULD results:          22 pass / 1 fail / 1 N-A
Failures + fix-by:       T2 (committed-vs-available time) — v1.1, owner [name]
N-A justifications:      T3 — no timers shipped in this artifact
Decision:                SHIP / BLOCKED
```

> **Evidence:** Governance, anchored in T1-package abandonment evidence ([Kenter-2023], [FOCUS-2023]) and the Ten Design Laws (foundation §7); individual items carry their own keys · **Confidence:** Moderate · **Rationale:** most documented abandonment drivers are inspectable pre-ship, so a mandatory review converts the evidence base into a repeatable quality bar. · **Expected outcome:** fewer artifacts abandoned in week one; consistent law compliance across products and channels. · **Downside:** slower shipping, and checklist theater if items are ticked without literal counting. · **Difficulty:** Low · **Priority:** High

---

## 2. The checklist

Columns: gate ([MUST]/[SHOULD]) · the yes/no question · one-line pass criterion · law and evidence behind it. Bare section references (§3, §4, §6, §8, §10) point into [00 — Evidence Foundation](00-evidence-foundation.md); "Law N" means the Ten Design Laws in its §7.

### 2.1 Capture

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| C1 | [MUST] | Is capture ≤2 interactions? | From intent to captured thought in at most two user actions (open + type/write); no required fields beyond the content itself | Law 4 · [Offloading-2025] |
| C2 | [SHOULD] | Can the user capture without filing? | No category, tag, date, or destination is demanded at capture time; The Inbox accepts raw text | Law 4 · [Offloading-2025] |
| C3 | [SHOULD] | Is The Inbox reachable from every screen? | Capture entry point visible (or one gesture away) from any view of the product | Law 4 · [LivingSMART-2015] |

### 2.2 Decisions

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| D1 | [MUST] | Does this reduce decisions? Count them. | Tallied decision count is lower than the thing it replaces, and no screen asks more than 3 primary choices | Law 3 · [IyengarLepper-2000] (6 options → 30% purchase vs 24 → 3%) |
| D2 | [MUST] | Does this reduce overwhelm — elements above the fold ≤7? | Literal count of distinct elements (cards, buttons, fields, headers, badges) in the first screenful is ≤7 | Law 3 · house rule; rationale via [IyengarLepper-2000]; isolated visual simplification is T3 per §6 |
| D3 | [SHOULD] | Does every choice have a smart default? | Each option arrives pre-selected with the recommended value; user can accept-all and proceed | Law 3 · [Jachimowicz-2019] (default effect d = 0.68) |
| D4 | [SHOULD] | Is optional depth behind progressive disclosure? | Advanced settings, extra fields, and edge cases are collapsed by default and skippable forever | Law 3 · T3 as isolated feature per §6 ruling; rationale [IyengarLepper-2000] |

### 2.3 Initiation

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| I1 | [MUST] | Does this improve task initiation — is the first action ≤2 minutes and pre-decided? | A new user can see and complete a concrete first action within ~2 minutes without making a plan first | Law 2 · [Gollwitzer-2006] (if-then plans d = 0.65); [Safren-2010] |
| I2 | [MUST] | Does every screen resolve to one next action? | Each screen has exactly one clearly-primary "do this now" — not a menu of equally weighted possibilities | Law 2 · [Safren-2010], [Solanto-2010] |
| I3 | [SHOULD] | Is the next action the most visually prominent thing? | The next action outweighs status displays, stats, and navigation in size/contrast | Law 2 · house rule operationalizing [Safren-2010] |
| I4 | [SHOULD] | Are tasks decomposable into first action → next action → done criteria? | The task structure offers (not demands) breakdown fields, and examples model them | Law 2 · [Matsumoto-2024] (problem-solving iSMD 0.42), [Safren-2010] |

### 2.4 Memory

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| M1 | [MUST] | Does this reduce working-memory demands — is nothing remembered across screens? | Any value needed on screen B is displayed on screen B; the user never transports a number, name, or step in their head | Law 1 · [Offloading-2025] (offloading helps most for prospective memory) |
| M2 | [SHOULD] | Is all context visible at the point of action? | Amounts, due dates, account names, and instructions sit on the same screen as the button that uses them | Law 1 · [Offloading-2025] |
| M3 | [SHOULD] | Does the artifact hold state mid-flow? | Leaving mid-task and returning later loses nothing and re-explains nothing the system can remember for you | Law 1/7 · design rationale; no direct evidence |

### 2.5 Time

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| T1 | [MUST] | Is time made concrete — dates not "later," durations on tasks? | Every commitment shows a real date (or explicit "Later" parking lot) and every task carries a duration estimate field | Law 9 · [Solanto-2010], [Lauder-2024]; problem evidence [TimePerception-Review] |
| T2 | [SHOULD] | Is committed time visible against available time? | Today's view can show total committed minutes vs the hours actually available | Law 9 · [Solanto-2010] (time-management scaffolds are the T1 part) |
| T3 | [SHOULD] | Are timers/countdowns optional, off by default, and labeled experimental? | Any visual timer ships opt-in with an Evidence Note (child-study evidence only) | Law 9 · [Hallez-2024] is children; T3 widget per §6 ruling |

### 2.6 Follow-through

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| F1 | [MUST] | Does this improve follow-through — is every cue tied to a pre-decided action, and is a practice loop present? | Each reminder/cue names one specific pre-decided act, and the workflow includes a recurring practice ritual (e.g., feeds The Weekly Reset) | Laws 5/6 · [Gollwitzer-2006], [Solanto-2010] (homework completion correlated with gains); constraint [Nordby-2022] |
| F2 | [SHOULD] | Are there zero generic nags? | No notification, email, or banner says "check in," "don't forget your budget," or any action-free prompt | Law 5 · [Nordby-2022] (reminders alone: no adherence effect), [FOCUS-2023] |
| F3 | [SHOULD] | Does this artifact feed The Weekly Reset? | Whatever it tracks or captures surfaces automatically in the weekly review | Law 6 · [Solanto-2010], [NICE-NG87] (regular follow-up), [Selaskowski-2022] |
| F4 | [SHOULD] | Is the habit horizon honest? | Any habit-related copy or metric assumes 2–5 months to automaticity, never "21 days"; momentum metrics are weekly-frequency, not consecutive-day | Law 7 · [Singh-2024], [Lally-2010] (median 66 days) |

### 2.7 Recovery

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| R1 | [MUST] | Does this reduce abandonment — after a missed day/week, is there a Comeback path? | The artifact defines what the user sees after a lapse, and it is Comeback Mode (one screen, one button, archive the backlog) — not a pile of overdue items | Law 7 · [Lally-2010], [Kenter-2023] |
| R2 | [MUST] | Can a user recover after missing a week without manual cleanup? | Re-entry requires zero backfilling, zero re-dating, zero deleting; stale items age out or archive automatically | Law 7 · [Lally-2010] (one miss ≠ failure); abandonment evidence [Kenter-2023], [FOCUS-2023] |
| R3 | [SHOULD] | Is return copy forward-facing? | The first thing a returning user reads points forward ("here's today") and never counts missed days | Law 7 · [KimCastelli-2021] (punitive gamification decays/negative long-term) |
| R4 | [SHOULD] | Are progress metrics miss-tolerant? | Progress is shown as frequency ("3 of 7 days this week") per Anchor Routines, never as a breakable streak | Law 7 · [Lally-2010], [KimCastelli-2021] |

### 2.8 Emotion and shame

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| E1 | [MUST] | Does any element punish, shame, or use loss-framing? (must be NO) | Zero red walls of failure, broken-streak alerts, guilt copy, "you only did X," or losable points/badges | Law 7 · [KimCastelli-2021]; voice rules §8/§10 |
| E2 | [MUST] | Is the empty state a teaching moment? | Every empty view shows what belongs there, one example, and the ≤2-minute first action — never a blank grid or guilt prompt | Laws 2/3 · design rationale on [Gollwitzer-2006], [Safren-2010]; no direct evidence for empty states |
| E3 | [SHOULD] | Does the voice pass? | Plain, warm, specific; no "just," "simply," "it's easy"; no clinical or hype vocabulary | §8 voice · §10 rules |
| E4 | [SHOULD] | Are money views emotionally neutral? | Spending and debt display without moralizing colors, labels, or judgment; the tone is logistics, not verdicts | Law 7 · problem evidence [Bangma-2019], [Swedish-Registry] (financial distress is high-stakes here) |

### 2.9 Accessibility

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| A1 | [MUST] | Does it work if the user only ever uses the Today screen? | Anchor Daily Board (or this artifact's core surface) delivers standalone value with zero other setup, forever | Laws 2/3 · partial-use is the norm: [Kenter-2023] (29% full completion; 59% ≥5 of 7 modules) |
| A2 | [SHOULD] | Is text readable under real conditions? | Sufficient contrast, body text at platform-comfortable size, paragraphs ≤3 lines in-product | Good practice; no direct ADHD evidence |
| A3 | [SHOULD] | Is the layout scannable? | Clear headers, one idea per line, generous white space; a skimmer gets the gist in 10 seconds | Law 3 · T3 (visual simplification isolated) per §6 ruling |
| A4 | [SHOULD] | Is motion calm? | No autoplaying/looping animation; sounds and pulses are opt-in | Design rationale (distraction); no direct evidence |
| A5 | [SHOULD] | Does it survive its worst real context? | Digital: primary flow works one-handed on a small phone. Printable: legible in black-and-white on a cheap printer | [LivingSMART-2015] (the phone is the structuring tool people carry); otherwise house rule |

### 2.10 Honesty

| # | Gate | Question | Passes when | Law · Evidence |
|---|---|---|---|---|
| H1 | [MUST] | Is every claim tier-labeled truthfully? | Each stated or implied benefit maps to a §4 key at its §3 tier, with T2/T3 flagged as indirect/experimental in adjacent copy (§10) | Governance · [Pasarelu-2020] (109 apps, none with proof — we don't join them) |
| H2 | [MUST] | Is the artifact free of banned language? | No "clinically proven," "treats/cures/fixes," "rewires," "dopamine hack," "neuroscience-based" halo, "guaranteed," "21 days," urgency theater, or shame hooks | §10 · [Singh-2024], [Stern-2016], [Elbe-2023], [Nordby-2022] |
| H3 | [SHOULD] | Is an Evidence Note present where a benefit is implied? | Any feature whose value is asserted carries the plain-language Evidence Notes microformat (Part 13 §4) | Governance · §10 |
| H4 | [SHOULD] | Are all numbers real? | Every number shown to the user comes from their own data or a cited §4 source — never an invented benchmark or fabricated example presented as typical | Law 10 · prime directive §0 |

**Tally: 15 [MUST] items, 23 [SHOULD] items.**

---

## 3. Worked examples

### 3.1 Failing artifact: "BudgetMaster Pro" cluttered budget spreadsheet (fictional)

A 12-tab spreadsheet with a 40-column transaction register, 14 pre-built category codes the user must memorize, conditional formatting that turns overspent rows red, a "No-Spend Streak" counter, a blank setup grid on first open, and a listing headline reading "Clinically proven ADHD budget — rewire your money brain in 21 days!"

Review (failures only; passing and N-A rows omitted):

| Item | Result | One-line reason |
|---|---|---|
| C1 [MUST] | Fail | Logging one expense = open file, find tab, find row, fill 6 required columns |
| D1 [MUST] | Fail | First-run tally: 19 decisions before any value (categories, codes, colors, sheet order) |
| D2 [MUST] | Fail | First screenful counts 40+ elements |
| I1 [MUST] | Fail | First action is "configure 14 categories" — a planning project, not a ≤2-minute pre-decided act |
| I2 [MUST] | Fail | Every tab presents dozens of equally weighted cells; no "do this now" |
| M1 [MUST] | Fail | Category codes live on tab 2; entry happens on tab 5; the user carries codes in their head |
| T1 [MUST] | Fail | Bills column headed "upcoming/later"; no dates, no durations on money tasks |
| F1 [MUST] | Fail | No cues at all, and no review ritual; the workflow ends at data entry |
| R1 [MUST] | Fail | A missed month greets the user with red zero rows; no Comeback path exists |
| R2 [MUST] | Fail | Recovery requires backfilling 30 days of transactions or deleting rows by hand |
| E1 [MUST] | Fail | Red overspend formatting + breakable No-Spend Streak = loss-framing and shame |
| E2 [MUST] | Fail | First open is a blank grid |
| A1 [MUST] | Fail | There is no Today surface; value exists only if the whole system is maintained |
| H1/H2 [MUST] | Fail | "Clinically proven," "rewire," "21 days" — three banned claims in one headline ([Pasarelu-2020], [Singh-2024]) |
| D3, D4, F2–F4, R3, R4, E4, H3 [SHOULD] | Fail | Nine SHOULD failures; not itemized because the ship decision is already made |

**Verdict: blocked.** 14 of 15 [MUST] items failed (M3-adjacent state handling was the only near-pass). Any one of them blocks alone. The fix path is not polish — it is adopting the Anchor Money System workflow: capture-first entry, one bill as the next action, dated bills, a Weekly Reset hook, Comeback-safe lapse handling, and truthful listing copy.

### 3.2 Passing artifact: Anchor Daily Board (planner "Today" screen)

Now / Next / Later columns; committed tasks capped at 3/day with duration fields; a one-tap capture button feeding The Inbox; after a ≥7-day gap the board opens into Comeback Mode (one button archives the backlog); return copy reads "Welcome back. Here's today."; listing copy carries tier labels and the not-a-treatment block.

| Item | Result | Note |
|---|---|---|
| C1, C2, C3 | Pass | Capture button on-screen; two interactions; no filing demanded |
| D1, D2 [MUST] | Pass | Three decisions max (pick Now, pick Next, defer rest); 6 elements above fold |
| D3, D4 | Pass | Defaults pre-fill from yesterday's Later; settings collapsed |
| I1, I2 [MUST] | Pass | First action pre-decided: "drag one task to Now" (~30 seconds); single primary action per state |
| I3, I4 | Pass | Now card visually dominant; breakdown fields optional with examples |
| M1 [MUST], M2, M3 | Pass | Durations, dates, notes on-card; board state persists mid-flow |
| T1 [MUST] | Pass | Dates or explicit Later parking; duration field on every task |
| T2 | **Fail** | Committed-minutes vs available-hours line not in v1.0 — logged for v1.1 |
| T3 | N-A | No timers shipped |
| F1 [MUST], F2, F3 | Pass | Every cue names one act; board feeds The Weekly Reset; zero generic nags |
| F4 | Pass | Momentum shown as days-used-this-week |
| R1, R2 [MUST], R3, R4 | Pass | Comeback Mode auto-triggers; archive is one button; no missed-day counts; no streaks |
| E1, E2 [MUST], E3, E4 | Pass | No loss-framing; empty state teaches with one example + first action; voice reviewed |
| A1 [MUST] | Pass | The board is the standalone surface — it never requires the rest of Anchor Life OS |
| A2–A5 | Pass | Contrast checked; scannable; no motion; one-handed phone layout verified |
| H1, H2 [MUST], H3, H4 | Pass | Claims tier-labeled; banned-language sweep clean; Evidence Notes attached; sample data marked as sample |

**Verdict: ships.** 15 of 15 [MUST] passed; 1 [SHOULD] failure (T2) with a logged fix for v1.1 — under the 2-failure block threshold. Ship log records reviewer, date, and the T2 fix commitment.

---

## 4. Printable one-page summary

Copy this section onto a single page and keep it next to the ship log.

**ANCHOR SHIP GATE — one page**
*Score every item Pass / Fail / N-A. Any [MUST] fail blocks ship. Two [SHOULD] fails block ship. Count literally; N-A needs a written reason.*

**The 15 [MUST] gates:**

- [ ] C1 — Capture in ≤2 interactions
- [ ] D1 — Fewer decisions than what it replaces (counted, ≤3 primary per screen)
- [ ] D2 — ≤7 elements above the fold
- [ ] I1 — First action ≤2 minutes and pre-decided
- [ ] I2 — Every screen resolves to one next action
- [ ] M1 — Nothing must be remembered across screens
- [ ] T1 — Time concrete: real dates, durations on tasks, no bare "later"
- [ ] F1 — Every cue triggers a pre-decided act; a practice loop exists
- [ ] R1 — Missed day/week lands in a Comeback path, not a backlog
- [ ] R2 — Recovery after a missed week needs zero manual cleanup
- [ ] E1 — Nothing punishes, shames, or loss-frames (must be NO)
- [ ] E2 — Every empty state teaches: what goes here + first action
- [ ] A1 — Works if the user only ever uses the Today screen
- [ ] H1 — Every claim tier-labeled truthfully (§10)
- [ ] H2 — Zero banned language (proven / cures / rewires / 21 days / guarantees)

**The 10 category prompts ([SHOULD] items live here):**

- [ ] Capture — no filing at capture; Inbox everywhere
- [ ] Decisions — defaults picked; depth collapsed
- [ ] Initiation — next action biggest on screen; breakdown offered
- [ ] Memory — context at point of action; state survives interruption
- [ ] Time — committed vs available visible; timers opt-in + labeled experimental
- [ ] Follow-through — no generic nags; feeds The Weekly Reset; 2–5 month habit honesty
- [ ] Recovery — forward-facing return copy; frequency not streaks
- [ ] Emotion — warm plain voice; neutral money views
- [ ] Accessibility — readable, scannable, calm, phone-ready / B&W-printable
- [ ] Honesty — Evidence Notes present; every number real

*Rubric: 15/15 MUST + ≤1 SHOULD fail (logged, dated) = ship. Anything else = fix first.*

---

*Previous: Part 05 · Next: Part 07 · Canonical rules: [00 — Evidence Foundation](00-evidence-foundation.md) · Full index in [README](README.md).*
