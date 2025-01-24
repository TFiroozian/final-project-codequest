import logging
import os
from google.cloud import bigquery

os.environ["GOOGLE_CLOUD_PROJECT"] = "final-school-project-444820"

logger = logging.getLogger()


class StackOverflowDataRetriever:
    """
    A class to fetch Stack Overflow data from the bigquery-public-data.stackoverflow dataset.
    """

    def __init__(self):
        """
        Initializes the BigQuery client using the specified Google Cloud project ID.
        """
        self.client = bigquery.Client()

    def get_dataframe(self, number_of_records: int = 100):
        """
        This function joins the posts_questions and posts_answers tables and retrieves the first number_of_records records of
        questions along with their corresponding accepted answers.

        :return: A pandas DataFrame containing questions and their accepted answers.
        """
        query = f"""
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
            LIMIT {number_of_records}
        """
        query_job = self.client.query(query)
        result_df = query_job.to_dataframe()
        return result_df


def create_index_with_dense_vector(client, index_name, dims):
    """ "Create an Elasticsearch index with a dense_vector field for embeddings"""
    mapping = {
        "mappings": {
            "properties": {
                "combined_text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                },
                "token_count": {"type": "integer"},
            }
        }
    }

    # Create the index
    if client.indices.exists(index=index_name):
        logger.info(f"Index {index_name} already exists!")
    else:
        client.indices.create(index=index_name, body=mapping)
        logger.info(
            f"Index {index_name} created successfully with dense_vector mapping."
        )
