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