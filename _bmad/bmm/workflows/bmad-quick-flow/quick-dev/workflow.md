# Quick Dev Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** Developer (bmm-dev)
**Module:** Business Modeling (BMM)
**Input:** Quick tech spec (from quick-spec workflow or user-provided)
**Duration:** Matches spec effort estimate (XS/S/M)

---

## Workflow Objective

Implement a quick tech spec rapidly and correctly, following the same quality standards as full story development but with a streamlined process appropriate for small changes.

---

## Phase 1: Load & Validate Spec (3 min)

**Before writing any code:**
1. Read the provided quick spec completely
2. Verify scope is clear (if not, ask for clarification)
3. Verify the identified files/functions still match the current code (codebase may have changed)
4. Confirm effort estimate is realistic

**If spec is incomplete or outdated:** Stop and request clarification before proceeding.

**Output:** Validated spec ready for implementation

---

## Phase 2: Implement (time-boxed to spec estimate)

**Implementation rules:**
1. Make only the changes described in the spec — no scope creep
2. Follow existing code style and patterns in the file
3. Do not add extra abstraction layers not required by the spec
4. Do not add error handling for scenarios outside the spec's scope
5. Use existing helpers/utilities already in the codebase

**Steps:**
1. Read the target file(s) before editing
2. Make the smallest change that satisfies the acceptance criteria
3. Verify no other tests break due to the change

**Output:** Implementation complete

---

## Phase 3: Test & Verify (5-10 min)

**Testing steps:**
1. Run existing tests to confirm no regression:
   ```
   python -m pytest -q
   ```
2. Add or update tests for the new behavior:
   - At least 1 test per acceptance criterion
   - Both success and failure path if applicable
3. Run coverage check:
   ```
   python -m pytest -q --cov=src/app --cov-report=term-missing
   ```
4. Confirm coverage remains at 100% (or project threshold)

**Output:** All tests green, coverage maintained

---

## Phase 4: Confirm Acceptance (2 min)

For each acceptance criterion in the spec:
- [ ] Criterion met? (verify with test or manual check)
- [ ] Test exists that proves it?

If any criterion is not met, return to Phase 2.

**Output:** Acceptance confirmation

---

## Quality Gates

- [ ] Only spec-described changes made (no scope creep)
- [ ] All existing tests still pass
- [ ] New tests added for all acceptance criteria
- [ ] Coverage maintained at project threshold
- [ ] All acceptance criteria are demonstrably met
