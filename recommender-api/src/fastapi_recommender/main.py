from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.fastapi_recommender.models import SessionLocal, User, Product, Rating

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

#@app.post("/purchases/")
#def create_purchase(user_id: int, product_id: int, quantity: int, db: Session = Depends(get_db)):
#    user = db.query(User).filter(User.id == user_id).first()
#    product = db.query(Product).filter(Product.id == product_id).first()

#    if not user:
#        raise HTTPException(status_code=404, detail="User not found")
#    if not product:
#        raise HTTPException(status_code=404, detail="Product not found")

#    purchase = Purchase(user_id=user_id, product_id=product_id, quantity=quantity)
#    db.add(purchase)
#    db.commit()
#    db.refresh(purchase)
#    return purchase

#@app.get("/purchases/")
#def get_purchases(db: Session = Depends(get_db)):
#    return db.query(Purchase).all()

#@app.get("/purchases/user/{user_id}")
#def get_purchases_by_user(user_id: int, db: Session = Depends(get_db)):
#    purchases = db.query(Purchase).filter(Purchase.user_id == user_id).all()
#    if not purchases:
#        raise HTTPException(status_code=404, detail="No purchases found for this user")
#    return purchases

# ---------------- RECOMMENDATIONS ROUTE ---------------- #

@app.get("/top_rated_products/")
def get_top_rated_products(db: Session = Depends(get_db)):
    top_products = (
        db.query(Product, func.avg(Rating.rating).label("avg_rating"))
        .join(Rating, Product.product_id == Rating.product_id)
        .group_by(Product.product_id)
        .order_by(func.avg(Rating.rating).desc())
        .limit(5)
        .all()
    )
    return [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "discounted_price": p.discounted_price,
            "avg_rating": round(avg_rating, 2)
        }
        for p, avg_rating in top_products
    ]