import os
from common.aws import get_bedrock_client, get_es_client
from common.embeddings import EmbeddingService
from common.secret_manager import export_secrets_to_env


def initialize_services():
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
