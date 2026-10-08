# Final manuscript claim review

**Audit date:** 2026-10-08
**Owner:** independent review A
**Scope:** read-only review of papers/sparse_es_regret/manuscript.md,
papers/sparse_es_regret/PRIOR_ART.md, and
docs/experiments/20261008_sparse_regret_paper_audit.md, with the linked
THEORY.md, readiness.json, source_manifest.json, and claims.csv read only to
check claim boundaries and provenance. No source, result, test, or Git state
was changed. No new experiment was run.

## Verdict

The draft is suitable as a **working mathematical/computational technical
note for human review**. It is not submission-ready and does not claim
confirmed novelty or priority. The manuscript, prior-art table, and audit
report consistently distinguish Huang's known regret criterion, Zhu and
Fukushima's absolute full-simplex WCVaR, Pertaia and Uryasev's mixture-weight
concavity, and Fan's abstract-only overlap. The readiness fields
writing_package_complete=true, novelty_priority_confirmed=false,
submission_ready=false, and human_source_verification=pending are
consistent with the prose.

The main remaining risks are wording and evidence labeling, not a discovered
counting or leakage failure. The strongest claims should be presented as a
working derivation under explicit assumptions, with human theorem/source
verification still pending.

## Findings requiring attention

### 1. Mark the theorem package as working and human-unverified

The manuscript states “We derive” and presents Proposition 1 and Proposition
2 declaratively (manuscript lines 7 and 25-31). The proof in THEORY.md is
coherent under the stated full-simplex, fixed-bank, scalar-ES assumptions,
and the audit records two AI reviews with no blocking objection. That is AI
review evidence, not human theorem verification. The audit report also calls
the structural result “correct within scope” (lines 9-14), which is stronger
than the readiness manifest supports.

Recommended wording is “we state and give a working proof of” or “the draft
derives, subject to independent verification,” and “the working derivation
appears correct under the stated scope.” Keep the actual proposition and
proof; add the status qualifier. Proposition 2's spectral/rank extension is
especially important to label as a mathematical result with no production
J-level solver: the audit explicitly says that solver was not implemented
(lines 99-105).

### 2. Add the tail-mass convention when comparing prior papers

The manuscript uses alpha as an upper-tail mass (line 23), whereas Huang,
Zhu--Fukushima, and Pertaia--Uryasev write their displayed CVaR formulas
using a confidence-level convention with a denominator such as \(1-\alpha\)
or \(1-\beta\). Their conceptual comparisons are accurate, including
Huang's absolute benchmark difference and separate percentage-ratio footnote,
but a reader could mistake the symbols as the same parameter. Add one short
notation sentence in Section 1 or before Proposition 1: the current alpha is
tail mass, and source confidence levels are reparameterized as needed.

### 3. Make synthetic/computational status visible in the abstract

The 168 cases, 29,847 LP solves, and 24 rational audits are counted
consistently: 72+72+24=168, and the audit separately reports the 32-point /
96-action continuous-law diagnostic. No leakage or double-counting signal
was found. The manuscript already says that no forecasting, market, or
investment claim is made and the audit explicitly calls the evidence finite
synthetic computation (lines 56-61).

For the abstract and timing paragraph, add “finite synthetic/configuration
cases” before the counts. This prevents a reader from reading 168 cases as
168 independent market observations. Keep “LP solves,” “active-set systems,”
and “rational audits” as separate units; the manuscript currently does so.

### 4. Replace “independent reference” with “separate LP comparator”

The LP path is a useful non-sparsity comparator and the rational path is an
additional exact check. The union control deliberately shares the bank hull,
and the manuscript says so. Because “independent” can be read as independent
data, independent replications, or fully independent software, use “separate
unrestricted-simplex LP comparator” in manuscript lines 41 and 47 and in the
audit's corresponding line 37. This preserves the algorithmic distinction
without implying statistical independence.

### 5. Add the prior-art evidence ID to the abstract claim record

Claim C001 covers the abstract's statement that the contribution does not
introduce ES regret and does not establish a calibrated uncertainty set or
forecast/investment improvement. Its current evidence list is
E101;E102;E103;E104. The “does not introduce ES regret” part is supported most
directly by the prior-art record E110, which is attached to C020 and C023 but
not C001. Either add E110 to C001 or split the abstract into computational
and prior-art claim records. This is a provenance repair, not a change to the
scientific conclusion.

## Source-description checks

- **Huang et al.** The description is accurate: Section 2 defines the
  law-specific absolute CVaR difference; Section 3 uses a finite rival-law
  list and the per-law optimum; footnote 4 is a separate percentage-regret
  ratio. The draft correctly distinguishes that continuous portfolio
  optimization from a fixed action-bank evaluator over a full probability-law
  simplex.
- **Zhu and Fukushima.** The description is accurate: the inspected report
  gives full-simplex **absolute** worst-CVaR minimax/RU machinery. The draft
  does not mislabel it as a relative-regret or support-two theorem.
- **Pertaia and Uryasev.** The description is accurate: Proposition 3.2 is
  mixture-weight CVaR concavity and Section 3.3 imposes a user-selected
  cardinality constraint in mixture fitting. The draft does not call that
  imposed cap an automatic two-component worst-regret result.
- **Fan.** The draft consistently says “abstract,” identifies engine-score
  mixtures as the accessible overlap, records HTTP 403 for the full text, and
  says that a theorem-level match cannot be excluded. It makes no priority
  claim from the search non-hit. Keep all Fan details qualified as
  abstract-reported until lawful full text is available.

The source manifest's unverified status is compatible with “source opened”
and local PDF inspection: it records that human verification has not occurred.
The manuscript banner and PRIOR_ART.md already explain this distinction.

## Integrity and readiness checks

The documents do not call AI review human peer review. The manuscript says AI
assistance and pending human verification; PRIOR_ART.md names two AI
reviewers and root; the audit explicitly says AI review is not peer review;
and readiness.json says AI is not an author. Preserve these statements.

The frozen result language is appropriately descriptive: float64 agreement is
not interval certification; timing is machine-level, not population-level;
large cases lack the generic LP timing comparator; and the policy run is old
evidence rather than a new selected outcome. The audit retains slower timing
cases, distinguishes three edge timings from one LP timing, and states that
no forecasting, OIC, HMM, neural, market, or PnL experiment was run. No
empirical leakage or outcome-based model selection is visible in the three
reviewed documents.

Readiness language is appropriately bounded. “Writing package complete” should
continue to mean that files and receipts are assembled, not that claims have
passed human review. Replace “Suitable now” in the prior-art claim boundary
with “Assembled now” if a stricter reading is desired; the adjacent
“not supported: ... ready to submit” line already prevents a submission-ready
interpretation.

## Final release gate

Before any venue or priority statement, obtain human verification of the
theorem assumptions/proof and primary-source locators, then obtain a human
assessment of the narrow contribution against the still-inaccessible Fan
full text and generic moment-extreme-point literature. No new benchmark sweep
is needed for this claim review. Until that gate passes, the defensible label
remains: **AI-audited working technical note; novelty and submission
readiness unresolved.**

## Review evidence boundary

This review read the named manuscript, prior-art table, experiment audit,
theory supplement, readiness manifest, source manifest, and claim ledger. It
did not rerun tests, open new test outcomes, train a model, or verify any
source with a human reviewer.
