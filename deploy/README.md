# Production deploy assets

These files assume:
- repo checkout at `/srv/ai-infrastructure-radar`
- backend virtualenv at `/srv/ai-infrastructure-radar/.venv`
- backend env file at `/etc/ai-radar/backend.env`
- frontend env file at `/etc/ai-radar/frontend.env`
- same-origin public host such as `https://app.example.com`

Recommended public edge:
- Caddy for automatic HTTPS and certificate renewal
- Nginx only if you already manage TLS certificates yourself

Install flow:
1. Point DNS `A` or `AAAA` for your public host to the VM.
2. Open inbound ports `80` and `443` on the VM security group / firewall.
3. Copy `deploy/env/backend.env.example` and `deploy/env/frontend.env.example` into `/etc/ai-radar/`.
4. Adjust the domain and database URL values.
5. Install the systemd units from `deploy/systemd/`.
6. For Caddy:
   - install the `caddy` package on the VM
   - copy `deploy/caddy/ai-infrastructure-radar.Caddyfile` to `/etc/caddy/Caddyfile`
   - replace `app.example.com` with the real host
7. For Nginx:
   - copy `deploy/nginx/ai-infrastructure-radar.conf`
   - replace `app.example.com` and certificate paths
8. Run `systemctl daemon-reload`.
9. Enable and start:
   - `ai-radar-backend.service`
   - `ai-radar-frontend.service`
   - `ai-radar-pipeline.timer`
   - `caddy.service` or `nginx.service`
