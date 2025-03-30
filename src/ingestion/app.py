import json
import sys

from google.cloud import bigquery
from aws_lambda_powertools import Logger

from .handler import IngestionHandler
from .retrievers import StackOverflowDataRetriever


from common.init_service import initialize_services


logger = Logger()

try:
    credentials = StackOverflowDataRetriever._get_credentials()
    bigquery_client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id
    )
    embedding_svc, _ = initialize_services()
    data_retriever = StackOverflowDataRetriever(bigquery_client)
    ingestion_handler = IngestionHandler(embedding_svc, data_retriever)
except Exception as e:
    logger.exception("Failed to initialize dependency services", e)
    sys.exit(1)


def lambda_handler(event, context):
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