from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.fastapi_recommender.models import SessionLocal, User, Product, Rating
from src.models.cbf_model import get_recommendations
from src.fastapi_recommender.cf_model import get_cf_recommendations, get_user_based_cf_recommendations
from src.fastapi_recommender.hybrid_model import mixed_hybrid_recommender
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import MinMaxScaler
import os
import sqlite3
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI()


class LoginRequest(BaseModel):
    user_id: str
    password: str

# Globals for CBF
df = None
similarity_matrix = None
price_scaled = None
mlb = None
scaler = None

# Globals for CF and hybrid
ratings_df = None
avg_ratings = None
top_pool = None
user_item_matrix = None
item_similarity_df = None
user_similarity_df = None

@app.on_event("startup")
def load_and_preprocess_data():
    global df, similarity_matrix, price_scaled, mlb, scaler
    global ratings_df, avg_ratings, top_pool
    global user_item_matrix, item_similarity_df, user_similarity_df

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "amazon_electronics.db")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM products", conn)
        ratings_df = pd.read_sql_query(
            "SELECT user_id, product_id, rating FROM ratings WHERE rating IS NOT NULL",
            conn
        )

    print(f"Loaded {len(df)} products and {len(ratings_df)} ratings")

    # --- CBF: category + price similarity matrix ---
    df_cbf = df.copy()
    df_cbf["category"] = df_cbf["category"].str.split(r"[|&]")
    df_cbf["category"] = df_cbf["category"].apply(lambda x: list(set(x)))

    mlb = MultiLabelBinarizer()
    category_matrix = mlb.fit_transform(df_cbf["category"])

    scaler = MinMaxScaler()
    price_scaled = scaler.fit_transform(df[["discounted_price"]])

    feature_matrix = np.hstack((category_matrix, price_scaled))
    similarity_matrix = cosine_similarity(feature_matrix)

    # --- CF: user-item matrix and similarity matrices ---
    valid_products = set(df["product_id"])
    ratings_clean = ratings_df[ratings_df["product_id"].isin(valid_products)].copy()

    user_item_matrix = ratings_clean.pivot_table(
        index="user_id", columns="product_id", values="rating"
    )
    user_item_filled = user_item_matrix.fillna(0)

    cf_item_sim = cosine_similarity(user_item_filled.T)
    item_similarity_df = pd.DataFrame(
        cf_item_sim,
        index=user_item_filled.columns,
        columns=user_item_filled.columns,
    )

    user_means = user_item_matrix.mean(axis=1)
    user_item_centered = user_item_matrix.sub(user_means, axis=0).fillna(0)
    cf_user_sim = cosine_similarity(user_item_centered)
    user_similarity_df = pd.DataFrame(
        cf_user_sim,
        index=user_item_matrix.index,
        columns=user_item_matrix.index,
    )

    # --- Precompute avg_ratings and top_pool for the hybrid recommender ---
    avg_ratings = ratings_df.groupby("product_id")["rating"].mean().to_dict()

    merged = pd.merge(df, ratings_df, on="product_id")
    top_pool = (
        merged
        .groupby(["product_id", "product_name", "category", "discounted_price"])["rating"]
        .mean()
        .reset_index(name="avg_rating")
        .sort_values("avg_rating", ascending=False)
    )

    print("Data preprocessing complete")

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

# ---------------- AUTH ROUTES ---------------- #

@app.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == credentials.user_id).first()

    if not user or user.user_pass != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "success": True,
        "user_id": user.user_id,
        "user_name": user.user_name,
    }

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

@app.get("/top_rated_products/") # produtos com maior média de ratings. recomendação não personalizada
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


@app.get("/top_products_cbf/user{user_id}")  #recomendações personalizadas para um utilizador
def get_top_rated_products(user_id: str, db: Session = Depends(get_db)):
    user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()

    rated_products = {rating.product_id: rating.rating for rating in user_ratings}
    recommendations = get_recommendations(rated_products,similarity_matrix,df,5)  # vai buscar todos os produtos recomendados

    products = db.query(Product).filter(Product.product_id.in_(recommendations)).all()

    return [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "discounted_price": p.discounted_price,
        }
        for p in products
    ]


@app.get("/recommendations/cf/{user_id}")
def get_recommendations_cf(user_id: str, n: int = 5, db: Session = Depends(get_db)):
    cf_ids = get_user_based_cf_recommendations(
        user_id, user_item_matrix, user_similarity_df, n=n * 4
    )
    if not cf_ids:
        cf_ids = get_cf_recommendations(
            user_id, user_item_matrix, item_similarity_df, n=n * 4
        )

    if not cf_ids:
        raise HTTPException(status_code=404, detail="No CF recommendations found for this user")

    cf_ids = cf_ids[:n]
    products = db.query(Product).filter(Product.product_id.in_(cf_ids)).all()
    product_map = {p.product_id: p for p in products}

    return [
        {
            "product_id": pid,
            "product_name": product_map[pid].product_name,
            "discounted_price": product_map[pid].discounted_price,
        }
        for pid in cf_ids
        if pid in product_map
    ]


@app.get("/recommendations/hybrid/{user_id}")
def get_recommendations_hybrid(user_id: str, n_top: int = 3, n_cbf: int = 3, n_cf: int = 4):
    results = mixed_hybrid_recommender(
        user_id=user_id,
        ratings_df=ratings_df,
        products_df=df,
        similarity_matrix=similarity_matrix,
        user_item_matrix=user_item_matrix,
        item_similarity_df=item_similarity_df,
        user_similarity_df=user_similarity_df,
        top_pool=top_pool,
        avg_ratings=avg_ratings,
        n_top=n_top,
        n_cbf=n_cbf,
        n_cf=n_cf,
    )
    return results

