# Docker Investigation TODO

## Problem
Container builds and starts, but the HTTP server doesn't respond. Health checks fail.

## Symptoms
- `docker run -p 8080:8000 nightwatch-backend` starts without error
- Process is running: `python -m nightwatch --mock-sensors --config /app/config/docker.yaml`
- No logs appear (stdout is empty)
- `curl localhost:8080/` returns "Connection reset by peer"
- Container marked as "unhealthy"

## Likely Causes (investigate in order)

### 1. Server not starting
The `DashboardServer.start()` may not be called, or it's starting on wrong interface.
- Check `nightwatch/__main__.py` async orchestration
- Verify `DashboardServer` actually calls uvicorn

### 2. Missing /health endpoint
The health check expects `/health` but it may not exist.
- Add `/health` route to `nightwatch/dashboard/server.py`
- Or remove HEALTHCHECK from Dockerfile temporarily

### 3. Event bus blocking
ZeroMQ pub/sub might be waiting for subscribers before proceeding.
- Check if event bus init blocks the main thread
- Try running without event bus to isolate

### 4. Async loop issue
The `asyncio.run()` in `__main__.py` may not be handling the server correctly.
- Dashboard server needs to run in background while detectors run
- May need `asyncio.gather()` or task management

## Quick Test
```bash
# Run interactively to see output
docker run -it --rm -p 8080:8000 nightwatch-backend

# Or bypass entrypoint to debug
docker run -it --rm nightwatch-backend /bin/bash
python -c "from nightwatch.dashboard.server import DashboardServer; print('import ok')"
```

## Fix Priority
1. Add `/health` endpoint (quick win)
2. Add print statements to trace startup
3. Fix async orchestration if needed
