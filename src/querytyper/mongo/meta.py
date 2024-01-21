"""MongoFilterMeta implementation."""
from typing import Any, Dict, Tuple, Type

from pydantic import BaseModel
from pydantic.main import ModelMetaclass

from querytyper.mongo.query import QueryField

DictStrAny = Dict[str, Any]


class MongoFilterMeta(ModelMetaclass):
    """
    Metaclass for query models.

    Use this metaclass to define query models.

    Example
    -------
    ```python
    class TransactionFilter(Transaction, metaclass=MongoFilterMeta):
        pass
    ```
    """

    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any]],
        namespace: DictStrAny,
    ) -> Type["MongoFilterMeta"]:
        """Override new class creation to set query fields as class attributes."""
        # check exactly one base class
        if len(bases) > 1:
            raise TypeError("MongoFilterMeta does not support multiple inheritance")
        if len(bases) < 1:
            raise TypeError(
                "The class with metaclass MongoFilterMeta requires a base class that inherits from BaseModel"
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
