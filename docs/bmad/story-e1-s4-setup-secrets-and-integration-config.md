# Story E1-S4 - Set Up Secrets and Integration Config

Status: Implemented  
Date: 18 March 2026  
Sprint: S1  
Epic: Epic 1 - Foundations and Compliance

## Story

As the system,
I want secure configuration for YouTube, Buffer, Instagram, and future analytics adapters,
so that credentials are safe and environment-specific.

## Acceptance criteria mapping

1. No credentials are hardcoded.
- Integration credentials are now read from environment settings (`PEANUTCLIP_*`).
- `.env.example` provides placeholders only.

2. Required integrations read config from secure environment variables or secret store.
- Settings model reads all integration values via `pydantic-settings` from env and `.env`.
- Required keys validated through `validate_required_integrations`.

3. Invalid or missing config produces actionable errors.
- `ensure_integrations_ready` raises `IntegrationConfigurationError` with a clear remediation message.

## Implemented files

- .env.example
- src/app/config.py
- src/app/integrations/readiness.py

## Notes

- This story sets the baseline for secure configuration and clear startup validation.
- Future stories can extend validation for additional integrations (for example TikTok analytics adapters).

## Next logical stories

- E2-S1 Detect new source uploads
- E2-S2 Create ingest jobs and source metadata