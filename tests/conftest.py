import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from nexus.core.main import app
from nexus.core.db.database import Base, get_db
from nexus.core.db.models import NodeModel, JobModel, MetricModel, LogModel, AlertModel

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Creates a fresh database session for a test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    Test client with database dependency overridden.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # Session closed by fixture above

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_node(db_session):
    """Creates a default test node."""
    from nexus.core.db.models import NodeModel
    from nexus.shared.models import NodeStatus
    from datetime import datetime
    import uuid

    node = NodeModel(
        id=str(uuid.uuid4()),
        name="test-node-1",
        ip_address="192.168.1.100",
        status=NodeStatus.ONLINE,
        node_metadata={"location": "Test Lab", "tags": ["test"]},
        last_seen=datetime.utcnow()
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node

@pytest.fixture(scope="function")
def auth_headers(test_node):
    """Returns valid auth headers for the test node."""
    from nexus.shared.auth import create_access_token
    
    token = create_access_token(data={"sub": test_node.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def mock_config():
    """Ensure consistent config for tests."""
    from nexus.core.api import auth
    # Force default shared secret to avoid env var interference
    original_secret = auth.config.shared_secret
    auth.config.shared_secret = "change-me-in-production"
    yield
    auth.config.shared_secret = original_secret
