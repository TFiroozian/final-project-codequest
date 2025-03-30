import json
from aws_lambda_powertools import Logger

from common.embeddings import EmbeddingService

logger = Logger()

class QueryHandler:
    def __init__(self, embedding_svc: EmbeddingService, bedrock_client):
        self._embedding_svc = embedding_svc
        self._bedrock_client = bedrock_client


    def _render_response(self, query: str, matched_docs: list[str]) -> str:

        system_prompt = """
        You're helping a developer to be more productive. You're given the developer query and a list of answers 
        found for the question on the internet. Given the most relevant matches, you need to provide a useful answer
        to the user. You're answer MUST be a valid markdown. Put the valid markdown inside <markdown> XML tag and keep anything
        else, including your thought outside of the XML tag. You're answer should not be very long. Keep it short and consise. 
        """

        matches = "\n".join([f"""
<match_{i}>
{match}
</match_{i}>
""" for i, match in enumerate(matched_docs)])

        prompt = f"""\
<user_query>
{query}
</user_query>

{matches}
"""

        temperature = 0.5
        inference_config = {"temperature": temperature}

        messages = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]
        system_prompts = [{"text": system_prompt}]

        converse_args = {
            "modelId": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "messages": messages,
            "system": system_prompts,
            "inferenceConfig": inference_config,
        }

        logger.info("Calling sonnet3.5 v2 to summarize findings", extra=converse_args)
        response = self._bedrock_client.converse(**converse_args)

        output_message = response['output']['message']

        result = "\n".join([content["text"] for content in output_message["content"]])
        start_tag = "<markdown>"
        end_tag = "</markdown>"
        if start_tag in result and end_tag in result:
            return result[result.find(start_tag) + len(start_tag): result.rfind(end_tag)]
        return result
    

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
            hits = self._embedding_svc.query_opensearch(query=embedding, k=5)

            if not hits:
                logger.warning("No hits found in Opensearch results.")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": f"No matches found"}),
                }
            
            logger.info(f"{len(hits)} found! Returning results!")
            matches = [hit["_source"].get("text", "") for hit in hits]
            rendered_response = self._render_response(query_text, matches)

            return {"statusCode": 200, "body": json.dumps({"markdown": rendered_response})}

        except Exception as e:
            logger.error("Error querying Opensearch: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Opensearch query failed: {str(e)}"}),
            }
