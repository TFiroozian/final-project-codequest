import json
import logging
from botocore.exceptions import ClientError
from retrievers import StackOverflowDataRetriever


logger = logging.getLogger()


class IngestionHandler:
    def __init__(
        self,
        embedding_svc,
        data_retriever: StackOverflowDataRetriever,
    ):
        self._embedding_svc = embedding_svc
        self._data_retriever = data_retriever

    def handle(self, event, *args, **kwargs):
        logger.debug("Starting IngestionHandler")
        es_documents = []

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
                es_documents.append({"embedding": embedding, "combined_text": combined_text})
            except ClientError as e:
                logger.error(f"Error generating embedding", extra={"error": e})
                continue

        # Save documents to Elasticsearch
        self._embedding_svc.save_to_elasticsearch(es_documents)
        logger.info(f"Processed and saved {len(es_documents)} documents to Elasticsearch.")
        return {"statusCode": 200, "body": json.dumps({"results": len(es_documents)})}

