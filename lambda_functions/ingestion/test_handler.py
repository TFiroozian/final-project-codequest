import json
from unittest.mock import MagicMock
import pytest
from .handler import IngestionHandler
from .retrievers import StackOverflowDataRetriever


@pytest.fixture
def handler(embedding_svc, data_retriever):
    return IngestionHandler(embedding_svc, data_retriever)


@pytest.fixture
def embedding_svc():
    embedding_svc = MagicMock()

    # Mock the generate_embedding method
    embedding_svc.generate_embedding.return_value = [0.1, 0.2, 0.3]
    return embedding_svc


@pytest.fixture
def data_retriever():
    retriever = MagicMock(spec=StackOverflowDataRetriever)
    # Mock get_dataframe to return a sample DataFrame
    mock_dataframe = MagicMock()
    # Make .iterrows() return two tuples: (index, row_dict)
    mock_dataframe.iterrows.return_value = [
        (0, {"question_title": "Title1", "question_body": "Body1", "accepted_answer_body": "Answer1"}),
        (1, {"question_title": "Title2", "question_body": "Body2", "accepted_answer_body": "Answer2"}),
    ]

    retriever.get_dataframe.return_value = mock_dataframe
    return retriever


def test_ingestion_runs_sucessfully(embedding_svc, data_retriever, handler):
    """
    Sucessfull test which
    Retrieves data from bigQuery.
    THEN Generates embeddings for each row.
    THEN Calls save_to_elasticsearch with the correct documents.
    """

    test_event = {"number_of_records": "2"}
    response = handler.handle(event=test_event, context=None)
    body = json.loads(response["body"])

    data_retriever.get_dataframe.assert_called_once_with(2)

    # The generate_embedding method should have been called twice (once per record) and
    # save_to_elasticsearch method should have been called exactly once
    assert embedding_svc.generate_embedding.call_count == 2
    assert embedding_svc.save_to_elasticsearch.call_count == 1

    call_args, _ = embedding_svc.save_to_elasticsearch.call_args
    assert len(call_args[0]) == 2

    # Check the structure of each document
    assert call_args[0][0]["embedding"] == [0.1, 0.2, 0.3]
    assert "Title: Title1" in call_args[0][0]["combined_text"]
    assert "Body: Body1" in call_args[0][0]["combined_text"]
    assert "Accepted Answer: Answer1" in call_args[0][0]["combined_text"]

    assert call_args[0][1]["embedding"] == [0.1, 0.2, 0.3]
    assert "Title: Title2" in call_args[0][1]["combined_text"]
    assert "Body: Body2" in call_args[0][1]["combined_text"]
    assert "Accepted Answer: Answer2" in call_args[0][1]["combined_text"]
