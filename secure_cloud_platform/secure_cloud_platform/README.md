# Secure Cloud Computing Platform (Base Project)

A base Flask project demonstrating core patterns of a secure cloud storage platform:
user authentication, envelope encryption for uploaded files, role-based access
control (user / admin), and an audit log of security-relevant actions.

## Features

- **Authentication**: Registration and login with salted password hashing (Werkzeug).
- **Envelope encryption**: Each uploaded file gets its own random encryption key
  (a "data key"). The file is encrypted with that key, and the key itself is
  encrypted with a server-side master key before being stored in the database.
  Compromising one file's key never exposes other files. Files are never written
  to disk unencrypted.
- **Role-based access control**: `user` role sees only their own files; `admin`
  role can view all files, all users, and the audit log.
- **Audit logging**: Logins, logouts, uploads, downloads, deletions, and access
  denials are recorded with timestamp and IP address.
- **Hardened sessions**: HTTP-only, SameSite cookies; secure flag auto-enabled
  in production.
- **File type allowlist and upload size limit** to reduce attack surface.

## Architecture

```
secure_cloud_platform/
├── app.py                # App factory, blueprint registration, error handlers
├── config.py             # Environment-driven configuration
├── models.py             # User, File, AuditLog (SQLAlchemy models)
├── auth.py                # /register, /login, /logout
├── files.py               # /, /upload, /download/<id>, /delete/<id>, /admin
├── utils/
│   ├── crypto_utils.py    # Envelope encryption helpers (Fernet/AES)
│   └── decorators.py      # @admin_required route guard
├── templates/             # Jinja2 HTML templates
├── static/style.css       # UI styling
├── generate_keys.py       # One-off script to generate SECRET_KEY / MASTER_KEY
├── make_admin.py          # CLI to promote a user to admin
└── requirements.txt
```

## Setup

1. **Install dependencies** (Python 3.10+ recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Generate secrets**:
   ```bash
   python generate_keys.py
   ```
   Copy the printed `SECRET_KEY` and `MASTER_KEY` values.

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Paste your generated keys into `.env`.

4. **Run the app**:
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000`. The SQLite database and tables are created
   automatically on first run.

5. **(Optional) Promote a user to admin**:
   ```bash
   python make_admin.py <username>
   ```

## Security notes / next steps for a production version

This is a teaching/base project. Before deploying for real use, you'd want to:

- Move the master key to a proper secrets manager / KMS instead of `.env`.
- Add HTTPS termination (e.g. via a reverse proxy) and set `FLASK_ENV=production`
  so secure cookies are enforced.
- Add rate limiting on `/login` to slow brute-force attempts.
- Add CSRF protection (e.g. `Flask-WTF`) on all forms.
- Move file storage to object storage (S3-compatible) rather than local disk
  for real horizontal scaling.
- Add email verification and password reset flows.
- Replace SQLite with PostgreSQL for concurrent production use.

## Tech stack

- Flask 3, Flask-SQLAlchemy, Flask-Login
- `cryptography` (Fernet / AES-128-CBC + HMAC) for encryption
- SQLite (default) — swap `DATABASE_URL` for Postgres/MySQL easily
- Vanilla HTML/CSS (no JS framework) for the base UI
