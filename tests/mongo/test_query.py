"""Test mongo query implementation."""

from typing import Dict, List, Optional
from pydantic import BaseModel
from querytyper import MongoQuery, MongoModelMetaclass


class Dummy(BaseModel):
    """Dummy base model."""

    str_field: str
    int_field: int
    float_field: float
    bool_field: bool
    list_field: List[str] = ["a", "b"]
    dict_field: Dict[str, int] = {"a": 1, "b": 2}
    optional_str: Optional[str] = None


class QueryModel(Dummy, metaclass=MongoModelMetaclass):
    """Test model."""


def test_query_equals() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a")
    assert isinstance(query, MongoQuery)
    assert query._dict == {"str_field": "a"}


def test_query_and() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery((QueryModel.str_field == "a") & (QueryModel.int_field >= 1))
    assert isinstance(query, MongoQuery)
    assert query._dict == {"str_field": "a", "int_field": {"$gte": 1}}


def test_query_or() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a") | MongoQuery(QueryModel.int_field > 1)
    assert isinstance(query, MongoQuery)
    assert query._dict == {"$or": [{"str_field": "a"}, {"int_field": {"$gt": 1}}]}


def test_query_in() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field in ["a", "b"])
    assert isinstance(query, MongoQuery)
    assert query._dict == {"str_field": ["a", "b"]}
