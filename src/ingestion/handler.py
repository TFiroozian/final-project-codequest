import json
from botocore.exceptions import ClientError

from common.embeddings import EmbeddingService
from .retrievers import StackOverflowDataRetriever


from aws_lambda_powertools import Logger

logger = Logger()


class IngestionHandler:
    def __init__(
        self,
        embedding_svc: EmbeddingService,
        data_retriever: StackOverflowDataRetriever,
    ):
        self._embedding_svc = embedding_svc
        self._data_retriever = data_retriever

    def handle(self, event, *args, **kwargs):
        logger.debug("Starting IngestionHandler")
        es_documents: list[tuple[str, list[float]]] = []

        number_of_records = int(event.get("number_of_records", "1000"))
        offset = int(event.get("records_offset", "0"))
        batch_size = int(event.get("batch_size", "100"))

        limit = batch_size
        total_indexed = 0

        while total_indexed < number_of_records:
            logger.info(
                f"Fetching and processing a barch of {limit} docs from {offset}"
            )
            data = self._data_retriever.get_dataframe(limit, offset)
            for _, row in data.iterrows():
                question_title = row["question_title"]
                question_body = row["question_body"]
                accepted_answer = row["accepted_answer_body"]

                combined_text = f"Title: {question_title}\nBody: {question_body}\nAccepted Answer: {accepted_answer}"

                # skip already indexed docs as generating model for them again only incurs extra costs
                if self._embedding_svc.check_if_indexed(combined_text):
                    continue

                try:
                    embedding = self._embedding_svc.generate_embedding(
                        text=combined_text
                    )
                    es_documents.append((combined_text, embedding))
                    total_indexed += 1
                except ClientError as e:
                    logger.error(f"Error generating embedding", extra={"error": e})
                    continue
            offset += limit

            # flush collected documents so far
            if es_documents:
                logger.info(f"Flushing {len(es_documents)} documents to database!")
                self._embedding_svc.save_to_opensearch(es_documents)
                es_documents = []

            logger.info(f"{total_indexed} documents are indexed so far!")

        logger.info(
            f"Processed and saved {len(es_documents)} documents to Elasticsearch."
        )
        return {"statusCode": 200, "body": json.dumps({"results": total_indexed})}
