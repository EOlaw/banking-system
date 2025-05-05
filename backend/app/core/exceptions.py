# backend/app/core/exceptions.py
from typing import Any, Dict, Optional

class CustomException(Exception):
    """Base class for custom exceptions."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.data = data or {}
        
        super().__init__(self.detail)