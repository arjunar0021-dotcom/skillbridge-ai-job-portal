# skillBridge: Job Portal (Django)

A role-based job portal where **job seekers** build profiles and apply for jobs, **employers** post jobs and manage applicants and interviews, and an **admin** manages the whole platform.

Built for the Entri Django final project (authentication, role-based access, CRUD, responsive UI, database, documentation).

## Features

| Area | What it does |
|---|---|
| Authentication | Sign up, login, logout (Django auth, custom `User` with a `role` field) |
| Roles | **Admin** (full control), **Employer** (staff/manager: own jobs and applicants), **Job Seeker** (user) |
| CRUD | Jobs (employer create/read/update/delete), seeker profile + resume, applications (apply/withdraw), interviews, users (admin) |
| Dashboards / reports | Role-specific dashboards with Chart.js charts, CSV export of applications |
| Search | Keyword (title, description, company, skill), location, job-type filters, pagination; applicant filters (status, skill, experience) |
| AI matching | Skill + experience match score per job, ranked recommendations, skill-gap analysis |
| REST API | `/api/jobs/`, `/api/applications/`, `/api/recommended/` (Django REST Framework) |
| Email | Notifications for new applications, status changes, interviews (printed to the terminal by default) |
| File uploads | Resumes (pdf/doc/docx, max 2 MB), profile photos and company logos |
| Saved jobs | Seekers can bookmark jobs and revisit them on the Saved jobs page |
| UI | Workspace layout (sidebar, breadcrumbs, split-view job search with filters, profile page), Bootstrap 5 + custom skillBridge theme |

## Roles and permissions

| Action | Seeker | Employer | Admin |
|---|---|---|---|
| Browse / search jobs | yes | yes | yes |
| Apply, withdraw, save jobs, see recommendations | yes | | |
| Create jobs | | yes | |
| Edit / delete jobs, view applicants, schedule interviews | | own jobs only | all |
| Manage users | | | yes |

Access is enforced in the views (`@role_required`) and in the queries (`jobs/permissions.py`), so an employer cannot reach another employer's data even by guessing a URL.

## Project structure

```
jobportal/
├── manage.py
├── requirements.txt
├── jobportal/        settings.py, urls.py, wsgi.py
├── accounts/         User (roles), Skill, SeekerProfile, Company, auth views, user management
├── jobs/             Job, Application, Interview, matching, REST API, seed command
├── dashboard/        landing page, role dashboards, CSV report
├── templates/
└── static/
```

## Setup

```bash
# 1. create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell / CMD)
source venv/bin/activate         # macOS / Linux

# 2. install requirements
pip install -r requirements.txt

# 3. create the database tables
python manage.py makemigrations accounts jobs
python manage.py migrate

# 4. load demo users, companies and jobs
python manage.py seed_demo

# 5. run
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo logins (created by `seed_demo`)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Employer | `employer1` | `Employer@123` |
| Employer | `employer2` | `Employer@123` |
| Job seeker | `seeker1` | `Seeker@123` |
| Job seeker | `seeker2` | `Seeker@123` |

Django admin panel: http://127.0.0.1:8000/admin/ (log in as `admin`).

To create your own admin instead: `python manage.py createsuperuser`.

## REST API

| Endpoint | Access | Description |
|---|---|---|
| `GET /api/jobs/?search=django` | public | Open jobs |
| `GET /api/jobs/<id>/` | public | One job |
| `GET /api/applications/` | logged in | Seeker: own; employer: applicants to own jobs; admin: all |
| `GET /api/recommended/` | seeker | Matches with score, matched and missing skills |

## Deployment (Render.com)

1. Push to GitHub.
2. New **Web Service** on Render, connect the repo.
3. Build command: `bash build.sh`  |  Start command: `gunicorn jobportal.wsgi`
4. Environment variables: `DEBUG=False`, `SECRET_KEY=<long random string>`.

SQLite and uploaded files reset on each deploy on Render's free tier; `seed_demo` runs on every build so the demo logins always exist. Use PostgreSQL and cloud storage for real production use.
