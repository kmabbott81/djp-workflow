# 00 — Evidence Foundation (Canonical Source of Truth)

> **Status:** Canonical. Every document in `docs/adhd-product-ecosystem/` must trace its claims to this file.
> **Sources:** Four independent evidence reviews supplied 2026-07-13 (referred to below as the *Copilot review*, *ChatGPT review*, *Claude review*, and *Gemini review*). This file synthesizes them, resolves their conflicts, and defines the shared vocabulary, evidence tiers, citation registry, design laws, and metadata format used across the blueprint.
> **Prime directive:** Never invent evidence. Never exaggerate certainty. When evidence is weak, say it is weak. When it is mixed, say it is mixed. When something is marketing, call it marketing.

---

## 1. How to use this document

1. Any claim of the form "X improves Y for adults with ADHD" must carry a **citation key** from §4 and a **tier label** from §3.
2. If a claim cannot be traced to §4, it must be written as *design rationale* ("we believe / mechanism-plausible / untested"), never as evidence.
3. Where the four source reviews disagree, the **ruling** in §6 wins.
4. Every substantive product recommendation uses the **metadata block** in §9.
5. Marketing copy must pass the language rules in §10 (elaborated in Part 13).

---

## 2. The four source reviews: convergence and divergence

All four reviews investigated the same question — which design features of digital budgeting, planning, organization, and executive-function tools are evidence-based for adults with ADHD, versus a static spreadsheet/planner baseline.

**Where all four converge (high confidence in the synthesis):**

- The strongest evidence supports **structured CBT-derived / metacognitive executive-function scaffolding** (calendar + task-list systems, task decomposition, time-management training, prioritization, problem-solving, distraction capture, review loops) — as *packages*, delivered live or digitally.
- **Digital delivery works when it delivers those same active ingredients** (multiple adult RCTs: attexis, MyADHD/Kenter, Pettersson iCBT, Inflow app, Living SMART, smartphone-assisted psychoeducation).
- **No head-to-head trial** compares an "ADHD-specific" planner/budget tool against Excel, Google Sheets, a printable, or a conventional planner. Superiority claims versus spreadsheets are **inference from mechanism**, not directly proven.
- **Financial dysfunction in adult ADHD is well documented** (more debt, less saving, impulsive buying, lower measured financial competence), but **no trial validates any budgeting tool or feature** against financial outcomes.
- **Refuted or unsupported:** "brain training" for real-world gains; neurofeedback superiority over sham; reminder-only systems; chatbot superiority over a decent conventional app; punitive streaks as a durable driver; "21-day habit" claims; financial-literacy education as a behavior-change engine; virtually all "ADHD-proven" app-store marketing (a systematic review found 109 ADHD apps, none with proof of effectiveness).
- **Adherence/abandonment is the central design bottleneck** (e.g., only 29% of MyADHD users completed all modules; FOCUS app engagement waned).

**Where they diverge (and how we rule — details in §6):**

- The **Gemini review** rates several isolated UI features (visual simplification, reminder systems, time-blindness widgets, financial friction, interactive checklists) as "clinically proven," partly on mechanistic/neurobiological grounds and partly on non-peer-reviewed sources (blogs, vendor pages) and child studies. The other three reviews rate the same features as *indirect, package-level, or experimental*. **Ruling: we adopt the conservative consensus.** Mechanistic plausibility is design rationale, not clinical proof.
- The Gemini review's neurobiological framing ("dopaminergic hypofunction destabilizes working memory") is a useful explanatory model but is stated more confidently than the clinical literature warrants; we use such framing sparingly and label it as mechanism, not outcome evidence.

---

## 3. Evidence tiers (used everywhere in this blueprint)

| Tier | Label | Meaning | Marketing language allowed |
|---|---|---|---|
| **T1** | **Clinically supported** | Adult-ADHD RCT(s) and/or meta-analytic support for the *intervention class or component* | "Built on strategies tested in randomized trials with adults with ADHD" |
| **T2** | **Moderately supported** | Package-level adult-ADHD evidence where the specific feature wasn't isolated, OR strong replicated evidence from general/clinical populations (indirect for ADHD) | "Based on principles studied in [population]; not yet tested in ADHD-specific trials" |
| **T3** | **Experimental** | Plausible mechanism; early, indirect, survey/HCI, or child-population evidence only | "Experimental — community-endorsed / mechanism-plausible, unproven" |
| **T4** | **Unsupported / refuted** | No supporting evidence, or trials show null/negative results | May not be marketed as beneficial. If shipped at all, labeled experimental and non-punitive |

**Confidence labels** (per recommendation): **High** (consistent findings, adult ADHD, low-moderate risk of bias), **Moderate** (consistent but indirect or package-level), **Low** (single study, high heterogeneity, or extrapolated).

A critical structural fact about this entire evidence base, acknowledged by all four reviews: **the unit of proof is almost always the multi-component package, not the isolated feature.** Component-level certainty is always lower than package-level certainty. An umbrella review of digital ADHD interventions [LopezCampos-2025] rates the overall field's evidence quality as low and notes ~30% of included reviews reported adverse effects (mostly video-game-based formats, including problematic-use/addiction signals) — a reason for humility and for measuring outcomes, not just shipping features.

---

## 4. Canonical evidence registry

Only the citation keys below may be used in this blueprint. Each entry lists: finding → tier for design translation.

### 4A. Core psychosocial treatment evidence (the "active ingredients")

| Key | Study | Finding | Tier |
|---|---|---|---|
| [Cochrane-2018] | Lopez et al., Cochrane review; 14 RCTs, n=700 adults 18–65 | CBT vs waitlist: self-rated ADHD SMD −0.84; CBT+meds vs meds alone: clinician-rated SMD −0.80. QoL not clearly improved. Certainty **very low → moderate**; short-term, heterogeneous | T1 (package) |
| [Knouse-2017] | Meta-analysis, 32 CBT studies, up to 896 adults | Symptoms vs control g = 0.65; functioning g = 0.51. Pre-post g ≈ 1.00 (95% CI 0.84–1.16); functioning 0.73. Effects **smaller vs active controls** | T1 (package) |
| [Young-2020] | Systematic review/meta-analysis of CBT RCTs for adult ADHD | Supports CBT efficacy; consistent with [Cochrane-2018] | T1 (package) |
| [Safren-2010] | RCT, n=86 medicated adults with persistent ADHD; 12-session CBT vs relaxation + educational support | ADHD rating d = 0.60; CGI d = 0.53; responders 67% vs 33%. Modules: calendar/task-list system, task breakdown, distractibility management ("write it down, return to task"), cognitive restructuring, procrastination, relapse prevention. Gains maintained at 6/12 months among responders | T1 (package & named components) |
| [Solanto-2010] | RCT, n=88 clinically diagnosed adults; 12-week group metacognitive therapy (MCT: time management, organization, planning) vs supportive therapy | Response OR 5.41 (95% CI 1.77–16.55); blind-rated AISRS-inattention improved 2.7 points more (95% CI 0.9–4.6; ≈0.56 SD). Home-exercise completion correlated with improvement. Active control strengthens causal claim | T1 (package & named components) |
| [Matsumoto-2024] | Component network meta-analysis of CBT for ADHD (BMJ Mental Health) | **Organisational strategies**: incremental OR 2.03 for treatment response. **Problem-solving techniques**: incremental SMD 0.42 for inattention. Third-wave (mindfulness/acceptance) components useful adjuncts. Best available *component-level* evidence; spans ADHD broadly — interpret carefully | T1 (components, with caution) |
| [Lauder-2024] | Meta-analysis of interventions for **work-relevant outcomes** in adult ADHD; 23 studies, n=3,835 | Psychosocial interventions pooled d = 0.56 on time management, organization, productivity, work functioning — vs d = 0.19 for pharmacological in this domain. CBT most robust | T1 (domain-relevant package) |
| [LGO] | "Let's Get Organised" (LGO-S) occupational-therapy time-management group protocol; multi-centre RCT protocol + pragmatic group time-management RCT (Gemini review) | Structured teaching of calendars, external timers, checklists improves time management and reduces inattention | T1 (package; cited less precisely — treat as supportive) |
| [NICE-NG87] | NICE guideline NG87 (2018/2019) | Recommends structured supportive psychological intervention focused on ADHD with **regular follow-up**, possibly with CBT elements. Notes ADHD symptoms (time management, forgetfulness) impair adherence to plans; emphasizes daily structure and tailored information | Guideline (T1-adjacent) |
| [UKAAN-2021] | Young et al., UK Adult ADHD Network occupational-therapy consensus | Consensus recommendations for OT interventions in adult ADHD (environmental structuring, routines) | Consensus (T2) |

### 4B. Digital delivery RCTs in adults with ADHD

| Key | Study | Finding | Tier |
|---|---|---|---|
| [attexis-2026] | D'Amelio et al., pragmatic RCT, n=337 adults with confirmed ADHD; fully self-guided digital CBT + mindfulness + reminders/self-monitoring vs TAU | ASRS baseline-adjusted mean diff −5.0, **d = 0.85**, p<.001 at 3 months; secondary gains in work/social functioning, depression, self-esteem, QoL (d = 0.32–0.61); effects present at 6 months. Caveats: self-report outcomes, sponsor conflict, package not feature-isolated | T1 (digital package) |
| [Kenter-2023] | "MyADHD" self-guided internet intervention RCT, n=120 adults with **self-reported** ADHD, vs online psychoeducation, 8 weeks | Symptoms d = 0.70; QoL d = 0.53 (3-month: 0.76 / 0.52). **Only 29% completed all modules; 59% ≥5 of 7** | T1 (digital package); adherence caveat |
| [Pettersson-2017] | iCBT RCT, n=45 diagnosed outpatients, vs waitlist | d = 1.07, maintained at 6 months. Small sample, waitlist comparator | T1 (digital package) |
| [Nasri-2023] | 3-arm RCT, n=104 outpatients (67% medicated): iCBT vs internet applied relaxation (iART) vs TAU, 12 weeks | iCBT vs TAU d = 0.42 post, 0.67 at 3 months, sustained to 12 months — but **iCBT NOT superior to active relaxation** | T1 vs TAU; humility about specificity |
| [Inflow-2026] | Antshel, McBride & Knouse, RCT n=154 adults; CBT-informed app, 8 weeks vs waitlist | Inattention η² = .15; hyperactive-impulsive η² = .05; ADHD-related QoL η² = .04; **no improvement in functional impairment**. Improvements in organization/time-management/planning behaviors **partially mediated** inattention gains. Waitlist control | T1 (digital package); mediation = key design signal |
| [LivingSMART-2015] | Moëll et al., RCT n=57; guided 6-week online course teaching adults with ADHD/subclinical ADHD to use smartphone apps to structure everyday life, with coach support | ASRS-Inattention 28.1 → 22.9; **33% clinically significantly improved vs 0% of controls** (blind evaluator) | T1 (coached mobile structuring) |
| [Selaskowski-2022] | RCT n=60 adults with ADHD; smartphone-assisted group psychoeducation vs paper brochures | Better inattention/impulsivity; **higher homework compliance**; no adverse events | T1 (mobile homework transfer; single study) |

### 4C. Null, negative, and cautionary findings (design constraints)

| Key | Study | Finding | Implication |
|---|---|---|---|
| [Nordby-2022] | Multiple-randomized trial of weekly SMS reminders inside a self-guided adult-ADHD internet intervention | **No overall effect** on module completion, logins, or practice of coping strategies; only narrow effects (e.g., faster log-in on some modules) | Reminders alone ≠ adherence. Cue must point to a pre-decided, small, low-friction action |
| [FOCUS-2023] | Carvalho et al., RCT n=73 diagnosed adults; monitoring app ± medication discount vs TAU, 3 months | **No improvement in medication possession ratio.** Discount arm: 100% app adoption, more early intake registrations. Engagement declined; retention low | Liked + opened ≠ outcomes. Immediate incentives move adoption, not sustained adherence |
| [Selaskowski-2023] | Chatbot-supported psychoeducation RCT (n=40 randomized / 34 completers) vs conventional app | Both improved; **no group×time superiority; no knowledge-quiz advantage** | Conversational AI is not a proven active ingredient |
| [Jang-2021] | Chatbot CBT/psychoeducation vs self-help book, n=46 "adults with attention deficit" (not all formally diagnosed) | ITT improvements (hyperactive-impulsive F=4.39 p=.04; total F=6.74 p=.01); per-protocol mainly impulsivity | Mixed, preliminary; does not overturn [Selaskowski-2023] |
| [Stern-2016] | Computerized cognitive training RCT, adults with ADHD, vs active control | **No significant** time×group benefit on neurocognition or QoL | No brain-training claims |
| [Elbe-2023] | Meta-analysis, 9 RCTs, n=285 adults: cognitive training | Overall effect barely significant (p=.048); **no significant improvement** for executive function, speed, short-term memory, or symptoms by outcome | No brain-training claims |
| [NimmoSmith-2020] | Systematic review, adult non-pharmacological RCTs | Working-memory training often null; **neurofeedback no different from sham** or MCT at post and 6 months; calls for functional/QoL core outcomes | No neurofeedback claims; measure function |
| [Zhang-2018] | Meditation-based therapies meta-analysis; 13 RCTs; adult subgroup n=339 | Adult symptoms g = −0.66 **but high heterogeneity, high/unclear risk of bias**; sensitivity analyses weakened results | Mindfulness = cautious adjunct (see [Matsumoto-2024] third-wave) |
| [LopezCampos-2025] | Umbrella review, 26 reviews, n=34,442 | Digital-intervention benefits "**inconclusive due to low evidence quality**"; 8/26 reviews reported adverse effects (esp. video-game-based, incl. addiction signals) | Humility; monitor harms; avoid compulsive-engagement design |
| [Pasarelu-2020] | Systematic review of ADHD mobile apps | **109 ADHD apps (23 psychoeducation): none provided proof of effectiveness** | The market's claims are marketing; ours must not be |

### 4D. The financial problem (need is proven; solutions are not)

| Key | Study | Finding | Tier |
|---|---|---|---|
| [Bangma-2019] | Bangma et al. case-control work on financial decision-making in adult ADHD (n≈45 ADHD / 51 controls; cited across all four reviews, with related papers 2019–2020) | Poorer self-reported financial situation, **more debts, less savings-account ownership, more impulsive buying**, lower standardized financial competence/capacity | Problem evidence (observational) |
| [Swedish-Registry] | Population study: 11.55M Swedish adults + 189,267 credit records (Gemini review) | ADHD adults start adulthood with standard credit metrics; **default rates grow exponentially by middle age**; financial distress associated with **~4× suicide risk**; among men with ADHD who died by suicide, debt rose in the 3 years prior | Problem evidence (observational; registry) |
| [Barkley-2008] | Milwaukee longitudinal study, 27-year follow-up (Claude review) | ADHD adults saved **3–4% of income vs 11%** for controls; substantially lower earnings (up to ~38% less) | Problem evidence (longitudinal) |
| [Pelham-2019] | Long-term financial outcomes of childhood ADHD | Financial gap widens over time | Problem evidence |
| [Einarsson-2024] | Impulsive buying / deferment of gratification in adult ADHD | More impulsive buying; weaker gratification deferral | Problem evidence |
| [DelayDiscounting-Meta] | Meta-analysis of case-control monetary delay-discounting studies in ADHD | **Steeper delay discounting** (stronger preference for immediate smaller rewards) | Problem evidence / mechanism |

**Ruling that governs every money product in this blueprint:** the evidence proves the *problem*, not any *tool*. No claim of proven savings, debt reduction, or bill-payment improvement may be made until we test it ourselves (see Part 14).

### 4E. Behavioral-science evidence (general population — indirect for ADHD, T2 unless noted)

| Key | Study | Finding |
|---|---|---|
| [Gollwitzer-2006] | Meta-analysis of implementation intentions ("if-then" plans); 94 tests, >8,000 participants; updated across 642 tests (Sheeran et al. 2024) | Goal attainment d = 0.65 (medium-large). Directly implementable: "If it is 8pm, then I pay one bill" |
| [Offloading-2025] | Meta-analysis, *Memory & Cognition* | Offloading intentions to external reminders reliably improves performance, **greatest for prospective memory** — the core ADHD-relevant deficit |
| [Jachimowicz-2019] | Meta-analysis of defaults; 58 studies, n=73,675 | Default effect d = 0.68 (95% CI 0.53–0.83); heterogeneous (some nulls); consumer-domain defaults stronger |
| [IyengarLepper-2000] | Choice-overload field experiment (jam study) | 6 options → 30% purchase vs 24 options → 3% (10× difference), despite more initial interest in the large display |
| [ThalerBenartzi-2004] | Save More Tomorrow (SMarT) field study | 401(k) savings 3.5% → 13.6% over 40 months; 78% still enrolled after 4 raises. **Caveat:** US DOL CLEAR rated original causal evidence "low" (non-random assignment); mechanism (auto-escalation defaults) later encoded in SECURE 2.0 |
| [Fernandes-2014] | Meta-analysis of financial-literacy education; 201 studies | Explains ~**0.1% of variance** in financial behavior; decays within ~20 months; weaker in low-income samples |
| [KaiserMenkhoff-2020] | Later meta-analysis of financial education | Effects ~5× larger than [Fernandes-2014] but still small; **"just-in-time," action-linked designs** do better than courses |
| [Lally-2010] | Habit-formation cohort study | Median **66 days** to automaticity (range 18–254). **Missing a single occasion did not materially harm** habit formation → design forgiveness in |
| [Singh-2024] | Habit-formation systematic review/meta-analysis; 20 studies, n=2,601 | Habits take **2–5 months**; SMD 0.69 for habit-score gains; morning and self-selected habits stronger. "21 days" is false |
| [SMS-Meta-2023] | SMS medication-adherence meta-analysis (type-2 diabetes) | SMD 0.36 (95% CI 0.14–0.59) — real but modest; two-way/personalized beats one-way blasts. Non-ADHD |
| [KimCastelli-2021] | Gamification meta-analysis (education/behavior change) | d = 0.48 overall but **<1 week d = 1.57 vs ~20 weeks d = 0.30, negative (−0.20) sustained over years** — engagement decays |
| [Li-2023] | Gamification learning-outcomes meta-analysis; 41 studies | g = 0.822 for learning outcomes (short-term, non-ADHD) |
| [ACCESS-2021] | Anastopoulos et al., multi-site RCT, n=250 **college students** with ADHD; CBT + mentoring/coaching | d = 0.39–1.21 on symptoms and executive functioning. Population caveat: college students |
| [PrevattYelland-2015] | ADHD coaching study, n=148 | Supportive but descriptive; coaching plausible, weaker design |
| [BodyDoubling-HCI] | Eagle et al. 2024 and related HCI/survey work; VR body-doubling design studies; BCI poster | Community-endorsed; plausible mechanisms (social facilitation, co-regulation); **no RCTs** |
| [Hallez-2024] | Visual-timer controlled experiment (elementary-school math assessments — **children**) | Visual timers reduced anticipatory anxiety and off-task behavior; heterogeneous engagement. Extrapolation to adults untested |
| [TimePerception-Review] | Decade review of time perception in adult ADHD | Documented deficits in time estimation/reproduction/horizon ("time blindness" as construct) — problem evidence, not intervention evidence |

### 4F. Measures glossary (for consistent reference)

ASRS = Adult ADHD Self-Report Scale. AISRS = Adult ADHD Investigator Symptom Rating Scale. AAQoL = Adult ADHD Quality of Life scale. WSAS = Work and Social Adjustment Scale. MPR = Medication Possession Ratio. OTMP = organization, time-management, and planning behaviors. TAU = treatment as usual. GRADE = Grading of Recommendations Assessment, Development and Evaluation.

---

## 5. What the evidence does NOT show (say this out loud, everywhere it matters)

1. **No direct trial** shows any ADHD-specific planner/budget/dashboard beats Excel, Google Sheets, printables, or a paper planner. All such positioning is mechanism-based inference. (All four reviews.)
2. **No component isolation** for: visual simplification, progressive disclosure, today-only views, countdown timers, streaks, colors, animations, dashboards, AI personalization — in adults with ADHD.
3. **No validated financial features**: nothing shows an app feature reduces debt, missed bills, overdrafts, or impulse spending in adults with ADHD.
4. **QoL gains are inconsistent** ([Cochrane-2018] found QoL not clearly improved; [attexis-2026], [Kenter-2023], [Inflow-2026] found QoL gains; [Inflow-2026] found **no functional-impairment change**).
5. **Long-term (>12 months) durability** of digital-intervention effects is largely unmeasured.
6. **Engagement ≠ outcome** ([FOCUS-2023]: liked, adopted, rated well — primary outcome null).

---

## 6. Conflict rulings (where the four reviews disagree)

| Topic | Divergence | Ruling used in this blueprint |
|---|---|---|
| Visual simplification | Gemini: "clinically proven (moderate)". Others: very low/low, indirect | **T3 (experimental)** as isolated feature; T2 as part of a structured package. Justify via cognitive-load theory + [IyengarLepper-2000], never as ADHD-proven |
| Reminder systems | Gemini: "clinically proven (high)". Others: direct ADHD trials null for adherence ([Nordby-2022], [FOCUS-2023]); indirect SMS meta positive | **T2 only when the cue triggers a pre-decided single action inside a structured system; T4 as a standalone strategy.** Never claim reminders alone fix follow-through |
| Time-blindness widgets (visual timers, countdowns) | Gemini: proven (child study + mechanism). Others: low/very low for widgets; T1 only for time-management *training* | **T3 for widgets** ([Hallez-2024] is children); **T1 for time-management skill scaffolds** ([Solanto-2010], [Lauder-2024]) |
| Financial friction (24h cool-downs, fund-locking) | Gemini: "clinically proven (moderate)". Others: very low, untested in ADHD | **T3 (experimental)**, mechanism-consistent with [DelayDiscounting-Meta]; ship behind honest labeling |
| Interactive checklists | Gemini: proven via [Solanto-2010]. Others: supported within packages | **T1 as part of MCT/CBT-style workflow**; T2 as standalone digital checklist |
| Chatbots/AI | Gemini: experimental-positive; [Jang-2021] mixed positive; [Selaskowski-2023] null superiority | **T3.** Optional delivery layer, never the claimed active ingredient |
| Body doubling | Gemini: moderate (VR/BCI studies). Others: surveys/HCI only | **T3, community-endorsed.** Offer as optional, never market as validated |
| Mindfulness | [Zhang-2018] low certainty vs [Matsumoto-2024] third-wave component support | **T2 adjunct** inside structured systems; never a standalone claim |
| attexis functional outcomes | Gemini: "significant improvements in functional impairment and QoL"; Copilot/ChatGPT: secondary gains d=0.32–0.61 incl. work/social functioning | Report as: secondary outcomes improved (d = 0.32–0.61) including work/social functioning and QoL — while [Inflow-2026] found **no** functional-impairment change; functional outcomes remain the weakest link |
| Neurobiological framing | Gemini asserts dopaminergic mechanisms confidently | Use as explanatory *model* sparingly; label as mechanism, cite outcome studies for outcome claims |

---

## 7. The Ten Design Laws (every feature must satisfy at least one; violations of a law require justification)

| # | Law | Evidence anchor | Tier |
|---|---|---|---|
| 1 | **Externalize, don't educate.** The tool performs or scaffolds the executive function (holds memory, sequences steps, tracks time) instead of teaching about it. ADHD is a performance disorder at the point of performance, not a knowledge disorder | [Fernandes-2014] (education fails), [Offloading-2025], [Safren-2010], [Solanto-2010] | T1/T2 |
| 2 | **One next action.** Every screen resolves to a single, small, pre-decided next step; task decomposition into first action → next action → done criteria | [Safren-2010], [Solanto-2010], [Matsumoto-2024] (problem-solving iSMD 0.42) | T1 |
| 3 | **Reduce decisions.** Fewer options, smart defaults, pre-filled templates, progressive disclosure | [Jachimowicz-2019] d=0.68, [IyengarLepper-2000] 30% vs 3% | T2 (indirect) |
| 4 | **Capture first, organize later.** Zero-friction external memory inbox; offload prospective memory by default | [Offloading-2025] (greatest for prospective memory), [LivingSMART-2015] | T1/T2 |
| 5 | **Cue → pre-decided action.** Reminders exist only to trigger a specific, small, already-decided act ("if 8pm → pay one bill"), never as generic nags | [Gollwitzer-2006] d=0.65; constraint from [Nordby-2022], [FOCUS-2023] | T2 with T1 constraints |
| 6 | **Practice loops and review rituals.** Weekly review, homework-style repetition, relapse-prevention framing; follow-up beats set-and-forget | [Solanto-2010] (homework correlated with gains), [Selaskowski-2022], [NICE-NG87] | T1 |
| 7 | **Forgiveness by design.** Missing a day/week must never punish or reset progress; recovery paths are first-class features. No punitive streaks | [Lally-2010] (one miss ≠ failure), [KimCastelli-2021] (gamification decays/negative long-term), abandonment evidence [Kenter-2023], [FOCUS-2023] | T2 |
| 8 | **Automate everything automatable.** Recurring tasks, categorization, transfers, resets happen without user initiation | [Jachimowicz-2019], [ThalerBenartzi-2004] (with its causal caveat), maintenance-burden abandonment rationale | T2 (indirect) |
| 9 | **Time made visible and scaffolded.** Time-management *workflows* (planning, prioritizing, scheduling) are T1; visual timers/countdown *widgets* are T3 experimental extras | [Solanto-2010], [Lauder-2024]; widgets: [Hallez-2024] (children) | T1 workflow / T3 widget |
| 10 | **Measure function, not engagement.** Success = bills paid, tasks done, weeks retained, recovery after lapse, QoL — never DAU/session length. Engagement is a cost, not a goal | [FOCUS-2023], [NimmoSmith-2020] (core-outcome call), [LopezCampos-2025] (harms) | Governance |

---

## 8. Shared product vocabulary (used by every document)

**Ecosystem working name: "Anchor"** — *placeholder pending trademark/brand validation; all documents use it consistently so it can be search-replaced.*

| Term | Meaning |
|---|---|
| **Anchor Life OS** | Flagship Notion-based life operating system (Part 3 §8, Part 8) |
| **Anchor Money System** | ADHD budget system: stepwise paycheck/bill workflow + financial dashboard (Notion + spreadsheet editions) |
| **Anchor Daily Board** | The planner's default "Today" screen: Now / Next / Later, one next action |
| **The Inbox** | Universal quick-capture (Law 4). Everything enters here; nothing requires filing at capture time |
| **The Weekly Reset** | The 15-minute guided weekly review ritual (Law 6). The single most protected workflow in the ecosystem |
| **Comeback Mode** | The lapse-recovery flow (Law 7): one screen, one button, no guilt, archive-the-backlog |
| **Anchor Routines** | Habit/routine system with miss-tolerant "momentum" metrics (weekly frequency, not streaks) |
| **Anchor Home Base** | Home-management system (shared checklists, recurring chores, capture) |
| **First Action Kit** | Free lead magnet (email opt-in) |
| **Anchor Lab** | Membership/community tier; also the venue for user research and product testing |
| **Anchor App** | Future SaaS (Part 2 roadmap); the only tier where automation (bank feeds, push cues) fully applies |
| **Evidence Notes** | The in-product and on-listing honesty layer: every feature's tier label, in plain language |

**Voice:** plain, warm, specific, non-clinical, never shaming, never hypey. We write like a calm friend who has read the research. Banned vocabulary and claim rules: §10 and Part 13.

---

## 9. Recommendation metadata format (mandatory)

Every substantive recommendation in Parts 1–14 carries this block:

> **Evidence:** T1 / T2 / T3 / T4 + citation keys · **Confidence:** High / Moderate / Low · **Rationale:** one sentence of mechanism · **Expected outcome:** the behavior it should change · **Downside:** the honest risk · **Difficulty:** Low / Medium / High · **Priority:** High / Medium / Low

**Compact tag legend** (allowed in long lists, e.g., the editorial calendar):
`[EF|T1]` = executive-function scaffolding theme, Tier 1 evidence behind the concept taught. Theme codes: EF (executive function), MO (money), PL (planning), HO (home), HA (habits), TB (time blindness), DF (decision fatigue), OR (organization), PW (product walkthrough), RE (research explanation). Tier code = the tier of the underlying claim being taught, per this registry.

---

## 10. Marketing language rules (summary — Part 13 is the full framework)

**Allowed:** "designed around strategies tested in randomized trials with adults with ADHD"; "built on CBT-derived organization and planning methods studied in adults with ADHD"; "we label every feature's evidence level"; "not a treatment."
**Never:** "clinically proven app/template," "treats/cures/fixes ADHD," "rewires your brain," "dopamine hack," "neuroscience-based" (as a vague halo), "guaranteed savings," "21 days to a habit," any outcome promise (finances, symptoms) we have not measured, urgency/scarcity theater, shame-based hooks ("stop being lazy").
**Mandatory disclosure:** these are self-help organization tools, not medical devices or therapy; they don't replace diagnosis, medication, or therapy; if a claim is T2/T3, the adjacent copy must say the evidence is indirect or experimental.

---

## 11. Canonical success metrics (what "working" means)

Primary (functional, user-consented, privacy-respecting; see Part 14 for instrumentation):
1. **Bill-payment timeliness** (self-logged: on-time bills / total)
2. **Late fees & overdrafts per month** (self-logged count)
3. **Savings-transfer completion rate** (planned vs executed)
4. **Task completion rate** on the Daily Board (done / committed, with committed ≤3/day by design)
5. **Weekly Reset completion rate** (target: ≥50% of active weeks — the single strongest leading indicator we can defend from [Solanto-2010] homework-completion correlation)
6. **Retention & recovery:** % active at weeks 4/12/26; **% who return within 14 days after a ≥7-day lapse** (Comeback Rate — our signature metric)
7. **Quality of life / functioning** (optional in-product check-ins adapted in spirit from AAQoL/WSAS-style self-report — clearly framed as self-tracking, not diagnosis)

Explicit non-goals: DAU, session length, notification open rate, streak length. Time-in-tool should trend **down** per unit of life managed (Law 10).

Benchmarks to beat (from the evidence): 29% full-module completion [Kenter-2023]; engagement decay by month 3 [FOCUS-2023]. Target: >40% of buyers still using any core workflow at week 12, measured by voluntary check-in panel (Part 14).

---

*Next: [01 — Product Vision](01-product-vision.md) · Full index in [README](README.md).*
