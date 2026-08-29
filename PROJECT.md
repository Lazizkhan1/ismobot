# 🤖 IsmoBot — Project Architecture & Documentation

## 📌 Overview
**IsmoBot** is an automated Telegram bot for event photography delivery and ordering with a built-in referral and tiered discount system. It is built using **Python 3.12**, **aiogram 3.x**, **SQLAlchemy 2.x (async)**, **PostgreSQL**, **Alembic**, and **Redis**.

---

## 🛠 Tech Stack
- **Framework**: [aiogram 3.x](https://docs.aiogram.dev/) (Telegram Bot API)
- **Database ORM**: [SQLAlchemy 2.x (async)](https://docs.sqlalchemy.org/) + `asyncpg`
- **Database Engine**: PostgreSQL
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **FSM Storage**: Redis (via `aiogram.fsm.storage.redis`)
- **Web Server**: `aiohttp` (Webhook mode)

---

## 📂 Project Directory Structure

```
ismobot/
├── alembic/                      # Database migrations
│   ├── env.py                   # Alembic environment config
│   └── versions/                # Migration scripts
├── database/                     # Database layer
│   ├── models.py                # SQLAlchemy declarative models
│   ├── session.py               # Async engine and session factory
│   ├── utils.py                 # Dict serialization helpers
│   ├── Users.py                 # User CRUD operations
│   ├── Discounts.py             # Discounts & milestone CRUD
│   ├── Referrals.py             # Referral relationships CRUD
│   ├── DiscountHistory.py       # Ledger for earned/consumed discounts
│   ├── OrderDiscount.py         # Order-to-discount association
│   ├── Orders.py                # Order management CRUD
│   ├── Categories.py            # Event categories CRUD
│   ├── OrderPhotos.py           # Order photos management
│   └── UserType.py              # User roles & permissions
├── handlers/                     # Bot routers and UI handlers
│   ├── common.py                # /start, /lang, /admin, main menu
│   ├── referral.py              # Referral menu, link generator, stats
│   ├── orders.py                # Order placement, video note, discount picker, cheque
│   ├── admin_menu.py            # Admin category & system management
│   ├── admin_orders.py          # Admin order review, photo upload, referrer award
│   ├── keyboard.py              # Inline and reply keyboard builders
│   ├── States.py                # FSM state groups
│   ├── Translation.py           # Bilingual localization (UZ / RU)
│   ├── constants.py             # Bot command lists
│   └── router.py                # Master router configuration
├── middleware/                   # Request middlewares
│   ├── Middleware.py            # User registration & language injection
│   └── LoggingMiddleware.py     # Request/callback logging
├── Config.py                     # Environment variables and constants
├── main.py                       # Application entry point (webhook & polling)
├── plan.md                       # Implementation plan & checklist
└── PROJECT.md                    # Project architecture & documentation
```

---

## 🗄 Database Schema & Relationships

### 1. `users`
- `id` (BigInteger, PK) — Telegram User ID
- `username` (String) — Telegram username
- `full_name` (String) — Telegram full name
- `lang` (String) — Selected language (`uz` or `ru`)
- `user_type` (Integer) — Role (1: Customer, 2: Admin, 3: Moderator)
- `referrer_id` (BigInteger, FK -> `users.id`) — Inviting user ID

### 2. `discounts`
- `id` (BigInteger, PK)
- `title` (String) — Discount title
- `description` (Text) — Short description
- `discount_amount` (Numeric) — Value (percentage e.g. 20.00 or discrete amount e.g. 10000.00)
- `is_percentage` (Boolean) — True for percentage discounts
- `discrete` (Boolean) — True for fixed sum discounts
- `referral_milestone` (Integer) — 1 (20%), 2 (50%), 3 (100%), NULL for overflow
- `is_overflow` (Boolean) — True for rewards per extra referral past 3

### 3. `referrals`
- `id` (BigInteger, PK)
- `referrer_id` (BigInteger, FK -> `users.id`)
- `new_customer_id` (BigInteger, FK -> `users.id`, UNIQUE)
- `created_at` (Timestamp)

### 4. `discount_history` (Ledger)
- `id` (BigInteger, PK)
- `user_id` (BigInteger, FK -> `users.id`)
- `discount_id` (BigInteger, FK -> `discounts.id`)
- `amount` (Numeric)
- `is_percentage` (Boolean)
- `status` (String) — `active` | `consumed` | `superseded`
- `superseded_by` (BigInteger, FK -> `discount_history.id`)
- `order_id` (BigInteger, FK -> `orders.id`)
- `created_at` (Timestamp)

### 5. `orders`
- `id` (BigInteger, PK)
- `user_id` (BigInteger, FK -> `users.id`)
- `category_id` (Integer, FK -> `categories.id`)
- `ceremony_date` (Date)
- `video_note_id` (String)
- `cheque_id` (String)
- `status` (Integer) — 0: Pending, 1: Accepted, 2: Paid, 3: Completed, -1: Canceled
- `discount` (Numeric) — Discount amount applied to this order
- `total_amount` (Numeric) — Final price after discount
- `cancel_reason` (String)
- `created_at` (Timestamp)

### 6. `order_discount`
- `id` (BigInteger, PK)
- `order_id` (BigInteger, FK -> `orders.id`)
- `discount_history_id` (BigInteger, FK -> `discount_history.id`)
- `applied_amount` (Numeric)
- `is_percentage` (Boolean)

---

## 🎁 Referral & Discount Business Logic

### Tiered Milestone Rewards:
- **1 Friend**: 20% off next order
- **2 Friends**: 50% off next order (supersedes previous 20% active entry)
- **3 Friends**: 100% off next order (supersedes previous 50% active entry)
- **4+ Friends**: +10 000 so'm discrete discount per extra friend (stacks additively)

### Order & Payment Flow:
1. **Category Selection** -> **Ceremony Date** -> **Face Verification Video (>= 3s)**.
2. After video is received:
   - **User has NO discounts**: Directly requests payment to card and prompts for payment screenshot (no picker, no extra buttons).
   - **User HAS discounts**: Presents a clean 2-button discount picker:
     - `[🎁 N% off]` (if percentage discount active)
     - `[💵 N so'm]` (if discrete balance > 0)
     - `[❌ Pay without discount]`
3. User selects discount -> previews discounted total -> confirms -> uploads payment screenshot.
4. When Admin completes the order, the referrer automatically receives a notification with `[🎁 Use Discount]`.
5. Tapping `[🎁 Use Discount]` checks for any in-progress order; if found, resumes directly to discount selection; otherwise navigates to main menu.

---

## ⚙️ Environment Variables Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `TOKEN` | String | Required | Telegram Bot API Token |
| `ADMIN_ID` | Integer | Required | Primary Telegram Admin User ID |
| `ORDER_PRICE` | Integer | `30000` | Base price for photo search & delivery |
| `OVERFLOW_DISCOUNT_AMOUNT` | Integer | `10000` | Reward amount per referral after 3 |
| `CARD_NUMBER` | String | `""` | Payment card number shown to customers |
| `DEFAULT_LANGUAGE` | String | `uz` | Fallback language (`uz` or `ru`) |
| `DB_HOST` | String | `localhost` | PostgreSQL host |
| `DB_PORT` | Integer | `5432` | PostgreSQL port |
| `DB_NAME` | String | `ismobot` | Database name |
| `DB_USER` | String | `postgres` | Database user |
| `DB_PASS` | String | `123` | Database password |
| `WEB_SERVER_HOST` | String | `0.0.0.0` | Webhook HTTP server binding host |
| `WEB_SERVER_PORT` | Integer | `8080` | Webhook HTTP server port |
| `BASE_WEBHOOK_URL` | String | `""` | Public HTTPS domain for webhooks |
| `WEBHOOK_PATH` | String | `/webhook` | URL path for webhook POST requests |
| `WEBHOOK_SECRET` | String | `secret` | Secret token for Telegram webhook validation |

---

## 🚀 Running the Project

### 1. Apply Migrations
```bash
alembic upgrade head
```

### 2. Run with Webhook
```bash
python main.py https://your-domain.com
```

### 3. Run with Docker Compose
```bash
docker-compose up -d --build
```
