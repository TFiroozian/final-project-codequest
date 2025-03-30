import json
from unittest.mock import MagicMock
import pytest

from .handler import QueryHandler


@pytest.fixture
def handler(embedding_svc):
    return QueryHandler(embedding_svc)


@pytest.fixture
def embedding_svc():
    embedding_svc = MagicMock()

    # Mock the generate_embedding method
    embedding_svc.generate_embedding.return_value = [0.1, 0.2, 0.3]

    # Mock the query_elasticsearch method
    embedding_svc.query_elasticsearch.return_value = {
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "hits": [
                {
                    "_index": "test-index",
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "combined_text": "Sample text",
                        "embedding": [0.1, 0.2, 0.3],
                    },
                }
            ],
        }
    }

    return embedding_svc


def test_returns_results_from_elasticsearch(embedding_svc, handler):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    THEN the handler gets the embedding and searches for the embedding in the ES
    THEN the lambda function returns the results.
    """
    test_event = {"queryStringParameters": {"query": "Sample query text"}}

    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.query_elasticsearch.assert_called_once_with(query_embedding=[0.1, 0.2, 0.3])

    embedding_svc.generate_embedding.assert_called_once_with(text="Sample query text")

    # Assertions
    assert response["statusCode"] == 200
    assert len(body.get("results")) == 1

    assert body.get("results")[0]["text"] == "Sample text"
    assert body.get("results")[0]["score"] == 1.0


def test_missing_query_parameter_returns_400(embedding_svc, handler):
    """
    WHEN the lambda function is called when the query parameter is missing
    THEN the handler returns 400 status code
    """

    test_event = {"queryStringParameters": {}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert body["error"] == "No query text provided in event."


def test_no_results_from_elasticsearch(embedding_svc, handler):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    THEN the handler gets the embedding and searches for the embedding in the ES
    WHEN there are no matching results
    THEN the lambda function returns 200 and empty result
    """
    embedding_svc.query_elasticsearch.return_value = {
        "hits": {
            "total": {"value": 0, "relation": "eq"},
            "hits": [],
        }
    }

    test_event = {"queryStringParameters": {"query": "Non-matching query text"}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.generate_embedding.assert_called_once_with(text="Non-matching query text")
    embedding_svc.query_elasticsearch.assert_called_once()

    assert response["statusCode"] == 200
    assert body["results"] == []  # No results returned


def test_embedding_generation_failure(embedding_svc, handler):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    WHEN an exception occurs when generating emdeddings
    THEN the lambda function returns 500 and no result
    """
    embedding_svc.generate_embedding.side_effect = Exception("Embedding service error")

    test_event = {"queryStringParameters": {"query": "Sample query text"}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.generate_embedding.assert_called_once_with(text="Sample query text")

    assert response["statusCode"] == 500
    assert body["error"] == "Embedding generation failed: Embedding service error"


def test_elasticsearch_query_failure(embedding_svc, handler):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    WHEN an exception occurs when calling ES
    THEN the lambda function returns 500 and no result
    """
    embedding_svc.query_elasticsearch.side_effect = Exception("Elasticsearch query error")

    test_event = {"queryStringParameters": {"query": "Sample query text"}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.generate_embedding.assert_called_once_with(text="Sample query text")
    embedding_svc.query_elasticsearch.assert_called_once()

    assert response["statusCode"] == 500
    assert body["error"] == "Elasticsearch query failed: Elasticsearch query error"
