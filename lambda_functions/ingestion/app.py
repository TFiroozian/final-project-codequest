import os
import sys
from google.cloud import bigquery
from botocore.exceptions import ClientError
from libraries import (
    StackOverflowDataRetriever,
    create_index_with_dense_vector,
)


from common.secret_manager import export_secrets_to_env
from common.logger import setup_logger
from common.embeddings import EmbeddingService
from common.aws import get_bedrock_client, get_es_client


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

    # In a real production application, I would move this step into a separate
    # migration or setup job prior to ingestion. It's included here for simplicity.
    create_index_with_dense_vector(
        es_client, embedding_svc.index_name, embedding_svc.embedding_dimensions
    )

    data_retriever = StackOverflowDataRetriever()

except Exception as e:
    logger.error("Unexpected Error", extra={"error": str(e)})
    sys.exit(1)


def query_lambda_handler(event, context):
    es_documents = []
    data = data_retriever.get_dataframe()
    for _, row in data.iterrows():
        question_title = row["question_title"]
        question_body = row["question_body"]
        accepted_answer = row["accepted_answer_body"]

        combined_text = f"Title: {question_title}\nBody: {question_body}\nAccepted Answer: {accepted_answer}"
        try:
            embedding = embedding_svc.generate_embedding(text=combined_text)

            # Create Elasticsearch document
            es_documents.append(
                {"embedding": embedding, "combined_text": combined_text}
            )
        except ClientError as e:
            logger.error(f"Error generating embedding", extra={"error": e})
            continue

    # Save documents to Elasticsearch
    embedding_svc.save_to_elasticsearch(es_documents)
    logger.info(f"Processed and saved {len(es_documents)} documents to Elasticsearch.")
