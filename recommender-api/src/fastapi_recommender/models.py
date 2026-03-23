from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Float

Base = declarative_base()

database_url = "sqlite:///./amazon_electronics.db"
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    user_name = Column(String, index=True)
    Country = Column(String)
    Age = Column(Integer)
    City = Column(String)
    Marital_Status = Column(String)

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, index=True)
    product_name = Column(String, index=True)
    category = Column(String)
    discounted_price = Column(Float)
    actual_price = Column(Float)
    discount_percentage = Column(Float)
    rating_count = Column(Integer)
    about_product = Column(String)
    img_link = Column(String)
    product_link = Column(String)

class Rating(Base):
    __tablename__ = "ratings"

    review_id = Column(String, primary_key=True, index=True)

    product_id = Column(String, ForeignKey("products.product_id"))
    user_id = Column(String, ForeignKey("users.user_id"))

    rating = Column(Float)
    review_title = Column(String)
    review_content = Column(String)

    Used_Device = Column(String)
    Day_of_Week = Column(String)