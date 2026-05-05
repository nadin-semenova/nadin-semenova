-- ============================================================
-- DATABASE SCHEMA: Delivery Service Analytics
-- PostgreSQL· Educational dataset · Aug–Sep 2022
-- ============================================================

-- Products catalogue
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name       VARCHAR(255),
    price      DECIMAL(10, 2)
);

-- Registered users
CREATE TABLE users (
    user_id           SERIAL PRIMARY KEY,
    birth_date        DATE,
    sex               VARCHAR(10),
    registration_date DATE
);

-- Orders placed by users
CREATE TABLE orders (
    order_id      SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users(user_id),
    creation_time TIMESTAMP,
    product_ids   INTEGER[]
);

-- User actions log
CREATE TABLE user_actions (
    user_id  INTEGER REFERENCES users(user_id),
    order_id INTEGER,
    action   VARCHAR(50),
    time     TIMESTAMP
);

-- Registered couriers
CREATE TABLE couriers (
    courier_id SERIAL PRIMARY KEY,
    birth_date DATE,
    sex        VARCHAR(10)
);

-- Courier actions log
CREATE TABLE courier_actions (
    courier_id INTEGER REFERENCES couriers(courier_id),
    order_id   INTEGER,
    action     VARCHAR(50),
    time       TIMESTAMP
);

-- ============================================================
-- DATA INSERTION (Sample Dataset)
-- ============================================================

INSERT INTO products (product_id, name, price) VALUES
(1, 'pork', 450.00), (2, 'chicken', 380.00), (3, 'beef', 520.00),
(4, 'milk', 95.00), (5, 'bread', 60.00), (6, 'buckwheat', 130.00),
(7, 'rice', 125.00), (8, 'pasta', 100.00), (9, 'sunflower oil', 160.00),
(10, 'olive oil', 350.00), (11, 'apples', 180.00), (12, 'oranges', 220.00),
(13, 'sausages', 290.00), (14, 'smoked fish', 410.00), (15, 'chocolate', 195.00),
(16, 'coffee', 420.00), (17, 'black tea', 180.00), (18, 'sparkling water', 75.00),
(19, 'chips', 110.00), (20, 'chewing gum', 55.00);

INSERT INTO users (user_id, birth_date, sex, registration_date) VALUES
(101, '1990-01-15', 'male', '2022-08-24'),
(102, '1995-03-20', 'female', '2022-08-24'),
(103, '1988-11-05', 'male', '2022-08-25'),
(104, '2000-06-30', 'female', '2022-08-25'),
(105, '1993-09-14', 'male', '2022-09-01');

INSERT INTO orders (order_id, user_id, creation_time, product_ids) VALUES
(1, 101, '2022-08-24 10:00:00', ARRAY[1, 3]),
(2, 102, '2022-08-24 12:30:00', ARRAY[2, 3, 6]),
(3, 103, '2022-08-25 09:15:00', ARRAY[5]),
(4, 104, '2022-08-25 14:00:00', ARRAY[4, 8, 9]),
(5, 101, '2022-08-26 11:20:00', ARRAY[7, 3]),
(6, 102, '2022-08-26 13:45:00', ARRAY[1, 10]),
(7, 105, '2022-09-01 08:50:00', ARRAY[2, 6, 8]),
(8, 103, '2022-09-01 19:30:00', ARRAY[5, 9]);

INSERT INTO user_actions (user_id, order_id, action, time) VALUES
(101, 1, 'create_order', '2022-08-24 10:00:00'),
(102, 2, 'create_order', '2022-08-24 12:30:00'),
(103, 3, 'create_order', '2022-08-25 09:15:00'),
(104, 4, 'create_order', '2022-08-25 14:00:00'),
(101, 5, 'create_order', '2022-08-26 11:20:00'),
(102, 6, 'create_order', '2022-08-26 13:45:00'),
(102, 6, 'cancel_order', '2022-08-26 13:52:00'),
(105, 7, 'create_order', '2022-09-01 08:50:00'),
(103, 8, 'create_order', '2022-09-01 19:30:00');

INSERT INTO couriers (courier_id, birth_date, sex) VALUES
(1, '1992-04-10', 'male'), (2, '1998-07-22', 'female'), (3, '1996-12-01', 'male');

INSERT INTO courier_actions (courier_id, order_id, action, time) VALUES
(1, 1, 'accept_order', '2022-08-24 10:05:00'),
(1, 1, 'deliver_order', '2022-08-24 10:28:00'),
(2, 2, 'accept_order', '2022-08-24 12:35:00'),
(2, 2, 'deliver_order', '2022-08-24 13:01:00'),
(3, 3, 'accept_order', '2022-08-25 09:20:00'),
(3, 3, 'deliver_order', '2022-08-25 09:55:00'),
(1, 4, 'accept_order', '2022-08-25 14:05:00'),
(1, 4, 'deliver_order', '2022-08-25 14:40:00'),
(2, 5, 'accept_order', '2022-08-26 11:25:00'),
(2, 5, 'deliver_order', '2022-08-26 11:58:00'),
(3, 7, 'accept_order', '2022-09-01 08:55:00'),
(3, 7, 'deliver_order', '2022-09-01 09:30:00'),
(1, 8, 'accept_order', '2022-09-01 19:35:00'),
(1, 8, 'deliver_order', '2022-09-01 20:10:00');
