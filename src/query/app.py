import json
import os
import sys

from common.init_service import initialize_services
from .handler import QueryHandler

from aws_lambda_powertools import Logger

logger = Logger()


try:
    embedding_svc, bedrock_client = initialize_services()
except Exception as e:
    logger.error("Failed to initialize dependency services", extra={"error": str(e)})
    sys.exit(1)

api_key = None
if os.getenv("AWS_SAM_LOCAL") != "true":
    api_key = os.getenv("API_KEY")


def lambda_handler(event, context):
    """
    AWS Lambda entry point. Expects 'query' in the event payload to run the search.
    For example, your event JSON might look like:
    {
      "query": "How to query in bigquery and store results in Elasticsearch?"
    }
    """
    try:
        return QueryHandler(embedding_svc, bedrock_client, api_key).handle(
            event, context
        )
    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }
