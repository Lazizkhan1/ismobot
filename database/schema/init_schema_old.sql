-- CREATE DATABASE ismobot;;

CREATE TABLE IF NOT EXISTS users
(
    id        BIGSERIAL PRIMARY KEY,
    username  VARCHAR(255),
    lang      VARCHAR(3),
    user_type INT
);

CREATE TABLE IF NOT EXISTS category_type
(
    id           BIGSERIAL PRIMARY KEY,
    name_uz      VARCHAR(255),
    name_en      VARCHAR(255),
    single_price DECIMAL(15, 0),
    group_price  DECIMAL(15, 0),
    deleted_at   TIMESTAMP DEFAULT NULL
);
CREATE TABLE IF NOT EXISTS categories
(
    id            BIGSERIAL PRIMARY KEY,
    name          VARCHAR(255),
    photo_id      VARCHAR,
    category_type INT,
    deleted_at    TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (category_type) REFERENCES category_type (id)
);
CREATE TABLE IF NOT EXISTS orders
(
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT,
    moderator_id  BIGINT    DEFAULT NULL,
    category_id   INT,
    ceremony_date DATE,
    single_person BOOLEAN,
    photo_id      VARCHAR(255),
    cheque_id     VARCHAR(255),
    status        INT       DEFAULT 0, -- 0: pending, 1: accepted, 2: paid, 3: completed, -1: canceled
    cancel_reason VARCHAR(255) DEFAULT NULL,
    canceled_at   TIMESTAMP DEFAULT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (moderator_id) REFERENCES users (id),
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE IF NOT EXISTS order_photos
(
    id       BIGSERIAL PRIMARY KEY,
    order_id INT,
    photo_id VARCHAR,
    type     VARCHAR, -- 0: photo, 1: file
    FOREIGN KEY (order_id) REFERENCES orders (id)
);

