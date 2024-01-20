"""MongoQuery ."""
import re
from collections.abc import Iterable
from pprint import pformat
from typing import Any, Dict, Generic, Tuple, Type, TypeVar, Union, cast

from pydantic import BaseModel
from pydantic.main import ModelMetaclass

T = TypeVar("T")
DictStrAny = Dict[str, Any]


class MongoQuery:
    """MongoQuery wrapper."""

    _dict: DictStrAny = {}

    def __init__(self, *args: Any) -> None:
        """Initialize a query object."""
        for arg in args:
            if not isinstance(arg, (QueryCondition, bool)):
                raise TypeError(
                    f"MongoQuery argument must be a QueryCondition or a boolean value, {type(arg)} is not supported."
                )
        # copy over the class _dict to the instance
        self._dict = MongoQuery._dict
        # clean up MongoQuery _dict at each instantiation
        MongoQuery._dict = {}

    def __del__(self) -> None:
        """MongoQuery destructor."""
        self._dict = {}
        MongoQuery._dict = {}

    def __repr__(self) -> str:
        """Overload repr method to pretty format it."""
        return pformat(self._dict)

    def __or__(
        self,
        other: "MongoQuery",
    ) -> "MongoQuery":
        """Overload | operator."""
        self._dict = {"$or": [self._dict, other._dict]}
        return self


class QueryCondition(DictStrAny):
    """MongoQuery condition."""

    def __init__(self, *args: Any, **kwargs: DictStrAny) -> None:
        """Overload init typing."""
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """Overload repr method to pretty format it."""
        return pformat({**self})

    def __and__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            MongoQuery._dict.update(other)
        return self

    def __rand__(
        self,
        other: Union["QueryCondition", bool],
    ) -> "QueryCondition":
        """Overload & operator."""
        if isinstance(other, QueryCondition):
            MongoQuery._dict.update(other)
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
        _dict = MongoQuery._dict
        field = _dict.get(self.name)
        if field is None:
            _dict[self.name] = other
        else:
            _dict[self.name] = (
                [*field, other]
                if isinstance(field, Iterable) and not isinstance(field, str)
                else [field, other]
            )
        return QueryCondition(_dict)

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
    regex: re.Pattern[str],
) -> QueryCondition:
    if isinstance(field, QueryField):
        return QueryCondition({field.name: {"$regex": regex.pattern}})
    return QueryCondition({field: {"$regex": regex.pattern}})


class MongoModelMetaclass(ModelMetaclass):
    """
    Metaclass for query models.

    Use this metaclass to define query models.

    Example
    -------
    ```python
    class TransactionFilter(Transaction, metaclass=MongoModelMetaclass):
        pass
    ```
    """

    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any]],
        namespace: DictStrAny,
    ) -> Type["MongoModelMetaclass"]:
        """Override new class creation to set query fields as class attributes."""
        # check exactly one base class
        if len(bases) > 1:
            raise TypeError("MongoModelMetaclass does not support multiple inheritance")
        if len(bases) < 1:
            raise TypeError(
                "The class with metaclass MongoModelMetaclass requires a base class that inherits from BaseModel"
            )
        # check the base class is a subclass of BaseModel
        if not issubclass(bases[0], BaseModel):
            raise TypeError(f"The base class must inherit from {BaseModel.__qualname__}")
        base_model_cls: Type[BaseModel] = super().__new__(cls, name, bases, namespace)
        for field_name, model_field in base_model_cls.__fields__.items():
            setattr(
                cls,
                field_name,
                QueryField[model_field.type_](  # type: ignore[name-defined]
                    name=field_name,
                    field_type=model_field.type_,
                ),
            )
        return cls
