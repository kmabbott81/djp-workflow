# 05 — UX Specification

> **Status:** Working spec. Traces to [00 — Evidence Foundation](00-evidence-foundation.md): tiers §3, citation registry §4, rulings §6, Ten Design Laws §7, vocabulary §8, metadata format §9.
> **Scope note:** Design targets below apply to the Notion implementation *where Notion allows* and fully to the future **Anchor App**. Wherever Notion cannot enforce a spec, the gap is called out inline as **Notion limit**.

**Executive summary.** This document specifies the global design system and twelve core screens of the Anchor ecosystem. The honest frame, per §6 rulings: the *workflows* these screens scaffold — calendar-plus-task-list structure, task decomposition, prioritization, weekly review — carry T1 package evidence in adults with ADHD [Safren-2010], [Solanto-2010], [Matsumoto-2024], [Lauder-2024]. The *interface choices* that deliver them — visual simplification, a today-only view, single-action heroes, timers, micro-animations — are T3 as isolated features, or T2-indirect where general-population behavioral science applies ([Jachimowicz-2019] defaults, [IyengarLepper-2000] choice reduction, [Gollwitzer-2006] if-then cues, [Offloading-2025] external memory). No UI choice in this document is "clinically proven," and none may be marketed as such. Every screen is built to the same skeleton: one next action, few visible choices, forgiveness on lapse, and recovery as a first-class path (Laws 2, 3, 7).

---

## Section A — Global design system

These rules apply to every screen in Section B and to every future surface. A screen that breaks one must justify it in its spec.

### A1. Color

**Principle: color is information, never decoration and never judgment.** One color is reserved for exactly one meaning — the single next action. If two things on a screen are action-colored, the design is wrong (Law 2).

Semantic palette (light / dark values are targets; verify contrast per build):

| Token | Light | Dark | Reserved meaning |
|---|---|---|---|
| `bg` | #FAFAF7 | #141517 | Page background. Calm off-white / soft near-black, never stark |
| `surface` | #FFFFFF | #1D1F23 | Cards, sheets |
| `ink` | #26282B | #ECEDEE | Primary text |
| `ink-soft` | #5A5E66 | #A6ABB5 | Secondary text, captions |
| `line` | #E4E2DC | #2E3136 | Borders, dividers |
| `action` | #1B5FD9 | #6FA4FF | **The single next action only.** Buttons and hero accents for the one pre-decided next step. Nothing else, ever |
| `positive` | #2E7D5B | #63C79B | Money in, bill paid, task done confirmations |
| `attention` | #B26A00 | #E5A54B | Money facts: due within 7 days |
| `urgent` | #A6462E | #E08A70 | Money facts only: past due, needs action today. **Never used for personal lapses, missed days, or streaks** |
| `calm` | #3E7C7B | #7FBFBE | Comeback Mode, rest states, "paused" |

Rules:

- **No red-shaming.** Lapse and return states (missed days, abandoned weeks, Comeback Mode) use `calm` and neutrals only. `urgent` terracotta is reserved for factual money states (a bill is past due), always paired with an action button and non-blaming copy.
- Both light and dark themes ship at launch; dark is not an afterthought (many users run devices dark for sensory comfort — preference support, no clinical claim).
- Contrast: text ≥ 4.5:1, large text and UI components ≥ 3:1 against their background — **stated as a WCAG 2.2 AA design target, not a certification.** Audit per release.
- Color never carries meaning alone (pair with icon, label, or position) — supports color-vision deficiency.
- **Notion limit:** Notion's theme colors are approximations; templates use Notion's default/gray backgrounds, blue for action buttons, and callout colors nearest to the semantic set. Exact tokens apply to the Anchor App and printables.

> **Evidence:** T3 as isolated visual design; T2 (indirect) as part of the structured package, per §6 ruling on visual simplification; [IyengarLepper-2000] for restraint in salient options · **Confidence:** Low · **Rationale:** one reserved action color makes the pre-decided next step the most salient element, reducing selection cost · **Expected outcome:** faster start on the committed task; no shame-triggered abandonment · **Downside:** untested in ADHD; a single accent can feel plain to some users · **Difficulty:** Low · **Priority:** High

### A2. Typography

- Type ramp (size/line-height): `display` 28/36 semibold · `title` 20/28 semibold · `body` 16/24 regular · `small` 14/20 regular.
- **Maximum 3 sizes on any one screen.** Most screens use `title` + `body` + `small`; only hero screens add `display` (and then drop one).
- Minimum body size 16px; `small` (14px) is floor for captions/metadata and is never used for instructions or actions.
- Line height ≥ 1.5 × font size for body text; paragraph width ≤ 65 characters.
- **Sentence case for all labels and buttons.** No all-caps except 2–3-letter abbreviations.
- **Reading level ≤ grade 7 for all UI copy.** Checked in copy review before ship (Part 13 process).
- Optional dyslexia-friendly font setting (system or bundled humanist sans with distinct letterforms). Framed as a comfort preference; **we make no effectiveness claim** — the evidence for special dyslexia fonts is not established, and no §4 citation covers it.
- Numerals over number words in UI ("3 tasks", not "three tasks"); tabular figures for money.
- **Notion limit:** Notion fixes its own type ramp; templates control hierarchy with heading levels, toggles, and bolding only. Full ramp applies to Anchor App, spreadsheets, and printables.

> **Evidence:** T3 as isolated feature; T2 (indirect) within the package (§6 visual-simplification ruling) · **Confidence:** Low · **Rationale:** fewer sizes and larger, looser text lower reading effort at the point of performance · **Expected outcome:** UI copy understood on first read; fewer mis-taps · **Downside:** no ADHD-specific typography trials exist · **Difficulty:** Low · **Priority:** Medium

### A3. Spacing

- **8px grid.** Allowed spacing values: 8, 16, 24, 32, 48, 64. Page padding 16 (small screens) / 24 (large). Card padding 16–24. Section gaps 24–32.
- List rows ≥ 56px tall; buttons ≥ 44px tall (see A6).
- **Generous whitespace is a feature, not waste.** Rationale, labeled honestly per §6: cognitive-load reduction and choice restraint are T2 (indirect) — supported by general-population choice-overload evidence ([IyengarLepper-2000]: 6 options outperformed 24 by 10×) and the defaults literature [Jachimowicz-2019] — and T3 as an isolated "ADHD-friendly layout" claim. We justify whitespace as mechanism ("fewer things competing for attention"), never as ADHD-proven.
- Practical rule: if a screen needs a scrollbar to show its *primary* action, remove elements until it doesn't.
- Chunking: no visible group holds more than 5 items without a "Show more" fold.
- **Notion limit:** Notion controls its own padding; templates approximate with empty blocks, dividers, and column layouts. Full grid applies to the Anchor App.

> **Evidence:** T2 (indirect) [IyengarLepper-2000], [Jachimowicz-2019]; T3 as isolated feature per §6 · **Confidence:** Moderate (for choice reduction), Low (for whitespace itself) · **Rationale:** fewer competing elements per viewport lowers the cost of choosing and starting · **Expected outcome:** primary action found and started faster · **Downside:** more scrolling for power users; density lovers may complain · **Difficulty:** Low · **Priority:** High

### A4. Motion and animation policy

- **Functional feedback only.** Animation exists to confirm what just happened or where something went — never to entertain, retain, or delay.
- Duration ≤ 300ms; standard transitions 150–200ms; easing gentle (ease-out).
- **`prefers-reduced-motion` is always respected**: all animation collapses to instant state changes with static confirmation. This is a hard rule, no exceptions.
- **Completion micro-feedback is allowed and bounded:** a ~200ms checkmark draw with a brief color settle to `positive` when a task, bill, or step completes. Labeled honestly: T3 experimental, immediate-reinforcement rationale — gamification-style reward effects are real but short-term and decay ([KimCastelli-2021]: d = 1.57 under a week vs 0.30 at ~20 weeks, negative over years). So micro-feedback is **never punitive, never blocking, always skippable**, and never the reason a user must wait.
- **Banned:** confetti lock-ins or any celebration that must play out before the next action; streak-loss animations (nothing animates a failure — there are no streaks anyway, see B10); shaking/error wiggles; looping attention-grabbers; badges raining down.
- No parallax, no auto-playing motion on load.
- **Notion limit:** Notion's own transitions apply; templates simply avoid gif decorations. Policy binds the Anchor App fully.

> **Evidence:** T3 [KimCastelli-2021] (short-term reinforcement only, decays) · **Confidence:** Low · **Rationale:** immediate, tiny confirmation closes the action loop without building a reward economy that later collapses · **Expected outcome:** completion feels registered; no engagement-bait patterns (Law 10) · **Downside:** even mild rewards can lose meaning; monitor for annoyance · **Difficulty:** Low · **Priority:** Medium

### A5. Notification policy

Applies to the Anchor App natively. For Notion, every template ships a **"pair your phone" card**: Notion's own notifications are not designed for this job, so users copy 2–3 pre-written reminders into their phone's clock/reminders/calendar app using the templates below. That keeps Law 5 intact on a tool we don't control.

Core rules, in order:

1. **Every notification is one pre-decided action** [Gollwitzer-2006] — a cue for a specific, small act the user already chose, deep-linking to the exact screen where the act happens. The evidence constraint is explicit: reminder-only systems failed in adult-ADHD trials ([Nordby-2022] — no adherence effect from SMS reminders; [FOCUS-2023] — engagement without outcomes). **Reminders alone fail; cues that trigger pre-decided actions inside a structured system are the only kind we send.** Generic nags ("Don't forget your goals!") are banned.
2. **Default quiet hours: 9:00pm–8:00am.** Nothing fires inside them; anything due in that window queues for the edge.
3. **Hard cap: ≤3 notifications per day (default).** User can lower to 0 or raise deliberately. Over cap, lowest priority drops. Priority order: today's pre-decided money/bill action → calendar transition warning → routine cue → morning plan.
4. **Transition warnings before calendar events** (default 10 minutes; adjustable): one warning, one line, names the event and the wrap-up act.
5. **Snooze without guilt.** Options: "Later today", "Tomorrow", "Pick a time". Snoozing is a scheduling act, not a failure — confirmations say "Moved to tomorrow", never "Skipped again". If the same cue is dismissed or snoozed twice, the next one offers "Change the time or turn this off?" — respect, not escalation.
6. Notification copy follows A7 (verbs first, ≤12 words, plain).

**Complete copy template set** (placeholders in braces):

- Bill cue: "8:00pm — pay the electric bill (2 min). Tap to open the bill screen."
- Money action (generic): "{time} — {action} ({est} min). Tap to start."
- Payday cue: "Payday. Run your money routine? About 10 minutes."
- Weekly Reset cue: "Sunday 5:00pm — Weekly Reset (15 min). We saved your place."
- Transition warning: "In 10 minutes: {event} at {time}. Start wrapping up."
- Routine cue: "After coffee: {routine} (2 min). Tap when done."
- Morning plan (optional, off by default): "Good morning. Today's one thing: {first action}."
- Comeback re-entry (sent once, 7–10 days after last activity; user can disable): "No pressure. One tap starts a fresh week when you're ready."
- Snooze confirmations: "Moved to later today." · "Moved to tomorrow." · "Moved to {day}."

> **Evidence:** T2 with T1 constraints (Law 5): [Gollwitzer-2006] d = 0.65 for if-then cues; constraints from [Nordby-2022], [FOCUS-2023]; [SMS-Meta-2023] modest indirect support for well-designed cues · **Confidence:** Moderate · **Rationale:** a cue only works when the decision was already made; caps and quiet hours protect trust so the few cues that fire still get acted on · **Expected outcome:** bill and reset cues convert to completed actions; notification fatigue avoided · **Downside:** capped cues mean some things go un-nudged; Notion pairing adds setup friction · **Difficulty:** Medium (App), Low (templates) · **Priority:** High

### A6. Accessibility

WCAG 2.2 AA is the **design target** across the ecosystem (not a claimed certification). On top of it, ADHD-specific accessibility here means **fewer elements, chunked content, and pre-made defaults** — reducing executive demand is an access need, not a style.

- **Keyboard:** full traversal on web/desktop; logical tab order matching visual hierarchy; visible focus ring (2px, offset, `action` color); Esc always closes sheets without losing entered data.
- **Screen readers:** every control labeled; the single next action is announced first after the screen title; toasts and state changes use polite live regions; momentum bars expose text values ("3 of 4 this week").
- **Touch targets ≥ 44×44px**, ≥ 8px apart. **Notion limit:** Notion's tap targets are its own; the target binds the Anchor App and any web surface.
- **Error copy never blames.** Pattern: what happened → what's safe → one next step. "That didn't save. Your text is still here. Try again." Never "Invalid input", never "You forgot…".
- **Focus management:** on step change in wizards, focus moves to the step heading; after deletion, focus moves to the next item, not the page top; nothing steals focus while typing.
- **No data-losing timeouts.** Wizards are exit-safe and resumable; timers never discard work (see B5).
- **Plain language everywhere:** ≤ grade 7, front-loaded verbs, one idea per sentence (A7).
- Reduced motion honored (A4); dark theme honored (A1); text scales to 200% without loss.
- Voice capture offered where the platform allows (supports motor and working-memory load alike).

> **Evidence:** Accessibility norms are a governance baseline (no tier claimed); the ADHD-specific "fewer elements, chunking, defaults" framing is T2 (indirect) [Jachimowicz-2019], [IyengarLepper-2000], [Offloading-2025] per §6 · **Confidence:** Moderate · **Rationale:** the same structure that helps attention (less to parse, less to decide) is standard cognitive accessibility · **Expected outcome:** usable with screen reader, keyboard, and at 200% zoom; no shame-loop from errors · **Downside:** AA-target auditing costs ongoing effort · **Difficulty:** Medium · **Priority:** High

### A7. Voice and microcopy rules

The voice everywhere: a calm friend who has read the research (§8). Rules:

1. **Verbs first.** "Pay the electric bill", not "Electric bill payment".
2. **≤12 words per instruction.** Split anything longer.
3. **No jargon.** Banned in UI: "leverage", "optimize", "workflow", "productivity system", "executive function" (in-product), "dopamine", "gamify". Say "plan", "list", "step", "next thing".
4. **No guilt, ever.** "Welcome back" — never "You've been away 12 days". No missed-day counts, no "streak lost", no "only 2 of 7 done". State what's next, not what didn't happen.
5. **No hype.** No "crush", "supercharge", "master your ADHD". No promised outcomes (§10): we say "designed around", "built on strategies tested in…", never "proven to".
6. Numerals for numbers; specific over vague ("2 min", not "quickly").
7. Never "just" or "simply" — if it were simple, the user wouldn't need us.
8. Questions only when we act on the answer.
9. **Evidence Notes** links appear where users might reasonably ask "says who?" — one line, plain: "Why this design? See the evidence note." The note states the tier in plain words ("experimental — makes sense in theory, not yet tested in trials").
10. Empty states teach (one warm line + one action); error states follow A6; lapse states follow Law 7.

> **Evidence:** Governance (Part 13 language rules); guilt-free lapse copy is T2 [Lally-2010] (one miss ≠ failure), [KimCastelli-2021] (punitive mechanics decay/backfire) · **Confidence:** Moderate · **Rationale:** shame predicts abandonment in a population defined by restart friction; plain short copy lowers reading cost at the moment of action · **Expected outcome:** users return after lapses instead of deleting the tool · **Downside:** warm minimalism can read as thin to detail-oriented users; Evidence Notes must stay current · **Difficulty:** Low · **Priority:** High

---

## Section B — Screen-by-screen specifications

**How to read these specs.** *Decision load* = interactive choices visible before any tap or scroll (transient elements like a 10-second undo do not count; the persistent capture button does). Target ≤5 per screen; any excess is justified in place. *Progressive disclosure map* levels: L0 = visible by default; L1 = one tap/expand away; L2 = two levels deep (settings, history, edge cases). Every screen inherits Section A; specs below only state screen-specific applications.

### B1. Anchor Daily Board (Today)

**Purpose.** Answer "what do I do right now?" within five seconds of opening. Hold today's plan — at most 3 committed tasks — as **Now / Next / Later**, with one hero next action (Law 2). This is the ecosystem's default screen.

**Visible elements (hierarchy order).**
1. **Now card (hero):** the committed task's *first action* as a verb phrase ("Call the pharmacy"), time estimate ("about 5 min"), and one `action`-colored **Start** button.
2. **Done** control on the Now card (secondary, quiet style).
3. **Next** row: one task, muted, with its first action visible.
4. **Later** row: one task plus a count of anything scheduled ("+2 scheduled").
5. Persistent **Capture** button (bottom corner; feeds The Inbox — Law 4).
6. Header: weekday + date, `small` type; done-today tally as plain text ("2 done"), no chart.

**Hidden elements (progressive disclosure, and why).**
- Full task list, calendar view, completed history → L1 behind "All tasks". Reason: the board must never become the pile; the pile is what users flee.
- Reorder/swap controls → L1 on long-press/hover. Editing is rarer than doing.
- Inbox unprocessed count → L1 inside Capture flyout, so it can't scold from the home screen.
- Settings, Evidence Notes → L2 overflow menu.

**Interaction flow.**
1. Open app → Now card focused/announced first.
2. Tap Start → opens Task detail focus (B4) or starts the act itself (external link) per task type.
3. Tap Done → 200ms check micro-feedback → Next task slides up to Now (≤300ms; instant under reduced motion).
4. Adding a 4th commitment triggers the cap sheet: "Today holds 3. Swap one out?" — options: swap (pick which), send to Later, cancel.
5. Capture at any moment → 2-interaction capture (B2) → returns here.

**Default state.** Morning: Now = first committed task from the Weekly Reset or yesterday's carry-over (carried tasks show no "overdue" mark — they are simply today's Now). If the day has no commitments, board shows the pick flow (see Empty).

**Error state.** Sync failure: quiet banner "Couldn't sync. Your list is safe on this device." Board stays fully usable offline. No modal, no blame.

**Empty state (teaching moment).** "Nothing planned yet. That's fine — pick one small thing." Buttons: "Choose from Inbox" (action color) · "Write a new task" (quiet). One captured pick lands directly in Now.

**Lapse/return state.** After ≥7 days inactive, the board does **not** show a backlog pile or overdue flags. It shows a calm card: "Been a while? No problem." → "Open Comeback Mode" (B6). Old tasks wait in All tasks untouched until the user decides there.

**Accessibility notes.** Now card is first in tab and reading order after the title. Start ≥ 44px. Done-today tally exposed as text. Cap sheet traps focus until dismissed, Esc-safe.

**Color usage.** `action` on Start only. Done confirmations `positive`. Next/Later in `ink-soft` on `surface`. No `urgent`/`attention` anywhere on this screen — money colors live on money screens.

**Typography.** `display` for the Now first action, `body` for rows/buttons, `small` for header and estimates. (3 sizes.)

**Spacing.** Now card padding 24; 32 gap between Now and Next/Later group; rows 56px. Hero occupies the first viewport with whitespace — no scrolling to see Start.

**Animations.** Done check (~200ms); Next→Now promotion slide (≤300ms). Nothing else moves. Reduced motion: instant swap.

**Notifications touching this screen.** Optional morning plan cue (off by default); calendar transition warnings deep-link here. Both count toward the daily cap (A5).

**Visual hierarchy.** 1st: Now first-action text. 2nd: Start button. 3rd: Next row. Everything else is deliberately quiet.

**Progressive disclosure map.** L0: Now/Next/Later, Start, Done, Capture. L1: All tasks, reorder, swap sheet, Inbox count. L2: settings, history, Evidence Notes.

**Decision load.** 5 visible choices (Start, Done, open Next, open Later, Capture). At target.

> **Evidence:** T1 for the daily calendar+task-list workflow and single-next-action decomposition [Safren-2010], [Solanto-2010], [Matsumoto-2024]; T3 for the today-only view as an isolated UI feature (§6); T2 (indirect) for the 3-task cap and choice restraint [IyengarLepper-2000], [Jachimowicz-2019] — the number 3 itself is untested design judgment · **Confidence:** Moderate · **Rationale:** the screen externalizes prioritization so the user starts instead of choosing · **Expected outcome:** higher task completion rate on committed tasks (§11 metric 4) · **Downside:** heavy days feel constrained; cap sheet adds one friction moment · **Difficulty:** Medium (App), Medium (Notion — cap is advisory only: a formula flags ">3 committed — pick your 3"; **Notion limit:** cannot hard-enforce) · **Priority:** High

### B2. The Inbox (capture)

**Purpose.** Zero-friction external memory (Law 4). Get a thought out of the user's head in **≤2 interactions, with zero categorization** [Offloading-2025] — no tags, no project, no date, no decisions at capture time.

**Visible elements (hierarchy order).**
1. Text field, auto-focused, placeholder: "What's on your mind?"
2. **Save** (action color; Enter key equivalent). Saving closes the sheet.
3. Voice input button (platforms that support it).
4. Behind the capture sheet, the Inbox list itself: unprocessed items newest-first, plus one **"Sort these (10 min)"** button → B3.

**Hidden elements (progressive disclosure, and why).**
- Item editing, delete, merge → L1 on item tap. Capture must stay write-only-fast.
- "Add detail now" (date, note) → L1 expander after save, for the rare moment it's worth it. Default path never shows it.
- Processing history → L2.

**Interaction flow.**
1. Interaction 1: tap Capture (or global shortcut / share-sheet / widget).
2. Interaction 2: type or speak, press Enter/Save. Toast: "Got it." Sheet closes. Two interactions, done.
3. Repeat capture chains without leaving the sheet ("Save + another" appears after first save — optional, still 1 interaction per item).
4. Items wait here untriaged, guilt-free, until B3 or the Weekly Reset.

**Default state.** Capture sheet opens empty with keyboard up. List behind shows up to 5 items then "Show all".

**Error state.** Save fails: "Saved on this device. It will sync later." Item is never lost; the field never clears on failure.

**Empty state (teaching moment).** "Empty. When something pops into your head, drop it here. Sorting comes later — that's the whole trick."

**Lapse/return state.** A giant unprocessed pile is never scolded ("47 items!" appears nowhere). List shows the first 5 and: "A lot in here? The Weekly Reset sorts it 10 minutes at a time — or Comeback Mode archives it."

**Accessibility notes.** Field labeled "Capture a thought"; toast announced politely; voice capture equal-priority, not buried; Esc closes and *keeps* typed text as a draft.

**Color usage.** `action` on Save only. Neutral everything else.

**Typography.** `title` for field text (what you write should look important), `body` list, `small` timestamps. (3 sizes.)

**Spacing.** Sheet padding 24; list rows 56px; one item per row, one line each, truncated — reading happens later.

**Animations.** Toast fade (150ms). No list reshuffle animation.

**Notifications touching this screen.** None. Capture is user-initiated by design; we never nag "you haven't captured today".

**Visual hierarchy.** 1st: text field. 2nd: Save. 3rd: "Sort these" button.

**Progressive disclosure map.** L0: field, Save, voice, list preview, Sort. L1: item edit/delete, add-detail expander, full list. L2: history.

**Decision load.** 4 (field, Save, voice, Sort these). Under target — intentionally the lowest-friction screen in the system.

> **Evidence:** T1/T2 (Law 4): offloading to external memory reliably helps, most for prospective memory [Offloading-2025]; coached smartphone structuring worked in adults with ADHD as a package [LivingSMART-2015] · **Confidence:** Moderate · **Rationale:** capture only works if it is cheaper than remembering; every added field re-imposes the executive cost the feature exists to remove · **Expected outcome:** thoughts and obligations reliably enter the system instead of evaporating · **Downside:** unprocessed piles grow; mitigated by B3, Weekly Reset, and Comeback Mode · **Difficulty:** Low (App); **Notion limit:** true 2-interaction capture needs the phone widget/share sheet; template ships setup instructions · **Priority:** High

### B3. Inbox processing view

**Purpose.** Turn the captured pile into decisions **one item at a time** — never a wall of rows. Four outcomes only: **do today / schedule / someday / delete**. This is the "organize later" half of Law 4, run standalone or as Weekly Reset step 1.

**Visible elements (hierarchy order).**
1. The current item, large, centered — one item is the whole stage.
2. Four choice buttons: **Do today** · **Schedule** · **Someday** · **Delete**.
3. Progress text: "3 of 14".
4. Quiet **Skip** link (returns item to the pile bottom).

**Hidden elements (progressive disclosure, and why).**
- The rest of the list — hidden on purpose; seeing 40 items while deciding on 1 is the overwhelm this screen exists to prevent.
- Edit item text → L1 tap on the item.
- Date picker → appears only after "Schedule" (a decision within a decision stays hidden until owed).
- Merge-duplicates, bulk actions → L2 overflow. Bulk-delete-all lives in Comeback Mode instead, where it has guardrails.

**Interaction flow.**
1. Enter from Inbox or Weekly Reset → item 1 appears.
2. Tap one of four choices. "Do today" checks the 3-task cap (may open the swap sheet from B1). "Schedule" opens a date sheet with 3 presets (Tomorrow · This weekend · Next week) + calendar.
3. Item animates out (≤200ms), next item in. Progress increments.
4. Delete shows a 10-second undo toast — no confirmation modal (undo is safer than a reflex-clicked "Are you sure?").
5. At any point, leave — progress is saved; the pile never resets.
6. On finish: "Inbox zero. Everything has a home." One button: "Back to Today".

**Default state.** Oldest unprocessed item first (oldest items are the ones silently rotting; surfacing them is the point). Suggested session copy at entry: "10 minutes is plenty. Stop anytime."

**Error state.** Cap conflict on "Do today" → swap sheet, never a dead end. Sync failure: decisions queue locally, banner per A6.

**Empty state (teaching moment).** "Nothing to sort. Capture freely — this is where it all gets handled."

**Lapse/return state.** Huge backlog (>25 items): entry banner offers "Sort the newest 10 and archive the rest?" — one tap runs it; archived items stay searchable. Copy: "Old items are safe in the archive. Nothing is lost."

**Accessibility notes.** Choice buttons are a labeled radio-style group with keys 1–4; focus moves to the new item on advance; undo toast is announced and keyboard-reachable; progress exposed as text.

**Color usage.** All four choices neutral `surface` + `ink` — **no action color here**, because there is no single right answer among the four. Delete is not red; it is a normal, guilt-free outcome. Undo toast uses `calm`.

**Typography.** `title` item text, `body` buttons, `small` progress. (3 sizes.)

**Spacing.** Item card padding 24, 32 above the button row; buttons ≥44px in a 2×2 grid (small screens) or one row (large).

**Animations.** Card exit/enter ≤200ms lateral fade. Reduced motion: instant swap.

**Notifications touching this screen.** None directly; the Weekly Reset cue (A5) leads here as step 1.

**Visual hierarchy.** 1st: the item text. 2nd: the four choices. 3rd: progress.

**Progressive disclosure map.** L0: item, 4 choices, skip, progress. L1: edit text, date sheet, undo. L2: bulk tools, archive offer.

**Decision load.** 6 (four outcomes + skip + the item itself as editable target). One over target — justified: the four outcomes *are* the feature (a triage needs its categories), and skip is the pressure-release valve that keeps any single decision optional.

> **Evidence:** T1 as part of the CBT/MCT organisational workflow — organisational strategies improved response odds (incremental OR 2.03) [Matsumoto-2024]; prioritization/triage drills are core modules in [Safren-2010], [Solanto-2010]; T2 for the one-at-a-time presentation itself [IyengarLepper-2000] (§6: interactive checklists T1 in workflow, lower standalone) · **Confidence:** Moderate · **Rationale:** one visible decision at a time converts an overwhelming pile into a sequence of small wins · **Expected outcome:** Inbox items regularly reach decisions; Weekly Reset step 1 completes · **Downside:** slower than bulk edit for the organized minority; date presets won't fit everyone · **Difficulty:** Medium (App); **Notion limit:** Notion can't hide the list or step through items — template approximates with a filtered "one unprocessed item" view + choice buttons (select property) · **Priority:** High

### B4. Task detail (decomposition template)

**Purpose.** Turn a vague task into a startable one using the CBT decomposition pattern: **First action / Next action / Done criteria** [Safren-2010], [Matsumoto-2024]. This screen is where "do taxes" becomes "find last year's return (5 min)".

**Visible elements (hierarchy order).**
1. Task name (editable, `title`).
2. **First action** field — placeholder: "The smallest first move. 'Open the email' counts."
3. **Next action** field — placeholder: "What comes right after?"
4. **Done criteria** field — placeholder: "How will you know it's done?"
5. Time estimate chips: 5 · 15 · 30 · 60+ min.
6. **Make this today's Now** button (action color) — the screen's single next action.

**Hidden elements (progressive disclosure, and why).**
- Due date, notes, links → L1 "More" expander. Most tasks need decomposition, not metadata; metadata-first forms train people to fill boxes instead of deciding the first move.
- Full checklist (beyond first/next) → L1 "Add more steps". Two steps ahead is enough runway; planning ten steps is procrastination wearing a badge.
- Recurrence → L1 under More. History/activity → L2.

**Interaction flow.**
1. Open from board, Inbox processing, or search.
2. Fill First action (or accept a suggested split if the App can offer one — suggestions are optional and editable, never auto-committed).
3. Optionally fill Next action, Done criteria, estimate.
4. Tap "Make this today's Now" (runs the 3-task cap check) or back out — everything auto-saves.
5. From the board, Start on this task opens it with First action promoted to the hero.

**Default state.** Fields empty with teaching placeholders; estimate unset; nothing required.

**Error state.** None blocking — an incomplete breakdown always saves. If committed to Today with no First action, one gentle inline line: "Add a first move? Small ones work best." (Never a modal, never required.)

**Empty state (teaching moment).** The placeholders are the teaching; additionally, first-ever open shows a one-time hint: "Big tasks stall. Name the first two minutes and the rest gets easier."

**Lapse/return state.** A task untouched for 30+ days shows a quiet offer: "Still matter? Keep · Someday · Archive." No "stale!" badge.

**Accessibility notes.** Three fields programmatically grouped as "Break it down"; placeholders duplicated as visible labels on focus (placeholders alone fail when typing starts); chips are a labeled radio group; 44px targets.

**Color usage.** `action` only on "Make this today's Now". Fields neutral. Done-criteria met (checked off later) confirms in `positive`.

**Typography.** `title` task name, `body` fields/buttons, `small` hints. (3 sizes.)

**Spacing.** 24 between the three decomposition fields; 32 before the commit button; fields full-width, one column — no side-by-side form grids.

**Animations.** None beyond standard focus transitions and save tick.

**Notifications touching this screen.** If the task is scheduled with a time, its cue (A5 generic template) deep-links here with First action shown first.

**Visual hierarchy.** 1st: task name. 2nd: First action field. 3rd: commit button.

**Progressive disclosure map.** L0: name, 3 decomposition fields, chips, commit. L1: More (date/notes/links/recurrence), extra steps, suggested splits. L2: history.

**Decision load.** 5 core interactive elements before the fold (name, first, next, done criteria, commit; chips count as one group). At target.

> **Evidence:** T1 — task breakdown and problem-solving are named active components: [Safren-2010] (task breakdown module; overall d = 0.60), [Solanto-2010], [Matsumoto-2024] (problem-solving incremental SMD 0.42 for inattention) · **Confidence:** High (component within packages), Moderate (this exact 3-field form) · **Rationale:** naming the first two minutes converts intention into a startable act at the point of performance · **Expected outcome:** committed tasks get started; fewer stalled "big rocks" · **Downside:** three fields can feel like homework; nothing is required, so some tasks stay vague · **Difficulty:** Low · **Priority:** High

### B5. The Weekly Reset wizard

**Purpose.** The 15-minute guided weekly review ritual (Law 6) — the single most protected workflow in the ecosystem (§8). Five timeboxed steps, **one decision per screen**, resumable at any point. This is the practice loop the strongest evidence keeps pointing at.

**Visible elements (hierarchy order).**
1. Current step content (one question or one action — never two).
2. One primary **Continue/Do it** button (action color).
3. Progress indicator: 5 dots + "Step 2 of 5 · about 3 min".
4. **Pause** link: "Pause — we'll hold your place."
5. **Skip this step** link (every step is skippable).

**The five steps.**
1. **Sort the Inbox** — embedded B3, capped at 10 items ("More next week is fine").
2. **Look back** — plain list of what got done this week. Copy: "Here's what happened. No scores." Nothing about what didn't.
3. **Look ahead** — next 7 days of calendar events, read-only scan, one prompt: "Anything need prep? Capture it."
4. **Money minute** — bills due ≤7 days (from B7); one prompt: "Anything to schedule now?"
5. **Pick your 3** — choose up to 3 committed tasks for the week's first day; sets B1.

**Hidden elements (progressive disclosure, and why).**
- Full task/bill lists behind each step's summary → L1. The wizard shows only what the current decision needs.
- Per-step optional countdown timer → L1 toggle, off by default (a visible timer is a T3 widget [Hallez-2024], child-study evidence; the minute text is the default, per Law 9).
- Reset-day/time settings, history of past resets → L2.

**Interaction flow.**
1. Enter from the weekly cue or menu → resumes at the last incomplete step.
2. Each step: read one prompt → act (or skip) → Continue.
3. Progress saves per step; closing the app mid-flow loses nothing (exit-safe).
4. Finish: "Reset done. Next week is set." One button: "See your board" → B1. Completion tick in `positive`, ~200ms.

**Default state.** Sunday 5:00pm suggestion (changed in setup or here at L2); wizard opens at step 1 or resume point.

**Error state.** Calendar not connected at step 3: "No calendar linked. Skip, or add events by hand." — step degrades, never blocks.

**Empty state (teaching moment).** First-ever run adds one intro line: "15 minutes, 5 steps. This one habit keeps the whole system honest." Empty inbox at step 1: "Nothing to sort — rare and delightful. Next step."

**Lapse/return state.** Missed resets are never counted or shown. Opening after skipped weeks starts fresh: "Let's reset from today." If the backlog is heavy, step 1 offers the archive shortcut (as B3).

**Accessibility notes.** Focus moves to the step heading on advance; dots exposed as "Step x of 5"; the optional timer is silent (no ticking) and never auto-advances or discards work; all steps keyboard-completable.

**Color usage.** `action` on the single Continue per step. Money minute uses `attention` only on genuinely due-soon rows. Look-back list in `positive` ticks.

**Typography.** `title` step prompt, `body` content, `small` progress. (3 sizes.)

**Spacing.** One-column, step content padded 24, button row pinned with 32 clearance — each step fits one viewport without scrolling on a phone.

**Animations.** Step transition slide ≤250ms; completion tick. Reduced motion: instant.

**Notifications touching this screen.** Weekly Reset cue (A5): "Sunday 5:00pm — Weekly Reset (15 min). We saved your place." Counts toward the cap; snooze options standard.

**Visual hierarchy.** 1st: step prompt. 2nd: Continue. 3rd: progress dots.

**Progressive disclosure map.** L0: current step, Continue, Pause, Skip, progress. L1: step detail lists, timer toggle. L2: schedule settings, past resets.

**Decision load.** Per step: 3–4 (act, Continue, Skip, Pause). Well under target — by design, since the whole wizard is one decision at a time.

> **Evidence:** T1 (Law 6): review/practice loops are core to [Safren-2010], [Solanto-2010] — homework completion correlated with improvement; regular follow-up per [NICE-NG87]; mobile transfer of session structure [Selaskowski-2022]; §11 names Reset completion the strongest defensible leading indicator · **Confidence:** High (ritual), Moderate (this exact 5-step wizard) · **Rationale:** a recurring, low-effort review is the maintenance dose that keeps every other screen truthful · **Expected outcome:** ≥50% of active weeks include a completed Reset (§11 metric 5) · **Downside:** 15 minutes is still a big ask on bad weeks — hence skippable steps and resume; **Notion limit:** resumability approximated with a per-step checklist template, not enforced · **Difficulty:** Medium · **Priority:** High

### B6. Comeback Mode

**Purpose.** The lapse-recovery flow (Law 7): one screen that turns "I abandoned it, it's ruined" into "I'm back, starting from today" — with **one button and zero guilt**. Recovery is a first-class feature because missing occasions doesn't erase progress [Lally-2010], but shame-shaped interfaces make people quit anyway.

**Visible elements (hierarchy order).**
1. Heading: "Welcome back."
2. One line: "Life happens. Your old list is safe — you don't have to sort it."
3. **One button (action color): "Archive it all — start from today."**
4. Quiet secondary link: "Look through the backlog first."
5. Nothing else. No stats, no dates, no counts.

**Hidden elements (progressive disclosure, and why).**
- The backlog itself → L1 behind the secondary link, in read-only batches of 10 with per-batch "Keep these / Archive these". Confronting the pile is opt-in, never the toll for re-entry.
- Restore-from-archive → L2 (archive is fully reversible and searchable; nothing is deleted).
- What triggers this screen (≥7-day inactivity, or manual from the menu — it is always available, not a punishment chamber) → explained in one L2 info note.

**Interaction flow.**
1. Return after ≥7 days → board offers Comeback Mode (B1 lapse state); or user opens it manually anytime.
2. Tap the one button → tasks, stale scheduled items, and unprocessed Inbox move to the archive; bills and money data are **not** archived (money facts stay live — see below).
3. Confirmation: "Fresh start. Pick one small thing for today." → drops into the B1 empty-state pick flow.
4. Or: browse backlog first, keep a handful, archive the rest, then same landing.

**Default state.** The one-button screen. The archive action is the default path; browsing is the exception.

**Error state.** Archive fails mid-way: "Some items didn't move yet. They're still safe. Try again." Partial archives are resumable; nothing ends up half-lost.

**Empty state (teaching moment).** If there's nothing to archive: "Nothing piled up. Pick one small thing for today." (Straight to the win.)

**Lapse/return state.** This screen *is* the lapse state. One rule from §11: this flow feeds the **Comeback Rate** — % who return within 14 days after a ≥7-day lapse — our signature metric. The screen itself never mentions the lapse length.

**Accessibility notes.** Heading announced first; the single button is the first focus stop; backlog browsing fully keyboardable; archive results announced ("214 items archived. All safe.").

**Color usage.** `calm` teal accents and neutrals only. The action button uses `action` blue as everywhere. **No red, no amber, nothing urgent** — per A1, lapse states never borrow money-state colors.

**Typography.** `title` heading, `body` line and button, `small` secondary link. (3 sizes.)

**Spacing.** Generous: content vertically centered, 48 gaps — the emptiness is the message: nothing is demanded of you here.

**Animations.** None on entry. Archive completion: single `positive` tick. No sweeping "cleanup" theatrics.

**Notifications touching this screen.** The single comeback re-entry cue (A5, once per lapse, 7–10 days, user-disableable) deep-links here. It is never repeated for the same lapse.

**Visual hierarchy.** 1st: "Welcome back." 2nd: the one button. 3rd: the quiet backlog link.

**Progressive disclosure map.** L0: heading, line, button, link. L1: backlog batches. L2: archive/restore, trigger explanation.

**Decision load.** 2. Deliberately the lowest in the ecosystem — a person at their most avoidant gets the smallest possible door back in.

> **Evidence:** T2 (Law 7): one missed occasion did not materially harm habit formation [Lally-2010]; punitive/streak mechanics decay or backfire long-term [KimCastelli-2021]; abandonment is the documented bottleneck [Kenter-2023] (29% module completion), [FOCUS-2023] (engagement decay) — the flow itself is our T3 design response, untested · **Confidence:** Moderate (rationale), Low (this exact flow) · **Rationale:** removing the backlog toll removes the main reason not to come back · **Expected outcome:** Comeback Rate — return within 14 days of a ≥7-day lapse (§11 metric 6) · **Downside:** aggressive archiving may bury items users still needed (mitigated: archive is reversible, money never archived) · **Difficulty:** Low (App); Medium (Notion — archive via one button automation; **Notion limit:** inactivity trigger impossible, entry is manual/linked from templates) · **Priority:** High

### B7. Money dashboard (Anchor Money System home)

**Purpose.** One glance answers: "what money thing needs me next, and what's coming?" One next financial action, bills due within 7 days, and a clearly-labeled estimate of what's okay to spend. The evidence mandate (§4D ruling): the *problem* is proven — more debt, fewer savings, more impulse buying [Bangma-2019], [Barkley-2008], [Swedish-Registry] — **no money feature is proven to fix it, and this screen says so** in its Evidence Notes.

**Visible elements (hierarchy order).**
1. **Next money action hero:** e.g., "Pay the electric bill — 2 min" + one `action` Start button (deep-links to B9).
2. **Due in the next 7 days:** up to 5 bill rows (name · amount · due-in) → each opens B9.
3. **Safe to Spend:** one figure + mandatory label: "Estimate — experimental" + "See the math" link.
4. **Add a bill** (quiet secondary).
5. `small` footer line: "Not financial advice. Estimates can be wrong." + Evidence Notes link.

**Hidden elements (progressive disclosure, and why).**
- Charts, category breakdowns, month history → L1 "Details". Dashboards that greet you with charts invite analysis instead of action; the hero must stay the action.
- Account balances (App with bank feed; manual in Notion) → L1, because a raw balance without bill context misleads.
- Safe-to-Spend math (balance − bills before next payday − planned savings, ÷ weeks remaining) → L1 behind "See the math", every variable shown and editable.
- Paycheck-day workflow entry (B8) → surfaces at L0 only on payday; otherwise L1.

**Interaction flow.**
1. Open → hero announces the one next money action.
2. Tap Start → B9 (bill) or B8 (payday) as applicable.
3. Tap a due row → B9 for that bill.
4. Tap Safe to Spend → the math, editable assumptions, "This is an estimate" repeated.
5. Add a bill → 3-field sheet (name, amount, due date; autopay toggle after).

**Default state.** Hero = soonest unhandled bill or, on payday, "Run your money routine (10 min)". If nothing is due ≤7 days: hero becomes "Nothing due this week." with quiet "Check upcoming" link — calm is allowed to be the message.

**Error state.** Bank feed broken (App): "Bank link lost. Numbers may be stale — reconnect when ready." Estimates hide rather than show wrong-confidently: Safe to Spend collapses to "Needs fresh numbers."

**Empty state (teaching moment).** "No bills here yet. Add one — future-you gets a heads-up before it's due." One button: "Add your first bill."

**Lapse/return state.** Money data is never archived by Comeback Mode. On return, the dashboard shows the same hero logic — if something went past due during the lapse, it appears as an `urgent` fact with an action ("Pay now — 2 min"), copy: "This one's past due. Paying today still counts." No accumulation shaming, no late-fee scolding.

**Accessibility notes.** Amounts read with currency and due-in ("Electric, 84 dollars, due in 3 days"); tabular figures; hero first in reading order; the "experimental" label is programmatically tied to the Safe-to-Spend value, not a floating footnote.

**Color usage.** `action` on the hero Start only. Due rows: `attention` amber accents ≤7 days; `urgent` terracotta only for past-due facts, always with an action. Paid confirmations `positive`. Balance text neutral `ink`.

**Typography.** `display` for the hero action (money screens earn the big size), `body` rows, `small` labels/disclaimer. (3 sizes.)

**Spacing.** Hero padding 24 with 32 below; rows 56px; max 5 rows before "Show all" fold (A3 chunking).

**Animations.** Paid tick on rows (~200ms). No number count-up animations (they dramatize; we inform).

**Notifications touching this screen.** Bill cues and payday cue (A5) deep-link here or to B9/B8. Money cues hold top priority within the daily cap.

**Visual hierarchy.** 1st: hero action text. 2nd: Start. 3rd: due-soon rows. Safe to Spend deliberately 4th — it informs restraint, it is not the call to action.

**Progressive disclosure map.** L0: hero, 5 due rows, Safe to Spend + label, add bill. L1: details/charts, balances, the math, all bills. L2: settings, history, Evidence Notes.

**Decision load.** 5 (Start, a due row, Safe-to-Spend math, Add a bill, Details). At target.

> **Evidence:** Problem evidence is strong and observational: [Bangma-2019], [Barkley-2008] (3–4% vs 11% savings), [Swedish-Registry], [Einarsson-2024], [DelayDiscounting-Meta]. The dashboard's design is T2 (indirect) for one-next-action + cue structure [Gollwitzer-2006], [Offloading-2025] and T3 as a money feature — **no tool or feature is validated against financial outcomes (§5.3)**; Safe to Spend is labeled experimental for exactly this reason · **Confidence:** Low (feature), High (problem) · **Rationale:** bills fail from prospective-memory gaps more than money gaps; surfacing the one due action attacks the failure point · **Expected outcome:** bill-payment timeliness and fewer late fees (§11 metrics 1–2) — measured, never promised · **Downside:** estimate errors could misguide spending; mitigated by labeling, visible math, and hiding stale numbers · **Difficulty:** Medium (Notion/spreadsheet manual entry), High (App bank feeds) · **Priority:** High

### B8. Paycheck-day workflow

**Purpose.** A stepwise wizard that runs the highest-stakes money ritual on the day money arrives: **bills → savings transfer → spending money**. Each step is one pre-written if-then prompt [Gollwitzer-2006] so the decisions were made earlier and payday is execution only.

**Visible elements (hierarchy order).**
1. Step content (one of three), with its if-then line at top, e.g. step 2: "If my paycheck lands, then I move $40 to savings right away."
2. One primary action button (action color): "Set these aside" / "Move it now" / "Done — that's my week".
3. Progress: 3 dots + "Step 1 of 3 · about 3 min".
4. Pause and Skip-step links (exit-safe, resumable — same chassis as B5).

**The three steps.**
1. **Bills until next payday:** checklist of bills due before the next paycheck, pre-checked, with total. Action: mark set-aside/scheduled (Notion) or open bank per bill (App deep-link).
2. **Savings transfer:** the pre-decided amount (set during setup/Weekly Reset, editable), one action. Optional **auto-escalation** offer, off by default, shown at most twice a year: "Raise it by $5 next time? You can undo this." — mechanism from [ThalerBenartzi-2004], stated with its honesty caveat in Evidence Notes (original causal evidence rated low; mechanism widely adopted).
3. **Spending money:** what remains, split per week: "About $85 a week is yours to spend — estimate." Sets the Safe-to-Spend inputs on B7.

**Hidden elements (progressive disclosure, and why).**
- Per-bill detail → L1 (tap a row → B9). The step needs the set, not each bill's story.
- Amount editing, payday schedule, split rules → L1 under "Adjust". Defaults do the work [Jachimowicz-2019]; adjustment is the exception.
- Past paydays log → L2.

**Interaction flow.**
1. Payday cue (A5) or B7 hero → step 1.
2. Confirm bills set-aside → step 2 → do the transfer (App: open bank with amount copied; future App ambition, not promised here: initiate transfer) → step 3 → see the weekly number → done.
3. Any step skippable; wizard resumes where left; finishing updates B7.
4. Completion: "Money routine done. See you next payday." + `positive` tick.

**Default state.** Amounts and checklist pre-filled from bill list and saved decisions — the target is **zero typing on payday**.

**Error state.** Paycheck didn't land: step 0 interject — "Paycheck not showing yet? Come back when it lands." (single button reschedules the cue for tomorrow; no shame). Bank-open fails: show amount + account name to do it manually.

**Empty state (teaching moment).** No bills entered: "First payday here? Add the bills that come out of this check — then this takes 10 minutes."

**Lapse/return state.** Skipped paydays are not tallied. Next payday cue fires as normal. If mid-cycle money already moved, steps show "Looks handled — skip?".

**Accessibility notes.** If-then line is the step's heading (announced first); checklist rows ≥44px with amounts read in full; focus to heading on step change; wizard never times out.

**Color usage.** `action` on each step's single button. Bill rows `attention` when due before next payday. Savings confirmation `positive`. No urgency theatrics.

**Typography.** `title` if-then heading, `body` content, `small` progress. (3 sizes.)

**Spacing.** One step per viewport; checklist capped at visible 5 + fold; 32 before the action button.

**Animations.** Step slide ≤250ms; ticks on completion. Reduced motion: instant.

**Notifications touching this screen.** Payday cue: "Payday. Run your money routine? About 10 minutes." (top cap priority). Optional next-day catch-up if untouched, once: "Money routine still open — 10 minutes when you're ready." Then silent until next payday.

**Visual hierarchy.** 1st: the if-then line. 2nd: the single action button. 3rd: the numbers (total / amount / weekly split).

**Progressive disclosure map.** L0: step, action, progress, skip/pause. L1: bill detail, adjust amounts/schedule. L2: history, escalation settings.

**Decision load.** Per step: 3–4 (act, adjust, skip, pause). Under target.

> **Evidence:** T2 (indirect): implementation intentions d = 0.65 [Gollwitzer-2006]; defaults d = 0.68 [Jachimowicz-2019]; auto-escalation mechanism [ThalerBenartzi-2004] *with its causal caveat stated*; just-in-time, action-linked money design beats courses [KaiserMenkhoff-2020], [Fernandes-2014]. T3 for the workflow as an ADHD money feature — untested against financial outcomes (§5.3); problem mandate from [Bangma-2019], [DelayDiscounting-Meta] · **Confidence:** Moderate (mechanisms), Low (feature) · **Rationale:** payday is the moment of maximum money and maximum impulse risk; pre-decided steps spend it on purpose before it evaporates · **Expected outcome:** savings-transfer completion rate (§11 metric 3) · **Downside:** irregular incomes break the model (planned variant: "when money arrives" trigger); bank deep-links vary by bank · **Difficulty:** Medium (Notion checklist version), High (App) · **Priority:** High

### B9. Bill screen (single bill)

**Purpose.** Everything about one bill, arranged so the next act takes ~2 minutes: **amount, due date, autopay flag, one action button.** A bill screen is a cue-to-action machine, not a record.

**Visible elements (hierarchy order).**
1. Bill name + amount (`display`-weight fact: "Electric — $84.00").
2. Due line, relative + absolute: "Due in 3 days (Thu, Jul 17)".
3. Autopay flag chip: "Autopay is on" (`positive` accent) or "No autopay — manual" (neutral).
4. **The 2-minute action button** (action color): "Pay now (2 min)" — opens the biller/bank link; after returning: "Mark paid".
5. Quiet "Snooze the reminder" link (standard A5 options).

**Hidden elements (progressive disclosure, and why).**
- Payment history → L1. Reassuring occasionally, noise daily.
- Notes, account number, login hint (stored locally/securely; the App never stores credentials in notes — guidance says use your password manager) → L1.
- Edit amount/date/autopay, delete bill → L1 "Edit".
- Reminder timing per-bill → L1 (defaults: 3 days before + day-of, within the global cap).

**Interaction flow.**
1. Arrive from cue, B7 row, or Weekly Reset money minute.
2. Tap "Pay now (2 min)" → external biller/bank opens (App remembers the link; Notion stores it as a property).
3. Return → "Mark paid" is now the single action → tap → `positive` tick, row updates on B7, next cue cancelled.
4. Autopay bills ask nothing: their action button reads "Check it went through" on/after the due date, once.

**Default state.** Next unpaid cycle shown. Amount pre-filled from last cycle for variable bills, marked "≈ last time — update if different".

**Error state.** Amount unknown: "Amount varies. Enter this month's when the bill arrives." (field, not blocker). Broken biller link: "Link didn't open. Here's the amount and account name to pay manually."

**Empty state (teaching moment).** New bill mid-creation shows the why: "Three facts — name, amount, due date — and future-you gets a heads-up in time."

**Lapse/return state.** Past due: `urgent` accent on the due line, copy "Past due. Paying today still counts.", button unchanged ("Pay now (2 min)"). No late-day counter, no fee guessing, no red wall.

**Accessibility notes.** Amount and due read as one sentence first ("Electric, 84 dollars, due in 3 days"); action button first focus stop; autopay chip has text, not color-only; snooze options keyboard-reachable.

**Color usage.** `action` on the one action button. `attention` due-soon accent; `urgent` past-due accent (money fact rule, A1); `positive` for paid/autopay-on. Everything else neutral.

**Typography.** `title` name+amount, `body` lines/button, `small` meta. (3 sizes.)

**Spacing.** Single column; facts block padded 24; 32 before the action button; total screen fits one viewport.

**Animations.** Paid tick (~200ms). Nothing else.

**Notifications touching this screen.** This bill's cues (default 3-days-before + day-of, e.g. "8:00pm — pay the electric bill (2 min). Tap to open the bill screen."), each deep-linking here; snooze per A5; cues auto-cancel on Mark paid.

**Visual hierarchy.** 1st: name + amount. 2nd: due line. 3rd: the action button (visually 3rd, but first in tab order — the eye reads the fact, the hand gets the act).

**Progressive disclosure map.** L0: facts, autopay chip, action, snooze. L1: history, notes, edit, per-bill reminders. L2: delete, advanced schedule.

**Decision load.** 3 (action button, snooze, edit entry point). Well under target.

> **Evidence:** T2 (indirect): cue → pre-decided single action [Gollwitzer-2006] under the [Nordby-2022]/[FOCUS-2023] constraints (Law 5); external memory for the due date [Offloading-2025]; T3 as a money feature — no validated effect on missed bills (§5.3); problem evidence [Bangma-2019], [Swedish-Registry] · **Confidence:** Moderate (mechanism), Low (outcome) · **Rationale:** most late bills are remembering-and-starting failures; one cue plus one 2-minute button removes both · **Expected outcome:** on-time bill share (§11 metric 1) · **Downside:** biller links rot; autopay "check it" nudges could annoy — capped at one · **Difficulty:** Low · **Priority:** High

### B10. Anchor Routines (routines view)

**Purpose.** Habit support without streak tyranny. Each routine shows a **weekly-frequency momentum bar** ("3 of 4 this week") — **no streak counters exist anywhere in the ecosystem** — and the screen sets honest expectations: routines take **2–5 months** to feel automatic [Singh-2024].

**Visible elements (hierarchy order).**
1. Header expectation line (persistent, `small`): "New routines take 2–5 months to stick. Most weeks beats perfect days."
2. Routine rows (max 3 active by default): name · anchor cue ("After coffee") · momentum bar "3 of 4 this week" · **Done today** button.
3. **Add a routine** (quiet; nudges restraint: "One at a time works best.").

**Hidden elements (progressive disclosure, and why).**
- Past weeks' momentum (12-week mini history) → L1 per routine. Trend is reflection material, not daily fuel.
- Target frequency editing, cue editing, pause routine → L1. Set-and-leave by design.
- "Why no streaks?" Evidence Note → L1 from the header line — the most-asked question gets a plain answer: "Streaks punish one bad day. Missing once doesn't undo a habit — research backs this. We count weeks, not chains."
- Archive/retire routine → L2.

**Interaction flow.**
1. Open (or arrive from routine cue) → today's un-done routines listed first.
2. Tap Done today → `positive` fill of one bar segment (~200ms). Done is per-day, once; tapping again undoes (mistake-friendly).
3. Add routine → 3 fields: name, cue ("After I…" — an if-then in disguise [Gollwitzer-2006]), times-per-week target (default 4, not 7 — perfect weeks are a trap).
4. Weekly rollover: bars reset to 0 of N **without ceremony** — last week folds into the L1 history; nothing is "lost".

**Default state.** ≤3 active routines, sorted: not-yet-done-today first. A routine with 0 this week renders its empty bar in neutral — never red, never flashing.

**Error state.** More than target done ("5 of 4"): bar caps with "+1" text — over-delivery acknowledged, not gamified.

**Empty state (teaching moment).** "Start with one routine. Tie it to something you already do — 'after coffee' beats '8:00am'." Button: "Add your first routine."

**Lapse/return state.** Weeks of zero: no accusatory gaps. Copy on return: "Pick up where you are, not where you left off." Momentum bars show only the current week; history (L1) renders missed weeks as quiet gaps without labels. Comeback Mode offers "pause all routines" rather than archiving them.

**Accessibility notes.** Bars expose text ("3 of 4 this week"); Done today ≥44px and toggles with announced state; expectation line is real text, not an image; cue text read with the routine name.

**Color usage.** Momentum fill `positive`; empty segments `line` neutral. **No red at any fill level** — an empty bar is information, not indictment. `action` reserved for nothing here by default (no single next action exists on a list screen; Done today buttons are `positive`-outline). 

**Typography.** `title` routine names, `body` buttons/cues, `small` header line + bar labels. (3 sizes.)

**Spacing.** Rows 64px (name + bar stack); 24 between rows; header line gets 16 breathing room — visible but not looming.

**Animations.** Bar segment fill ≤200ms. **No streak-loss animation exists because no streak exists.** Weekly reset is instant and silent.

**Notifications touching this screen.** Per-routine cue at its anchor time (A5 template: "After coffee: meds list (2 min). Tap when done."), lowest cap priority; default one cue per routine per day, skipped silently when over cap.

**Visual hierarchy.** 1st: first un-done routine's name. 2nd: its Done today button. 3rd: momentum bars. Header expectation line reads last by design — present, never nagging.

**Progressive disclosure map.** L0: expectation line, ≤3 rows, Done buttons, add. L1: history, editing, why-no-streaks note. L2: archive, pause-all.

**Decision load.** 5 with three routines (3 × Done + add + a row expand). At target; grows linearly with routines — the 3-active default is the guardrail.

> **Evidence:** T2 (indirect): habits take 2–5 months, SMD 0.69, self-selected/morning stronger [Singh-2024]; median 66 days and one miss ≠ failure [Lally-2010]; cue-anchoring is implementation-intention structure [Gollwitzer-2006]; the anti-streak stance from [KimCastelli-2021] decay/negative long-term and Law 7. T3 for momentum bars as a specific widget — our design, untested · **Confidence:** Moderate (principles), Low (widget) · **Rationale:** weekly frequency preserves motivation information while deleting the all-or-nothing failure mode · **Expected outcome:** routines survive imperfect weeks; honest timeline expectations reduce week-3 quitting · **Downside:** users trained on streak apps may miss the dopamine of chains; Evidence Note explains the trade · **Difficulty:** Low · **Priority:** Medium

### B11. Anchor Home Base (shared board)

**Purpose.** The household's shared surface: chores that reset themselves, visible ownership without scorekeeping, and an optional co-working timer for starting the hard stuff together. Shared structure, zero blame mechanics.

**Visible elements (hierarchy order).**
1. **This week's chores** list: chore · owner chip (name/avatar) · Done button per row. Grouped by day-ish ("Early week / Late week"), not hourly schedules.
2. **Focus together** card: "Work alongside someone — 25 minutes. **Experimental.**" One Start button. (T3 body doubling, labeled on the surface itself.)
3. Shared **Capture** button (household inbox: "Out of dish soap").
4. `small` note: "Chores reset on their own. Done means done for this round."

**Hidden elements (progressive disclosure, and why).**
- Recurrence settings per chore (weekly/biweekly/monthly; auto-reset — Law 8) → L1. Residents do chores; one setup person tunes schedules.
- Reassign owner, swap week → L1 on row. 
- Completion history → L2, and it is **per-chore, never per-person totals** — no leaderboards, no "Alex did 12, Sam did 3" tallies. Comparison scoreboards are shame mechanics wearing team jerseys.
- Household member management, quiet-hours for shared cues → L2 settings.

**Interaction flow.**
1. Open → your chores float first, others' visible below (transparency without surveillance).
2. Tap Done → `positive` tick; chore leaves the active list; its next occurrence schedules itself silently (auto-reset — no one re-adds "clean litter box" ever).
3. Capture household needs → shared Inbox → processed in either partner's Weekly Reset or a shared B3 pass.
4. Focus together → both parties see a shared 25-minute timer + each picks one task from their own board; end chime optional; nothing is scored, recorded, or streaked.

**Default state.** Current cycle's chores only. Future occurrences invisible (they exist in settings, not in view — the pile stays small).

**Error state.** Two people mark the same chore: last write wins, both see "Done — you two sorted it." (never an ownership conflict dialog). Offline edits merge on sync.

**Empty state (teaching moment).** "Add the chores nobody remembers until they're urgent. Set them once — they come back on their own."

**Lapse/return state.** Undone chores roll into the next cycle **without stacking** ("Vacuum" never becomes "Vacuum ×3"). No per-person miss counts. Copy if a cycle was fully skipped: "New week, fresh list."

**Accessibility notes.** Owner chips carry names in text (not avatar-color-only); Done buttons ≥44px; the Experimental label is part of the Focus-together accessible name; timer is silent by default with optional gentle end sound; shared cues respect *each member's* quiet hours.

**Color usage.** Neutral rows; `positive` ticks; `calm` for the Focus-together card. No `action` hero — a shared board has no single owner-action; each row's Done is `positive`-outline. No urgency colors on chores, ever (a chore is never "overdue red" — it just rolls).

**Typography.** `title` section headers, `body` rows/buttons, `small` notes/labels. (3 sizes.)

**Spacing.** Rows 56px; groups separated 32; ≤5 chores visible per group before fold (A3).

**Animations.** Done tick; timer progress is a static ring updated per minute (no hypnotic sweep). Reduced motion: numeric countdown text only.

**Notifications touching this screen.** Optional per-chore day-of cue, **off by default** for shared chores (default is the board, not nags between partners); Focus-together session-start invite to the other member (single, actionable, declineable without message: "Maybe later" sends nothing back but "Not this time").

**Visual hierarchy.** 1st: your first chore row. 2nd: its Done button. 3rd: Focus together card.

**Progressive disclosure map.** L0: this cycle's chores, Done, capture, Focus together. L1: recurrence, reassign, swap. L2: history (per-chore), members, settings.

**Decision load.** 6 typical (3–4 chore Dones + capture + Focus start). One over target — justified: each Done is the same repeated verb, not a novel decision; cognitive cost scales far below the raw count.

> **Evidence:** T2: environmental structuring and routines per consensus [UKAAN-2021], [NICE-NG87]; automation of recurring resets is Law 8 [Jachimowicz-2019] (indirect) plus maintenance-burden abandonment rationale [Kenter-2023]. Co-working timer: **T3, community-endorsed, no RCTs** [BodyDoubling-HCI], labeled Experimental in the UI per §6; timer widget itself T3 [Hallez-2024] (children) per Law 9 · **Confidence:** Moderate (structure/auto-reset), Low (body doubling) · **Rationale:** recurring chores are pure prospective-memory load; auto-reset deletes that load; shared visibility adds gentle social structure without scorekeeping shame · **Expected outcome:** recurring chores happen without a household manager re-entering them; no partner-resentment mechanics · **Downside:** body doubling may do nothing for many users (it says so on the card); shared boards can expose imbalance — we surface facts, not scores · **Difficulty:** Medium; **Notion limit:** auto-reset needs Notion recurring templates/automations (plan-dependent) — template ships both automated and manual-reset variants · **Priority:** Medium

### B12. First-run setup wizard

**Purpose.** From install to a working system in **≤5 minutes**, with the **first win inside 2 minutes**: one captured item and one chosen next action sitting on the Anchor Daily Board. Smart defaults everywhere [Jachimowicz-2019]; every step skippable; no dead ends. The adherence evidence says early overwhelm kills tools [Kenter-2023] — setup is where we prove we're different.

**Visible elements (hierarchy order).**
1. Current step (one prompt, one input or one confirm — same one-decision chassis as B5).
2. Primary button (action color): "Save it" / "Make it my next action" / "Looks good" / "Finish".
3. Progress: 5 dots + "about 1 min".
4. **"Skip for now"** on every step (equal visual weight to Continue on optional steps).

**The five steps.**
1. **Capture one thing** (≤60s): "What's one thing on your mind? Anything counts." → The Inbox exists and works. *(First win, part 1.)*
2. **Pick your next action** (≤60s): that item (or a fresh one) gets a first action and lands in Now on B1. Copy: "That's it. That's the system." *(First win, part 2 — inside 2 minutes.)*
3. **Confirm defaults** (one screen, one button): quiet hours 9pm–8am · max 3 notifications/day · Weekly Reset Sunday 5pm · 3-task daily cap. "Looks good" accepts all; "Change something" opens L1 editors. Notification permission is requested *here*, after the defaults are visible — ask once, with the cap on screen.
4. **Add one bill** (optional, skippable): name, amount, due date → first cue scheduled. "Skip for now" prominent.
5. **Pick one routine** (optional, skippable): choose from 6 starter routines (exactly 6 — a deliberate [IyengarLepper-2000] nod) or write one; anchor it to an existing habit ("after coffee").

**Hidden elements (progressive disclosure, and why).**
- All settings beyond the four defaults → L2 post-setup. Setup is not the settings screen.
- Data import, calendar linking, household invites, bank feed (App) → L1 "Later" checklist that lands on the board's overflow menu as "Finish setting up (3 things)" — never blocking day one.
- Evidence Notes and "what we don't claim" → L1 link on the final screen: "This is a self-help tool, not treatment. See what the evidence says."

**Interaction flow.**
1. Step 1 capture → 2 pick next action → **board is now alive** → 3 confirm defaults (+ permission) → 4 bill (or skip) → 5 routine (or skip) → land on B1 with Now populated.
2. Quitting mid-way keeps everything done so far; reopening resumes (exit-safe, like B5).
3. Total interactive time budget: ≤5 minutes; steps 1–3 alone ≤3 minutes.

**Default state.** Step 1, keyboard up, zero fields pre-required. No account questionnaire, no "tell us about your ADHD" quiz — profiling is not a prerequisite for a captured thought.

**Error state.** Notification permission denied: "No problem. Cues stay off — turn them on anytime in settings." (System keeps working; nothing re-begs.) Sync/account issues never block steps 1–2, which work locally.

**Empty state (teaching moment).** The wizard *is* the ecosystem's teaching moment; each step teaches by doing its feature once, in ≤12-word instructions, not by tour screens. No feature carousel, no 9-slide onboarding.

**Lapse/return state.** Abandoned setup: next open resumes at the incomplete step with everything prior intact. After 7+ days: Comeback logic applies even here — "Pick up where you left off (about 2 min left)."

**Accessibility notes.** Focus to step heading per step; permission prompts preceded by in-app explanation (no naked OS dialogs); all steps keyboard-completable; time estimates are text, not timers; voice capture available from step 1.

**Color usage.** `action` on each step's primary button only. `calm` accents on skip confirmations ("Skipped — you can add this later."). No progress-pressure colors.

**Typography.** `title` step prompts, `body` inputs/buttons, `small` progress + reassurances. (3 sizes.)

**Spacing.** One decision per viewport; 32 between prompt and input; Skip visually adjacent to primary (not hidden in a corner as a dark-pattern ghost).

**Animations.** Step slide ≤250ms; a single completion tick at the end. **No confetti.**

**Notifications touching this screen.** None sent during setup. Setup *schedules* the first cues (bill, Weekly Reset) and states each one aloud as it does: "We'll nudge you Sunday at 5pm. Change it anytime."

**Visual hierarchy.** 1st: step prompt. 2nd: input/primary button. 3rd: Skip for now.

**Progressive disclosure map.** L0: five steps, primary, skip, progress. L1: default editors, starter-routine list, "Later" checklist. L2: full settings, imports, integrations, Evidence Notes.

**Decision load.** Per step: 2–3 (input, primary, skip). The five-step total asks ≤7 decisions to a working system — the smallest honest number we could reach.

> **Evidence:** T2 (indirect): defaults d = 0.68 [Jachimowicz-2019]; restrained option sets [IyengarLepper-2000]; early-win rationale is T3 — immediate reinforcement is real but short-term [KimCastelli-2021], and the real target is beating documented early abandonment [Kenter-2023] (29% completion), [FOCUS-2023]; capture-first start per Law 4 [Offloading-2025] · **Confidence:** Moderate · **Rationale:** the first session must deliver the product's core loop once (capture → one next action), not describe it · **Expected outcome:** higher week-1 activation into the Daily Board and first Weekly Reset; setup completion ≥ step 3 for most installs · **Downside:** skipped optional steps mean some users never meet money/routines — the "Finish setting up" checklist is the recovery path · **Difficulty:** Medium; **Notion limit:** Notion templates can't run a true wizard — shipped as a numbered "Start here" page with checkboxes mirroring the five steps and pre-filled defaults · **Priority:** High

---

## Cross-cutting compliance notes

- **Law coverage:** every screen above names its laws; Law 10 (Measure function, not engagement) governs all of them — no screen contains DAU-bait, streaks, or session-length mechanics, and each metadata block points at a §11 functional metric.
- **Evidence honesty in-product:** Evidence Notes (§8) are reachable from B1, B7, B10, B11, and setup step 5's closing screen — every place a tier-label question ("is this proven?") is likely.
- **What we never claim (§5, §10):** no screen or its marketing may say "clinically proven", promise financial outcomes, or imply the UI itself is ADHD-tested. The tested things are the workflows these screens scaffold; the screens are our best honest translation.
- **Open measurement obligations (Part 14):** the 3-task cap value, Safe-to-Spend accuracy, Comeback Rate lift, and momentum-bar comprehension are all our own untested design decisions flagged for the Anchor Lab research pipeline.

---

*Prev: [04 — Product Specifications](04-product-specifications.md) · Next: [06 — Notion Implementation](06-notion-implementation.md) · Full index in [README](README.md).*
