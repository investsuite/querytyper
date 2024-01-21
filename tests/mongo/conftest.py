"""Tests fixtures and configurations."""
from typing import Dict, List, Optional

from pydantic import BaseModel

from querytyper import MongoFilterMeta


class Dummy(BaseModel):
    """Dummy base model."""

    str_field: str
    int_field: int
    float_field: float
    bool_field: bool
    list_field: List[str] = ["a", "b"]
    dict_field: Dict[str, int] = {"a": 1, "b": 2}
    optional_str: Optional[str] = None


class QueryModel(Dummy, metaclass=MongoFilterMeta):
    """Test model."""
