from models import SessionLocal, User, Product, Rating
from pathlib import Path
import pandas as pd

db = SessionLocal()

current_folder = Path(__file__).parent
csv_file = current_folder / "amazon_electronics.csv"

df = pd.read_csv(csv_file)
print("CSV loaded successfully!")

# Products import
for _,row in df.iterrows():
    product = Product(
        product_id=row["product_id"],
        product_name=row["product_name"],
        category=row["category"],
        discounted_price=float(row["discounted_price"].replace(',', '')) if pd.notna(row["discounted_price"]) else None,
        actual_price=float(row["actual_price"].replace(',', '')) if pd.notna(row["actual_price"]) else None,
        discount_percentage=float(row["discount_percentage"].replace('%', '')) if pd.notna(row["discount_percentage"]) else None,
        rating_count=int(row["rating_count"].replace(',', '')) if pd.notna(row["rating_count"]) else None,
        about_product=row["about_product"],
        img_link=row["img_link"],
        product_link=row["product_link"]
    )
    db.add(product)

db.commit()

print("Products imported successfully!")

# Users import
for _,row in df.iterrows():
    user = User(
        user_id=row["user_id"],
        user_name=row["user_name"],
        Country=row["Country"],
        Age=row["Age"],
        City=row["City"],
        Marital_Status=row["Marital_Status"]
    )
    db.add(user)

db.commit()

print("Users imported successfully!")

# Ratings import
for _,row in df.iterrows():
    rating = Rating(
        product_id=row["product_id"],
        user_id=row["user_id"],
        rating=row["rating"],
        review_id=row["review_id"],
        review_title=row["review_title"],
        review_content=row["review_content"],
        Used_Device=row["Used_Device"],
        Day_of_Week=row["Day_of_Week"]
    )
    db.add(rating)

db.commit()

print("Ratings imported successfully!")

db.close()