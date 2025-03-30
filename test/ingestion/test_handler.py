import json
import re
from unittest.mock import MagicMock, call
import pytest
from common.embeddings import EmbeddingService
from ingestion.handler import IngestionHandler
from ingestion.retrievers import StackOverflowDataRetriever
from botocore.exceptions import ClientError


@pytest.fixture
def handler(embedding_svc, data_retriever):
    return IngestionHandler(embedding_svc, data_retriever)


@pytest.fixture
def embedding_svc():
    embedding_svc = MagicMock(spec=EmbeddingService)

    # Mock the generate_embedding method
    embedding_svc.generate_embedding.return_value = [0.1, 0.2, 0.3]

    def exsists_side_effect(doc: str):
        title_search = re.search("Title(\d+)", doc, re.IGNORECASE)
        return int(title_search.group(1)) % 2 == 0

    embedding_svc.check_if_indexed.side_effect = exsists_side_effect
    return embedding_svc


@pytest.fixture
def data_retriever():
    retriever = MagicMock(spec=StackOverflowDataRetriever)
    mock_dataframe = MagicMock()
    index = 0
    batch_size = 1

    def side_effect():
        result = [
            (
                index + i,
                {
                    "question_title": f"Title{index + 1 + i}",
                    "question_body": f"Body{index + 1 + i}",
                    "accepted_answer_body": f"Answer{index + 1 + i}",
                },
            )
            for i in range(batch_size)
        ]
        return result

    mock_dataframe.iterrows.side_effect = side_effect

    def get_dataframe_side_effect(limit, offset):
        nonlocal batch_size, index
        batch_size = limit
        index = offset
        return mock_dataframe

    retriever.get_dataframe.side_effect = get_dataframe_side_effect
    return retriever


def test_ingestion_happy(embedding_svc, data_retriever, handler):
    """
    Sucessfull test which
    Retrieves data from bigQuery.
    THEN Generates embeddings for each row.
    THEN Calls save_to_elasticsearch with the correct documents.
    """

    test_event = {"number_of_records": "10", "batch_size": "2", "records_offset": "4"}
    response = handler.handle(event=test_event, context=None)
    assert response == {"statusCode": 200, "body": json.dumps({"results": 10})}

    # calls to fetch dataframes with limits and offsets
    assert data_retriever.get_dataframe.call_args_list == [
        call(2, 4),
        call(2, 6),
        call(2, 8),
        call(2, 10),
        call(2, 12),
        call(2, 14),
        call(2, 16),
        call(2, 18),
        call(2, 20),
        call(2, 22),
    ]

    # The generate_embedding method should have been called once per each doc being indexed
    # save_to_elasticsearch method should have been called exactly once
    assert embedding_svc.generate_embedding.call_count == 10
    # 10 batches (since batch size is 2 and number of records is 10 and 1 record in each batch is already written) should be saved to the DB
    assert embedding_svc.save_to_opensearch.call_count == 10

    call_args = embedding_svc.save_to_opensearch.call_args_list

    for i in range(10):
        assert (
            call_args[i][0][0][0][0]
            == f"""\
Title: Title{2*i + 5}
Body: Body{2*i + 5}
Accepted Answer: Answer{2*i + 5}"""
        )
        assert call_args[i][0][0][0][1] == [0.1, 0.2, 0.3]


def test_ingestion_embedding_failures(embedding_svc, data_retriever, handler):

    call_count = 0

    def generate_embedding_intermittent_failures(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:
            raise ClientError(MagicMock(), "InvokeModel")
        else:
            return [0.1, 0.2, 0.3]

    embedding_svc.generate_embedding.side_effect = (
        generate_embedding_intermittent_failures
    )
    embedding_svc.check_if_indexed.side_effect = lambda *args: False

    test_event = {"number_of_records": "10", "batch_size": "10", "records_offset": "0"}
    response = handler.handle(event=test_event, context=None)
    # half of the items had successful embeddings generated for them, so we should be able to save that half
    assert response == {"statusCode": 200, "body": json.dumps({"results": 10})}

    assert data_retriever.get_dataframe.call_args_list == [
        call(10, 0),
        call(10, 10),
    ]
