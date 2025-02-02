from aws_cdk import (
    Stack,
    RemovalPolicy,
)
from constructs import Construct
from aws_cdk.aws_opensearchservice import Domain
from aws_cdk import (
    aws_ec2 as ec2,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretsmanager,
)


class codeQuestInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get default VPC
        default_vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)
        # TODO: update this to use private subnets later

        subnet = default_vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets[0]

        # Create an OpenSearch cluster with smallest instance size avaiable to reudce the costs
        # In a real production environment i'd create a multi AZ instance with master / multiple data nodes for high availability
        opensearch_cluster = opensearch.Domain(
            self,
            "CodequestOpenSearch",
            version=opensearch.EngineVersion.OPENSEARCH_2_15,
            vpc=default_vpc,
            vpc_subnets=[ec2.SubnetSelection(subnets=[subnet])],
            capacity=opensearch.CapacityConfig(
                data_nodes=1,
                data_node_instance_type="t3.small.search",
                multi_az_with_standby_enabled=False,
            ),
            ebs=opensearch.EbsOptions(volume_size=10),
            enforce_https=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Store cluster details in AWS Secrets Manager
        opensearch_secret = secretsmanager.Secret(
            self,
            "OpenSearchSecret",
            secret_name="codequest/opensearch/credentials",
            description="Stores OpenSearch cluster endpoint and credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=f'{{"username":"admin","endpoint":"{opensearch_cluster.domain_endpoint}"}}',
                generate_string_key="password",
                exclude_punctuation=True,
            ),
        )
