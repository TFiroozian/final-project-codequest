import json
import os
import logging
from elasticsearch.helpers import bulk


logger = logging.getLogger()


class EmbeddingService:
    """A class the provides a method to generate embeddings, and queries Elasticsearch using those embeddings."""

    def __init__(self, es_client, bedrock_client, index_name: str, model_id: str):
        """
        :param es_client: The ElasticSearch client, used to query Elasticsearch
        :param bedrock_client: The Amazon Bedrock client, used to fetch embeddings
        :param index_name: The name of the Elasticsearch index to query.
        :param model_id: The ID of the Amazon model that is used to generate embeddings.
        """
        logger.debug("Initializing EmbeddingService...")

        self.es_client = es_client
        self.bedrock_client = bedrock_client
        self.index_name = index_name
        self.model_id = model_id
        self.embedding_dimensions = os.environ.get("EMBEDDING_DIMENSIONS", 1024)

    def generate_embedding(self, text):
        """
        Generates embeddings for the given input text.

        :param text: The text to generate embedding for.
        :return: A list (or vector) of embeddings
        """

        logger.debug(f"Generating embeddings with {self.model_id} model.")

        content_type = accept = "application/json"
        payload = json.dumps({"inputText": text, "embeddingTypes": ["binary"]})

        response = self.bedrock_client.invoke_model(
            body=payload,
            modelId=self.model_id,
            accept=accept,
            contentType=content_type,
        )

        response_body = json.loads(response.get("body").read())
        return response_body["embeddingsByType"]["binary"]

    def query_elasticsearch(self, query_embedding, k=1):
        """
        Query Elasticsearch using the generated embedding with a KNN search.

        :param query_embedding: The embedding (list/array) to use as the query vector.
        :param k: Number of similar documents to retrieve.
        :return: The Elasticsearch search response.
        """

        query = {
            "size": k,
            "knn": {
                "query_vector": query_embedding,
                "field": "embedding",
                "k": k,
                "num_candidates": 100,
            },
        }

        logger.debug("Querying Elasticsearch with a KNN search.")

        response = self.es_client.search(index=self.index_name, body=query)
        return response

    def save_to_elasticsearch(self, documents):
        """
        Index a batch of documents into Elasticsearch.
        :param documents: The list of documents that we're inserting into ES index.
        """

        logger.info(f"Indexing {len(documents)} documents into Elasticsearch...")
        actions = [{"_index": self.index_name, "_source": doc} for doc in documents]

        bulk(self.es_client, actions)
        logger.info("Documents saved to Elasticsearch successfully.")
