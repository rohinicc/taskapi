import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app import cache

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_cached(key):
    return None

def override_set_cached(key, data):
    pass

def override_delete_cached(key):
    pass

def override_flush_tasks():
    pass

app.dependency_overrides[get_db] = override_get_db
cache.get_cached = override_get_cached
cache.set_cached = override_set_cached
cache.delete_cached = override_delete_cached
cache.flush_tasks = override_flush_tasks


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sample_task():
    return {"title": "Test task", "description": "A sample task"}
