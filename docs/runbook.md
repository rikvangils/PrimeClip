# PeanutClip — Production Runbook

## Quick-reference checklist

Before every deploy, confirm all items are green:

- [ ] `GET /health/ready` returns `200` on the target environment
- [ ] `alembic upgrade head --sql` dry-run shows only expected DDL
- [ ] Current image tag is recorded (rollback target)
- [ ] TikTok developer app credentials and token are valid
- [ ] On-call person notified (production deploys only)

---

## 1. First-time environment setup

### 1.1 Required environment variables

Copy `.env.example` to `.env` and fill in every value.  
The minimum viable production set is:

| Variable | Where to get it |
|---|---|
| `PEANUTCLIP_DATABASE_URL` | Your managed Postgres connection string |
| `PEANUTCLIP_SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PEANUTCLIP_YOUTUBE_API_KEY` | Google Cloud Console → Credentials |
| `PEANUTCLIP_TIKTOK_ACCESS_TOKEN` | TikTok OAuth access token with `video.upload` scope — see §1.2 |
| `PEANUTCLIP_TIKTOK_API_BASE_URL` | Keep default unless TikTok docs specify otherwise |
| `PEANUTCLIP_TIKTOK_CLIENT_KEY` | TikTok app credentials (for code exchange + refresh) |
| `PEANUTCLIP_TIKTOK_CLIENT_SECRET` | TikTok app credentials (for code exchange + refresh) |
| `PEANUTCLIP_TIKTOK_REDIRECT_URI` | Must match TikTok app redirect config |
| `PEANUTCLIP_TIKTOK_REFRESH_TOKEN` | Optional at startup; runtime refresh endpoint can rotate it |
| `PEANUTCLIP_PUBLISH_PROVIDER` | Set to `tiktok` to enable automated upload |

### 1.2 TikTok account wiring (required for automated posting)

**Step 1 — Create a TikTok Developer app**

1. Log in to https://developers.tiktok.com
2. Create a new app
3. Add Login Kit and Content Posting API products
4. Request `video.upload` scope approval

**Step 2 — Complete OAuth and capture user access token**

```bash
curl --location 'https://open.tiktokapis.com/v2/post/publish/status/fetch/' \
--header 'Authorization: Bearer <access_token>' \
--header 'Content-Type: application/json; charset=UTF-8' \
--data '{"publish_id":"test"}'
```

Set:

```
PEANUTCLIP_TIKTOK_ACCESS_TOKEN=<oauth_access_token>
PEANUTCLIP_TIKTOK_API_BASE_URL=https://open.tiktokapis.com
PEANUTCLIP_TIKTOK_CLIENT_KEY=<client_key>
PEANUTCLIP_TIKTOK_CLIENT_SECRET=<client_secret>
PEANUTCLIP_TIKTOK_REDIRECT_URI=<your_callback_uri>
PEANUTCLIP_TIKTOK_REFRESH_TOKEN=<refresh_token>
```

You can also let PeanutClip manage token exchange and refresh via API:

```bash
# 1) Build authorize URL
curl "https://<your-app>/review/integrations/tiktok/oauth/start"

# 2) After consent, TikTok redirects to callback with ?code=...
#    PeanutClip exchanges code and returns token payload.
curl "https://<your-app>/review/integrations/tiktok/oauth/callback?code=<code>&state=<state>"

# 3) Rotate expired access tokens
curl -X POST "https://<your-app>/review/integrations/tiktok/token/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

**Step 3 — Enable TikTok publishing**

```
PEANUTCLIP_PUBLISH_PROVIDER=tiktok
```

**Step 4 — Verify**

```bash
curl https://<your-app>/health/ready
# Expected: {"status":"ready"}
```

A `503` means a required credential is missing; the response body will name the missing variable.

Note: TikTok may still require creator-side confirmation in-app for final post completion, depending on account/app permissions.

Note: publishing and status sync now attempt one automatic refresh retry when TikTok returns an auth/token error.

---

## 2. Deploy procedure

### 2.1 Standard deploy (CI/CD)

Push to `main` — the `deploy.yml` workflow runs automatically:

1. Full test suite with coverage gate (100%)
2. Docker image built and pushed to `ghcr.io`
3. Alembic migrations applied to staging
4. Wait for `/health/ready` → 200 on staging
5. Manual approval gate (GitHub Environments)
6. Alembic migrations applied to production
7. `/health/ready` smoke test on production

### 2.2 Manual deploy (emergency)

```bash
# 1. Pull latest image
docker pull ghcr.io/<org>/<repo>:latest

# 2. Run migrations
docker run --rm \
  --env-file .env \
  -e PYTHONPATH=/app/src \
  ghcr.io/<org>/<repo>:latest \
  python -m alembic upgrade head

# 3. Restart container
docker stop peanutclip-app
docker run -d \
  --name peanutclip-app \
  --env-file .env \
  -p 8000:8000 \
  ghcr.io/<org>/<repo>:latest

# 4. Confirm readiness
curl http://localhost:8000/health/ready
```

---

## 3. Rollback procedure

### 3.1 Application rollback

```bash
# Identify the last good image tag in GitHub Packages or CI logs, e.g. sha-abc1234

docker stop peanutclip-app
docker run -d \
  --name peanutclip-app \
  --env-file .env \
  -p 8000:8000 \
  ghcr.io/<org>/<repo>:sha-abc1234
```

### 3.2 Database rollback

> **Warning**: only downgrade if you are certain the previous revision is backward compatible.

```bash
# Downgrade one revision
docker run --rm \
  --env-file .env \
  -e PYTHONPATH=/app/src \
  ghcr.io/<org>/<repo>:sha-abc1234 \
  python -m alembic downgrade -1

# Downgrade to a specific revision
python -m alembic downgrade <revision_id>

# Show current revision
python -m alembic current

# Show migration history
python -m alembic history
```

---

## 4. Smoke tests

Run these after any deploy or restart:

```bash
BASE=https://<your-app>

# Liveness
curl -f $BASE/health
# → {"status":"ok"}

# Readiness — validates all integration configs
curl -f $BASE/health/ready
# → {"status":"ready"}

# Review queue accessible
curl -f "$BASE/review/queue?limit=5"

# Compliance endpoint accessible
curl -f "$BASE/review/clips/1/compliance"
```

---

## 5. Incident response

### 503 on `/health/ready`

The response body will say exactly which variable is missing, e.g.:

```json
{"detail": "PEANUTCLIP_BUFFER_ACCESS_TOKEN is required when publish_provider=buffer"}
```

Fix: set the variable and restart the container.

### TikTok posts not appearing

1. Check `PEANUTCLIP_PUBLISH_PROVIDER=tiktok` (not `manual`)
2. Verify `PEANUTCLIP_TIKTOK_ACCESS_TOKEN` is still valid (tokens can expire)
3. Confirm your TikTok app has approved `video.upload` scope
4. Test the token manually with a status endpoint request:
   ```bash
  curl --location 'https://open.tiktokapis.com/v2/post/publish/status/fetch/' \
  --header "Authorization: Bearer $PEANUTCLIP_TIKTOK_ACCESS_TOKEN" \
  --header 'Content-Type: application/json; charset=UTF-8' \
  --data '{"publish_id":"v_inbox_file~v2.example"}'
   ```
5. Review the `TikTokApiError` entries in application logs

### Database migration fails mid-deploy

1. The old application version is still running — do **not** hard-restart
2. Identify the failing migration in `alembic history`
3. Fix the migration file and redeploy, or manually apply the DDL
4. If data is inconsistent, restore from the pre-deploy database snapshot

### High memory / CPU

The Dockerfile defaults to `--workers 2`. Tune via environment variable:

```
PEANUTCLIP_WORKERS=4
```

Update the container CMD accordingly or pass `--workers` to uvicorn in the run command.

---

## 6. Regular maintenance

| Task | Frequency | Command |
|---|---|---|
| Rotate `PEANUTCLIP_SECRET_KEY` | 90 days | Update env, rolling restart |
| Rotate TikTok access token | On expiry / revocation | §1.2 Step 2 |
| Check Alembic has no pending migrations | Before each deploy | `alembic current` |
| Review dependency updates | Monthly | `pip list --outdated` |
