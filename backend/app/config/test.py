# backend/app/config/test.py
import os
from .settings import Settings

class TestSettings(Settings):
    """Test settings configuration."""
    
    # Use a test database
    POSTGRES_DB: str = os.getenv("POSTGRES_TEST_DB", "banking_system_test")
    
    # Disable email and SMS sending in tests
    TESTING: bool = True

test_settings = TestSettings()