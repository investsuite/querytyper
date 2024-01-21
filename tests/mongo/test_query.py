"""Test mongo query implementation."""

import re

import pytest
from pydantic import BaseModel, EmailStr

from querytyper import MongoFilterMeta, MongoQuery, exists, regex_query
from querytyper.mongo.query import QueryCondition

from .conftest import Dummy, QueryModel


class User(BaseModel):
    """User database model."""

    id: int
    name: str
    email: EmailStr


def test_readme_example() -> None:
    """Test readme example."""

    class User(BaseModel):
        """User database model."""

        id: int
        name: str
        age: int
        email: EmailStr

    class UserFilter(User, metaclass=MongoFilterMeta):
        """User query filter."""

    query = MongoQuery(
        (UserFilter.name == "John")
        & (UserFilter.age >= 10)
        & (
            UserFilter.email
            in [
                "john@example.com",
                "john@gmail.com",
            ]
        )
    )
    assert isinstance(query, MongoQuery)
    assert query == {
        "name": "John",
        "age": {"$gte": 10},
        "email": [
            "john@example.com",
            "john@gmail.com",
        ],
    }


def test_query_equals() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a")
    assert isinstance(query, MongoQuery)
    assert query == {"str_field": "a"}


def test_query_less_then() -> None:
    """Test MongoQuery less_then override."""
    query = MongoQuery(QueryModel.int_field <= 1)
    assert isinstance(query, MongoQuery)
    assert query == {"int_field": {"$lte": 1}}
    query = MongoQuery(QueryModel.int_field < 1)
    assert isinstance(query, MongoQuery)
    assert query == {"int_field": {"$lt": 1}}


def test_query_and() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery((QueryModel.str_field == "a") & (QueryModel.int_field >= 1))
    assert isinstance(query, MongoQuery)
    assert query == {"str_field": "a", "int_field": {"$gte": 1}}


def test_query_or() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a") | MongoQuery(QueryModel.int_field > 1)
    assert isinstance(query, MongoQuery)
    assert query == {"$or": [{"str_field": "a"}, {"int_field": {"$gt": 1}}]}


def test_query_in() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field in ["a", "b"])
    assert isinstance(query, MongoQuery)
    assert query == {"str_field": ["a", "b"]}


def test_query_init_error() -> None:
    """Test MongoQuery equals override."""
    with pytest.raises(
        TypeError,
        match="MongoQuery argument must be a QueryCondition, dict or a boolean value, <class 'str'> is not supported.",
    ):
        MongoQuery("random string")


def test_query_repr() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a")
    assert isinstance(query, MongoQuery)
    assert repr(query) == "{'str_field': 'a'}"


def test_query_condition_repr() -> None:
    """Test MongoQuery equals override."""
    condition = QueryCondition(QueryModel.str_field == "a")
    assert isinstance(condition, QueryCondition)
    assert repr(condition) == "{'str_field': 'a'}"


def test_querycondition_and() -> None:
    """Test Query condition & override."""
    conditions = QueryCondition(QueryModel.str_field == "a") & QueryCondition(
        QueryModel.int_field >= 1
    )
    assert isinstance(conditions, QueryCondition)
    # test also boolean is supported
    conditions = QueryCondition(QueryModel.str_field == "a") & True
    assert isinstance(conditions, QueryCondition)
    condition = QueryCondition(QueryModel.str_field == "a")
    conditions = True & condition
    assert isinstance(conditions, QueryCondition)
    assert isinstance(condition, QueryCondition)


def test_metaclass_type_errors() -> None:
    """Test MongoFilterMeta."""
    with pytest.raises(
        TypeError,
        match="The class with metaclass MongoFilterMeta requires a base class that inherits from BaseModel",
    ):

        class Test(metaclass=MongoFilterMeta):
            """Test class."""

    class AnotherDummy(BaseModel):
        """Dummy base model."""

        another_field: str

    with pytest.raises(TypeError, match="MongoFilterMeta does not support multiple inheritance"):

        class MultipleInheritanceTest(Dummy, AnotherDummy, metaclass=MongoFilterMeta):
            """Test class."""

    with pytest.raises(TypeError, match="The base class must inherit from BaseModel"):

        class TestNoBaseModel(str, metaclass=MongoFilterMeta):
            """Test class."""


def test_regex_query() -> None:
    """Test regex query."""
    condition = regex_query(QueryModel.str_field, re.compile("^a"))
    assert isinstance(condition, QueryCondition)
    assert condition == {"str_field": {"$regex": "^a"}}
    condition = regex_query("str_field", re.compile("^a"))
    assert isinstance(condition, QueryCondition)
    assert condition == {"str_field": {"$regex": "^a"}}


def test_exists_query() -> None:
    """Test exists query."""
    condition = exists(QueryModel.str_field)
    assert isinstance(condition, QueryCondition)
    assert condition == {"str_field": {"$exists": True}}
    condition = exists("str_field")
    assert isinstance(condition, QueryCondition)
    assert condition == {"str_field": {"$exists": True}}
    with pytest.raises(
        TypeError, match="Field must be a QueryField or str, <class 'int'> is not supported."
    ):
        exists(1)


def test_query_condition_init() -> None:
    """Test QueryCondition initializer and TypeErrors."""
    with pytest.raises(TypeError, match="QueryCondition must receive only one dict as input."):
        QueryCondition(1)
        QueryCondition(1, 2, 3)
    condition = QueryCondition({"field": "value"})
    assert "field" in condition
    assert condition["field"] == "value"
