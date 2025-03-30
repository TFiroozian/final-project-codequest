import os
from urllib.parse import urlparse
import boto3
import logging
from boto3 import Session

from opensearchpy import OpenSearch, RequestsAWSV4SignerAuth, RequestsHttpConnection

logger = logging.getLogger()


def get_opensearch_client(opensearch_host: str, region: str):
    """Initialize and return an OpenSearch client."""

    logger.info("Initializing OpenSearch connection")

    url = urlparse(opensearch_host)
    service = "es"
    credentials = Session().get_credentials()
    auth = RequestsAWSV4SignerAuth(credentials, region, service)

    # Local setup: connect to Docker container without SSL
    if os.getenv("AWS_SAM_LOCAL") == "true":
        return OpenSearch(
            hosts=[{"host": "opensearch-node", "port": 9200}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    # Cloud setup: use proper auth and secure connection
    return OpenSearch(
        hosts=[{"host": url.netloc, "port": url.port or 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
    )


def get_bedrock_client():
    """
    Initialize and return a Bedrock client which
    is used to interact with Amazon Bedrock runtime APIs.
    """

    logger.info("Initializing Bedrock Client")
    return boto3.client(service_name="bedrock-runtime")
