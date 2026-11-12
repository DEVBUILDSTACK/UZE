# HOW TO USE THE DIAGRAMS — For SoSem

**From:** James and DeepSeek
**To:** SoSem

---

## What the diagrams are

Four Mermaid files in `docs/diagrams/`, each for a specific audience:

| File | Audience | What it shows |
|---|---|---|
| `01-marketplace-flow.md` | Non-technical | Two service lines feeding each other |
| `02-technical-stack.md` | Engineering | Four language boundaries |
| `03-end-to-end-sequence.md` | Both | Demo walkthrough — call order, payload, phases |
| `04-intent-lifecycle.md` | Rust engineer | Contract states to enforce |

Read the annotation block before the diagram. It tells you whose conversation the diagram is serving.

---

## What the diagrams are NOT

**They are not the specification.** The specification is:
- The compose schema
- The Alembic migration chain
- The intent schema
- The R4 read-through contract
- The USDC-only settlement invariant
- The ratified decisions in `04-DECISIONS-LOG.md`

**If a diagram and the specification disagree, the specification wins.** Fix the diagram.

**They are not frozen.** Unlike migrations, the diagrams get updated when the architecture changes.

**They are not normative for implementation.** They show the shape, not the code.

---

## How to use each diagram

### Diagram 1 (Marketplace Flow)

**Use it when:** explaining the product to non-technical stakeholders.

**Use it as a check:** when a feature introduces a third service line or an undocumented participant type, either the feature is out of scope or the diagram needs updating. Decide.

**Do not update it lightly.** Diagram 1 is the simplest expression of the product. A new box is a signal the feature may be too complex.

### Diagram 2 (Technical Stack)

**Use it as a boundary check at every PR:**
- Am I writing this in the right language?
- Am I respecting the layer boundary?
- Am I adding an arrow that wasn't there? (If yes, that's a new integration — flag it.)

**If the PR needs a new arrow, the PR description says so.**

**Update it when:** Sprint 2 adds the Intent Gateway as a module, or a new SDK enters, or an arrow reflects a real integration decision.

### Diagram 3 (End-to-End Sequence)

**Use it as the demo rehearsal script.** Every dry run follows this sequence.

**Use it as the acceptance test.** When Sprint 1.5 closes, the demo behavior should match Diagram 3 exactly.

**Update it when:** the settlement flow changes.

### Diagram 4 (Intent Lifecycle)

**Use it as a contract specification.** The Rust contract must enforce exactly these states.

**Use it as a code review checklist.** Every `require!` or `assert!` should correspond to a state transition or an invariant in Diagram 4.

**Update it when:** the state machine genuinely changes. Adding a new state is a real change; adding a log message is not.

---

## The divergence rule

If the build diverges from a diagram, two correct responses:

**Correct 1:** Fix the build to match the diagram.
**Correct 2:** Update the diagram to match the build, and note in the PR why.

**Wrong:** Ship the divergent build without updating the diagram. This is how documentation becomes lies.

**The choice is a judgment call. The rule is: name the choice, don't default to it.**

---

## What to do if a diagram becomes wrong

**Path A — you're confident and the fix is obvious.** Update, note it in the daily report, move on. Naming is a fix.

**Path B — you're not confident.** File the question. Topology is a decision.

**The test:** visual change = Path A. Topology change = Path B.

---

## Where the diagrams live and how they're maintained

```

docs/diagrams/
├── 01-marketplace-flow.md
├── 02-technical-stack.md
├── 03-end-to-end-sequence.md
└── 04-intent-lifecycle.md

```

**In every PR that touches architecture:** check whether any diagram needs updating. If yes, update it in the same PR. If no, say so in the PR description.

**At each sprint close:** review all four diagrams. Update anything stale.

**At each milestone:** export as SVG into `docs/diagrams/exports/` for slides.

---

## One final rule

**The diagrams are the shared vocabulary.**

When you file a report saying "the settlement flow works," James and I verify by looking at Diagram 3. When a blockchain engineer asks "which layer owns X?", Diagram 2 answers. When James explains the product, Diagram 1 is the reference.

If the diagrams and reality diverge, the vocabulary breaks. Keep them in sync — not with effort, but with discipline.

**The diagrams aren't decoration. They're how four audiences — James, his business partner, the blockchain engineers, and you — share one picture of what we're building.**
