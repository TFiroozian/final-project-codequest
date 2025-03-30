import json
from aws_lambda_powertools import Logger

from common.embeddings import EmbeddingService

logger = Logger()

class QueryHandler:
    def __init__(self, embedding_svc: EmbeddingService):
        self._embedding_svc = embedding_svc

    def handle(self, event, context):
        logger.debug("Starting QueryHandler. Event received: %s", event)

        # Extract the user query from the event
        query_params = event.get("queryStringParameters") or {}
        query_text = query_params.get("query")
        if not query_text:
            logger.warning("No 'query' text provided in the event: %s", query_params)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No query text provided in event."}),
            }

        logger.info("Query recieved, generating embedding!")

        try:
            # Generate the embeding from the query_text.
            embedding = self._embedding_svc.generate_embedding(text=query_text)
        except Exception as e:
            logger.error("Error generating embedding: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Embedding generation failed: {str(e)}"}),
            }

        logger.info("generated embedding, querying for the hits!")

        try:
            # Query ES with the generated embeddings and return results
            hits = self._embedding_svc.query_opensearch(query=embedding)

            if not hits:
                logger.warning("No hits found in Opensearch results.")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": f"No matches found"}),
                }
            
            logger.info(f"{len(hits)} found! Returning results!")

            results = [
                {
                    "score": hit["_score"],
                    "text": hit["_source"].get("text", ""),
                } for hit in hits
            ]

            return {"statusCode": 200, "body": json.dumps({"results": results})}

        except Exception as e:
            logger.error("Error querying Opensearch: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Opensearch query failed: {str(e)}"}),
            }
