# Beam Workflow Library: favourite workflows

- **Exported:** 2026-11-24
- **Favourites:** 2 of 6 workflows
- **Library:** Beam Workflow Library v1 (beamnxw)
- **Order:** library order (BWL-002, BWL-005)

## Contents

1. BWL-002: Turn research into a technical guide
2. BWL-005: Evaluate and report an issue

---

## BWL-002: Turn research into a technical guide

- **ID:** BWL-002
- **Category:** Research & writing
- **Role sequence:** Planner → Writer → Evaluator → Owner
- **Scope seed:** technical-guide

### Task

Turn a research report the owner has accepted into an original guide with a stated audience, prerequisites, concrete steps and limits, without inventing firsthand use.

### Inputs

- The accepted research report with its source list (for example the output of BWL-001)
- Audience, and what they should be able to do afterwards
- Prerequisites the reader is assumed to have
- Examples that were really run or verified, and by whom (or none)
- Format, length and tone
- Tools the session really has

### Role sequence

1. **Planner**: Fixes audience and purpose and outlines the guide, mapping each section to claims in the report. Hands on: An outline and a list of gaps in the report.
2. **Writer**: Drafts the guide from the report only, keeping each claim attached to its source. Hands on: A draft with every step marked as verified example or not run here.
3. **Evaluator**: Traces each step and claim back to the report and removes implied firsthand experience. Hands on: The checked draft and a list of changes.
4. **Owner**: Edits, accepts or returns the guide and decides whether it is published. Hands on: A decision on the draft.

### Steps

1. Paste the research report and fill in audience, purpose and prerequisites.
2. Planner pass: review the outline and settle any gap that would make a step misleading.
3. Writer pass: draft audience, prerequisites, numbered steps with expected results, limits and sources.
4. Mark each step "Verified example supplied" or "From sources, not run here".
5. Evaluator pass: trace every step and claim to the report and remove firsthand wording that was not supplied.
6. Read the guide and the gap list, then decide what happens next.

### Prompt

```text
You are helping me turn a research report into a technical guide. Work through the three passes below in order. Each pass is a responsibility, not a separate worker. I am the operator: I supply the inputs, hand work from one pass to the next, and make every decision about the result.

<inputs>
Audience: {{AUDIENCE}}
What the reader should be able to do afterwards: {{PURPOSE}}
Prerequisites the reader already has: {{PREREQUISITES}}
Format, length and tone: {{FORMAT_LENGTH_TONE}}
</inputs>

<research_report>
{{RESEARCH_REPORT_WITH_SOURCES}}
</research_report>

<verified_examples>
{{EXAMPLES_ACTUALLY_RUN_AND_BY_WHOM_OR_NONE}}
</verified_examples>

<tools>
Tools available in this session: {{TOOLS_AVAILABLE}}
If a tool is not listed above, you do not have it. Say what you could not do instead of describing a result you did not observe.
</tools>

The research report is the only source of facts for this guide. Do not add facts from memory or from tools, even where the report looks incomplete.

Pass 1 - Planner
Write a short outline. Next to each section, note which claims in the report it rests on. List anything the guide needs that the report does not cover. If a gap would make a step unsafe or misleading, stop and ask me before drafting.

Pass 2 - Writer
Draft the guide in this order:
1. Who this is for, and what they will be able to do.
2. Prerequisites.
3. Steps, numbered. Each step says what to do and what the reader should see when it worked.
4. Limits: what the guide does not cover, known failure cases, and anything date-sensitive.
5. Sources, carried over from the report with their links.
Mark every step either "Verified example supplied" (it appears under <verified_examples>) or "From sources, not run here".

Pass 3 - Evaluator
Re-read the draft as someone who did not write it. Trace every step and every factual claim back to the report. Remove or flag anything you cannot trace. Remove any sentence that implies firsthand use, such as "I ran", "we tested" or "in our experience", unless it quotes a supplied verified example and names who ran it.

Output format
- The guide.
- Gaps: what the report did not cover.
- Changes made in Pass 3, one line each.

Rules
- No invented firsthand experience, results, timings or savings.
- Keep each claim attached to its source link from the report.
- Write for the stated audience. Explain a term the first time it appears if the prerequisites do not cover it.
- Do not describe the guide as reviewed, approved or tested. That is my decision.

Before you finish, answer each line with yes, no or not checked:
- Every step and claim traces to the research report.
- Every step states its expected result.
- No sentence claims firsthand use that was not supplied.
- The limits section is present and specific.
- Source links are retained.
```

### Completion checks

- [ ] No invented firsthand experience.
- [ ] Every step identifies its expected result.
- [ ] Claims retain their source links.
- [ ] Every step and claim traces to the research report.
- [ ] A specific limits section is present.

### Authority boundaries

- No new facts beyond the research report, even where it looks incomplete.
- No statement that the guide was tested, reviewed or approved.
- No results, timings or savings that the report does not contain.
- Publication is the owner's decision.

### Sources

- [Claude Code Docs: Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
  - Publisher: Anthropic (Claude Code documentation)
  - Published: Living page, no fixed date. Read: 2026-11-10.
  - What this card takes from it: Loose support only. We take two ideas: supply the context the session cannot find for itself (here, audience and prerequisites), and have the work re-read by a reviewer that did not write it. The page is about coding sessions; the guide structure and the firsthand-use rule are our own adaptation.

---

## BWL-005: Evaluate and report an issue

- **ID:** BWL-005
- **Category:** Quality & handoff
- **Role sequence:** Evaluator → Recorder → Owner
- **Scope seed:** evaluate-result

### Task

Check a supplied result against its contract without editing it, and report passed, failed and untested checks separately, with reproduction steps for every failure.

### Inputs

- The feature contract or expected behaviour
- The specific result snapshot (commit, build, archive or local URL) and how to start it
- Environment details: OS, browser, runtime versions
- Verification tools the session really has (browser automation, test runner, or none)

### Role sequence

1. **Evaluator**: Confirms the snapshot, exercises each contract check and sorts it into Passed, Failed or Untested. Hands on: Findings with evidence for each check.
2. **Recorder**: Writes the report and one reproducible issue for every failed check. Hands on: The issue report.
3. **Owner**: Decides what the findings mean: accept, send back for repair, or re-test. Hands on: A decision. The report itself gives no verdict.

### Steps

1. Paste the contract, name the exact snapshot and list the verification tools available.
2. Evaluator pass: confirm the snapshot identity before testing anything.
3. Exercise each check as a user would where tools allow. Otherwise inspect and label it "Inspected, not run".
4. Sort every check into Passed, Failed or Untested.
5. Recorder pass: write an issue with steps, expected and actual result, and evidence for each failure.
6. Read the report and decide what happens next. Run the untested checks yourself if they matter.

### Prompt

```text
You are helping me evaluate a result against its contract and report what you find. You report; you do not fix. Work through the two passes below in order. Each pass is a responsibility, not a separate worker. I am the operator: I supply the inputs, hand work from one pass to the next, and make every decision about the result.

<contract>
{{FEATURE_CONTRACT_OR_EXPECTED_BEHAVIOUR}}
</contract>

<inputs>
Result snapshot (commit, build, archive or local URL): {{RESULT_SNAPSHOT_ID_AND_LOCATION}}
How to start it: {{STARTUP_INSTRUCTIONS}}
Environment (OS, browser, runtime versions): {{ENVIRONMENT}}
</inputs>

<tools>
Tools available in this session: {{TOOLS_AVAILABLE}}
If a tool is not listed above, you do not have it. Say what you could not do instead of describing a result you did not observe.
</tools>

Pass 1 - Evaluator
First confirm you are looking at the snapshot named above, and say how you confirmed it. Then take the contract checks one at a time. Where your tools allow, exercise the result the way a user would and compare what you see with the expected result. Where they do not, you may read the code, but record that as "Inspected, not run". Judge the snapshot itself, not anyone's description of it.

Put every check in exactly one group:
- Passed: you ran it and observed the expected result.
- Failed: you ran it and observed something different.
- Untested: you could not run it. Give the reason and the steps I can use to run it.

Pass 2 - Recorder
Write the report in the format below. For every failed check, write an issue someone else can reproduce without asking you anything.

Output format
1. Snapshot evaluated, and how it was confirmed.
2. Environment and tools actually used.
3. Counts: passed, failed, untested.
4. Passed: check number and the evidence you saw.
5. Failed: one issue per check, with
   - Title
   - Steps to reproduce, numbered, starting from a fresh start of the app
   - Expected result, quoted from the contract
   - Actual result
   - Evidence: command output, log line or screenshot path
   - Location in the code, only if you found it
6. Untested: check number, reason, and how to run it.
7. Outside the contract: other problems you noticed, clearly separated.

Rules
- Do not edit, repair or re-run the build with changes. If you changed anything in order to test, say exactly what.
- Do not move a failure to "passed" because the rest looks good, and do not call a problem minor unless the contract does.
- Report gaps against the contract. Leave out style preferences the contract does not mention.
- State any tool you did not have. A check you could not run is untested, never passed.
- Give no overall approval or rejection. I decide what happens next.

Before you finish, answer each line with yes, no or not checked:
- Passed, failed and untested checks are in separate lists.
- Every failure has reproduction steps, expected result and actual result.
- The snapshot identifier appears in the report.
- Missing tool access is disclosed.
- Nothing in the result was edited.
```

### Completion checks

- [ ] Passed, failed and untested checks are distinct.
- [ ] Every failure includes reproduction steps and the expected behaviour.
- [ ] Missing tool access is disclosed.
- [ ] The report names the snapshot that was evaluated.
- [ ] Nothing in the result was edited during evaluation.

### Authority boundaries

- Report only: no fixes, no silent edits to the result.
- Findings come from the snapshot itself, not from a description of the work.
- A check that could not be run is untested, never passed.
- No overall approval or rejection. That decision belongs to the owner.

### Sources

- [Anthropic: Harness design for long-running apps](https://www.anthropic.com/research/harness-design-long-running-apps)
  - Publisher: Anthropic
  - Published: 2026-03-24. Read: 2026-11-10.
  - What this card takes from it: The article reports that separating the party judging the work from the party doing it is a strong lever, that an evaluator should exercise the running result as a user would against agreed criteria, and that evaluators tend to talk themselves out of real issues. We adapt this to a report-only prompt with three result groups.
- [Claude Code Docs: Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
  - Publisher: Anthropic (Claude Code documentation)
  - Published: Living page, no fixed date. Read: 2026-11-10.
  - What this card takes from it: Supports review by someone who did not write the code, reviewing against the spec, and reporting gaps that affect correctness while leaving style aside.

---

## Note

Original beamnxw material. These six cards are our own adaptations of public guidance, not official Anthropic presets. The library prepares instructions for a person to paste into a session; it does not run a model or orchestrate agents. Roles are responsibilities and handoffs carried out in sequence, not separate workers and not evidence of parallel execution. No prompt in this library has been tested in a separate Claude session.

The three source pages were read by plain HTTP request on 2026-11-10 and are used as methodological grounding only. Each source line says what the card takes from the page.
