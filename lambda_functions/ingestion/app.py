import json
import sys
from handler import IngestionHandler
from retrievers import StackOverflowDataRetriever
from utils import create_index_with_dense_vector


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

    ingestion_handler = IngestionHandler(embedding_svc, data_retriever)
except Exception as e:
    logger.exception("Failed to initialize dependency services", e)
    sys.exit(1)


def lambda_handler(event, context):
    try:
        return ingestion_handler.handle(event, context)

    except Exception as e:
        logger.exception("Unexpected Error", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal failure"}),
        }


if __name__ == "__main__":
    ingestion_handler.handle() 