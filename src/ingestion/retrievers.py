import json
import os
from google.cloud import bigquery
from google.oauth2 import service_account


from aws_lambda_powertools import Logger

logger = Logger()


class StackOverflowDataRetriever:
    """
    A class to fetch Stack Overflow data from the bigquery-public-data.stackoverflow dataset.
    """

    def __init__(self, bigquery_client: bigquery.Client):
        """
        Initialize the retriever with an authenticated BigQuery client.
        :param bigquery_client: Authenticated BigQuery client instance.
        """
        self._bigquery_client = bigquery_client

    def get_dataframe(self, number_of_records: int = 100, offset: int | None = None):
        """
        This function joins the posts_questions and posts_answers tables and retrieves the first number_of_records records of
        questions along with their corresponding accepted answers.

        :param number_of_records: Number of rows to return (default: 100)
        :param offset: Optional offset for pagination
        :return: pandas DataFrame with columns: question_title, question_body, accepted_answer_body
        """

        query = f"""\
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
LIMIT {number_of_records}\
"""
        if offset:
            query += f"\nOFFSET {offset}"

        query_job = self._bigquery_client.query(query)
        result_df = query_job.to_dataframe()
        return result_df

    @staticmethod
    def _get_credentials():
        """
        Load Google Cloud service account credentials either from file or inlined secret.

        :return: Credentials object for Google BigQuery client
        :raises ValueError: If neither key path nor content is provided
        """

        key_path = os.getenv("SERVICE_ACCOUNT_KEY_PATH")
        key_content = os.getenv("SERVICE_ACCOUNT_KEY")
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        if key_path:
            return service_account.Credentials.from_service_account_file(
                key_path,
                scopes=scopes,
            )
        elif key_content:
            return service_account.Credentials.from_service_account_info(
                json.loads(key_content),
                scopes=scopes,
            )
        else:
            raise ValueError("Service account credentials unavailable")
