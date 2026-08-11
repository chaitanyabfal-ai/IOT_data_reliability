# Runbook — IoT Queuing System (FastAPI + Celery + Redis)

## 1. Prerequisites for Ubuntu GNOME Terminal

Before starting the project, make sure Docker is installed and usable from your normal GNOME terminal session.

### Check if Docker is already installed

```bash
docker --version
docker compose version
```

If Docker is not installed, install it on Ubuntu using the official Docker repository or package manager workflow:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Allow your user to use Docker without sudo

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Then reopen the GNOME terminal or log out and log back in.

### Verify Docker access

```bash
docker ps
```

If this works without sudo, Docker is configured correctly.

---

## 2. Project setup

From the repository root:

```bash
cd /path/to/IOT_queuingfix
ls
```

The project includes:

- `app/` — FastAPI + Celery logic
- `docker/` — Dockerfile and Docker Compose file
- `docs/` — project documentation

---

## 3. Configure on-prem server variables

Set the IP and endpoint of the on-prem server that this app should fetch data from. Replace the values below with your actual server details:

```bash
export ON_PREM_SERVER_IP=192.168.1.25
export ON_PREM_SERVER_PORT=9000
export ON_PREM_DATA_ENDPOINT=/api/data
export ON_PREM_PROTOCOL=http
```

This produces the target URL:

```bash
http://192.168.1.25:9000/api/data
```

The app reads these values via the environment and uses them in the fetcher logic.

---

## 4. Start the stack

Use the modern Docker Compose command, not the old standalone `docker-compose` command:

```bash
cd /path/to/IOT_queuingfix
docker compose -f docker/docker-compose.yml up --build -d
```

This will start:

- Redis
- TimescaleDB/PostgreSQL
- FastAPI API server
- Celery worker

### Alternative: run from the docker folder

```bash
cd /path/to/IOT_queuingfix/docker
docker compose up --build -d
```

> Use `docker compose` in GNOME terminal; the legacy `docker-compose` binary may not exist on newer Ubuntu installs.

---

## 5. Verify the services are running

```bash
docker compose -f docker/docker-compose.yml ps
```

Check that:

- the `fastapi` service is running
- the `celery_worker` service is running
- Redis and TimescaleDB are healthy

You can also inspect logs:

```bash
docker compose -f docker/docker-compose.yml logs -f fastapi
docker compose -f docker/docker-compose.yml logs -f celery_worker
```

---

## 6. Test the API

### Health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok"}
```

### Send a sensor payload

```bash
curl -X POST http://localhost:8000/sensor-data/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": "sensor1", "temperature": 25.5, "humidity": 60}'
```

Expected response:

```json
{"status": "queued", "data": {"device_id": "sensor1", "temperature": 25.5, "humidity": 60}}
```

### Fetch on-prem server data

```bash
curl http://localhost:8000/on-prem-data
```

This endpoint requests the configured remote on-prem URL and returns the JSON payload from that server.

---

## 7. Troubleshooting in GNOME terminal

### Docker command not found

```bash
which docker
```

If nothing is returned, Docker is not installed or not in PATH.

### Permission denied to Docker socket

```bash
docker ps
```

If you see a permission error, run:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Then close and reopen the terminal.

### `docker compose` command is not recognized

Use the plugin-based command:

```bash
docker compose version
```

If the command is missing, install Docker Compose plugin or use the legacy `docker-compose` command only if it is present.

### Tasks are not being processed

Check the worker logs:

```bash
docker compose -f docker/docker-compose.yml logs celery_worker
```

Potential causes:

- Redis is not reachable
- Celery import path is wrong
- environment variables are malformed
- the app failed to start properly

### Redis connectivity issues

```bash
docker exec -it $(docker compose -f docker/docker-compose.yml ps -q redis) redis-cli ping
```

Expected output:

```text
PONG
```

### Database connection issues

Check the Postgres/TimescaleDB container logs:

```bash
docker compose -f docker/docker-compose.yml logs timescaledb
```

Ensure credentials match the expected values in the application configuration.

---

## 8. Scaling workers

To run multiple Celery workers, increase the worker replica count:

```bash
docker compose -f docker/docker-compose.yml up --scale celery_worker=3 -d
```

This is helpful when the volume of sensor data increases and the queue needs more parallel processing capacity.

---

## 9. Stop and clean up

To stop the stack:

```bash
docker compose -f docker/docker-compose.yml down
```

To stop and remove volumes as well:

```bash
docker compose -f docker/docker-compose.yml down -v
```

This is useful for a full reset during testing or redeployment.

---

## 10. Useful maintenance notes

- Monitor Redis memory and queue growth
- Monitor FastAPI logs for unexpected HTTP errors
- Track Celery task failures and retries
- Use persistent volumes for TimescaleDB data
- Keep environment variables centralized and secure in production
- Use host firewalls or private networking for on-prem internal communications

---

## 11. Verification checklist

Before considering the deployment ready:

- Docker is installed and usable from GNOME terminal
- `docker compose version` succeeds
- `docker compose -f docker/docker-compose.yml up --build -d` succeeds
- `curl http://localhost:8000/health` returns success
- `curl -X POST http://localhost:8000/sensor-data/ ...` returns a queued response
- Celery worker logs show task processing
- The on-prem fetch endpoint returns expected data from the configured server

---

If needed, this project can also be extended with a `.env` file, a `Makefile`, or a helper script for common Ubuntu GNOME terminal startup tasks.
