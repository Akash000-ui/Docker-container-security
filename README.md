# Container Security Monitoring Framework for Docker-Based Applications

Academic B.Tech major project for monitoring Docker containers, detecting security misconfigurations, scanning images for vulnerabilities, and presenting findings in a web dashboard.

## Current status

Phase 2 is implemented:

- Flask application factory
- Environment-based configuration
- SQLite database in the ignored `instance/` directory
- SQLAlchemy extension and initial `User` model
- Dashboard placeholder
- Health endpoint
- User-friendly 404 and 500 pages
- Initial responsive visual design

## Development setup

Use the dedicated Conda environment created during Phase 0:

```powershell
conda activate container-security
pip install -r requirements.txt
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

Check application and database health at <http://127.0.0.1:5000/health>.

## Planned implementation order

1. Authentication
2. Docker SDK integration
3. Container monitoring
4. Security configuration rules
5. Risk scoring and alerts
6. Trivy image scanning
7. Charts and reports

The project design baseline is documented in [docs/phase-1-design.md](docs/phase-1-design.md).

