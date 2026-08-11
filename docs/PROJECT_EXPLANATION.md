# IoT Queuing and Processing System

## Overview

This project is designed for an industrial or on-prem IoT environment where multiple devices continuously generate telemetry such as temperature, humidity, and device-level operational signals. The primary objective is to accept incoming data from edge devices or sensors, immediately acknowledge receipt through a lightweight API layer, and then process the workload asynchronously in the background without blocking the HTTP request pipeline.

The architecture combines several proven components:

- FastAPI for exposing a clean, high-performance REST API
- Celery for asynchronous task execution
- Redis as the broker and lightweight queueing backend
- PostgreSQL-compatible TimescaleDB for time-series persistence
- Docker Compose for repeatable local and on-prem deployment

This design is especially useful in real-world IoT systems where ingestion volume can spike suddenly, sensor nodes must not wait for slow database writes, and processing should continue reliably even under load.

---

## Business and System Purpose

In a typical IoT deployment, sensors produce readings continuously, often in bursts rather than at a steady pace. If those readings are written directly to a database during a live HTTP request, the application can become slow or unstable under load. This project addresses that by separating the ingestion path from the processing path.

The system behaves in two distinct phases:

1. Intake and acknowledgement
   - A device sends data to the API.
   - The API validates the payload.
   - The request is acknowledged quickly.

2. Background processing
   - The actual data handling is queued to Celery.
   - A worker consumes the task from Redis.
   - The worker processes or stores the data in a persistence layer.

This makes the system resilient and scalable, especially when multiple devices send data simultaneously.

---

## High-Level Architecture

### 1. IoT Device Layer
IoT devices or gateways send telemetry to the application through HTTP endpoints. These devices are not expected to wait for long-running database writes or business logic. They simply post a payload and receive a quick response indicating the task has been queued.

### 2. FastAPI Ingestion Layer
FastAPI acts as the ingestion front-end. It exposes endpoints for receiving device payloads and validating them using Pydantic models.

When a post arrives, the API does not process the full workload itself. Instead, it hands off the work to Celery using a task queue.

### 3. Redis Queue Layer
Redis is used as the message broker for Celery. It stores queued jobs until a worker is available to consume them. Redis is ideal for this role because it is lightweight, fast, and robust for task dispatch patterns.

### 4. Celery Worker Layer
Celery workers continuously pull tasks from Redis and execute the processing logic. This layer is responsible for business operations such as:

- validating or enriching sensor data
- storing data in a database
- performing analytics or downstream processing
- triggering alerts or integration workflows

### 5. Persistence Layer
The application is structured to support PostgreSQL-compatible TimescaleDB storage. TimescaleDB is a strong fit for IoT data because it is optimized for time-series data and high write throughput.

---

## Request Flow (End-to-End)

The normal lifecycle of a sensor message is as follows:

1. A device sends JSON payload to `POST /sensor-data/`.
2. FastAPI validates the payload using the data model.
3. The API calls `process_sensor_data.delay(...)`.
4. Celery serializes the task and pushes it into Redis.
5. A worker picks up the queued task from Redis.
6. The worker executes the processing function.
7. The task can persist data into TimescaleDB or trigger additional logic.
8. The client receives a quick acknowledgment that the task was accepted for processing.

This pattern is highly beneficial because the device-facing latency remains low even when the back-end processing is slow or under heavy load.

---

## Why This Architecture Works Well

### Decoupling of concerns
The API is responsible only for receiving and validating input. The worker handles processing. This separation improves maintainability and makes the system easier to scale.

### Better resilience under load
When the database or downstream services slow down, the queue absorbs the delay instead of making the API layer unresponsive.

### Horizontal scalability
More Celery workers can be launched to process larger volumes of events without changing the public API interface.

### Stronger reliability and observability
Celery integrates well with monitoring and retry patterns. Queued tasks can be retried, time-limited, and observed in logs or monitoring dashboards.

---

## Detailed Component Breakdown

### `app/main.py`
This is the FastAPI application entrypoint. It defines the API routes and request validation. The main ingestion endpoint accepts sensor payloads and enqueues a Celery task.

Responsibilities:

- define API routes
- validate incoming payloads
- enqueue work asynchronously
- expose health or fetch endpoints for system monitoring

### `app/tasks.py`
This is where the long-running or data-processing logic lives. The task is registered with Celery using a task name and can be extended to persist to the database, run transformations, trigger alerts, or connect to external systems.

### `app/celery_app.py`
This creates the central Celery application instance and configures the broker, result backend, serializers, and timezone. This keeps task configuration centralized and easier to manage.

### `app/config.py`
This file is the configuration layer for Redis, PostgreSQL, Celery, and on-prem server integration. It reads values from environment variables so the system remains portable across local, staging, and production environments.

### `app/on_prem_fetcher.py`
This module is specifically meant for reading data from an on-prem server IP. It builds a target URL using variables like server IP, port, and endpoint, then fetches JSON data using Python’s standard library HTTP handling. This is particularly useful when the system must pull data from a legacy machine or local facility server rather than only receiving data from remote devices.

### `app/schemas.py`
This file defines the request and response models with validation logic. Using Pydantic ensures the API rejects malformed data early and maintains consistent data structures.

### `app/models.py`
This is the SQLAlchemy model for the sensor dataset. It maps to a TimescaleDB/PostgreSQL table and defines the shape of persisted telemetry records.

---

## On-Prem Server Integration

The project is designed to work in an on-prem environment where the application may need to connect to a local or internal machine instead of a public cloud service. This is handled through configurable variables such as:

- `ON_PREM_SERVER_IP`
- `ON_PREM_SERVER_PORT`
- `ON_PREM_DATA_ENDPOINT`
- `ON_PREM_PROTOCOL`

These are important because many industrial deployments use a private LAN, a factory network, or a controlled server environment where the application must fetch or query data from an internal system. The fetcher builds the target URL dynamically, avoiding hard-coded network assumptions.

This flexibility is essential for enterprise and industrial IoT systems where infrastructure is often segmented and network topology is controlled by the organization rather than by public cloud availability.

---

## Docker and Deployment Model

The project uses Docker Compose to orchestrate the stack locally and in on-prem test environments. The stack consists of:

- FastAPI service
- Celery worker service
- Redis broker
- TimescaleDB/PostgreSQL service

This model provides several advantages:

- repeatable deployments
- consistent runtime dependencies
- easy local testing
- straightforward migration toward bigger deployed environments

The Docker configuration is designed so the app runs as a containerized service while maintaining easy access to required dependencies and environment variables.

---

## Operational Characteristics

### Reliability
The queueing mechanism protects the API from becoming blocked by slow persistence operations. Tasks are accepted quickly and processed independently.

### Scalability
As the number of devices increases, the worker pool can be scaled horizontally to match demand.

### Maintainability
Clear separation of API, task processing, and configuration makes debugging and expansion easier later.

### Security
In real deployments, credentials, Redis endpoints, and internal network addresses should be managed using environment variables, secrets management, and restricted networking. Production deployments should never expose internal services unnecessarily.

---

## Typical Use Cases

This system fits several categories of workloads:

- industrial monitoring
- warehouse temperature tracking
- water and energy telemetry collection
- agricultural sensor networks
- building management systems
- machine health monitoring

In each case, the key need is the same: ingest data quickly, decouple processing from request handling, then run analysis or persistence asynchronously.

---

## Production Considerations

Although the project is robust for local and on-prem testing, production usage should include additional hardening:

- secure Redis with access controls and TLS where required
- protect database credentials and configuration using secret management
- enable proper persistence and backup for Postgres/TimescaleDB
- add retries, dead-letter handling, and task monitoring for Celery
- set proper service health checks for FastAPI, Redis, and workers
- restrict network access to trusted internal hosts
- implement log aggregation and metrics collection

---

## Design Summary

The project is not just a simple example of a Python API; it represents a practical distributed IoT pattern:

- sensor data enters through an API
- the API responds immediately
- work is queued for asynchronous processing
- Redis handles task distribution
- workers process the workload reliably
- persistent storage preserves telemetry for later analysis

This gives the system a strong balance of responsiveness, scalability, and operational reliability, making it well suited for real-world on-prem IoT deployment scenarios.

---

## Project Layout

- `app/` — FastAPI app, Celery configuration, task logic, schemas, and models
- `docker/` — Docker build and deployment configuration
- `docs/` — architecture and operational guidance
- `requirements.txt` — runtime dependencies

---

## Final Note

This project demonstrates a production-oriented pattern for handling IoT telemetry. The design focuses on availability, responsiveness, and maintainability while keeping the system flexible enough for internal network-driven deployments. It is a clean foundation for scaling into more advanced analytics, alerting, and industrial monitoring environments.