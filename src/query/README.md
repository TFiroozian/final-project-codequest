# 🔍 Query Lambda

This AWS Lambda function handles users queries. When triggered, the Lambda:

1. Extracts a user query from the Lambda event (`queryStringParameters.query`).
2. Generates an embedding for the query using a shared `EmbeddingService`.
3. Queries an OpenSearch index to retrieve top matching documents.
4. Sends those matches to Claude via Bedrock for summarization.
5. Returns a concise markdown response back to the user.