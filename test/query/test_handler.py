import json
from unittest.mock import MagicMock
import pytest

from query.handler import QueryHandler


@pytest.fixture
def handler(embedding_svc, bedrock_client):
    return QueryHandler(embedding_svc, bedrock_client)


@pytest.fixture
def bedrock_client():
    bedrock_client = MagicMock()
    bedrock_client.converse.return_value = {
        "output": {
            "message": {
                "role": "user",
                "content": [{"text": "<markdown>here's the result: `print('foo-bar')`</markdown>"}]
            }
        }
    }
    return bedrock_client


@pytest.fixture
def embedding_svc():
    embedding_svc = MagicMock()

    # Mock the generate_embedding method
    embedding_svc.generate_embedding.return_value = [0.1, 0.2, 0.3]

    # Mock the query_elasticsearch method
    embedding_svc.query_opensearch.return_value = [
        {
            "_index": "test-index",
            "_id": i,
            "_score": 1.0,
            "_source": {
                "text": f"Sample text{i}",
                "embedding": [0.1, 0.2, 0.3],
            },
        }
        for i in range(5)
    ]

    return embedding_svc


def test_returns_results_from_elasticsearch(embedding_svc, handler, bedrock_client):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    THEN the handler gets the embedding and searches for the embedding in the ES
    THEN summarizes the result by calling LLM model
    THEN the lambda function returns the results.
    """
    test_event = {"queryStringParameters": {"query": "Sample query text"}}

    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.query_opensearch.assert_called_once_with(query=[0.1, 0.2, 0.3], k=5)

    embedding_svc.generate_embedding.assert_called_once_with(text="Sample query text")

    # validate LLM call is rendered successfully
    bedrock_client.converse.assert_called_once_with(
        modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0', 
        messages=[{'role': 'user', 'content': [{'text': '<user_query>\nSample query text\n</user_query>\n\n\n<match_0>\nSample text0\n</match_0>\n\n\n<match_1>\nSample text1\n</match_1>\n\n\n<match_2>\nSample text2\n</match_2>\n\n\n<match_3>\nSample text3\n</match_3>\n\n\n<match_4>\nSample text4\n</match_4>\n\n'}]}], 
        system=[{'text': "\n        You're helping a developer to be more productive. You're given the developer query and a list of answers \n        found for the question on the internet. Given the most relevant matches, you need to provide a useful answer\n        to the user. You're answer MUST be a valid markdown. Put the valid markdown inside <markdown> XML tag and keep anything\n        else, including your thought outside of the XML tag. You're answer should not be very long. Keep it short and consise. \n        "}], 
        inferenceConfig={'temperature': 0.5}
    )

    # Assertions
    assert response["statusCode"] == 200
    assert body["markdown"] == "here's the result: `print('foo-bar')`"


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
    THEN the lambda function returns 404 and appropriate error 
    """
    embedding_svc.query_opensearch.return_value = []
    test_event = {"queryStringParameters": {"query": "Non-matching query text"}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.generate_embedding.assert_called_once_with(text="Non-matching query text")
    embedding_svc.query_opensearch.assert_called_once()

    assert response["statusCode"] == 404
    assert body["error"] == 'No matches found'


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


def test_opensearch_query_failure(embedding_svc, handler):
    """
    GIVEN a valid search query
    WHEN the lambda function is called with the query string
    WHEN an exception occurs when calling ES
    THEN the lambda function returns 500 and no result
    """
    embedding_svc.query_opensearch.side_effect = Exception("Opensearch query error")

    test_event = {"queryStringParameters": {"query": "Sample query text"}}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    embedding_svc.generate_embedding.assert_called_once_with(text="Sample query text")
    embedding_svc.query_opensearch.assert_called_once()

    assert response["statusCode"] == 500
    assert body["error"] == "Opensearch query failed: Opensearch query error"
