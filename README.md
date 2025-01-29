# XCart API

Minimal e-commerce REST API with SQLite database.

## Setup & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

## API Documentation

Swagger UI available at http://localhost:8000/docs

## Endpoints

### Auth
- `POST /auth/register` - Register user
- `POST /auth/login` - Login user

### Products
- `GET /products` - List all products
- `GET /products/{id}` - Get product details

### Cart (Requires Auth)
- `GET /cart` - View cart
- `POST /cart/add` - Add to cart
- `DELETE /cart/{id}` - Remove from cart

### Orders (Requires Auth)
- `POST /orders` - Place order
- `GET /orders` - List orders

## Note

SQLite database with 10 sample products is created automatically on first run.
