import json
import sys
from handler import IngestionHandler
from libraries import (
    StackOverflowDataRetriever,
    create_index_with_dense_vector,
)


from common.init_service import initialize_services
from common.logger import setup_logger

logger = setup_logger()


try:
    embedding_svc = initialize_services()

    # In a real production application, I would move this step into a separate
    # migration or setup job prior to ingestion. It's included here for simplicity.
    create_index_with_dense_vector(
        embedding_svc.es_client,
        embedding_svc.index_name,
        embedding_svc.embedding_dimensions,
    )

    data_retriever = StackOverflowDataRetriever()

except Exception as e:
    logger.error("Failed to initialize dependency services", extra={"error": str(e)})
    sys.exit(1)


def lambda_handler(event, context):
    try:
        embedding_svc = initialize_services()
        return IngestionHandler(embedding_svc, data_retriever).handle(event, context)

    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }
