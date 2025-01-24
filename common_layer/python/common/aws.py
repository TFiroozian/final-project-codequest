import boto3
from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger()


def get_es_client(es_host: str):
    """Initialize and return an Elasticsearch client."""

    logger.debug("Initializing Elasticsearch connection")
    return Elasticsearch([es_host])


def get_bedrock_client():
    """
    Initialize and return a Bedrock client.
    """
    logger.debug("Initializing Bedrock Client")
    return boto3.client(service_name="bedrock-runtime")
