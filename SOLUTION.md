# Solution Steps

1. Design the PostgreSQL schema for the e-commerce inventory system, ensuring normalization and setting up all necessary tables (categories, products, inventory, price_history, inventory_history), indexes, unique constraints, and foreign keys. Write schema.sql.

2. Implement the SQLAlchemy models in Python (models.py), accurately reflecting table structures, keys, indexes, relationships, and nullable rules, using declarative syntax and appropriate relationship() calls.

3. Configure the async database engine and session using SQLAlchemy's async capabilities (database.py), providing a dependency-injectable session factory for FastAPI integration.

4. Develop async CRUD operations for category, product, inventory, price history, and inventory history in crud.py, making sure to use async/await and efficient select/commit/refresh patterns.

5. Support search and filter endpoints in list queries, making use of indexable columns, optional filters, and limits/offsets for pagination in crud.py CRUD functions.

6. Implement concurrency-safe inventory adjustments by validating quantities and always logging every change into history tables in the same transaction.

7. On each relevant business event (inventory or price change), insert a corresponding entry into the history table, and demonstrate use of FastAPI-compatible background tasks for logging or auditing asynchronously.

8. Ensure all business logic is atomic using transactions, and that foreign keys, optimism of queries, and data integrity are always maintained.

9. Test database integration by running schema.sql and attempting all CRUD and search functions via the provided FastAPI app.

