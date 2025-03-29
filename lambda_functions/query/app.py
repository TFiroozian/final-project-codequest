import json
import os
import sys

from common.logger import setup_logger
from common.init_service import initialize_services
from handler import QueryHandler

logger = setup_logger()


try:
    embedding_svc = initialize_services()
except Exception as e:
    logger.info(f"hello {os.environ.get("ES_HOST")}")
    logger.error("Failed to initialize dependency services", extra={"error": str(e)})
    sys.exit(1)


def lambda_handler(event, context):
    """
    AWS Lambda entry point. Expects 'query' in the event payload to run the search.
    For example, your event JSON might look like:
    {
      "query": "How to query in bigquery and store results in Elasticsearch?"
    }
    """
    try:
        return QueryHandler(embedding_svc).handle(event, context)

    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }
