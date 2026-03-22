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