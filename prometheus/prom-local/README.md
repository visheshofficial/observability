
From the prom-local/ directory:
# Run, stop, resume

```bash
# Start in background
docker compose up -d

# Check containers
docker compose ps

# View Prometheus UI
open http://localhost:9090

# Stop (keeps data & config)
docker compose down

# Start again (picks up same TSDB and config)
docker compose up -d
```