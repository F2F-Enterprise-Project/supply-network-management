# F2F Supply & Network (SNM) Service
**Build Version:** 0.2.1

## Overview
The Supply & Network Management (SNM) service is the integration gateway for the Farm-to-Fork (F2F) ecosystem. It manages the primary registry for vendors, product categories, and incoming shipment lots. This service is built using the LightAPI v2 framework, which allows a single class to function as the ORM model, Pydantic schema, and REST endpoint simultaneously.

## Core Technologies
- Framework: LightAPI v2 (Starlette + Pydantic v2 + SQLAlchemy 2.0).
- Database: SQLite (supplynetwork.db) utilized for the MVP phase.
- Runtime: Python 3.12-slim in a Docker-containerized environment.
- Integration: Synchronous REST requests to the external AgNet API.

## Installation & Running
**Prerequisites**
- Docker and Docker Compose installed.
- An AGNET_SECTION_KEY environment variable configured for external API authentication.

**Launching the Service**

To build the image and start the service along with its dependencies, run:

```Bash
docker-compose up --build
```
The service will be available at http://localhost:8000.

The database is automatically created and seeded with sample data when the Docker image is built. No manual setup required.

## API Contracts
1. **Operational Endpoints**

These endpoints are required for global monitoring and compliance verification.

- Health Check (`GET /api/v1/health`): Returns the service status and current UTC time.

- Version Check (`GET /api/v1/version`): Returns the current build version (`0.2.1`).

2. **Business Domain Endpoints**

All business endpoints utilize `api/v1/` as the route prefix.


| Endpoint              | Data Model  | Description                                                        |
| --------------------- | ----------- | ------------------------------------------------------------------ |
| /api/v1/vendors       | Vendor      | Merges local registry with live data from AgNet (146.190.243.241). |
| /api/v1/categories    | Category    | Manages the 3-level product hierarchy.                             |
| /api/v1/products      | Product     | The master product catalog for the fulfillment system.             |
| /api/v1/shipments     | Shipment    | Records incoming vendor shipment metadata.                         |
| /api/v1/shipment-lots | ShipmentLot | Tracks individual lots with UUIDs (lot_id) and quantities.         |

## Global Integration Standards
**Timestamp Format**

All timestamps generated or returned by this service follow the ISO-8601 UTC format with the mandatory `Z` suffix.

- Format: `YYYY-MM-DDTHH:MM:SSZ`.

- Example: `2026-04-06T08:35:00Z`.

**Data Precision and Normalization**

- Quantity Precision: All shipment quantities (`quantity_on_hand`) must be treated as high-precision values, specifically decimal(14,3), regardless of the source format.

- Unit Enforcement: Product units are strictly normalized to `kg` (kilograms) or `l` (liters).

**Optimistic Locking**

Every domain model includes a `version` field. To perform a `PUT` or `PATCH` update, the client must provide the current version number in the request body to prevent concurrent data conflicts.

## Documentation Links
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI Spec: `http://localhost:8000/openapi.json`
