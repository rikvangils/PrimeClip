# Teach Me Testing Workflow
## ProjectFire: AI Virtual Creators Network

**Agent:** QA Engineer (tea-tea)
**Module:** TEA (Testing Engineering Architecture)
**Duration:** Progressive sessions (20-30 min per session)

---

## Workflow Objective

Teach testing progressively through structured sessions tailored to the ProjectFire codebase. The learner builds confidence from basic to advanced testing concepts using real code from this project.

---

## Session Structure

Each session follows the same pattern:
1. **Concept introduction** (5 min) — What and why
2. **Code example** (10 min) — Live example from ProjectFire
3. **Guided exercise** (10 min) — Learner writes a test with guidance
4. **Review** (5 min) — Feedback and explanation

---

## Session 1: pytest Fundamentals

**Concept:** What is a test? Why do we test?

**Live example from ProjectFire:**
```python
# tests/test_review_core_logic.py
def test_approve_clip_returns_updated_status():
    # Arrange: set up mock data
    # Act: call the function
    # Assert: verify the outcome
```

**Exercise:** Write a test that verifies a clip candidate with score > 0.8 would rank higher than one with score 0.5.

**Key principles:**
- Arrange → Act → Assert pattern
- One assertion per test
- Descriptive test names

---

## Session 2: Fixtures and conftest.py

**Concept:** How to share setup across tests

**Live example from ProjectFire:**
```python
# tests/conftest.py
@pytest.fixture
def db():
    # in-memory database setup

@pytest.fixture
def client(db):
    # FastAPI TestClient with injected db
```

**Exercise:** Create a fixture that provides a `ClipCandidate` with standard test data.

**Key principles:**
- Fixtures for repeated setup
- Scope: function (default), module, session
- conftest.py for shared fixtures

---

## Session 3: Mocking External Dependencies

**Concept:** How to test code that calls external systems (Buffer, FFmpeg)

**Live example from ProjectFire:**
```python
def test_publish_clip_success(monkeypatch):
    monkeypatch.setattr("app.review.publishing.call_buffer_api",
                        lambda *args, **kwargs: {"id": "buf123"})
    # test proceeds without real Buffer call
```

**Exercise:** Write a test for the rendering pipeline that mocks `subprocess.run` (FFmpeg).

**Key principles:**
- Never call real external services in unit tests
- monkeypatch vs unittest.mock
- Target the import path, not the source module path

---

## Session 4: API Testing with TestClient

**Concept:** How to test FastAPI endpoints end-to-end

**Live example from ProjectFire:**
```python
def test_get_review_queue_returns_list(client):
    response = client.get("/review/queue")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Exercise:** Write a test for `POST /review/queue/{id}/approve` — both success (200) and not-found (404).

**Key principles:**
- TestClient simulates HTTP without running a server
- Test both success and failure paths
- Check status codes AND response body

---

## Session 5: Coverage and Test Design

**Concept:** What coverage means and how to use it

**Live example from ProjectFire:**
```bash
python -m pytest --cov=src/app --cov-report=term-missing
```

**Exercise:** Find an uncovered line in `src/app/review/` and write the test that covers it.

**Key principles:**
- Coverage shows lines executed, not behavior verified
- 100% coverage ≠ 100% correct behavior
- Use coverage as a gap-finding tool, not a goal in itself
- `--cov-fail-under` as CI quality gate

---

## Session 6: Advanced — Edge Cases and Regression

**Concept:** Testing the hard stuff: None values, empty lists, race conditions

**Live example from ProjectFire:**
```python
def test_insights_with_no_snapshots_returns_empty_dashboard():
    # edge case: what if there's no performance data yet?
```

**Exercise:** Find a JSONB field in the models and write a test that verifies behavior when the field is None vs an empty dict.

**Key principles:**
- Always test empty state (empty list, None, zero)
- Regression tests: when a bug is found, write a test before fixing
- Boundary testing: min/max values, first/last elements

---

## Learning Resources

- pytest docs: https://docs.pytest.org
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Coverage.py: https://coverage.readthedocs.io
- ProjectFire tests: `tests/` directory (real examples)

---

## Quality Gates (per session)

- [ ] Learner can explain the concept in their own words
- [ ] Exercise test is written and passes
- [ ] Learner understands when to use this technique
- [ ] Connection to ProjectFire codebase is clear
