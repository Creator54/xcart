from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class ProductBase(BaseModel):
    name: str
    price: float


class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItem(BaseModel):
    id: int
    product: Product
    quantity: int

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    total_amount: float

    class Config:
        from_attributes = True
