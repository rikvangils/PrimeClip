from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.models import RightsStatus
from app.db.session import get_db
from app.main import app
from app.review.compliance import assert_clip_compliant, get_clip_compliance, set_clip_compliance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _override_db():
    yield None


def _make_audit(
    rights_status: RightsStatus = RightsStatus.approved,
    fan_account_disclosed: bool = True,
    decision_reason: str | None = "ok",
    reviewer_id: str | None = "reviewer-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        rendered_clip_fk=uuid.uuid4(),
        rights_status=rights_status,
        fan_account_disclosed=fan_account_disclosed,
        decision_reason=decision_reason,
        reviewer_id=reviewer_id,
        created_at=datetime.now(timezone.utc),
    )


def _make_clip(clip_id: uuid.UUID | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=clip_id or uuid.uuid4())


# ---------------------------------------------------------------------------
# Unit tests: get_clip_compliance
# ---------------------------------------------------------------------------


def test_get_clip_compliance_returns_none_when_no_record() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    result = get_clip_compliance(db=db, rendered_clip_id=str(uuid.uuid4()))

    assert result is None
    db.scalar.assert_called_once()


def test_get_clip_compliance_returns_latest_audit_record() -> None:
    audit = _make_audit()
    db = MagicMock()
    db.scalar.return_value = audit

    result = get_clip_compliance(db=db, rendered_clip_id=str(audit.rendered_clip_fk))

    assert result is audit


# ---------------------------------------------------------------------------
# Unit tests: set_clip_compliance
# ---------------------------------------------------------------------------


def test_set_clip_compliance_raises_when_clip_not_found() -> None:
    db = MagicMock()
    db.scalar.return_value = None  # clip lookup returns None

    with pytest.raises(ValueError, match="Rendered clip not found"):
        set_clip_compliance(
            db=db,
            rendered_clip_id=str(uuid.uuid4()),
            rights_status=RightsStatus.approved,
            decision_reason=None,
            reviewer_id=None,
            fan_account_disclosed=True,
        )


def test_set_clip_compliance_creates_and_returns_audit() -> None:
    clip = _make_clip()
    created_audit = _make_audit()
    db = MagicMock()
    db.scalar.return_value = clip

    # db.refresh should populate the audit object (simulate by returning it)
    def fake_refresh(obj):
        obj.id = created_audit.id
        obj.created_at = created_audit.created_at

    db.refresh.side_effect = fake_refresh

    with patch("app.review.compliance.ComplianceAudit") as MockAudit:
        audit_instance = MagicMock()
        audit_instance.id = created_audit.id
        audit_instance.rendered_clip_fk = clip.id
        audit_instance.rights_status = RightsStatus.approved
        audit_instance.decision_reason = "clean"
        audit_instance.reviewer_id = "admin"
        audit_instance.fan_account_disclosed = True
        audit_instance.created_at = created_audit.created_at
        MockAudit.return_value = audit_instance

        result = set_clip_compliance(
            db=db,
            rendered_clip_id=str(clip.id),
            rights_status=RightsStatus.approved,
            decision_reason="clean",
            reviewer_id="admin",
            fan_account_disclosed=True,
        )

    db.add.assert_called_once_with(audit_instance)
    db.commit.assert_called_once()
    assert result is audit_instance


def test_set_clip_compliance_stores_rejected_status() -> None:
    clip = _make_clip()
    db = MagicMock()
    db.scalar.return_value = clip

    with patch("app.review.compliance.ComplianceAudit") as MockAudit:
        audit_instance = MagicMock()
        audit_instance.rights_status = RightsStatus.rejected
        audit_instance.fan_account_disclosed = False
        MockAudit.return_value = audit_instance

        result = set_clip_compliance(
            db=db,
            rendered_clip_id=str(clip.id),
            rights_status=RightsStatus.rejected,
            decision_reason="copyright claim",
            reviewer_id=None,
            fan_account_disclosed=False,
        )

    assert result.rights_status == RightsStatus.rejected
    assert result.fan_account_disclosed is False


# ---------------------------------------------------------------------------
# Unit tests: assert_clip_compliant
# ---------------------------------------------------------------------------


def test_assert_clip_compliant_raises_when_no_audit_record() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(ValueError, match="approved"):
        assert_clip_compliant(db=db, rendered_clip_id=str(uuid.uuid4()))


def test_assert_clip_compliant_raises_when_rights_status_is_unknown() -> None:
    audit = _make_audit(rights_status=RightsStatus.unknown, fan_account_disclosed=True)
    db = MagicMock()
    db.scalar.return_value = audit

    with pytest.raises(ValueError, match="approved"):
        assert_clip_compliant(db=db, rendered_clip_id=str(audit.rendered_clip_fk))


def test_assert_clip_compliant_raises_when_rights_status_is_pending() -> None:
    audit = _make_audit(rights_status=RightsStatus.pending, fan_account_disclosed=True)
    db = MagicMock()
    db.scalar.return_value = audit

    with pytest.raises(ValueError, match="approved"):
        assert_clip_compliant(db=db, rendered_clip_id=str(audit.rendered_clip_fk))


def test_assert_clip_compliant_raises_when_rights_status_is_rejected() -> None:
    audit = _make_audit(rights_status=RightsStatus.rejected, fan_account_disclosed=True)
    db = MagicMock()
    db.scalar.return_value = audit

    with pytest.raises(ValueError, match="approved"):
        assert_clip_compliant(db=db, rendered_clip_id=str(audit.rendered_clip_fk))


def test_assert_clip_compliant_raises_when_fan_account_not_disclosed() -> None:
    audit = _make_audit(rights_status=RightsStatus.approved, fan_account_disclosed=False)
    db = MagicMock()
    db.scalar.return_value = audit

    with pytest.raises(ValueError, match="Fan-account disclosure"):
        assert_clip_compliant(db=db, rendered_clip_id=str(audit.rendered_clip_fk))


def test_assert_clip_compliant_passes_when_approved_and_disclosed() -> None:
    audit = _make_audit(rights_status=RightsStatus.approved, fan_account_disclosed=True)
    db = MagicMock()
    db.scalar.return_value = audit

    # Should not raise
    assert_clip_compliant(db=db, rendered_clip_id=str(audit.rendered_clip_fk))


# ---------------------------------------------------------------------------
# Unit tests: scheduling gate in publishing.py
# ---------------------------------------------------------------------------


def test_schedule_clip_for_distribution_raises_when_not_compliant(monkeypatch) -> None:
    from app.review.publishing import schedule_clip_for_distribution
    from app.db.models import ReviewStatus, RenderStatus

    clip_id = str(uuid.uuid4())
    clip = SimpleNamespace(
        id=clip_id,
        review_status=ReviewStatus.approved,
        render_path="/clips/test.mp4",
    )

    db = MagicMock()
    db.scalar.return_value = clip

    monkeypatch.setattr(
        "app.review.publishing.assert_clip_compliant",
        lambda db, rendered_clip_id: (_ for _ in ()).throw(
            ValueError("Clip rights status must be approved before scheduling.")
        ),
    )

    with pytest.raises(ValueError, match="rights status"):
        schedule_clip_for_distribution(
            db=db,
            rendered_clip_id=clip_id,
            platform=__import__("app.db.models", fromlist=["Platform"]).Platform.instagram,
            scheduled_at=datetime.now(timezone.utc),
            caption="Test caption",
        )


# ---------------------------------------------------------------------------
# API endpoint tests: GET /review/clips/{id}/compliance
# ---------------------------------------------------------------------------


def test_get_compliance_record_returns_404_when_no_record(monkeypatch) -> None:
    monkeypatch.setattr("app.review.api.get_clip_compliance", lambda db, rendered_clip_id: None)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get("/review/clips/nonexistent-id/compliance")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "No compliance record" in response.json()["detail"]


def test_get_compliance_record_returns_existing_record(monkeypatch) -> None:
    audit_id = uuid.uuid4()
    clip_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    audit = SimpleNamespace(
        id=audit_id,
        rendered_clip_fk=clip_id,
        rights_status=SimpleNamespace(value="approved"),
        decision_reason="all clear",
        reviewer_id="reviewer-007",
        fan_account_disclosed=True,
        created_at=now,
    )
    monkeypatch.setattr("app.review.api.get_clip_compliance", lambda db, rendered_clip_id: audit)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.get(f"/review/clips/{clip_id}/compliance")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["rights_status"] == "approved"
    assert payload["fan_account_disclosed"] is True
    assert payload["reviewer_id"] == "reviewer-007"
    assert payload["decision_reason"] == "all clear"


# ---------------------------------------------------------------------------
# API endpoint tests: POST /review/clips/{id}/compliance
# ---------------------------------------------------------------------------


def test_set_compliance_record_returns_422_for_invalid_rights_status(monkeypatch) -> None:
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/clips/some-clip-id/compliance",
            json={"rights_status": "totally-invalid-value"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_set_compliance_record_returns_404_when_clip_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.review.api.set_clip_compliance",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("Rendered clip not found: xyz")),
    )
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            "/review/clips/xyz/compliance",
            json={"rights_status": "approved", "fan_account_disclosed": True},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_set_compliance_record_creates_and_returns_audit(monkeypatch) -> None:
    audit_id = uuid.uuid4()
    clip_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    audit = SimpleNamespace(
        id=audit_id,
        rendered_clip_fk=clip_id,
        rights_status=SimpleNamespace(value="approved"),
        decision_reason="rights confirmed",
        reviewer_id="admin",
        fan_account_disclosed=True,
        created_at=now,
    )
    monkeypatch.setattr("app.review.api.set_clip_compliance", lambda **kwargs: audit)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            f"/review/clips/{clip_id}/compliance",
            json={
                "rights_status": "approved",
                "decision_reason": "rights confirmed",
                "reviewer_id": "admin",
                "fan_account_disclosed": True,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["rights_status"] == "approved"
    assert payload["fan_account_disclosed"] is True
    assert payload["reviewer_id"] == "admin"
    assert payload["decision_reason"] == "rights confirmed"
    assert payload["compliance_audit_id"] == str(audit_id)


def test_set_compliance_record_supports_pending_status(monkeypatch) -> None:
    audit_id = uuid.uuid4()
    clip_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    audit = SimpleNamespace(
        id=audit_id,
        rendered_clip_fk=clip_id,
        rights_status=SimpleNamespace(value="pending"),
        decision_reason=None,
        reviewer_id=None,
        fan_account_disclosed=False,
        created_at=now,
    )
    monkeypatch.setattr("app.review.api.set_clip_compliance", lambda **kwargs: audit)
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as client:
        response = client.post(
            f"/review/clips/{clip_id}/compliance",
            json={"rights_status": "pending"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["rights_status"] == "pending"
    assert response.json()["fan_account_disclosed"] is False
