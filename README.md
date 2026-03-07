# Campus Security Alert System (CSAS)

Web-based application for real-time security alerts and incident management on campus. Built with Python, FastAPI, SQLAlchemy, and SQLite per the CSAS Requirements Specification (Group 19).

## Features

- **Authentication**: Register/login with university ID and email (FR-01). Bcrypt password hashing (FR-15). JWT for API (FR-20). Optional session expiry (FR-05). Failed login logging (FR-07).
- **RBAC**: Roles — Student, Staff, Security Officer, Administrator (FR-03). Admin can assign/modify/revoke roles (FR-04).
- **Alerts**: Create and broadcast alerts (Security Officer/Admin). Severity, location, incident type (FR-08, FR-09). 90-day retention (FR-14). Real-time SSE stream (FR-10).
- **Incident reporting**: Users report incidents; security is notified (FR-12).
- **Audit & dashboard**: Audit log for all relevant actions (FR-22, FR-23). Metrics and heat-map data (FR-24, FR-27). Filter/export logs (FR-25).
- **Security**: Rate limiting on login and alerts (FR-21). Input validation via Pydantic. Use TLS in production (FR-17).

## Setup

1. **Python**: 3.11+ recommended.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment**: Copy `.env.example` to `.env` and set at least:
   - `SECRET_KEY` (min 32 chars for production)
   - Optionally `DATABASE_URL` (default: `sqlite:///./csas.db`)

4. **Run**:
   ```bash
   uvicorn app.main:app --reload
   ```
   - Web UI: http://127.0.0.1:8000
   - API docs: http://127.0.0.1:8000/docs

## Usage

- **Register** at `/register` with institutional email and university ID.
- **Login** at `/login` (or `POST /api/auth/login` with form `username`/`password`). Use the returned JWT as `Authorization: Bearer <token>` for protected API calls.
- **Alerts**: List at `/alerts` or `GET /api/alerts`. Create via `POST /api/alerts` (Security Officer/Admin only). Subscribe to live updates at `GET /api/alerts/stream` (SSE).
- **Report incident**: `/report` or `POST /api/incidents`.
- **Dashboard**: `/dashboard` (metrics and heat-map; Security Officer/Admin).
- **Admin**: `/admin` (user list, role changes, audit log, export).

## Database

SQLite by default (`./csas.db`). To use PostgreSQL, set `DATABASE_URL=postgresql://...` and ensure the driver is installed. Tables are created on startup via `init_db()`.

## Production notes

- Set `SECRET_KEY` and disable `DEBUG`.
- Run behind HTTPS (TLS 1.2+) (FR-17).
- Keep secrets in environment or a secrets manager (SRS §5.1).
