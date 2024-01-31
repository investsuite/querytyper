"""MongoQuery implementation."""
import re
from collections.abc import Iterable
from collections import UserDict
from typing import Any, Dict, Generic, Type, TypeVar, Union, cast

T = TypeVar("T")
DictStrAny = Dict[str, Any]

class _BaseQuery(UserDict):

    def __init__(self, *args: Any) -> None:
        """
        Initialize a query object.
        """
        if not len(args) == 1:
            raise TypeError(
                f"The initializer takes 1 positional argument but {len(args)} were given."
            )
        arg = args[0]
        if not isinstance(arg, (dict, bool)):
            raise TypeError(
                    f"The initializer argument must be a dictionary like object, {type(arg)} is not supported."
                )
        if isinstance(arg, dict):
            super().__init__(arg)
        else:
            arg
    
    @property # type: ignore[misc]
    def __class__(self) -> Type[dict]: # type: ignore[override]
        """Return true if isinstance(self, dict)."""
        return dict

class MongoQuery(_BaseQuery):
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

    def __or__(
        self,
        other: "MongoQuery",
    ) -> "MongoQuery":
        """Overload | operator."""
        return MongoQuery({"$or": [self, other]})


class QueryCondition(_BaseQuery):
    """Class to represent a single query condition."""

    def __and__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            self.update(other)
        return self

    def __rand__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            self.update(other)
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
        self._query_dict: DictStrAny = {}

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
        field = self._query_dict.get(self.name)
        if field is None:
            self._query_dict[self.name] = other
        else:
            self._query_dict[self.name] = (
                [*field, other]
                if isinstance(field, Iterable) and not isinstance(field, str)
                else [field, other]
            )
        return QueryCondition(self._query_dict)

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
        # return False


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
