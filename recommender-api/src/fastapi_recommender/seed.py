from models import SessionLocal, User, Product, Rating
from pathlib import Path
import pandas as pd

db = SessionLocal()

current_folder = Path(__file__).parent
csv_file = current_folder / "amazon_electronics.csv"

df = pd.read_csv(csv_file, delimiter=';')
print("CSV loaded successfully!")

# Products Import

existing_product_ids = {
    pid for (pid,) in db.query(Product.product_id).all()  #evita inserir produtos duplicados
}

for _, row in df.iterrows():
    product_id = row["product_id"]

    if product_id in existing_product_ids:
        continue

    product = Product(
        product_id=product_id,
        product_name=row["product_name"],
        category=row["category"],
        discounted_price=float(row["discounted_price"]),
        actual_price=float(row["actual_price"]),
        discount_percentage=float(row["discount_percentage"]),
        rating_count=int(row["rating_count"]),
        about_product=row["about_product"],
        img_link=row["img_link"],
        product_link=row["product_link"]
    )

    db.add(product)

    # Important: update the set immediately
    existing_product_ids.add(product_id)

db.commit()

print("Products imported successfully!")

# Users import
existing_user_ids = {
    uid for (uid,) in db.query(User.user_id).all()
}

for row in df.itertuples(index=False):
    user_id = row.user_id

    if user_id in existing_user_ids:
        continue

    user = User(
        user_id=user_id,
        user_name=row.user_name,
        user_pass="pass123",
        Country=row.Country,
        Age=row.Age,
        City=row.City,
        Marital_Status=row.Marital_Status
    )

    db.add(user)

    # Prevent duplicates later in the CSV
    existing_user_ids.add(user_id)

db.commit()

print("Users imported successfully!")

# Ratings import

def parse_to_float(value):
    try:
        if pd.isna(value):
            return None
        clean_value = str(value).replace(',', '.').replace('%', '').strip()
        return float(clean_value)
    except (ValueError, TypeError):
        return None

for row in df.itertuples(index=False):

    rating = Rating(
        product_id=row.product_id,
        user_id=row.user_id,
        rating=parse_to_float(row.rating),
        review_id=row.review_id,
        review_title=row.review_title,
        review_content=row.review_content,
        Used_Device=row.Used_Device,
        Day_of_Week=row.Day_of_Week
    )
    db.add(rating)

db.commit()
print("Ratings imported successfully!")







db.commit()
print("Ratings imported successfully!")


# Synthetic Ratings import

import random

def add_synthetic_ratings_per_user(min_ratings=5):
    existing_ratings = {
        (r.user_id, r.product_id)
        for r in db.query(Rating).all()
    }

    existing_review_ids = {
        r.review_id
        for r in db.query(Rating).all()
    }

    products_df = pd.read_sql(
        db.query(Product).statement,
        db.bind
    )

    ratings_df = pd.read_sql(
        db.query(Rating).statement,
        db.bind
    )

    for user_id in ratings_df["user_id"].unique():
        user_ratings = ratings_df[ratings_df["user_id"] == user_id]

        if len(user_ratings) >= min_ratings:
            continue

        base_rating_row = user_ratings.iloc[0]
        base_product_id = base_rating_row["product_id"]
        base_rating = base_rating_row["rating"]

        if pd.isna(base_rating):
            base_rating = 4.0

        base_product = products_df[
            products_df["product_id"] == base_product_id
        ]

        if base_product.empty:
            continue

        base_categories = str(base_product.iloc[0]["category"]).split("|")
        main_category = base_categories[0]

        candidate_products = products_df[
            products_df["category"].str.contains(main_category, na=False, regex=False)
        ]

        candidate_products = candidate_products[
            ~candidate_products["product_id"].isin(user_ratings["product_id"])
        ]

        needed = min_ratings - len(user_ratings)
        sample_size = min(needed, len(candidate_products))

        if sample_size <= 0:
            continue

        sampled_products = candidate_products.sample(
            n=sample_size,
            random_state=42
        )

        for _, product in sampled_products.iterrows():
            new_product_id = product["product_id"]

            if (user_id, new_product_id) in existing_ratings:
                continue

            new_review_id = f"SYN_{user_id}_{new_product_id}"

            if new_review_id in existing_review_ids:
                continue

            variation = random.choice([-1, -0.5, 0, 0.5, 1])
            new_rating = max(1, min(5, float(base_rating) + variation))

            synthetic_rating = Rating(
                review_id=new_review_id,
                product_id=new_product_id,
                user_id=user_id,
                rating=new_rating,
                review_title="Synthetic rating",
                review_content="Generated synthetic interaction for recommendation testing",
                Used_Device="Unknown",
                Day_of_Week="Unknown"
            )

            db.add(synthetic_rating)

            existing_ratings.add((user_id, new_product_id))
            existing_review_ids.add(new_review_id)

    db.commit()
    print("Synthetic ratings added successfully!")


add_synthetic_ratings_per_user(min_ratings=5)





db.close()