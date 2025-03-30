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

        number_of_records = int(event.get("number_of_records", "100"))
        data = self._data_retriever.get_dataframe(number_of_records)
        for _, row in data.iterrows():
            question_title = row["question_title"]
            question_body = row["question_body"]
            accepted_answer = row["accepted_answer_body"]

            combined_text = f"Title: {question_title}\nBody: {question_body}\nAccepted Answer: {accepted_answer}"
            try:
                embedding = self._embedding_svc.generate_embedding(text=combined_text)

                # Create Elasticsearch document
                es_documents.append((combined_text, embedding))
            except ClientError as e:
                logger.error(f"Error generating embedding", extra={"error": e})
                continue

        # Save documents to Elasticsearch
        self._embedding_svc.save_to_opensearch(es_documents)
        logger.info(f"Processed and saved {len(es_documents)} documents to Elasticsearch.")
        return {"statusCode": 200, "body": json.dumps({"results": len(es_documents)})}

