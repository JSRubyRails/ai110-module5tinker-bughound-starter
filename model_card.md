# BugHound Mini Model Card (Reflection)

Fill this out after you run BugHound in **both** modes (Heuristic and Gemini).

---

## 1) What is this system?

**Name:** BugHound  
**Purpose:** Analyze a Python snippet, propose a fix, and run reliability checks before suggesting whether the fix should be auto-applied.

**Intended users:** Students learning agentic workflows and AI reliability concepts.

---

## 2) How does it work?

Describe the workflow in your own words (plan → analyze → act → test → reflect).  
Include what is done by heuristics vs what is done by Gemini (if enabled).

- BugHound runs a five-step loop: plan a scan, analyze the snippet for issues act by proposing a fix, test it via assess_risk, and reflect on whether it's safe to auto-apply. Heuristics do regex/substring detection and mechanical fixes offline, while Gemini (when enabled) does the analysis and fix generation via prompts, falling back to heuristics on any API error, unparseable JSON, or empty output.

---

## 3) Inputs and outputs

**Inputs:**

- What kind of code snippets did you try?
- What was the “shape” of the input (short scripts, functions, try/except blocks, etc.)?

**Outputs:**

- What types of issues were detected?
- What kinds of fixes were proposed?
- What did the risk report show?


- Inputs were short Python snippets — a clean function, a function with a bare except:/print/TODO, and a comments-only file (mostly small functions and try/except blocks). Outputs were categorized issues (Code Quality/Reliability/Maintainability with severity), fixes like print(→logging.info( and except:→except Exception as e:, and a risk report with score, level, reasons, and a should_autofix flag.

---

## 4) Reliability and safety rules

List at least **two** reliability rules currently used in `assess_risk`. For each:

- What does the rule check?
- Why might that check matter for safety or correctness?
- What is a false positive this rule could cause?
- What is a false negative this rule could miss?


- Bare-except modification penalty: checks whether an except: was changed; this matters because altering error handling can change control flow, but it could false-positive on a genuinely safe narrowing and false-negative if the fix swallows a new exception type.

- Missing-return penalty: flags when return disappears from the fixed code, which matters because a dropped return silently changes behavior, though it false-positives when a refactor legitimately removes a redundant return and false-negatives when a return is kept but its value is wrong.

---

## 5) Observed failure modes

Provide at least **two** examples:

1. A time BugHound missed an issue it should have caught  
2. A time BugHound suggested a fix that felt risky, wrong, or unnecessary  

For each, include the snippet (or describe it) and what went wrong.


- Missed issue: the analyzer never flags real bugs like x / y division-by-zero or the bare except: return 0 that hides errors — it only pattern-matches surface tokens.

- Risky/unnecessary fix: on the comments-only file it flagged a print( inside a comment and rewrote the comment to logging.info(, a destructive edit to non-code (the false positive we later guardrailed).

---

## 6) Heuristic vs Gemini comparison

Compare behavior across the two modes:

- What did Gemini detect that heuristics did not?
- What did heuristics catch consistently?
- How did the proposed fixes differ?
- Did the risk scorer agree with your intuition?


- Gemini can catch semantic issues heuristics miss (e.g., division-by-zero, logic errors) rather than just print/except:/TODO tokens, while heuristics catch those three surface patterns consistently and deterministically. Gemini's fixes tend to be more context-aware, whereas heuristic fixes are blunt string replacements — and the risk scorer, being token-based, agreed with intuition only for obvious cases.

---

## 7) Human-in-the-loop decision

Describe one scenario where BugHound should **refuse** to auto-fix and require human review.

- What trigger would you add?
- Where would you implement it (risk_assessor vs agent workflow vs UI)?
- What message should the tool show the user?


- BugHound should refuse to auto-fix when a Medium/High-severity issue is present even if the score lands in "low" — the exact trigger we added in assess_risk (should_autofix = level=="low" and not has_serious_issue). It belongs in risk_assessor (the single guardrail layer), with a message like "Auto-fix withheld: a medium/high severity issue needs human review."

---

## 8) Improvement idea

Propose one improvement that would make BugHound more reliable *without* making it dramatically more complex.

Examples:

- A better output format and parsing strategy
- A new guardrail rule + test
- A more careful “minimal diff” policy
- Better detection of changes that alter behavior

Write your idea clearly and briefly.


- Add a "minimal-diff" guardrail: reject or down-score any fix whose changed-line count exceeds a small threshold relative to the original, so blunt rewrites (like prepending import logging and rewriting many lines) get routed to human review.
