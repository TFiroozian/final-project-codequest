import json
import logging


logger = logging.getLogger()


class QueryHandler:
    def __init__(self, embedding_svc):
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

        logger.debug("Received query: %s", query_text)

        try:
            # Generate the embeding from the query_text.
            embedding = self._embedding_svc.generate_embedding(text=query_text)
        except Exception as e:
            logger.error("Error generating embedding: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Embedding generation failed: {str(e)}"}),
            }

        try:
            # Query ES with the generated embeddings and return results
            results = self._embedding_svc.query_elasticsearch(query_embedding=embedding)

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
