import json
import hashlib
import os
from typing import Iterable
from opensearchpy import OpenSearch
from opensearchpy import helpers

from aws_lambda_powertools import Logger

logger = Logger()


class EmbeddingService:
    """A class the provides a method to generate embeddings, and queries Elasticsearch using those embeddings."""

    def __init__(self, opensearch_client: OpenSearch, bedrock_client, index_name: str, model_id: str):
        """
        :param es_client: The ElasticSearch client, used to query Elasticsearch
        :param bedrock_client: The Amazon Bedrock client, used to fetch embeddings
        :param index_name: The name of the Elasticsearch index to query.
        :param model_id: The ID of the Amazon model that is used to generate embeddings.
        """
        logger.info("Initializing EmbeddingService...")

        self._opensearch_client = opensearch_client
        self._bedrock_client = bedrock_client
        self._index_name = index_name
        self._model_id = model_id
        self._embedding_dimensions = os.environ.get("EMBEDDING_DIMENSIONS", 1024)

    def _create_if_not_exit(self):
        if not self._opensearch_client.indices.exists(self._index_name):
            logger.info(f"Creating {self._index_name} index!")
            self._opensearch_client.indices.create(
                self._index_name,
                body={
                    "settings": {"index.knn": True},
                    "mappings": {
                        "properties": {
                            "embedding": {"type": "knn_vector", "dimension": self._embedding_dimensions},
                        }
                    },
                },
            )

    def generate_embedding(self, text) -> list[float]:
        """
        Generates embeddings for the given input text.

        :param text: The text to generate embedding for.
        :return: A list (or vector) of embeddings
        """
        logger.debug(f"Generating embeddings with {self._model_id} model.")

        content_type = accept = "application/json"
        payload = json.dumps({"inputText": text, "dimensions": self._embedding_dimensions, "normalize": True})

        response = self._bedrock_client.invoke_model(
            body=payload,
            modelId=self._model_id,
            accept=accept,
            contentType=content_type,
        )
        response_body = json.loads(response.get("body").read())
        logger.debug("Generated embedding", extra={
            "embedding": response_body
        })
        return response_body["embedding"]

    def query_opensearch(self, query: list[float], k: int=1):
        """
        Query Elasticsearch using the generated embedding with a KNN search.

        :param query_embedding: The embedding (list/array) to use as the query vector.
        :param k: Number of similar documents to retrieve.
        :return: The Elasticsearch search response.
        """

        self._create_if_not_exit()

        search_query = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query, 
                        "k": k
                    }
                }
            }
        }

        logger.info("Querying Elasticsearch with a KNN search.")

        results = self._opensearch_client.search(index=self._index_name, body=search_query)
        return results["hits"]["hits"]


    def check_if_indexed(self, content: str) -> bool:
        document_id = hashlib.sha256(content.encode()).hexdigest()
        return self._opensearch_client.exists(self._index_name, document_id)


    def save_to_opensearch(self, documents: Iterable[tuple[str, list[float]]]):
        """
        Index a batch of documents into Elasticsearch.
        :param documents: The list of documents that we're inserting into ES index.
        """
        self._create_if_not_exit()
        vectors = [

            {
            "_index": self._index_name,
            "_id": hashlib.sha256(text.encode()).hexdigest(),
            "embedding": vector,
            "text": text,
        } for text, vector in documents]
        logger.info(f"Indexing {len(vectors)} documents into OpenSearch...")

        helpers.bulk(self._opensearch_client, vectors)
        self._opensearch_client.indices.refresh(index=self._index_name)

        logger.info("Documents saved to Elasticsearch successfully.")
