# Examples

## FastAPI CRUD

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped, mapped_column, Session
from schemap import AutoBase

app = FastAPI()
engine = create_engine("sqlite:///./db.sqlite3")

class User(AutoBase):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

AutoBase.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/users")
def create_user(data: User.CreateSchema, session: Session = Depends(get_session)):
    user = User.from_schema(data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user.to_schema()

@app.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user.to_schema(User.PublicSchema)

@app.patch("/users/{user_id}")
def update_user(user_id: int, data: User.UpdateSchema, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(user, key, value)
    session.commit()
    session.refresh(user)
    return user.to_schema()
```

Hide sensitive fields from API responses with `exclude_public`:

```python
from schemap import SchemaConfig

class User(AutoBase):
    __tablename__ = "users"
    __schema_config__ = SchemaConfig(exclude_public=["email", "phone"])
    ...
```

## Custom validators

```python
from schemap import AutoBase, SchemaConfig

def must_be_positive(v: float) -> float:
    if v <= 0:
        raise ValueError("Must be positive")
    return v

class Product(AutoBase):
    __tablename__ = "products"
    __schema_config__ = SchemaConfig(
        extra_validators={"price": must_be_positive}
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[float]

p = Product.CreateSchema(price=10.5)  # OK
# Product.CreateSchema(price=-5.0)    # Raises pydantic.ValidationError
```

## Inheritance patterns

### Single-table inheritance

```python
class Animal(AutoBase):
    __tablename__ = "animals"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    name: Mapped[str]
    __mapper_args__ = {"polymorphic_on": type}

class Dog(Animal):
    __mapper_args__ = {"polymorphic_identity": "dog"}
    breed: Mapped[str] = mapped_column(nullable=True)

class Cat(Animal):
    __mapper_args__ = {"polymorphic_identity": "cat"}
    color: Mapped[str] = mapped_column(nullable=True)
```

Each subclass gets its own set of four schemas with its own columns.

### Custom base class

```python
from schemap import SchemaMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(SchemaMixin, DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

class User(Base):
    __tablename__ = "users"
    name: Mapped[str]
```
