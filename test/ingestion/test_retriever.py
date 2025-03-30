from unittest.mock import MagicMock
import pytest

from ingestion.retrievers import StackOverflowDataRetriever


@pytest.fixture
def bigquery_client():
    return MagicMock()


@pytest.fixture
def stackoverflow_retriever(bigquery_client):
    return StackOverflowDataRetriever(bigquery_client)


def test_get_dataframe(bigquery_client, stackoverflow_retriever):
    stackoverflow_retriever.get_dataframe(50)
    bigquery_client.query.assert_called_once_with(
        f"""\
WITH accepted_answers AS (
    SELECT
        q.id AS question_id,
        q.title AS question_title,
        q.body AS question_body,
        q.accepted_answer_id,
        a.body AS accepted_answer_body
    FROM
        `bigquery-public-data.stackoverflow.posts_questions` q
    LEFT JOIN
        `bigquery-public-data.stackoverflow.posts_answers` a
    ON
        q.accepted_answer_id = a.id
    WHERE
        q.accepted_answer_id IS NOT NULL
)
SELECT * FROM accepted_answers
LIMIT 50\
"""
    )


def test_get_dataframe_with_offset(bigquery_client, stackoverflow_retriever):
    stackoverflow_retriever.get_dataframe(50, 10)
    bigquery_client.query.assert_called_once_with(
        f"""\
WITH accepted_answers AS (
    SELECT
        q.id AS question_id,
        q.title AS question_title,
        q.body AS question_body,
        q.accepted_answer_id,
        a.body AS accepted_answer_body
    FROM
        `bigquery-public-data.stackoverflow.posts_questions` q
    LEFT JOIN
        `bigquery-public-data.stackoverflow.posts_answers` a
    ON
        q.accepted_answer_id = a.id
    WHERE
        q.accepted_answer_id IS NOT NULL
)
SELECT * FROM accepted_answers
LIMIT 50
OFFSET 10\
"""
    )
