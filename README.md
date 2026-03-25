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


Run the following command to init the database:
```bash
python src/fastapi_recommender/database.py
```

Run the following command to populate the database:

```bash
python src/fastapi_recommender/seed.py
```

---

Run the server:

```bash
pipenv run uvicorn src.fastapi_recommender.main:app --reload
```

---

```bash
cd frontend 
python -m http.server 8080
```

Go to http://localhost:8080


### Swagger UI

http://127.0.0.1:8000/docs
