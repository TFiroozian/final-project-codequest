import os
from common.aws import get_bedrock_client, get_es_client
from common.embeddings import EmbeddingService
from common.secret_manager import export_secrets_to_env


def initialize_services() -> EmbeddingService:
    """
    Initialize and set up all necessary connections and services for the Lambda function.

    This function is invoked once when the Lambda starts. It performs the following tasks:
    - Exports secrets to environment variables.
    - Establishes a connection to Elasticsearch using the provided ES_HOST.
    - Initializes the Bedrock client.
    - Creates an instance of the EmbeddingService with the configured clients and environment variables.

    Returns:
        EmbeddingService: An instance of the EmbeddingService configured with Elasticsearch and Bedrock clients.
    """

    export_secrets_to_env()

    es_client = get_es_client(es_host=os.environ.get("ES_HOST"))
    bedrock_client = get_bedrock_client()

    embedding_svc = EmbeddingService(
        es_client=es_client,
        bedrock_client=bedrock_client,
        index_name=os.environ.get("ES_INDEX_NAME"),
        model_id=os.environ.get("BEDROCK_MODEL_ID"),
    )

    return embedding_svc
