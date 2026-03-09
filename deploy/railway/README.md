# Railway deploy

This is the fastest path to get the app live without setting up a VM.

Use four Railway services in one project:
- `pgvector` database
- `backend` private service
- `frontend` public service
- `pipeline` cron service

## Why this works
- The frontend fetches data server-side, so only the frontend needs a public domain.
- The backend can stay private and be reached from the frontend over Railway private networking.
- Railway gives the frontend HTTPS automatically on its generated domain.
- The pipeline can run as a cron service using the same backend image, but with a one-shot start command.

## 1. Create the Railway project
1. Push this repo to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. Add a `pgvector` database service, not plain Postgres.

Reason:
- the app's migrations enable the `vector` extension
- the plain database service may not satisfy that requirement

## 2. Create the backend service
Create a service named `backend` from the same repo.

Settings:
- Root directory: repo root
- Dockerfile path: `deploy/docker/backend.prod.Dockerfile`
- Start command: leave default, or set `/app/scripts/start_backend.sh`
- Public networking: off

Environment:
```env
APP_ENV=production
DATABASE_URL=${{pgvector.DATABASE_URL}}
BACKEND_CORS_ORIGINS=["https://<frontend-public-domain>"]
BACKEND_TRUSTED_HOSTS=["backend.railway.internal","backend","127.0.0.1","localhost","testserver"]
SEC_USER_AGENT=ai-infrastructure-radar ops@example.com
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
```

Notes:
- `backend.railway.internal` assumes the Railway service name is `backend`
- if you rename the service, update that hostname too

## 3. Create the frontend service
Create a service named `frontend` from the same repo.

Settings:
- Root directory: repo root
- Dockerfile path: `deploy/docker/frontend.prod.Dockerfile`
- Public networking: on

Environment:
```env
INTERNAL_API_URL=http://backend.railway.internal:8000
NEXT_PUBLIC_API_URL=https://<frontend-public-domain>
```

Notes:
- Railway will assign a public domain like `https://frontend-production-xxxx.up.railway.app`
- use that value for both the frontend public domain and backend CORS origin initially

## 4. Create the pipeline service
Create a third app service named `pipeline` from the same repo.

Settings:
- Root directory: repo root
- Dockerfile path: `deploy/docker/backend.prod.Dockerfile`
- Start command: `/app/scripts/start_pipeline_once.sh`
- Public networking: off

Environment:
```env
APP_ENV=production
DATABASE_URL=${{pgvector.DATABASE_URL}}
BACKEND_CORS_ORIGINS=["https://<frontend-public-domain>"]
BACKEND_TRUSTED_HOSTS=["backend.railway.internal","backend","127.0.0.1","localhost","testserver"]
SEC_USER_AGENT=ai-infrastructure-radar ops@example.com
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
```

Then convert this service to a cron job with schedule:
```text
0 */6 * * *
```

That runs the pipeline every 6 hours.

## 5. First deploy check
After the first backend deploy:
- watch the logs for `alembic upgrade head`
- confirm the service stays healthy

After the first frontend deploy:
- open the Railway-generated frontend URL
- verify the dashboard renders

After the first pipeline run:
- verify `/api/operations/status` from the frontend-backed app shows fresh timestamps

## 6. What to test
Use the frontend public URL:
```bash
curl -fsS https://<frontend-public-domain>/api/health
curl -fsS https://<frontend-public-domain>/api/dashboard/summary
curl -fsS https://<frontend-public-domain>/api/operations/status
```

Expected:
- health returns `status: ok`
- dashboard summary returns ranked items
- operations status returns `overall_status: ok`

## 7. Custom domain later
Once the generated Railway domain works:
1. attach your custom domain to the `frontend` service
2. update:
   - `NEXT_PUBLIC_API_URL`
   - `BACKEND_CORS_ORIGINS`
3. redeploy `backend` and `frontend`

## 8. Current limitation
This Railway path does not use the repo's Caddy/Nginx edge service.

That is intentional:
- Railway already provides HTTPS and routing for the public frontend
- the frontend talks to the backend privately
- this is the lowest-friction hosted path without a VM
