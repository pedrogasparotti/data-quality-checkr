import pytest
from pathlib import Path
from unittest.mock import MagicMock

from data_quality_checker.connector.output_log import DBConnector


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test_validation.db"


@pytest.fixture
def db_connector(temp_db: Path) -> DBConnector:
    """Create a DBConnector instance with a temporary database."""
    return DBConnector(temp_db)


@pytest.fixture
def mock_db_connector() -> MagicMock:
    """Create a mock DBConnector for testing without DB writes."""
    mock = MagicMock(spec=DBConnector)
    mock.log = MagicMock()
    return mock
