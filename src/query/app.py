import json
import os
import sys

from common.init_service import initialize_services
from .handler import QueryHandler

from aws_lambda_powertools import Logger

logger = Logger()


def lambda_handler(event, context):
    logger.info("Initializing!")
    try:
        embedding_svc = initialize_services()
    except Exception as e:
        logger.info(f"hello {os.environ.get("ES_HOST")}")
        logger.error("Failed to initialize dependency services", extra={"error": str(e)})
        sys.exit(1)

    """
    AWS Lambda entry point. Expects 'query' in the event payload to run the search.
    For example, your event JSON might look like:
    {
      "query": "How to query in bigquery and store results in Elasticsearch?"
    }
    """
    logger.info("Started handler!")
    try:
        return QueryHandler(embedding_svc).handle(event, context)

    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }
