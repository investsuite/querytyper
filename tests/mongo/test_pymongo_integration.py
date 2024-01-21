"""Test querytyper integration with pymongo."""
import re
from typing import Any, Dict
from mongomock import MongoClient

from querytyper import MongoQuery, regex_query
from .conftest import Dummy, QueryModel


def test_integration_with_pymongo() -> None:
    """Test writing and query documents to and from MongoDB."""
    client: MongoClient[Dict[str, Any]] = MongoClient()
    collection = client.get_database("test").get_collection("test")
    doc_num = 10
    collection.insert_many(
        [
            Dummy(
                str_field=f"{i} test string",
                int_field=i,
                float_field=float(i),
                bool_field=True,
            ).dict()
            for i in range(doc_num)
        ]
    )
    # found_doc = collection.find_one(MongoQuery(QueryModel.int_field == 1)._query_dict)
    found_doc = collection.find_one(MongoQuery(QueryModel.int_field == 1))
    assert found_doc is not None
    found_dummy = Dummy(**found_doc)
    assert found_dummy.int_field == 1
    found_docs = list(collection.find(MongoQuery(regex_query(QueryModel.str_field, re.compile("test")))))
    assert len(found_docs) == doc_num