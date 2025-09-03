-- PostgreSQL schema for the inventory system

BEGIN;

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(40) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(1000),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    price NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX ix_products_sku ON products(sku);
CREATE INDEX ix_product_name_sku ON products(name, sku);
CREATE INDEX ix_products_category_id ON products(category_id);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    old_price NUMERIC(12,2),
    new_price NUMERIC(12,2) NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ix_price_history_product_id ON price_history(product_id);

CREATE TABLE inventory_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    old_quantity INTEGER,
    new_quantity INTEGER NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT now(),
    reason VARCHAR(255)
);
CREATE INDEX ix_inventory_history_product_id ON inventory_history(product_id);

COMMIT;
