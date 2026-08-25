<div align="center">

# SmartSchool

**School Management System for The Holy Child Pre-Cadet & High School**
দি হলি চাইল্ড প্রি-ক্যাডেট এন্ড হাই স্কুল · Longorpara, Sribordi, Sherpur
*Play Group to Class 10 · Established 2006*

Django REST Framework · PostgreSQL · JWT · React · Vite · Tailwind CSS

</div>

---

## What this is

A production-shaped full-stack school management platform. The centrepiece is a
**dynamic role-based access control system**: an administrator invents a role,
ticks the permissions it carries, assigns it to a user — and both the React
navigation and the Django API adapt immediately, with no code change.

Nothing in the codebase branches on a role *name*. Every authorisation decision
asks one question: *does this user hold permission code X?*

In front of it sits the school's **own public website** — hero slider, about,
teachers, administration and results — open to every visitor, with every word
and image on it editable from the dashboard by whoever holds the code for it.

```
Admin creates Role  →  selects permissions  →  assigns Role to User
        ↓
User inherits the permission codes
        ↓
React hides navigation the user cannot reach   (convenience)
Django rejects requests the user cannot make   (security)
```

---

## Table of contents

- [Quick start](#quick-start)
- [Environment variables](#environment-variables)
- [Database setup](#database-setup)
- [Project structure](#project-structure)
- [The public website](#the-public-website)
- [Authentication](#authentication)
- [The role & permission system](#the-role--permission-system)
- [API reference](#api-reference)
- [Error handling](#error-handling)
- [Frontend architecture](#frontend-architecture)
- [Testing & verification](#testing--verification)
- [Production notes](#production-notes)

---

## Quick start

### Backend

```bash
cd backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then fill in SECRET_KEY, database and admin credentials

python manage.py migrate
python manage.py seed_initial_data      # permissions, roles, admin account
python manage.py seed_initial_data --demo   # ...plus sample school data
python manage.py runserver
```

The API is now on **http://127.0.0.1:8000** and Swagger on
**http://127.0.0.1:8000/api/docs/**.

### Frontend

```bash
cd frontend

npm install
cp .env.example .env          # defaults already point at the dev proxy
npm run dev
```

The app is now on **http://localhost:5173**. Sign in with the admin credentials
you put in `backend/.env`.

> The Vite dev server proxies `/api` and `/media` to `http://127.0.0.1:8000`, so
> the browser stays on a single origin and CORS never gets in your way locally.

---

## Environment variables

### `backend/.env`

| Variable | Purpose |
| --- | --- |
| `DJANGO_ENV` | `development` (default) or `production` — selects the settings module. |
| `DEBUG` | `True` locally. Always `False` in production. |
| `SECRET_KEY` | **Required.** Generate with the command below. |
| `ALLOWED_HOSTS` | Comma-separated hostnames. Required in production. |
| `DATABASE_ENGINE` | `django.db.backends.postgresql` (default). |
| `DATABASE_NAME` / `_USER` / `_PASSWORD` / `_HOST` / `_PORT` | PostgreSQL connection. |
| `JWT_SIGNING_KEY` | Defaults to `SECRET_KEY` when left blank. |
| `JWT_ACCESS_MINUTES` | Access-token lifetime (default 60). |
| `JWT_REFRESH_DAYS` | Refresh-token lifetime (default 7). |
| `CORS_ALLOWED_ORIGINS` | Origins allowed to call the API. |
| `CSRF_TRUSTED_ORIGINS` | Origins trusted for CSRF. |
| `TIME_ZONE` | `Asia/Dhaka` by default. |
| `DJANGO_ADMIN_EMAIL` / `_PASSWORD` / `_NAME` | Consumed by `seed_initial_data`. |
| `SCHOOL_*` | School identity served by `/api/v1/school/info/` and shown on the landing page. |

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

> **Never commit `.env`.** `.env.example` is the committed template; it contains
> no real credentials.

### `frontend/.env`

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | API base path. `/api/v1` by default, which routes through the dev proxy. |
| `VITE_PROXY_TARGET` | Where the dev proxy forwards `/api` and `/media`. |
| `VITE_PORT` | Dev server port (5173). |

---

## Database setup

PostgreSQL is the target database. Create a role and database, then point
`backend/.env` at them:

```bash
sudo -u postgres psql <<'SQL'
CREATE ROLE holychild WITH LOGIN PASSWORD 'change-me';
CREATE DATABASE holychild OWNER holychild;
ALTER ROLE holychild SET client_encoding TO 'utf8';
ALTER ROLE holychild SET default_transaction_isolation TO 'read committed';
ALTER ROLE holychild SET timezone TO 'Asia/Dhaka';
SQL
```

```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=holychild
DATABASE_USER=holychild
DATABASE_PASSWORD=change-me
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

> If your PostgreSQL listens on a non-default port (5433 is common when two
> versions are installed), set `DATABASE_PORT` accordingly — check with
> `pg_lsclusters` or `pg_isready`.

**SQLite escape hatch.** For a quick look at the project without provisioning
PostgreSQL, override the engine on the command line — the settings understand it
and nothing else changes:

```bash
DATABASE_ENGINE=django.db.backends.sqlite3 DATABASE_NAME=db.sqlite3 python manage.py migrate
```

---

## Project structure

```
TheHollyChild/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config/
│   │   ├── settings/           base.py · development.py · production.py
│   │   ├── middleware.py       request-scoped current user (audit columns)
│   │   ├── urls.py             /api/v1/… + /api/docs/ + /api/redoc/
│   │   ├── wsgi.py · asgi.py
│   └── apps/
│       ├── common/             BaseModel, RBAC permission classes, pagination,
│       │                       error envelope, CRUD viewsets, OpenAPI fragments
│       ├── accounts/           User · Role · Permission · auth · seed command
│       ├── principal/          Principal · Notice · ApprovalRequest
│       ├── teachers/           Teacher · Designation · Department
│       ├── students/           Student · Guardian
│       ├── classes/            SchoolClass · Section · AcademicSession
│       ├── subjects/           Subject · ClassSubject
│       ├── attendance/         StudentAttendance · TeacherAttendance
│       ├── fees/               FeeCategory · FeeStructure · Invoice · Payment
│       ├── exams/              ExamType · Exam · ExamSchedule · Result
│       ├── dashboard/          SchoolEvent · ActivityLog · SchoolProfile
│       └── website/            HeroSlide · AboutSection · Achievement ·
│                               SuccessfulStudent — the public landing page
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── scripts/render-smoke.mjs    SSR render check (`npm run smoke`)
    └── src/
        ├── components/
        │   ├── ui/             Button · Card · Input · Modal · Table · Badge · …
        │   ├── common/         Logo · Can · DataTable · CrudPage · ErrorBoundary
        │   ├── landing/        Navbar · HeroSlider · AboutSchool ·
        │                       Administration · TeachersSection ·
        │                       SuccessfulStudents · Footer
        │   └── dashboard/      StatCard · Charts
        ├── layouts/            DashboardLayout · Sidebar · Topbar · AuthLayout
        ├── routes/             AppRoutes · ProtectedRoute · PermissionRoute
        ├── services/           api.js (interceptors) · authService · resource services
        ├── context/            AuthContext · ToastContext
        ├── hooks/              useAuth · useApi · usePaginatedList · useToast · …
        ├── pages/              landing · auth · dashboard · academics ·
        │                       website · principal · finance · system
        └── utils/              constants · permissions · navigation · formatters
```

The larger backend apps use package-style modules
(`models/`, `serializers/`, `views/` directories with `__init__.py` re-exports);
the smaller ones use single files. Both follow the same conventions.

---

## The public website

`/` is the school's own website, and it is open to everyone — no token is sent
and no section requires a session. Every word and image on it is editable from
the dashboard, so a rename, a new banner or this year's results never need a
deploy.

The rule the whole page is built on: **reading is public, writing is a
permission code.** Each model behind the site has two endpoints — an
`AllowAny` read-only one under `/public/` exposing only presentation fields,
and a permission-gated viewset that owns create, update and delete. They never
share a serializer; the public shape is a deliberate subset. The staff
directory is the clearest case: the public one carries photo, designation,
department and subjects, and no email, phone, national ID or date of birth.

### The sections

| Section | Reads | Managed at | Code |
| --- | --- | --- | --- |
| Hero slider | `GET /api/v1/public/hero-slides/` | Public Website → Hero slider | `content.*` |
| About the school | `GET /api/v1/public/about/` | Public Website → About the school | `content.*` |
| Achievements | (part of `/public/about/`) | Public Website → Achievements | `content.*` |
| Teachers | `GET /api/v1/public/teachers/` | Academics → Teachers | `teacher.*` |
| Administration | `GET /api/v1/public/administration/` | Principal's Office → Administration | `principal.*` |
| Successful students | `GET /api/v1/public/successful-students/` | Public Website → Successful students | `achiever.*` |

Two supporting endpoints: `GET /api/v1/public/successful-students/years/`
returns the distinct academic years, newest first, which is what fills the year
filter; and `GET /api/v1/school/info/` returns the school's identity and
headline counts.

### Hero slider

Slides rotate every six seconds and can be stepped through with the arrows,
the dots or the arrow keys. Rotation pauses on hover, on keyboard focus and
whenever the tab is hidden, and stops for good once a visitor uses the arrows —
someone reading a slide should not have it pulled away from them. With no
slides uploaded the hero falls back to a built-in gradient banner carrying the
school's name and figures, so a fresh install still looks finished.

### Administration

`Principal.office` distinguishes the two seats, `principal` and
`vice_principal`. One record per office is `is_current` at a time, so recording
a vice principal does not stand the principal down. Both are governed by the
same `principal.*` codes and administered on one screen.

### Successful students

Deliberately independent of the student register: a pupil who left in 2019 still
belongs on the honour board, and a name on it need not have an enrolment record
behind it. `student` links the two when the pupil is still on the roll, and is
optional precisely so it can be left empty when they are not. Visitors filter
by academic year, which re-queries rather than filtering in memory.

### Uploading files

Any endpoint that accepts a file accepts `multipart/form-data`, and every
serializer behind one extends `apps.common.serializers.MultipartModelSerializer`
rather than DRF's `ModelSerializer`. The difference is one field class: DRF
reads an *absent* boolean in an HTML form as `False`, which is right for an
unticked checkbox and wrong for an API — without it, creating a record with a
photograph attached would file it away deactivated. See
`FormSafeBooleanField` for the detail, and `apps.website.tests` for the
regression tests.

---

## Authentication

JWT via `djangorestframework-simplejwt`, with refresh-token rotation and
blacklisting.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | Self-registration (API only — no public sign-up page). |
| `POST` | `/api/v1/auth/login/` | Email, phone or username + password. Returns `access`, `refresh` and the user with permission codes. |
| `POST` | `/api/v1/auth/token/refresh/` | Rotates the token pair. |
| `POST` | `/api/v1/auth/logout/` | Blacklists the refresh token. |
| `GET` | `/api/v1/auth/me/` | The signed-in user. |
| `PATCH` | `/api/v1/auth/me/` | Update your own profile (never your own role). |
| `POST` | `/api/v1/auth/change-password/` | Change your own password. |

Login response:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 4,
    "name": "Nasrin Akter",
    "email": "teacher@holychildschool.edu.bd",
    "role": "Teacher",
    "permissions": ["student.view", "attendance.view", "attendance.create", "class.view"]
  }
}
```

Send the access token on every protected request:

```
Authorization: Bearer <access_token>
```

### Signing in with a phone number

The login form has one identity box. `identifier` accepts an **email address, a
phone number or a username**, and
`apps.accounts.backends.EmailPhoneOrUsernameBackend` works out which it is.
`email`, `phone` and `username` are accepted as aliases for `identifier`, so
older clients keep working.

```json
{ "identifier": "01700000000", "password": "••••••••" }
{ "identifier": "teacher@holychildschool.edu.bd", "password": "••••••••" }
```

Phone matching ignores formatting **and the country code** — an account filed
as `+880 1700-000000` signs in as `01700000000`. Identity is the last ten
digits (`apps.accounts.utils.phone_key`); the stored string keeps whatever the
office typed. Because the number is a credential it must point at exactly one
account, so `User.phone` carries a conditional unique constraint (blank stays
freely repeatable) and the serializers reject a second account claiming the
same number written differently.

Anyone signed in can change their own password from **My profile**
(`POST /api/v1/auth/change-password/`), which re-checks the current password
and validates the new one against Django's full password policy.

### Where sign-in leads

Signing in lands on the **school's public home page**, not the dashboard. The
header's *Admin* button becomes *Dashboard*, and from there each role reaches
whatever its permission codes allow. The public site is the front door for
everyone; the dashboard is one click further in.

**There is no public sign-up.** The landing page carries a single *Admin*
button; `/register` redirects to `/login`. Accounts are created by an
administrator through `POST /api/v1/users/`, which itself requires
`user.create`.

The `POST /api/v1/auth/register/` endpoint remains for programmatic use and is
deliberately restricted: the role is assigned by the server (the default
self-registration role, `Student`), and a `role`, `is_staff` or `is_superuser`
field in the request body is ignored — there is no path by which a registrant
can promote themselves.

Registration validates: unique email, matching password confirmation, Django's
full password policy, phone format, and a minimum-length full name.

---

## The role & permission system

### The model

```
User  ──(FK)──▶  Role  ──(M2M)──▶  Permission
```

A user holds exactly one role. The role carries any number of permission codes.
`user.get_permission_codes()` resolves the set; superusers implicitly hold
everything.

### Permission codes

Codes are `module.action` — 62 of them, seeded from
`apps/accounts/constants.py`:

```
student.view    student.create    student.update    student.delete
teacher.view    teacher.create    teacher.update    teacher.delete
class.*  subject.*  attendance.*  exam.*  fee.*  payment.*  admission.*  notice.*
result.view  result.create  result.update  result.delete  result.publish
principal.view  principal.update  principal.approve
content.*       website content — hero slider, about copy, achievements
achiever.*      the public successful-students honour board
report.view  report.export
user.*  role.*  permission.view  setting.view  setting.update  dashboard.view
```

Adding a module to `PERMISSION_MODULES` and re-running `seed_initial_data` is all
it takes to extend the surface — the seed is idempotent and never destroys
customised roles.

Note that `result.publish` is separate from `result.update`: a teacher can enter
marks without being able to release them.

### Seeded roles

| Role | Slug | Notes |
| --- | --- | --- |
| Super Admin | `super-admin` | Every permission. System role — cannot be renamed or deleted. |
| School Admin | `school-admin` | Full academic and finance operations, plus the public website. System role. |
| Principal | `principal` | Oversight, approvals, notices, result publication, public website. |
| Teacher | `teacher` | Attendance, marks, and read access to their classes. |
| Accountant | `accountant` | Fees, invoices, payments, financial reports. |
| Receptionist | `receptionist` | Admissions intake and the student directory. |
| Student | `student` | Read-only view of their own academic information. |
| Parent | `parent` | Read-only view of their children's records. |

### Enforcement on the API

`apps/common/permissions.py` provides the reusable classes:

```python
HasPermission          # view.required_permission — a single code
HasAllPermissions      # view.required_permissions — every code
HasAnyPermission       # view.required_permissions — at least one
HasActionPermission    # resolves the code from the current action
permission_required()  # factory for one-off views
IsSuperAdmin           # reserved for system-level operations
```

In practice a CRUD viewset declares one line:

```python
class StudentViewSet(RBACModelViewSet):
    permission_module = "student"
    # list/retrieve → student.view   create → student.create
    # update/partial_update → student.update   destroy → student.delete
```

and overrides individual actions where the mapping differs:

```python
class ResultViewSet(RBACModelViewSet):
    permission_module = "result"
    permission_map = {"publish": "result.publish"}
```

**The contract:**

| Situation | Response |
| --- | --- |
| No token, or an invalid one | `401 AUTHENTICATION_FAILED` |
| Valid token, missing the required code | `403 PERMISSION_DENIED` |
| Valid token, holds the code | `200` / `201` |

React route protection is a convenience only. Django is the authority, and it is
tested as such — see [Testing & verification](#testing--verification).

### Managing roles

```http
GET    /api/v1/roles/
POST   /api/v1/roles/
GET    /api/v1/roles/{id}/
PUT    /api/v1/roles/{id}/
PATCH  /api/v1/roles/{id}/
DELETE /api/v1/roles/{id}/
POST   /api/v1/roles/{id}/permissions/    # replace the permission set
```

```jsonc
// POST /api/v1/roles/
{
  "name": "Teacher",
  "description": "Classroom staff.",
  "permissions": ["student.view", "attendance.view", "attendance.create", "class.view"]
}
```

The response echoes the codes back as `permissions`, plus expanded objects as
`permission_details` for the permission-matrix UI.

Guard rails: system roles cannot be renamed or deleted; the Super Admin role
always holds every permission; a role still assigned to users cannot be deleted.

---

## API reference

Interactive documentation, generated by **drf-spectacular**:

| URL | What it is |
| --- | --- |
| `/api/docs/` | Swagger UI — try requests against a live token. |
| `/api/redoc/` | ReDoc — a readable reference. |
| `/api/schema/` | The raw OpenAPI 3 document. |

Every endpoint documents its request body, response schema, authentication
requirement, error responses and permission code, grouped under tags:
*Authentication · Users · Roles · Permissions · Dashboard · Principal · Teachers ·
Students · Classes · Subjects · Attendance · Fees · Exams · Website · Public site*.

### Endpoint map

All resources live under `/api/v1/` and use plural nouns.

| Area | Endpoints |
| --- | --- |
| Access control | `users/` · `users/{id}/assign-role/` · `roles/` · `roles/{id}/permissions/` · `permissions/` · `permissions/grouped/` |
| Principal's office | `principals/` · `principals/current/` · `principals/dashboard/` · `notices/` · `notices/{id}/publish/` · `approval-requests/` · `approval-requests/{id}/decide/` · `approval-requests/mine/` |
| Teachers | `teachers/` · `teachers/statistics/` · `teachers/me/` · `designations/` · `departments/` |
| Students | `students/` · `students/statistics/` · `guardians/` |
| Classes | `classes/` · `sections/` · `academic-sessions/` |
| Subjects | `subjects/` · `class-subjects/` |
| Attendance | `attendance/` · `attendance/register/` · `attendance/bulk/` · `attendance/summary/` · `teacher-attendance/` |
| Fees | `fee-categories/` · `fee-structures/` · `invoices/` · `invoices/statistics/` · `invoices/outstanding/` · `payments/` · `payments/recent/` |
| Exams | `exams/` · `exams/upcoming/` · `exam-types/` · `exam-schedules/` · `results/` · `results/publish/` · `results/student-summary/` |
| Dashboard | `dashboard/overview/` · `dashboard/summary/` · `dashboard/attendance-trend/` · `dashboard/enrollment/` · `dashboard/fee-trend/` · `dashboard/activities/` · `events/` |
| Website content | `hero-slides/` · `website/about/` · `achievements/` · `successful-students/` |
| Public (no auth) | `school/info/` · `public/hero-slides/` · `public/about/` · `public/teachers/` · `public/administration/` · `public/principal/` · `public/successful-students/` · `public/successful-students/years/` |

### Two endpoints worth knowing

**`GET /api/v1/dashboard/overview/`** returns the entire dashboard payload —
summary cards, attendance trend, enrolment breakdown, fee trend, upcoming events
and exams, recent payments, notices and activity — in one request, saving the
dashboard eight round trips on load.

**`POST /api/v1/attendance/bulk/`** submits a whole section's register in one
call and *upserts*, so re-submitting the same date corrects the existing marks
rather than failing on the uniqueness constraint:

```json
{
  "date": "2026-08-25",
  "section": 3,
  "entries": [
    { "student": 11, "status": "present" },
    { "student": 12, "status": "absent", "remarks": "Informed by guardian" },
    { "student": 13, "status": "late", "check_in_time": "09:20:00" }
  ]
}
```

### List conventions

Every list endpoint supports `page`, `page_size`, `search`, `ordering`, and
`paginated=false` (returns the full array — used by the UI's dropdowns).

```jsonc
{
  "success": true,
  "count": 381,
  "total_pages": 20,
  "current_page": 1,
  "page_size": 20,
  "next": "http://localhost:8000/api/v1/students/?page=2",
  "previous": null,
  "results": [ /* … */ ]
}
```

---

## Error handling

One exception handler (`apps/common/exception_handler.py`) normalises every
error into a single envelope:

```json
{
  "success": false,
  "message": "You do not have permission to perform this action.",
  "code": "PERMISSION_DENIED",
  "errors": {}
}
```

Field-level validation returns **422** with the offending fields, so the frontend
can branch cleanly between "malformed request" and "fix these inputs":

```json
{
  "success": false,
  "message": "email: A user with this email already exists.",
  "code": "VALIDATION_ERROR",
  "errors": { "email": ["A user with this email already exists."] }
}
```

| Status | Code |
| --- | --- |
| 400 | `BAD_REQUEST` |
| 401 | `AUTHENTICATION_FAILED` |
| 403 | `PERMISSION_DENIED` |
| 404 | `NOT_FOUND` |
| 422 | `VALIDATION_ERROR` |
| 500 | `INTERNAL_SERVER_ERROR` |

### On the frontend

`src/services/api.js` is the single Axios instance. Its interceptors:

- attach the access token to every request;
- on a `401`, refresh the token once and **retry the original request** —
  concurrent 401s share one refresh rather than stampeding the endpoint;
- if the refresh fails, clear the tokens, tear down auth state and redirect to
  login with a "session expired" notice;
- convert every failure into an `ApiError` carrying `message`, `code`, `status`
  and per-field `errors`, so forms can render inline messages without parsing
  anything.

```
Access token expires
        ↓
POST /auth/token/refresh/  ──▶  new access token  ──▶  original request retried
        ↓ (fails)
tokens cleared  ──▶  auth state reset  ──▶  redirect to /login
```

---

## Frontend architecture

### Auth context

```jsx
const {
  user,
  isAuthenticated,
  permissions,
  login,
  logout,
  register,
  refreshUser,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
} = useAuth()

hasPermission('student.view')   // → boolean
```

The cached user is shown immediately on boot so the shell does not flash, then
`/auth/me/` re-validates it. The server's answer always wins.

### Route protection

`/` is deliberately outside both guards — the school's website is public, and
signing in adds the management surface rather than unlocking the site.
Everything under `/app` is wrapped twice: `ProtectedRoute` for authentication
and `PermissionRoute` for the code the screen needs.

```jsx
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

<PermissionRoute permission="student.view">
  <StudentList />
</PermissionRoute>

<PermissionRoute anyOf={['principal.view', 'principal.approve']}>
  <Approvals />
</PermissionRoute>
```

A user without the code lands on a proper **403 Forbidden** page that names the
role they hold and points them at an administrator.

### Permission-aware navigation

The sidebar is data (`src/utils/navigation.js`). Each entry names a permission
code, never a role:

```js
{ label: 'Students', to: '/app/students', icon: GraduationCap, permission: 'student.view' }
```

`visibleNavigation()` filters the entries a user cannot reach, then drops any
section left empty. A Teacher sees *Dashboard · Students · Classes · Subjects ·
Attendance · Exams · Results*; an Accountant sees *Dashboard · Fees · Invoices ·
Payments · Reports*; a School Admin additionally sees the *Public Website*
section. Nobody wrote any of those lists — they all fall out of the codes.

Inside a page, `<Can>` hides individual controls:

```jsx
<Can permission="student.create">
  <Button>Admit student</Button>
</Can>
```

### Design system

Brand colours are taken from the school signboard: deep institutional blue
(`brand`), the red banner (`crimson`) and gold lettering (`gold`). They are
defined once as Tailwind theme tokens in `src/index.css`.

The UI is built from a small primitive set — `Button`, `Card`, `Input`,
`Select`, `Textarea`, `Modal`, `Table`, `Badge`, `Avatar`, `Alert`, `Pagination`,
`EmptyState`, `Spinner` — with consistent typography, spacing, radii and focus
rings throughout. Motion is limited to transitions, and `prefers-reduced-motion`
is respected.

`CrudPage` renders a complete list-plus-modal screen from a column and field
declaration; the reference-data modules (subjects, classes, fee heads, sessions,
notices) use it, while screens with real behaviour of their own — attendance,
roles, results, students — are written by hand.

---

## Testing & verification

### Backend

```bash
cd backend
python manage.py test
```

28 tests covering the security contract end to end:

- registration assigns the server-controlled default role, and **ignores** a
  self-assigned `role` / `is_superuser` / `is_staff` in the request body;
- validation rejects mismatched confirmations, duplicate emails and weak
  passwords with `422` and per-field errors;
- login returns tokens plus the resolved permission list; bad credentials give
  `401`;
- logout blacklists the refresh token, and reusing it afterwards gives `401`;
- unauthenticated requests give **401**; authenticated-but-unauthorised requests
  give **403**;
- granting a code to a role unlocks the endpoint immediately, and revoking it
  locks it again;
- a user with no role, or with a deactivated role, holds no permissions;
- a superuser bypasses every check;
- the full dynamic-role flow: create a role → create a user against it → confirm
  the user's access matches the role exactly → edit the role → confirm access
  follows;
- system roles and in-use roles cannot be deleted; the permission catalogue is
  read-only.

Verify the OpenAPI document generates cleanly:

```bash
python manage.py spectacular --file schema.yml   # 195 operations, 0 warnings, 0 errors
```

### Frontend

```bash
cd frontend
npm run lint     # oxlint
npm run build    # production bundle
npm run smoke    # renders all 27 screens through Vite's SSR pipeline
```

`npm run smoke` executes every screen with its providers and fails on any
runtime render error — a fast, dependency-free guard that a clean build alone
does not give you.

---

## Production notes

Set `DJANGO_ENV=production` and `DEBUG=False`. `config/settings/production.py`
then enforces:

- `ALLOWED_HOSTS` must be set (the app refuses to start otherwise);
- HTTPS redirect, HSTS with preload, and `SECURE_PROXY_SSL_HEADER`;
- secure, HTTP-only session cookies and secure CSRF cookies;
- `X-Frame-Options: DENY`, `nosniff`, and a same-origin referrer policy;
- WhiteNoise with compressed, manifest-hashed static files.

```bash
cd backend
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_initial_data          # idempotent — safe on every deploy
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

```bash
cd frontend
npm run build    # serve dist/ from your web server, proxying /api and /media to Django
```

Security posture already in place: JWT with rotation and blacklisting, Argon2-
grade password hashing via Django's hashers, password-policy validation,
serializer-level input validation on every write, explicit CORS and CSRF origin
lists, soft deletes so records are never silently destroyed, audit columns
(`created_by` / `updated_by`) on every model, and permission enforcement on the
API rather than in the client.

Before going live: rotate `SECRET_KEY` and `JWT_SIGNING_KEY`, change the seeded
admin password, restrict `CORS_ALLOWED_ORIGINS` to your real frontend origin, and
put the API behind TLS.

---

<div align="center">

**The Holy Child Pre-Cadet & High School** · Longorpara, Sribordi, Sherpur, Bangladesh

</div>
