# PRD Validation Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Product Manager (bmm-pm) + Business Analyst (bmm-analyst)
**Module:** Business Modeling (BMM)
**Input:** `docs/prd.md`
**Output:** Validation report (inline comments or separate `docs/prd-validation.md`)
**Duration:** 30-45 minutes

---

## Workflow Objective

Validate that the ProjectFire PRD meets quality standards before implementation begins, checking for:

1. **Completeness** — All required sections are present and filled
2. **Clarity** — Requirements are unambiguous and testable
3. **Consistency** — No contradictions between sections
4. **Feasibility** — Technical requirements are realistic
5. **Alignment** — PRD aligns with product brief and market research

---

## Validation Checklist

### Section 1: Structural Completeness

Read `docs/prd.md` and verify presence of:

- [ ] Product vision statement (1-2 sentences)
- [ ] Explicit scope boundaries (in/out of scope)
- [ ] At least 2 user personas with goals and pain points
- [ ] Numbered functional requirements (REQ-XXX format)
- [ ] Non-functional requirements with measurable thresholds
- [ ] Epic list with E1–E6 (or full epic range)
- [ ] Success metrics with quantified targets

**Fail condition:** Any section missing or contains only placeholder text

---

### Section 2: Requirement Quality

For each functional requirement, verify:

- [ ] Has a priority level (Must/Should/Could/Won't)
- [ ] Is written as a user story or clear capability statement
- [ ] Has at least one measurable acceptance criterion
- [ ] Does not contain implementation decisions (what, not how)
- [ ] Is traceable to at least one epic

**Sample check (pick 5 random requirements):**
```
REQ-XXX: [title]
□ Has priority
□ Is persona-linked
□ Has acceptance criterion
□ Avoids HOW language
□ Links to an epic
```

**Fail condition:** More than 20% of checked requirements fail any criterion

---

### Section 3: Consistency Check

Cross-reference PRD with source documents:

| PRD claim | Source document | Match? |
|-----------|-----------------|--------|
| Target market | product-brief.md | |
| Revenue model | market-research.md | |
| Technical stack | architecture.md | |
| Epic structure | epics-and-stories.md | |

- [ ] No contradictions found between PRD and product-brief.md
- [ ] No contradictions found between PRD and market-research.md
- [ ] Epic count matches epics-and-stories.md

**Fail condition:** Any factual contradiction found

---

### Section 4: Feasibility Review

Evaluate technical NFRs against known stack:

- [ ] Performance thresholds are measurable and realistic (FastAPI, PostgreSQL, FFmpeg)
- [ ] Security requirements align with OWASP standards
- [ ] Test coverage targets are achievable with pytest
- [ ] No requirement implicitly requires out-of-scope infrastructure

**Fail condition:** Any NFR that cannot be verified with existing tooling

---

### Section 5: Stakeholder Alignment

Verify the PRD reflects agreed project direction:

- [ ] Vision matches `docs/product-brief.md` vision statement
- [ ] Personas reflect target users described in market research
- [ ] Scope exclusions are explicitly stated and defensible
- [ ] Priority distribution is reasonable (>50% Must requirements should be in E1-E3)

---

## Validation Scoring

| Category | Weight | Score (0-10) | Notes |
|----------|--------|--------------|-------|
| Structural completeness | 25% | | |
| Requirement quality | 30% | | |
| Consistency | 20% | | |
| Feasibility | 15% | | |
| Stakeholder alignment | 10% | | |
| **Total** | 100% | | |

**Threshold to proceed:** Average score ≥ 7.0, no 0-score in any category

---

## Output

For each failed check, document:
```
ISSUE: [Section - Check name]
Severity: Critical / Major / Minor
Finding: [What was found]
Required action: [What must be fixed]
```

Save complete validation report and update PRD accordingly before moving to architecture phase.

## Quality Gates

- [ ] All 5 validation sections completed
- [ ] Scoring table filled in
- [ ] All Critical/Major issues logged
- [ ] PRD updated to address critical findings
- [ ] Validation report saved or inline comments added
