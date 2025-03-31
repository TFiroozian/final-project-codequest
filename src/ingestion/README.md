# 📥 Ingestion Lambda

This AWS Lambda ingests Stack Overflow Q&A data from BigQuery and indexes it into OpenSearch using embeddings. In detail it:

1. Retrieves accepted Q&A pairs from `bigquery-public-data.stackoverflow`.
2. Combines each question and answer into a document.
3. Generates an embedding for each document.
4. Indexes documents into OpenSearch if not already stored.

## Requirements

- Google Cloud BigQuery access
- Valid service account (via `SERVICE_ACCOUNT_KEY` or `SERVICE_ACCOUNT_KEY_PATH`)
- OpenSearch access
