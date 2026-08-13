<h1>telegram bot </h1>

## Database migrations

Alembic is now the schema source of truth.

For a fresh database:

```bash
alembic upgrade head
```

For an existing production database that already has the old schema, mark the
initial migration as applied before deploying code that expects Alembic:

```bash
alembic stamp head
```

After that, future deployments can run:

```bash
alembic upgrade head
```
