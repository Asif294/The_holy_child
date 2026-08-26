<div align="center">

# SmartSchool

**School Management System for The Holy Child Pre-Cadet & High School**
দি হলি চাইল্ড প্রি-ক্যাডেট এন্ড হাই স্কুল · Longorpara, Sribordi, Sherpur
*Play Group to Class 10 · Established 2006*

Django REST Framework · PostgreSQL · JWT · React · Vite · Tailwind CSS

</div>

---

## What this is

A full-stack school platform built around **dynamic role-based access control**.
An administrator invents a role, ticks the permissions it carries, assigns it to
a user — and both the React navigation and the Django API adapt immediately,
with no code change. Nothing branches on a role *name*; every authorisation
decision asks one question: *does this user hold permission code X?*

In front of it sits the school's **own public website** — hero slider, about,
teachers, administration and results — open to every visitor, with every word
and image on it editable from the dashboard.

```
Admin creates Role → ticks permissions → assigns Role to User
        ↓
React hides navigation the user cannot reach   (convenience)
Django rejects requests the user cannot make   (security)
```

---

## Quick start

```bash
# Backend — http://127.0.0.1:8000
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                     # fill in SECRET_KEY, database, admin credentials
python manage.py migrate
python manage.py seed_initial_data       # permissions, roles, admin account (add --demo for sample data)
python manage.py runserver
```

```bash
# Frontend — http://localhost:5173
cd frontend
npm install
cp .env.example .env                     # defaults already point at the dev proxy
npm run dev
```

Sign in with the admin credentials from `backend/.env`. The Vite dev server
proxies `/api` and `/media` to Django, so the browser stays on one origin and
CORS never gets in the way locally.

**Database.** PostgreSQL is the target; point `DATABASE_*` in `backend/.env` at
a role and database you have created. For a quick look without provisioning it:

```bash
DATABASE_ENGINE=django.db.backends.sqlite3 DATABASE_NAME=db.sqlite3 python manage.py migrate
```

---

## Docker

Two self-contained stacks under `docker/`, one per environment. Each holds its
own compose file, Dockerfiles, nginx config and `.env`:

```
docker/
├── README.md    the command reference — running, resetting, tests, database, logs
├── dev/         docker-compose.yml · Dockerfile.backend · Dockerfile.frontend · nginx.conf · .env
└── prod/        docker-compose.yml · Dockerfile.backend · Dockerfile.frontend · nginx.conf · .env
```

```bash
# Development — Django autoreloads, Vite hot-reloads, both behind nginx
cd docker/dev
cp .env.example .env          # fill in SECRET_KEY, the database and admin passwords
docker compose up --build     # http://localhost:8080

# Production
cd docker/prod
cp .env.example .env          # then set DOMAIN and your real hostnames
docker compose up -d --build
```

**Development** puts the whole site on **http://localhost:8080** — nginx serves
`/static/` and `/media/` from the shared volumes, forwards `/api/` and
`/admin/` to Django, and passes everything else to the Vite dev server with the
websocket upgrade that hot reloading needs. Both application containers run
against a bind mount, so an edit on the host reloads in the container. The two
published host ports — nginx on **8080** and Postgres on **5434** — are set in
`docker/dev/.env`, so they can move out of the way of anything already running.

**Production** is the same shape with the pieces swapped: gunicorn instead of
`runserver`, and the built React app served by its own nginx instead of Vite.
The outer nginx terminates TLS, redirects HTTP, rate-limits `/api/` and
`/admin/`, and is the only service publishing a port. `DOMAIN` from `.env` is
substituted into `nginx.conf` when the container starts.

> First deploy: the HTTPS block needs certificates that do not exist yet.
> Comment out the `443` server, bring the stack up on HTTP, issue the
> certificates through the `/.well-known/acme-challenge/` location into
> `docker/prod/certbot/`, then uncomment it and restart nginx.

Both stacks migrate, collect static files and seed permissions, roles and the
admin account on every start — all three are idempotent, so a restart is never
a special case. The database, uploads and static files live in named volumes
and survive `docker compose down`; `down -v` destroys them.

```bash
docker compose logs -f backend                     # follow one service
docker compose exec backend python manage.py test  # run the suite in the container
docker compose exec db psql -U holy_user the_holy  # a psql prompt
```

> Running Django on the host against the containerised database instead? Point
> `backend/.env` at it — `DATABASE_HOST=localhost` and `DATABASE_PORT=5434`,
> with the engine, name, user and password from `docker/dev/.env`.

Everything else — resetting a stack, running the tests, dumping the database,
issuing certificates — is in **[`docker/README.md`](docker/README.md)**.

---

## Configuration

Both `.env.example` files document every variable; these are the ones that
matter on a first run.

| `backend/.env` | |
| --- | --- |
| `DJANGO_ENV` · `DEBUG` | `development` / `production`, and `False` in production. |
| `SECRET_KEY` | **Required.** `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `ALLOWED_HOSTS` | Comma-separated. Required in production. |
| `DATABASE_*` | PostgreSQL connection. |
| `JWT_*` | Signing key (defaults to `SECRET_KEY`) and token lifetimes. |
| `CORS_ALLOWED_ORIGINS` · `CSRF_TRUSTED_ORIGINS` | Origins allowed to call the API. |
| `DJANGO_ADMIN_*` · `SCHOOL_*` | Consumed by `seed_initial_data`; school identity for the landing page. |

| `frontend/.env` | |
| --- | --- |
| `VITE_API_BASE_URL` | API base path — `/api/v1` by default. |
| `VITE_PROXY_TARGET` · `VITE_PORT` | Dev proxy target and port. |

> **Never commit `.env`.** `.env.example` is the committed template.

---

## Project structure

```
backend/
├── config/         settings (base · development · production) · urls · middleware
└── apps/
    ├── common/     BaseModel, RBAC permission classes, pagination, error envelope,
    │               CRUD viewsets, OpenAPI fragments
    ├── accounts/   User · Role · Permission · auth · seed command
    ├── principal/  Principal · Notice · ApprovalRequest
    ├── teachers/   Teacher · Designation · Department
    ├── students/   Student · Guardian
    ├── classes/    SchoolClass · Section · AcademicSession
    ├── subjects/   Subject · ClassSubject
    ├── attendance/ StudentAttendance · TeacherAttendance
    ├── fees/       FeeCategory · FeeStructure · Invoice · Payment
    ├── exams/      ExamType · Exam · ExamSchedule · Result
    ├── dashboard/  SchoolEvent · ActivityLog · SchoolProfile
    └── website/    HeroSlide · AboutSection · Achievement · SuccessfulStudent

frontend/src/
├── components/     ui/ (primitives) · common/ (Can · CrudPage · DataTable) ·
│                   landing/ · dashboard/
├── layouts/        DashboardLayout · Sidebar · Topbar · AuthLayout
├── routes/         AppRoutes · ProtectedRoute · PermissionRoute
├── services/       api.js (interceptors) · authService · resource services
├── context/        AuthContext · ToastContext
├── hooks/          useAuth · useApi · usePaginatedList · useToast · …
├── pages/          landing · auth · dashboard · academics · website ·
│                   principal · finance · system
└── utils/          constants · permissions · navigation · formatters
```

Larger backend apps use package-style modules (`models/`, `serializers/`,
`views/`); smaller ones use single files. Both follow the same conventions.

---

## Roles & permissions

```
User ──(FK)──▶ Role ──(M2M)──▶ Permission
```

A user holds one role; the role carries any number of `module.action` codes,
seeded from `apps/accounts/constants.py`:

```
student.*  teacher.*  class.*  subject.*  attendance.*  exam.*  admission.*
fee.*  payment.*  notice.*  content.*  achiever.*  user.*  role.*
result.view|create|update|delete|publish     principal.view|update|approve
report.view|export   permission.view   setting.view|update   dashboard.view
```

Adding a module to `PERMISSION_MODULES` and re-running `seed_initial_data` is
all it takes to extend the surface — the seed is idempotent and never destroys
customised roles. Note that `result.publish` is separate from `result.update`:
a teacher can enter marks without being able to release them.

Seeded roles: **Super Admin** (everything) · **School Admin** (academics,
finance, website) · **Principal** (oversight, approvals, publication) ·
**Teacher** (attendance, marks, their classes) · **Accountant** (fees,
invoices, payments) · **Receptionist** (admissions, directory) · **Student** and
**Parent** (read-only). The first two are system roles and cannot be renamed or
deleted; a role still assigned to users cannot be deleted either.

**Enforcement.** A CRUD viewset declares one line and the action mapping falls
out of it; `permission_map` covers the exceptions:

```python
class StudentViewSet(RBACModelViewSet):
    permission_module = "student"      # list → student.view, create → student.create, …

class ResultViewSet(RBACModelViewSet):
    permission_module = "result"
    permission_map = {"publish": "result.publish"}
```

No token → `401`. Valid token without the code → `403`. React route guards and
`<Can>` are a convenience; Django is the authority, and it is tested as such.

On the frontend the sidebar is data (`src/utils/navigation.js`) where each entry
names a code, never a role — so what a Teacher or an Accountant sees is derived,
not written down anywhere.

---

## The public website

`/` is open to everyone — no token is sent and no section requires a session.
The rule the whole page is built on: **reading is public, writing is a
permission code.** Each model behind the site has an `AllowAny` read-only
endpoint under `/public/` exposing only presentation fields, and a
permission-gated viewset that owns create, update and delete. They never share a
serializer — the public staff directory carries photo, designation, department
and subjects, and no email, phone, national ID or date of birth.

---

## API

| URL | |
| --- | --- |
| `/api/docs/` | Swagger UI — try requests against a live token. |
| `/api/redoc/` | ReDoc reference. |
| `/api/schema/` | Raw OpenAPI 3 document. |

Generated by drf-spectacular; every endpoint documents its body, responses,
auth requirement and permission code. Resources live under `/api/v1/` as plural
nouns.

**Auth** is JWT with refresh rotation and blacklisting:
`auth/login|logout|token/refresh|register|me|change-password`. Login takes one
`identifier` — email, phone number or username — and returns `access`, `refresh`
and the user with their resolved permission codes. Phone matching ignores
formatting and the country code, so `+880 1700-000000` signs in as
`01700000000`. There is no public sign-up: accounts are created by an
administrator, and adding a teacher issues theirs automatically.

**Lists** support `page`, `page_size`, `search`, `ordering` and
`paginated=false`, and return `{success, count, total_pages, current_page,
page_size, next, previous, results}`.

**Errors** are normalised by one handler into a single envelope; field
validation returns `422` with the offending fields, so a form can render inline
messages without parsing anything:

```json
{
  "success": false,
  "message": "email: A user with this email already exists.",
  "code": "VALIDATION_ERROR",
  "errors": { "email": ["A user with this email already exists."] }
}
```

`400 BAD_REQUEST` · `401 AUTHENTICATION_FAILED` · `403 PERMISSION_DENIED` ·
`404 NOT_FOUND` · `422 VALIDATION_ERROR` · `500 INTERNAL_SERVER_ERROR`.

`src/services/api.js` is the single Axios instance: it attaches the token,
refreshes once on a `401` and retries the original request (concurrent 401s
share one refresh), clears state and redirects to login if that fails, and turns
every failure into an `ApiError` carrying `message`, `code`, `status` and
per-field `errors`.

---

## Testing

```bash
cd backend  && python manage.py test
cd backend  && python manage.py spectacular --file schema.yml   # 0 warnings, 0 errors

cd frontend && npm run lint     # oxlint
cd frontend && npm run build
cd frontend && npm run smoke    # renders every screen through Vite's SSR pipeline
```

The backend suite covers the security contract end to end: registration cannot
self-assign a role, unauthenticated is `401` and unauthorised is `403`, granting
a code unlocks an endpoint immediately and revoking it locks it again, a
deactivated role holds nothing, and system or in-use roles cannot be deleted.
`npm run smoke` fails on any runtime render error — a guard a clean build alone
does not give you.

---

## Production

Set `DJANGO_ENV=production` and `DEBUG=False`; `config/settings/production.py`
then requires `ALLOWED_HOSTS`, forces HTTPS with HSTS, secures the session and
CSRF cookies, sets `X-Frame-Options: DENY` and `nosniff`, and serves static
files through WhiteNoise.

```bash
cd backend
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_initial_data          # idempotent — safe on every deploy
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

cd frontend && npm run build                # serve dist/, proxying /api and /media to Django
```

Already in place: JWT rotation and blacklisting, Django's password hashing and
policy, serializer-level validation on every write, explicit CORS and CSRF
origin lists, soft deletes, and `created_by` / `updated_by` audit columns on
every model.

Before going live: rotate `SECRET_KEY` and `JWT_SIGNING_KEY`, change the seeded
admin password, restrict `CORS_ALLOWED_ORIGINS` to your real frontend origin,
and put the API behind TLS.

---

<div align="center">

**The Holy Child Pre-Cadet & High School** · Longorpara, Sribordi, Sherpur, Bangladesh
Developed by **Asifur Rahman** · WhatsApp [01885430525](https://wa.me/8801885430525)

</div>
