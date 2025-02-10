
import logging


logger = logging.getLogger()

def create_index_with_dense_vector(client, index_name, dims):
    """ "Create an Elasticsearch index with a dense_vector field for embeddings"""
    mapping = {
        "mappings": {
            "properties": {
                "combined_text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                },
                "token_count": {"type": "integer"},
            }
        }
    }

    # Create the index
    if client.indices.exists(index=index_name):
        logger.info(f"Index {index_name} already exists!")
    else:
        client.indices.create(index=index_name, body=mapping)
        logger.info(f"Index {index_name} created successfully with dense_vector mapping.")
