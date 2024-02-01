"""MongoQuery implementation."""
import re
from collections.abc import Iterable
from typing import Any, Dict, Generic, Type, TypeVar, Union, cast

T = TypeVar("T")
DictStrAny = Dict[str, Any]


class MongoQuery(DictStrAny):
    """
    MongoQuery is the core `querytyper` class to write MongoDB queries.

    It's a special dict subclass that keeps track of the query conditions
    and returns a dictionary that is compatible with the `filter` argument of
    the find methods of a pymongo collection.

    Example
    -------
    ```python
    query = MongoQuery(FilterModel.str_field == "a")
    collection = MongoClient(...).get_database("db_name").get_collection("collection_name")
    found_doc = collection.find_one(query)
    ```
    """

    _query_dict: DictStrAny = {}

    def __init__(self, *args: Any, **kwargs: DictStrAny) -> None:
        """
        Initialize a query object.
        """
        for arg in args:
            if not isinstance(arg, (QueryCondition, dict, bool)):
                raise TypeError(
                    f"MongoQuery argument must be a QueryCondition, dict or a boolean value, {type(arg)} is not supported."
                )
            if isinstance(arg, QueryCondition):
                MongoQuery._query_dict.update(arg)
        super().__init__(MongoQuery._query_dict)
        # clean up the class query dict after each instantiation
        MongoQuery._query_dict = {}

    def __del__(self) -> None:
        """MongoQuery destructor."""
        MongoQuery._query_dict = {}

    def __or__(
        self,
        other: "MongoQuery",
    ) -> "MongoQuery":
        """Overload | operator."""
        MongoQuery._query_dict = {"$or": [self, other]}
        return MongoQuery()


class QueryCondition(DictStrAny):
    """Class to represent a single query condition."""

    def __init__(self, *args: Any, **kwargs: DictStrAny) -> None:
        """
        Initialize a QueryCondition instance.

        It should receive a dict as only argument.

        Example
        -------
        ```python
        QueryCondition({"field": "value"})
        ```

        It also overloads dict __init__ typing.
        """
        arg = args[0]
        if len(args) != 1 or not isinstance(arg, dict):
            raise TypeError("QueryCondition must receive only one dict as input.")
        if isinstance(arg, dict):
            super().__init__(**arg)
            for k, v in arg.items():
                self.__setitem__(k, v)

    def __and__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            MongoQuery._query_dict.update(other)
        return self

    def __rand__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            MongoQuery._query_dict.update(other)
        return self

    def __bool__(self) -> bool:
        """Overload `bool(self)` return value for `in` operator overriding."""
        return False


class QueryField(Generic[T]):
    """QueryField descriptor to define query fields."""

    def __init__(
        self,
        name: str,
        field_type: T,
    ) -> None:
        """Initialize QueryField instance."""
        self.name = name
        self.field_type = field_type

    def __get__(
        self,
        instance: Any,
        cls: Type[Any],
    ) -> T:
        """Get the value of the field in the class namespace."""
        return cast(T, cls.__dict__[self.name])

    def __eq__(  # type: ignore[override]
        self,
        other: object,
    ) -> QueryCondition:
        """Overload == operator."""
        _query_dict = MongoQuery._query_dict
        field = _query_dict.get(self.name)
        if field is None:
            _query_dict[self.name] = other
        else:
            _query_dict[self.name] = (
                [*field, other]
                if isinstance(field, Iterable) and not isinstance(field, str)
                else [field, other]
            )
        return QueryCondition(_query_dict)

    def __gt__(
        self,
        other: T,
    ) -> QueryCondition:
        """Overload > operator."""
        return self == {"$gt": other}

    def __ge__(
        self,
        other: T,
    ) -> QueryCondition:
        """Overload >= operator."""
        return self == {"$gte": other}

    def __lt__(
        self,
        other: T,
    ) -> QueryCondition:
        """Overload < operator."""
        return self == {"$lt": other}

    def __le__(
        self,
        other: T,
    ) -> QueryCondition:
        """Overload <= operator."""
        return self == {"$lte": other}

    def __contains__(
        self,
        other: T,
    ) -> QueryCondition:
        """Overload in operator."""
        if not issubclass(cast(type, self.field_type), str):
            raise TypeError(
                f"Cannot check if field {self.name} contains {other} because {self.name} is not a subclass of str but {self.field_type}"
            )
        if not isinstance(other, str):
            raise ValueError("Comparison value must be a valid string.")
        return self == {"$regex": other}


def exists(
    field: Any,
) -> QueryCondition:
    """Mongo exists operator."""
    if isinstance(field, QueryField):
        return QueryCondition({field.name: {"$exists": True}})
    if isinstance(field, str):
        return QueryCondition({field: {"$exists": True}})
    raise TypeError(f"Field must be a QueryField or str, {type(field)} is not supported.")


def regex_query(
    field: Union[QueryField[str], str],
    regex: re.Pattern,
) -> QueryCondition:
    return (
        QueryCondition({field.name: {"$regex": regex.pattern}})
        if isinstance(field, QueryField)
        else QueryCondition({field: {"$regex": regex.pattern}})
    )
