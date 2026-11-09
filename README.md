## Seeding

The project provides a custom Django management command to populate the local development database with sample users, categories, tags, posts, and comments.

Run the command from the project root (the directory containing `manage.py`), after running migrations:

```bash
python manage.py migrate
python manage.py seed
```

### Arguments

| Argument | Default | Description |
| --- | ---: | --- |
| `--users` | `20` | Number of sample users to generate. |
| `--posts` | `100` | Number of sample posts to generate. |
| `--comments` | `500` | Number of sample comments to generate. |
| `--clear` | off | Clear existing data before seeding. Use only in your development database; confirm the deletion logic preserves superusers. |

### Example

```bash
python manage.py seed --users 50 --posts 300 --comments 1500
```

Example console output:

```text
Users: 50 created
Categories: 8 created
Tags: 20 created
Posts: 300 created
Comments: 1500 created
Done in 2.41 seconds
```

The execution time will vary by machine and database. To reseed from scratch, add `--clear` (this deletes data according to your command's implementation):

```bash
python manage.py seed --users 50 --posts 300 --comments 1500 --clear
```

> **Development only:** Seeded accounts and passwords are test data, not suitable for production.

## Django Unfold Admin

The Django Unfold administrative interface is available at [`/admin/`](http://127.0.0.1:8000/admin/) when the local development server is running. Log in with a staff or superuser account.

### Dashboard

The dashboard shows user, post, and comment statistics, posts by category, top authors, and published/draft proportions.

![Admin dashboard](docs/screenshots/dashboard.png)

### Post list with filters open

The post list provides search, filters, status labels, publishing actions, comment counts, and related-data navigation.

![Post list with filters open](docs/screenshots/post-list-filters.png)

### Post edit page

The post edit page contains tabbed fields, an editor for the body, publishing controls, and related comments.

![Post edit page](docs/screenshots/post-edit.png)

### User list

The user list displays user details, account status labels, post counts, filters, and bulk activation/deactivation actions.

![User list](docs/screenshots/user-list.png)

> Add the four **real screenshots from your running admin interface** to `docs/screenshots/` using these exact filenames before submitting. These image links will not display until the files have been committed.
