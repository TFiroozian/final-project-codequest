import boto3
from elasticsearch import Elasticsearch
import logging
import os

logger = logging.getLogger()


def get_es_client(es_host: str):
    """Initialize and return an Elasticsearch client."""

    logger.debug("Initializing Elasticsearch connection")

    # TODO: Add back after enabling fine grained auth
    # region = os.getenv("AWS_REGION", "us-east-1")
    # service = 'es'
    # credentials = boto3.Session().get_credentials()
    # aws_auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    return Elasticsearch([es_host])


def get_bedrock_client():
    """
    Initialize and return a Bedrock client.
    """
    logger.debug("Initializing Bedrock Client")
    return boto3.client(service_name="bedrock-runtime")
