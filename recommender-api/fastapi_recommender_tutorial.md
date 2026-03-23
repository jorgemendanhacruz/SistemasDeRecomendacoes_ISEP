# FastAPI Tutorial: Building an API with a Non-Personalized Recommender

## 1. Setting Up FastAPI

### Install FastAPI and Required Dependencies Using Pipenv

Ensure you have Python installed, then install Pipenv:

```bash
pip install pipenv
```

Create a new project and initialize a virtual environment:

```bash
mkdir fastapi-recommender
cd fastapi-recommender
pipenv install --python 3.10
```

Add dependencies:

```bash
pipenv install fastapi uvicorn sqlalchemy
pipenv install fastapi[all]
```
if doens't work ...

```bash
python -m pipenv install fastapi uvicorn sqlalchemy
python -m pipenv install fastapi[all]
```

Activate the virtual environment:

```bash
pipenv shell
```

---

## 2. Project Directory Structure

```
fastapi-recommender/
│── src/
│   ├── fastapi_recommender/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── seed.py
│── frontend/
│   ├── index.html
│── Pipfile
│── README.md
```

---

## 3. Database Integration with SQLAlchemy

### Define the Database Models

Create `src/fastapi_recommender/models.py`:

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

database_url = "sqlite:///./test.db"
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    
    user = relationship("User")
    product = relationship("Product")
```

---

### Create Database Tables

Create `src/fastapi_recommender/database.py`:

```python
from models import Base, engine
Base.metadata.create_all(bind=engine)
```


---

## 4. Seeding Dummy Data

Create `src/fastapi_recommender/seed.py`:

```python
from models import SessionLocal, User, Product, Purchase

db = SessionLocal()

# Create dummy users
users = [
    User(name="Alice"),
    User(name="Bob"),
    User(name="Charlie"),
]

db.add_all(users)
db.commit()

# Create dummy products
dummy_products = [
    Product(name="Laptop", description="High-end gaming laptop", price=1500),
    Product(name="Smartphone", description="Latest model smartphone", price=999),
    Product(name="Headphones", description="Noise-cancelling headphones", price=199),
    Product(name="Smartwatch", description="Water-resistant smartwatch", price=249),
    Product(name="Tablet", description="Lightweight tablet", price=499)
]

db.add_all(dummy_products)
db.commit()

# Add dummy purchases
purchases = [
    Purchase(user_id=1, product_id=1, quantity=50),
    Purchase(user_id=2, product_id=2, quantity=30),
    Purchase(user_id=3, product_id=3, quantity=40),
    Purchase(user_id=1, product_id=4, quantity=20),
    Purchase(user_id=2, product_id=5, quantity=35)
]

db.add_all(purchases)
db.commit()
db.close()
```
Run the following command to init the database:
```bash
python src/fastapi_recommender/database.py
```

Run the following command to populate the database:

```bash
python src/fastapi_recommender/seed.py
```

---

## 5. Building the API with FastAPI

### Create API Endpoints in `src/fastapi_recommender/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.fastapi_recommender.models import SessionLocal, User, Product, Purchase

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- USER ROUTES ---------------- #

@app.post("/users/")
def create_user(name: str, db: Session = Depends(get_db)):
    user = User(name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ---------------- PRODUCT ROUTES ---------------- #

@app.post("/products/")
def create_product(name: str, description: str, price: int, db: Session = Depends(get_db)):
    product = Product(name=name, description=description, price=price)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.get("/products/")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# ---------------- PURCHASE ROUTES ---------------- #

@app.post("/purchases/")
def create_purchase(user_id: int, product_id: int, quantity: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    product = db.query(Product).filter(Product.id == product_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    purchase = Purchase(user_id=user_id, product_id=product_id, quantity=quantity)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase

@app.get("/purchases/")
def get_purchases(db: Session = Depends(get_db)):
    return db.query(Purchase).all()

@app.get("/purchases/user/{user_id}")
def get_purchases_by_user(user_id: int, db: Session = Depends(get_db)):
    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
    if not purchases:
        raise HTTPException(status_code=404, detail="No purchases found for this user")
    return purchases

# ---------------- RECOMMENDATIONS ROUTE ---------------- #

@app.get("/recommendations/")
def get_top_purchased_products(db: Session = Depends(get_db)):
    top_products = (
        db.query(Product, func.sum(Purchase.quantity).label("total_purchases"))
        .join(Purchase)
        .group_by(Product.id)
        .order_by(func.sum(Purchase.quantity).desc())
        .limit(5)
        .all()
    )
    return [{"id": p.id, "name": p.name, "price": p.price, "total_purchases": total_purchases} for p, total_purchases in top_products]
```

Run the server:

```bash
pipenv run uvicorn src.fastapi_recommender.main:app --reload
```

---

## 6. Creating a Simple Frontend
### Create html file in `frontend/index.html`

```bash
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top Recommended Items</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            text-align: center;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            padding: 10px;
            background: #e0e0e0;
            margin: 5px 0;
            border-radius: 5px;
        }
    </style>
    <script>
        async function loadRecommendations() {
            try {
                const response = await fetch("http://127.0.0.1:8000/recommendations/");
                const products = await response.json();

                const recommendationsList = document.getElementById("recommendations");
                recommendationsList.innerHTML = "";

                if (products.length === 0) {
                    recommendationsList.innerHTML = "<li>No recommendations available.</li>";
                } else {
                    products.forEach(product => {
                        const listItem = document.createElement("li");
                        listItem.innerHTML = `<strong>${product.name}</strong> - $${product.price} <br> <span>Total Purchases: ${product.total_purchases}</span>`;
                        recommendationsList.appendChild(listItem);
                    });
                }
            } catch (error) {
                console.error("Error fetching recommendations:", error);
                document.getElementById("recommendations").innerHTML = "<li>Failed to load recommendations.</li>";
            }
        }
        window.onload = loadRecommendations;
    </script>
</head>
<body>
    <div class="container">
        <h1>Top Recommended Items</h1>
        <ul id="recommendations"></ul>
    </div>
</body>
</html>

```
### **Start a local web server**

```bash
cd frontend 
python -m http.server 8080
```

Go to http://localhost:8080


### Swagger UI

http://127.0.0.1:8000/docs
