# Render Blueprint deploy

This is the lowest-friction hosted path for the current repo.

What it creates from one `render.yaml` file:
- `radar-db` Postgres database
- `radar-backend` private backend service
- `radar-frontend` public frontend service
- `radar-pipeline` cron job every 6 hours

## Why this is easier
- one Blueprint creates the whole stack
- Render gives the frontend HTTPS automatically
- the frontend proxies `/api/*` to the private backend
- you do not need a VM, Caddy, or a public backend URL

## What you do
1. Push the repo to GitHub.
2. In Render, click `New +` -> `Blueprint`.
3. Select the repo.
4. Render detects `render.yaml`.
5. Fill in any prompted secrets:
   - `GITHUB_TOKEN` if you want GitHub API access beyond anonymous limits
   - `HUGGINGFACE_TOKEN` if you want authenticated Hugging Face API access
6. Create the Blueprint.

## After deploy
Open the `radar-frontend` service URL and test:

```bash
curl -fsS https://<frontend>.onrender.com/api/health
curl -fsS https://<frontend>.onrender.com/api/dashboard/summary
curl -fsS https://<frontend>.onrender.com/api/operations/status
```

## Notes
- The Blueprint keeps the backend private.
- The frontend health check uses `/api/health`, so it validates the backend path too.
- `BACKEND_TRUSTED_HOSTS` is set to `["*"]` in this Blueprint because Render private hostnames are platform-assigned and the backend is not internet-facing.
- The database plan in `render.yaml` is `basic-256mb` to keep first deploy friction low. Upgrade it once you want better headroom.
