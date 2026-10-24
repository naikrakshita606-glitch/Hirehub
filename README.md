# HireHub

HireHub is a full-stack Flask recruitment portal with role-based access for candidates, recruiters, and admins. It includes job search, applications, resume uploads, interview scheduling, analytics, reporting, and a REST API layer.

## Features
- **Candidates:** profile and resume management, job search and filtering, tailored recommendations, applications/status tracking, interviews, and notifications
- **Recruiters:** profile management, owned job creation/editing/closing, applicant review and status updates, resume access for applicants, interview scheduling, and notifications
- **Admins:** user and role management, analytics, reports, audit logs, and profile management
- Registration, password hashing, login/logout, role-based authorization, and expiring session cookies
- Responsive browser UI and JSON REST endpoints for authentication, profiles, jobs, applications, interviews, recommendations, notifications, and analytics

## Role workflow
- Register as a candidate or recruiter. Admin accounts are provisioned from `.env`.
- Recruiters create jobs and review applications from their recruiter dashboard.
- Candidates maintain their profile, upload a resume, apply to open jobs, and follow status changes and interviews from their dashboard.
- Admins use the admin dashboard to manage accounts, review reports, and inspect audit history.

The REST API is available under `/api`; authentication endpoints include `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout`. Login establishes a session cookie. Candidate resume upload/download is available at `/api/profile/resume`. Job and application management endpoints require a session and the appropriate role; admin reports and audit data are available from `/api/reports` and `/api/audit-logs`.

Recruiters can reschedule, cancel, or mark interviews completed from the interview page. Admins can download a CSV report from the reports page.

## Run locally
1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```
2. In PowerShell, allow activation for the current session only, then activate and install dependencies:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   To avoid activating the environment, install with its Python directly:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Configure MongoDB in `.env`. If you do not have a `.env` yet, create one from the example:
   ```powershell
   Copy-Item .env.example .env
   ```
   Set `MONGO_URI` to your MongoDB connection string and `MONGO_DB_NAME` to the database HireHub should use. For local MongoDB, the example values connect to `mongodb://localhost:27017` and use the `hirehub` database. For MongoDB Atlas, put your Atlas connection string in `MONGO_URI` and the intended database name in `MONGO_DB_NAME`.
4. Make sure MongoDB is running or reachable, then start the app:
   ```powershell
   python run.py
   ```
   If you skipped activation, use:
   ```powershell
   .\.venv\Scripts\python.exe run.py
   ```
5. Open `http://localhost:5000`.

The app loads `.env` from the project root, regardless of the directory from which it is started. `MONGO_REQUIRED=true` makes startup fail clearly if the configured MongoDB database is unreachable, preventing the app from appearing to work while saving data only in temporary memory. Set it to `false` only for isolated tests or temporary local experimentation.

All users, jobs, applications, interviews, notifications, and audit entries are persisted in the configured MongoDB database (`hirehub` by default). Uploaded resume files are stored in the configured `UPLOAD_FOLDER`; the associated filename and candidate profile are stored in MongoDB.

Create the recommended MongoDB indexes after configuring `.env`:
```powershell
.\.venv\Scripts\python.exe scripts\create_indexes.py
```
The indexes enforce unique account emails and one application per candidate/job pair, and support recruiter, search, notification, and audit queries.

## Default admin account

The default admin account is created automatically when the app starts, if it does not already exist:
- Email: admin@hirehub.local
- Password: admin123

You can set `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` in `.env` before the first start to use different credentials. Change the default password before deploying anywhere beyond local development. Admin accounts cannot be created through public registration.
