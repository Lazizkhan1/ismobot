 # Reorganize Routers and Migrate DB to SQLAlchemy/Alembic

  ## Summary

  - Split the aiogram handlers by business flow, with role-specific admin routing kept separate where it is already a natural boundary.
  - Replace psycopg2/import-time schema initialization with SQLAlchemy 2 async ORM, asyncpg, and Alembic migrations.
  - Preserve current bot behavior, callback data, FSM states, statuses, role IDs, table names, and user-facing flows.

  ## Key Changes

  - Router layout:
      - Create focused routers for common commands/language, customer order flow, admin category/order menu flow, admin order actions, and rating/cancel callbacks.
      - Keep one top-level router assembly module that registers middleware once and includes subrouters in explicit order.
      - Move Bot construction out of handlers/MessageHandler.py into a bot/app bootstrap module so handlers do not own application setup.

  - Database layer:
      - Add SQLAlchemy async engine/session setup from existing Config.DB_* values.
      - Add ORM models for users, categories, orders, and order_photos matching the existing schema and integer enum behavior.
      - Replace service SQL calls with async SQLAlchemy queries while keeping service method intent and return shape compatible with existing handler usage, preferably dict-like DTOs or
        small mapping helpers.

      - Remove database/Database.py schema execution from runtime startup.

  - Alembic:
      - Add Alembic config/env wired to SQLAlchemy metadata.
      - Create an initial migration matching the current schema, including the default SARBON category seed.
      - Support existing production DBs by documenting alembic stamp head; fresh DBs use alembic upgrade head.

  - Dependency/config cleanup:
      - Replace psycopg2/psycopg2-binary with sqlalchemy, alembic, and asyncpg.
      - Update both pyproject.toml/uv.lock and requirements.txt, preserving the current deployment scripts that install from requirements.txt.
      - Fix the existing requirements.txt encoding issue if needed so Docker/prod installs are reliable.

  - Safe improvements:
      - Fix obvious async FSM misuse in admin category handling, such as missing await state.get_data(), without changing the category add/remove behavior.
      - Remove unused imports and module-level service singletons where practical.
      - Keep current dirty worktree changes intact and refactor around them rather than reverting them.

  ## Test Plan

  - Add focused service tests for users, categories, orders, and order photos against a test database or transaction-scoped async session.
  - Add handler-level smoke tests where feasible for router registration and callback/FSM paths.
  - Run:
      - python -m compileall .
      - Alembic migration check: fresh DB alembic upgrade head
      - Bot startup import check without contacting Telegram where possible.

  - Manual acceptance scenarios:
      - New user /start creates user and asks language.
      - Customer creates order through category/date/video/payment screenshot.
      - Admin accepts order, uploads photos, completes with /done.
      - Admin cancels order with reason.
      - Admin lists/adds/removes categories.
      - Language change still updates stored language.

  ## Assumptions

  - Use async SQLAlchemy ORM with asyncpg.
  - Do not change table names, callback payloads, FSM state names, status integers, or role integers.
  - Alembic becomes the source of schema truth; database/schema/init_schema.sql may remain only as historical reference or be replaced by migrations.
  - Existing production data must not be dropped or rewritten during migration.