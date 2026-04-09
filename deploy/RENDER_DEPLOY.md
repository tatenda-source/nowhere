# Deploy Nowhere on Render (Free Tier)

The `render.yaml` blueprint at the repo root provisions everything automatically:
- **nowhere-api** -- FastAPI backend (Docker, free web service)
- **nowhere-web** -- Static PWA site (free static site)
- **nowhere-redis** -- Redis 75 MB (free, no persistence -- fine for 24h ephemeral data)

## Steps

1. Sign up or log in at [render.com](https://render.com) using your GitHub account.
2. Go to **Blueprints** in the dashboard, then click **New Blueprint Instance**.
3. Connect the `tatenda-source/nowhere` repository. Render detects `render.yaml` automatically.
4. Review the proposed services and click **Apply**. Secrets (`JWT_SECRET`, `DEVICE_TOKEN_SECRET`) are auto-generated.
5. Wait for the build to complete (~3-5 minutes).
6. Visit `https://nowhere-web.onrender.com` to use the app.

## Notes

- **Cold starts**: The free web service spins down after 15 minutes of inactivity. The first request after idle takes ~30 seconds while the container restarts. This is expected on the free plan.
- **Redis limits**: 75 MB, no persistence across restarts. All data uses TTL anyway, so this is acceptable.
- **WebSockets**: The static site rewrites `/ws/*` to the backend, so WebSocket connections work transparently.
- **Custom domain**: In the Render dashboard, go to each service's Settings and add your domain under Custom Domains. Update the `ALLOWED_ORIGINS` env var on `nowhere-api` to include the new origin.
