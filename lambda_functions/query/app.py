import json
import os
import sys

from common.aws import get_bedrock_client, get_es_client
from common.secret_manager import export_secrets_to_env
from common.embeddings import EmbeddingService
from common.logger import setup_logger


try:
    logger = setup_logger()
    export_secrets_to_env()

    es_client = get_es_client(es_host=os.environ.get("ES_HOST"))
    bedrock_client = get_bedrock_client()

    embedding_svc = EmbeddingService(
        es_client=es_client,
        bedrock_client=bedrock_client,
        index_name=os.environ.get("ES_INDEX_NAME"),
        model_id=os.environ.get("BEDROCK_MODEL_ID"),
    )

except Exception as e:
    logger.error("Unexpected Error", extra={"error": str(e)})
    sys.exit(1)


def query_lambda_handler(event, context):
    """
    AWS Lambda entry point. Expects 'query' in the event payload to run the search.
    For example, your event JSON might look like:
    {
      "query": "How to query in bigquery and store results in Elasticsearch?"
    }
    """

    logger.debug("Starting query_lambda_handler. Event received: %s", event)

    # Extract the user query from the event
    query_params = event.get("queryStringParameters") or {}
    query_text = query_params.get("query")
    if not query_text:
        logger.warning("No 'query' text provided in the event: %s", query_params)
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No query text provided in event."}),
        }

    logger.debug("Received query: %s", query_text)

    try:
        # Generate the embeding from the query_text.
        embedding = embedding_svc.generate_embedding(text=query_text)
    except Exception as e:
        logger.error("Error generating embedding: %s", e, exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Embedding generation failed: {str(e)}"}),
        }

    try:
        # Query ES with the generated embeddings and return results
        results = embedding_svc.query_elasticsearch(query_embedding=embedding)

        hits = []
        if results and "hits" in results and "hits" in results["hits"]:
            for hit in results["hits"]["hits"]:
                hits.append(
                    {
                        "score": hit["_score"],
                        "text": hit["_source"].get("combined_text", ""),
                    }
                )
        else:
            logger.debug("No hits found in Elasticsearch results.")

        return {"statusCode": 200, "body": json.dumps({"results": hits})}

    except Exception as e:
        logger.error("Error querying Elasticsearch: %s", e, exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Elasticsearch query failed: {str(e)}"}),
        }
