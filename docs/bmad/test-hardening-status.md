# Test Hardening Status

## Waarom dit document
Dit is een korte, simpele statuspagina die laat zien wat al getest is en hoe je de tests draait.

## Wat is nu afgedekt
- Health endpoint: basis check dat de app leeft.
- Experiments API: contract checks en foutpaden (validatie en ontbrekende records).
- Trend packs API: aanmaken, status/promotion foutpaden.
- Scheduling/publishing API: success path en foutpaden (bijvoorbeeld clip niet goedgekeurd of job niet gevonden).
- Performance snapshots API: foutpaden voor ingest en detail-opvraag.
- Core review-logica:
  - Authenticity scoreberekening en retry-penalty.
  - Queue risk-flag logica.
  - Publish status mapping en Buffer profile resolutie.
- Publishing en trend packs services:
  - Manual export generatie en distributie-routing.
  - Sync status success/failure pad.
  - Fatigue berekening en duplicate trend-pack check.
- Publication views API:
  - Lijst endpoint contract check.
  - Kalender endpoint contract check.
  - Input-validatie (ongeldige limit/platform geeft 422).
- Recommendations API:
  - Generate endpoint contract check.
  - List endpoint contract check.
  - Input-validatie (minimum_samples/limit).
- Insights API:
  - Dashboard endpoint contract check.
  - Input-validatie (observation_window).
- Publication views service (directe logica-tests):
  - Snapshot-samenvatting (leeg resultaat, getallen, None-coercering).
  - List publication jobs (lege DB, item opbouw).
  - Kalender groepering (op datum, ongesorteerd, unscheduled-sleutel).
- Queue service (directe logica-tests):
  - Risk-flag detectie (ontbrekende score, lage score, errors, hoge retry).
  - Review-beslissing: approve/revise/reject + not-found pad.
- Compliance gate (nieuw):
  - Compliance audit ophalen/wegschrijven (rights status + reviewer + reden).
  - Scheduling blokkeert als rights_status niet approved is.
  - Scheduling blokkeert als fan-account disclosure ontbreekt.
  - API-contracten voor GET/POST compliance endpoints inclusief foutpaden.
- Recommendations service (directe logica-tests):
  - Platform-keuze logica (_choose_platform: hoog/medium/laag/None auth).
  - Tijdslot-keuze logica (_choose_time_slot: stream/live/hoog ranking/default).
  - Not-found pad voor get_scheduling_recommendation.
- Insights service (directe logica-tests):
  - Top-score groepering (_top_grouped_scores: leeg/sortering/limit/lege lijsten).
  - Dashboard met lege DB geeft fallback aanbeveling.

## Hoe je tests draait
1. Installeer dependencies:
   - python -m pip install -r requirements.txt
2. Draai alle tests:
   - python -m pytest -q

## CI (automatische checks)
- Bestand: .github/workflows/tests.yml
- Trigger:
  - push op main/master
  - pull_request
- Actie:
  - installeert dependencies
  - draait python -m pytest -q met coverage voor src/app/review
  - faalt als coverage onder 100% komt
  - maakt pytest-report.xml en coverage.xml
  - print aantallen tests (totaal/geslaagd/gefaald/errors/overgeslagen) in CI-log
  - uploadt pytest-report.xml en coverage.xml als artifacts
- Versies:
  - draait op Python 3.11 en 3.12 (matrix)
- Snelheid:
  - gebruikt pip-cache op basis van requirements.txt

## Huidige status
- Laatste lokale run (2026-03-19): 252 tests geslaagd, 0 gefaald
- Laatste lokale coverage run (2026-03-19): 100.00% op src/app/review (drempel: 100%)
- Compliance module coverage (2026-03-19): 100.00% op src/app/review/compliance.py
- Doel: API hardening regressies vroeg afvangen
