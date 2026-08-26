# Docker

Two self-contained stacks. Everything a stack needs — compose file,
Dockerfiles, nginx config, environment — lives in its own folder:

```
docker/
├── dev/     PostgreSQL · Django (runserver) · Vite dev server · nginx      → http://localhost
└── prod/    PostgreSQL · Django (gunicorn)  · built React app  · nginx     → https://$DOMAIN
```

Each stack declares its own compose project name — `holy-child-dev` and
`holy-child-prod` — so its containers, volumes and network never collide with
another project's, and `down` can only ever remove its own.

**Every command below runs from inside `docker/dev` or `docker/prod`.** That is
what makes compose pick up the right `.env`, the right containers and the right
volumes. Run them from the repo root and you will get the wrong stack, or none.

```bash
cd docker/dev     # …or docker/prod
```

---

## First run

```bash
cp .env.example .env      # fill in SECRET_KEY, DATABASE_PASSWORD, DJANGO_ADMIN_PASSWORD
docker compose up --build
```

The backend container migrates, collects static files and seeds permissions,
roles and the admin account before it starts serving. All three are idempotent,
so this happens on every start and never needs to be repeated by hand.

In production also set `DOMAIN` and `ALLOWED_HOSTS` before the first build, and
read the certificate note at the bottom of this file.

---

## Running

| | |
| --- | --- |
| `docker compose up` | start in the foreground, logs on screen |
| `docker compose up -d` | start detached |
| `docker compose up -d --build` | rebuild images first — after a dependency change |
| `docker compose stop` | stop the containers, keep them |
| `docker compose start` | start them again |
| `docker compose restart backend` | restart one service |
| `docker compose down` | stop and remove containers; **volumes survive** |
| `docker compose ps` | what is running, and on which ports |

Changed a `.env` value, or an nginx config? Those are read at container start,
so `docker compose up -d` (or `restart nginx`) is enough — no rebuild. Changed
`requirements.txt` or `package.json`? That needs `--build`.

---

## Resetting

From gentlest to most destructive.

```bash
# Restart one misbehaving service
docker compose restart backend

# Rebuild images and recreate the containers — keeps the database
docker compose up -d --build --force-recreate

# Rebuild from scratch, ignoring every cached layer
docker compose build --no-cache
docker compose up -d --force-recreate
```

```bash
# FULL RESET — deletes the database, the uploads and the collected static files
docker compose down -v
docker compose up --build
```

`down -v` removes the named volumes, so the next start comes up with an empty
database: migrations run again and the seed recreates the roles and the admin
account. **Every school record, and every uploaded photograph, is gone.** Take a
dump first (see below) if the data matters.

To reset the database *only*, leaving the images and uploads alone:

```bash
docker compose down
docker volume rm holy-child-dev_postgres-data      # holy-child-prod_… in production
docker compose up -d
```

---

## Tests

```bash
# The whole backend suite
docker compose exec backend python manage.py test

# One app, or one test
docker compose exec backend python manage.py test apps.teachers
docker compose exec backend python manage.py test apps.teachers.tests.StaffAccountTests

# Verbose, and stop at the first failure
docker compose exec backend python manage.py test -v 2 --failfast
```

Django builds and destroys its own `test_…` database, so the suite never
touches development data.

The frontend checks:

```bash
docker compose exec frontend npm run lint     # oxlint
docker compose exec frontend npm run build    # production bundle
docker compose exec frontend npm run smoke    # renders every screen
```

With the stack down, `docker compose run --rm backend python manage.py test`
does the same thing in a throwaway container.

---

## Django management

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_initial_data          # permissions, roles, admin
docker compose exec backend python manage.py seed_initial_data --demo   # …plus sample school data
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py spectacular --file schema.yml
```

---

## Database

```bash
# A psql prompt
docker compose exec db psql -U holy_user the_holy

# Dump to a file on the host
docker compose exec -T db pg_dump -U holy_user the_holy > backup.sql

# Restore that dump
docker compose exec -T db psql -U holy_user the_holy < backup.sql
```

In development the database is also on **localhost:5433**, so pgAdmin, DBeaver
or a host-side `psql` can reach it. Production does not publish the port at all
— the backend container is the only thing that can connect.

---

## Logs and shells

```bash
docker compose logs -f                  # everything, following
docker compose logs -f backend          # one service
docker compose logs --tail=100 nginx    # the last hundred lines

docker compose exec backend bash        # a shell in the API container
docker compose exec frontend sh         # …in the frontend container (alpine)
docker compose exec nginx nginx -t      # check the nginx config without restarting
```

---

## Where things are

| | Development | Production |
| --- | --- | --- |
| The site | http://localhost | `https://$DOMAIN` |
| API docs | http://localhost/api/docs/ | `https://$DOMAIN/api/docs/` |
| Django admin | http://localhost/admin/ | `https://$DOMAIN/admin/` |
| PostgreSQL | localhost:5433 | not published |
| Uploads | `holy-child-dev_media-files` volume | `holy-child-prod_media-files` volume |

---

## Production certificates

The HTTPS block in `prod/nginx.conf` needs certificates that do not exist on a
first deploy, and nginx will not start without them. Bring the stack up on HTTP
once, issue them, then switch:

1. Comment out the `listen 443` server block in `prod/nginx.conf`.
2. `docker compose up -d --build`
3. Issue the certificates into `prod/certbot/` through the
   `/.well-known/acme-challenge/` location that the port-80 server already
   serves.
4. Uncomment the block, then `docker compose restart nginx`.

`DOMAIN` from `.env` is substituted into the config each time the container
starts, so it is set in one place only.

---

## When something is wrong

| Symptom | Usually |
| --- | --- |
| `port is already allocated` | Another stack owns port 80 or 5433. Stop it, or change the mapping in `docker-compose.yml`. |
| `error getting credentials … gpg` | The Docker credential helper cannot decrypt its store. Remove the `credsStore` line from `~/.docker/config.json`, or repair `pass`. |
| Backend restarts in a loop | Read `docker compose logs backend`. Usually a missing `SECRET_KEY`, or `ALLOWED_HOSTS` without the host you are using. |
| `502 Bad Gateway` from nginx | The backend is not up yet, or it crashed on start. Check its logs. |
| Hot reload stopped working | `docker compose restart frontend`. If it persists, remove the `node_modules` volume: `docker compose down && docker compose up --build`. |
| A `$` in `.env` disappears | Compose reads that file for `${…}` substitution too. Keep `$` out of secrets — generate them with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. |
