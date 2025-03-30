import json
import sys

from google.cloud import bigquery
from aws_lambda_powertools import Logger

from .handler import IngestionHandler
from .retrievers import StackOverflowDataRetriever


from common.init_service import initialize_services


logger = Logger()

try:
    # Initialize BigQuery client using service account credentials
    credentials = StackOverflowDataRetriever._get_credentials()
    bigquery_client = bigquery.Client(
        credentials=credentials, project=credentials.project_id
    )

    # Initialize OpenSearch + Bedrock clients and the embedding service
    embedding_svc, _ = initialize_services()

    # Set up data retriever and ingestion handler
    data_retriever = StackOverflowDataRetriever(bigquery_client)
    ingestion_handler = IngestionHandler(embedding_svc, data_retriever)
except Exception as e:
    logger.exception("Failed to initialize dependency services", e)
    sys.exit(1)


def lambda_handler(event, context):
    """
    AWS Lambda entry point for handling ingestion requests.

    :param event: Lambda event payload
    :param context: Lambda runtime context
    :return: JSON response with status code
    """
    try:
        return ingestion_handler.handle(event, context)

    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }


if __name__ == "__main__":
    ingestion_handler.handle()
