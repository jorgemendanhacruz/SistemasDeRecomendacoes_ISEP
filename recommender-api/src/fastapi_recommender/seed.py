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
    pid for (pid,) in db.query(Product.product_id).all()
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

db.close()