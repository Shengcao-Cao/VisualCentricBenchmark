# Diagramma — Workflow Architecture

```mermaid
graph TD
    U((User))
    MA(Main Agent)
    E(Rendering Engine)
    RA(Reviewer Subagent)

    U -->|prompt + optional reference image| MA
    MA -->|get_engine_context\nwrite_source\napply_patch| E
    E -->|SVG or compile errors| MA
    MA -->|review_output| RA
    RA -->|approved / rejected + findings| MA
    MA -->|diagram + source + explanation| U
    U -->|follow-up prompt| MA
```

---

## Multi-Agent Problem Editing Architecture

Six agents. Two implemented workflow variations (A and B), one proposed (C). Backwards-compatible with user-facing chat.

In **batch mode**, the pipeline runs autonomously without the Leader — problems flow directly through the agent sequence. The **Leader** is only involved when a user interacts via chat.

### Agents

| Agent | Role |
|---|---|
| **Leader** | User-facing only. Classifies intent, dispatches to Editor or Coder, formalizes results. Not involved in batch processing. |
| **Editor** | Proposes edits to a problem (question, options, answer, images). |
| **Coder** | Reproduces/renders the problem's diagram via the rendering engine tool loop. *(Renamed from "Main Agent".)* |
| **Verifier** | Checks whether the edited problem is still solvable and internally consistent. |
| **Reviewer** | Visually compares rendered diagram against reference. *(Independent agent, no longer a Coder subagent.)* |
| **Auditor** | Verifies the final diagram is faithful to the edited problem. Runs after the Coder's last pass, before completion. |

---

### Variation A: Edit-First

The problem is edited before the diagram is rendered. The Coder renders a diagram for the *edited* problem. The Auditor then verifies faithfulness — if rejected, the Coder re-renders.

> **Fragility note:** The Reviewer is not used in Variation A. The original reference image depicts the *pre-edit* state, so visual comparison is unreliable. The Auditor provides the quality gate instead.

```mermaid
graph TD
    U((User))
    B((Batch))
    L(Leader)
    Ed(Editor)
    V(Verifier)
    C(Coder)
    A(Auditor)
    E(Rendering Engine)

    U -->|problem + intent| L
    L -->|"dispatch: edit"| Ed
    L -->|"dispatch: reproduce"| C
    B -->|problem| Ed
    Ed -->|proposed edits| V
    V -->|"solvable? yes/no + feedback"| Ed
    Ed -->|finalized edits| C
    C -->|write_source\napply_patch| E
    E -->|SVG or errors| C
    C -->|rendered diagram| A
    A -->|"faithful? yes/no + feedback"| C
    A -->|approved| L
    L -->|"formalized result"| U
```

```mermaid
stateDiagram-v2
    [*] --> EDITING
    EDITING --> VERIFYING : proposal ready
    EDITING --> FAILED : no proposal
    VERIFYING --> RENDERING : solvable
    VERIFYING --> EDITING : not solvable (retry, max 3)
    VERIFYING --> FAILED : max retries exceeded
    RENDERING --> AUDITING : has auditor
    RENDERING --> COMPLETE : no auditor configured
    AUDITING --> COMPLETE : faithful
    AUDITING --> RENDERING : not faithful (retry, max 3)
    AUDITING --> FAILED : max retries exceeded
    COMPLETE --> [*]
    FAILED --> [*]
```

**Sequence:** Editor ↔ Verifier → Coder ↔ Auditor → Output

1. **Editor** proposes edits to the problem (question text, options, answer, images)
2. **Verifier** checks the edited problem is still solvable — loops with Editor if not
3. **Coder** renders a diagram for the finalized edited problem
4. **Auditor** verifies the rendered diagram is faithful to the edited problem — loops with Coder if not
5. Output: edited problem + rendered diagram

---

### Variation B: Reproduction-First

The original diagram is reproduced first, then edits are applied. This gives the Editor the reproduced source code as context, and allows a second Coder pass to update the diagram after edits. The Auditor verifies faithfulness after the update phase.

```mermaid
graph TD
    U((User))
    B((Batch))
    L(Leader)
    C(Coder)
    R(Reviewer)
    E(Rendering Engine)
    Ed(Editor)
    V(Verifier)
    A(Auditor)

    U -->|problem + intent| L
    L -->|"dispatch: reproduce"| C
    L -->|"dispatch: edit"| Ed
    B -->|problem| C
    C -->|write_source\napply_patch| E
    E -->|SVG or errors| C
    C -->|rendered diagram| R
    R -->|"approved / rejected + findings"| C
    C -->|reproduced diagram| Ed
    Ed -->|proposed edits| V
    V -->|"solvable? yes/no + feedback"| Ed
    Ed -->|finalized edits| C
    C -->|updated diagram| A
    A -->|"faithful? yes/no + feedback"| C
    A -->|approved| L
    L -->|"formalized result"| U
```

```mermaid
stateDiagram-v2
    [*] --> REPRODUCING
    REPRODUCING --> REVIEWING_REPRODUCTION : coder done
    REVIEWING_REPRODUCTION --> EDITING : approved
    REVIEWING_REPRODUCTION --> REPRODUCING : rejected (retry, max 5)
    REVIEWING_REPRODUCTION --> FAILED : max retries exceeded
    EDITING --> VERIFYING : proposal ready
    EDITING --> FAILED : no proposal
    VERIFYING --> UPDATING : solvable
    VERIFYING --> EDITING : not solvable (retry, max 3)
    VERIFYING --> FAILED : max retries exceeded
    UPDATING --> AUDITING : has auditor
    UPDATING --> COMPLETE : no auditor configured
    AUDITING --> COMPLETE : faithful
    AUDITING --> UPDATING : not faithful (retry, max 5)
    AUDITING --> FAILED : max retries exceeded
    COMPLETE --> [*]
    FAILED --> [*]
```

**Sequence:** Coder ↔ Reviewer → Editor ↔ Verifier → Coder ↔ Auditor → Output

1. **Coder** reproduces the original diagram from the reference image
2. **Reviewer** compares the reproduction against the original reference — loops with Coder if rejected
3. **Editor** proposes edits to the problem (now with the reproduced source code as context)
4. **Verifier** checks the edited problem is still solvable — loops with Editor if not
5. **Coder** updates the diagram to match the edited problem
6. **Auditor** verifies the updated diagram is faithful to the edited problem — loops with Coder if not
7. Output: edited problem + updated diagram

---

### Variation C: Parallel (Proposed)

The editing and reproduction processes have no dependencies between them — they can run simultaneously. After both complete, the Coder applies the edits to the reproduced source and the Auditor validates faithfulness.

> **Status:** Not yet implemented. Variation B is used by the batch processor.

```mermaid
graph TD
    U((User))
    B((Batch))
    L(Leader)
    Ed(Editor)
    V(Verifier)
    C1(Coder)
    R(Reviewer)
    E(Rendering Engine)
    C2(Coder)
    A(Auditor)

    U -->|problem + intent| L
    L -->|"dispatch: edit + reproduce"| Ed
    L -->|"dispatch: edit + reproduce"| C1
    B -->|problem| Ed
    B -->|problem| C1

    Ed -->|proposed edits| V
    V -->|"solvable? yes/no + feedback"| Ed

    C1 -->|write_source\napply_patch| E
    E -->|SVG or errors| C1
    C1 -->|rendered diagram| R
    R -->|"approved / rejected + findings"| C1

    Ed -->|finalized edits| C2
    C1 -->|reproduced source| C2
    C2 -->|apply edits to\nreproduced source| E

    C2 -->|updated diagram| A
    A -->|"faithful? yes/no + feedback"| C2
    A -->|approved| L
    L -->|"formalized result"| U
```

**Sequence:** (Editor ↔ Verifier ‖ Coder ↔ Reviewer) → Coder ↔ Auditor → Output

1. **In parallel:**
   - **Editor** proposes edits; **Verifier** checks solvability — loops until valid
   - **Coder** reproduces the original diagram; **Reviewer** compares against reference — loops until approved
2. Both streams join: **Coder** receives the finalized edits + reproduced source, applies edits to the diagram
3. **Auditor** verifies the updated diagram is faithful to the edited problem — loops with Coder if not
4. Output: edited problem + updated diagram

---

### Auditor Agent

The auditor is a self-contained LLM loop that verifies whether the final rendered diagram is **faithful** to the edited problem. It runs after the last Coder pass (RENDERING in Variation A, UPDATING in Variation B) and before pipeline completion.

**Tools:**

| Tool | Purpose |
|------|---------|
| `crop_region` | Crop a specific region from the rendered diagram for closer inspection |
| `compute` | Execute a Python snippet to verify numerical/geometric properties |

**Result:**

| Field | Description |
|-------|-------------|
| `faithful` | `true` (diagram matches the edited problem) or `false` (mismatch detected) |
| `confidence` | Confidence score (0–1) |
| `issues` | List of specific faithfulness issues found |
| `feedback` | Actionable feedback for the Coder on what to fix (passed on rejection) |

**Behavior on rejection:** The auditor's feedback is fed back to the Coder, which re-renders/re-updates the diagram. This loop repeats up to the configured max retries (same as the coder-reviewer retry limit). If the auditor produces no parseable result after internal retries, it auto-approves to avoid pipeline deadlock.

**Optional:** The auditor is only invoked if an `auditor` LLM is configured in agent settings. If unconfigured, the pipeline skips directly from RENDERING/UPDATING to COMPLETE.

---
