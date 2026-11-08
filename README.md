# Blog API — Practice Work 1

Django REST Framework blog API. Project organization and model/admin conventions follow
[MaratulyTemirbolat/crm-django](https://github.com/MaratulyTemirbolat/crm-django),
but only features required by **Practice Work 1** are included.

![Blog API entity–relationship diagram](docs/erd.png)

## What is implemented

- `apps.auths`: custom user (`AbstractBaseUser` + `PermissionsMixin`), email login,
  password hashing, custom manager, Django admin, JWT login/refresh, registration.
- `apps.blog`: `Category`, `Tag`, `Post`, `Comment` models, admin configuration,
  serializers, and REST CRUD endpoints.
- Separate `requirements/base.txt`, `dev.txt`, `prod.txt` dependencies.
- Separate `settings/base.py`, `settings/conf.py`, `settings/env/local.py`,
  `settings/env/prod.py`, `settings/urls.py`, `settings/wsgi.py`, `settings/asgi.py`.
- `BLOG_`-prefixed variables loaded by `python-decouple` from `settings/.env`.
- SQLite locally and PostgreSQL in production. Lint configuration in `pyproject.toml`.
- An ERD covering the custom user, categories, tags, posts, comments and M2M table.

No CRM/task-management apps or unrelated features were copied from the reference.

## Project structure

```text
blog-api/
├── apps/
│   ├── auths/       # user, JWT registration/login, admin, migrations, tests
│   └── blog/        # category, tag, post, comment, admin, migrations, tests
├── docs/erd.png
├── logs/.gitkeep
├── requirements/{base,dev,prod}.txt
├── settings/
│   ├── .env.example
│   ├── conf.py
│   ├── base.py
│   ├── env/{local,prod}.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp settings/.env.example settings/.env
```

Replace `BLOG_SECRET_KEY` in `settings/.env` with a randomly generated value.
For example, run `python -c 'import secrets; print(secrets.token_urlsafe(48))'`.
With `BLOG_ENV_ID=local`, start with:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**API URLs** (prefix `http://127.0.0.1:8000`):

| HTTP | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Register an account |
| POST | `/api/auth/login/` | Obtain JWT access/refresh tokens with email/password |
| POST | `/api/auth/refresh/` | Refresh an access token |
| GET/POST | `/api/posts/` | List posts or create one |
| GET/PUT/PATCH/DELETE | `/api/posts/<slug>/` | Post details and editing |
| GET/POST | `/api/categories/` | List/add categories |
| GET/POST | `/api/tags/` | List/add tags |
| GET/POST | `/api/comments/` | List/add comments |
| GET/PUT/PATCH/DELETE | `/api/comments/<id>/` | Comment details and editing |

Category/tag edits are limited to staff. Authors can change their own posts and
comments. Draft posts are visible only to their authors and staff. Writing requires
a JWT access token (`Authorization: Bearer <token>`).

Category/tag slugs are submitted as strings in posts; tags are an optional list.
A post without a category can use `null` or omit `category`. A post's `status`
is either `draft` (default) or `published`.

## Check your work

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
ruff check .
```

Initial migrations are committed, and `AUTH_USER_MODEL = "auths.User"` is set
in `settings/base.py` before migrations.

## Git / GitHub homework workflow

Create a **public** repository named `blog-api`, push both `main` and `hw1`.
In the supplied ZIP, local Git history already contains an `hw1` branch merged
into `main`, and `hw1` remains available.

```bash
git remote add origin https://github.com/YOUR_USERNAME/blog-api.git
git push -u origin main
git push -u origin hw1
```

For future work, create `hw2`, `hw3`, etc., and merge into `main` without
deleting the homework branches. Do not commit `settings/.env` or logs.
