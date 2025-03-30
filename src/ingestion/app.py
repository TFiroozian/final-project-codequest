import json
import sys
from .handler import IngestionHandler
from .retrievers import StackOverflowDataRetriever


from common.init_service import initialize_services

from aws_lambda_powertools import Logger

logger = Logger()

try:
    embedding_svc = initialize_services()
    data_retriever = StackOverflowDataRetriever()
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