import os
import json
import boto3
from dotenv import load_dotenv
import logging


logger = logging.getLogger()


def export_secrets_to_env(secret_name: str = None):
    """
    Exports secrets as environmnet variables within the current Lambda runtime.

    If the Lambda is running locally it loads the variables from .env file otherwise,
    it fetchs secrets from AWS Secrets Manager

    :param secret_name: The name or ARN of the secret to retrieve from AWS Secrets Manager.
    """
    # Check if running locally
    if os.getenv("AWS_SAM_LOCAL") == "true":
        logger.info("Running locally. Loading variables from .env...")
        load_dotenv()

    elif secret_name:

        secrets_manager_client = boto3.client("secretsmanager")
        logger.debug("Retrieving secrets for %s from AWS Secrets Manager.", secret_name)

        response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString", None)

        if secret_string is None:
            logger.error("No SecretString found for secret: %s", secret_name)
            return

        secret_dict = json.loads(secret_string)

        for key, value in secret_dict.items():
            os.environ[key] = str(value)
            logger.debug("Set environment variable %s to %s", key, value)
