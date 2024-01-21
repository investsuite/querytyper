"""Test mongo query implementation."""

import re
from typing import Dict, List, Optional

import pytest
from pydantic import BaseModel, EmailStr

from querytyper import MongoModelMetaclass, MongoQuery, exists, regex_query
from querytyper.mongo.query import QueryCondition


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

    class UserFilter(User, metaclass=MongoModelMetaclass):
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
    assert query._query_dict == {
        "name": "John",
        "age": {"$gte": 10},
        "email": [
            "john@example.com",
            "john@gmail.com",
        ],
    }


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
    assert query._query_dict == {"str_field": "a"}


def test_query_less_then() -> None:
    """Test MongoQuery less_then override."""
    query = MongoQuery(QueryModel.int_field <= 1)
    assert isinstance(query, MongoQuery)
    assert query._query_dict == {"int_field": {"$lte": 1}}
    query = MongoQuery(QueryModel.int_field < 1)
    assert isinstance(query, MongoQuery)
    assert query._query_dict == {"int_field": {"$lt": 1}}


def test_query_and() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery((QueryModel.str_field == "a") & (QueryModel.int_field >= 1))
    assert isinstance(query, MongoQuery)
    assert query._query_dict == {"str_field": "a", "int_field": {"$gte": 1}}


def test_query_or() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field == "a") | MongoQuery(QueryModel.int_field > 1)
    assert isinstance(query, MongoQuery)
    assert query._query_dict == {"$or": [{"str_field": "a"}, {"int_field": {"$gt": 1}}]}


def test_query_in() -> None:
    """Test MongoQuery equals override."""
    query = MongoQuery(QueryModel.str_field in ["a", "b"])
    assert isinstance(query, MongoQuery)
    assert query._query_dict == {"str_field": ["a", "b"]}


def test_query_init_error() -> None:
    """Test MongoQuery equals override."""
    with pytest.raises(
        TypeError,
        match="MongoQuery argument must be a QueryCondition or a boolean value, <class 'str'> is not supported.",
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
    assert condition == MongoQuery._query_dict


def test_metaclass_type_errors() -> None:
    """Test MongoModelMetaclass."""
    with pytest.raises(
        TypeError,
        match="The class with metaclass MongoModelMetaclass requires a base class that inherits from BaseModel",
    ):

        class Test(metaclass=MongoModelMetaclass):
            """Test class."""

    class AnotherDummy(BaseModel):
        """Dummy base model."""

        another_field: str

    with pytest.raises(
        TypeError, match="MongoModelMetaclass does not support multiple inheritance"
    ):

        class MultipleInheritanceTest(Dummy, AnotherDummy, metaclass=MongoModelMetaclass):
            """Test class."""

    with pytest.raises(TypeError, match="The base class must inherit from BaseModel"):

        class TestNoBaseModel(str, metaclass=MongoModelMetaclass):
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
