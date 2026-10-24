# Container Security Monitoring Framework for Docker-Based Applications

Academic B.Tech major project for monitoring Docker containers, detecting security misconfigurations, scanning images for vulnerabilities, and presenting findings in a web dashboard.

## Current status

Phase 8 is implemented:

- Flask application factory
- Environment-based configuration
- SQLite database in the ignored `instance/` directory
- SQLAlchemy extension and initial `User` model
- Administrator login and logout
- Hashed administrator passwords
- Protected dashboard routes
- CLI command for creating the first administrator
- Docker SDK integration with Docker Desktop
- Container inventory synchronization to SQLite
- Container list and detail pages
- Container inventory JSON APIs
- Docker availability in the health endpoint
- CPU, memory, network, and block I/O monitoring
- Container process and recent log APIs
- Runtime metrics stored in SQLite
- Live runtime monitoring page with five-second refresh
- Rule-based container security analysis
- Timestamped security findings stored in SQLite
- Security findings page and API
- Security score and risk category calculation
- Persistent open/resolved alerts with deduplication
- Alert dashboard and resolve action
- Trivy image vulnerability scanning
- CVE/package/severity result storage
- Vulnerability scan history and dashboard
- Vulnerability scan and result APIs
- Dashboard placeholder
- Health endpoint
- User-friendly 404 and 500 pages
- Initial responsive visual design

## Development setup

Use the dedicated Conda environment created during Phase 0:

```powershell
conda activate container-security
pip install -r requirements-dev.txt
```

Copy the environment template if needed:

```powershell
Copy-Item .env.example .env
```

Run the application:

```powershell
python run.py
```

Open the dashboard at <http://127.0.0.1:5000>.

Create the first administrator in a separate terminal:

```powershell
flask --app run.py create-admin
```

The command asks for a username and password without printing the password.

Check application and database health at <http://127.0.0.1:5000/health>.

## Planned implementation order

1. Charts and reports

Runtime monitoring endpoints:

```text
GET /api/containers/<docker_id>/stats
GET /api/containers/<docker_id>/logs?tail=200
GET /api/containers/<docker_id>/processes
GET /api/containers/<docker_id>/security
GET /api/alerts
POST /alerts/<alert_id>/resolve
POST /vulnerabilities/scan
POST /api/images/<image_name>/scan
GET /api/scans/<scan_id>
GET /api/vulnerabilities?severity=CRITICAL
```

The project design baseline is documented in [docs/phase-1-design.md](docs/phase-1-design.md).

