from aws_cdk import (
    Stack,
    RemovalPolicy,
)
from constructs import Construct
from aws_cdk.aws_opensearchservice import Domain, AdvancedSecurityOptions
from aws_cdk.aws_iam import PolicyStatement, Effect, Role, ArnPrincipal, User
from aws_cdk import (
    aws_ec2 as ec2,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretsmanager,
)
from aws_cdk import Fn, CfnOutput


class codeQuestInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get default VPC
        default_vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)
        # TODO: update this to use private subnets later

        subnet = default_vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets[0]

        tara_user_arn = "arn:aws:iam::186495367013:user/tara"

        security_group = ec2.SecurityGroup(self, 'SecurityGroup', vpc=default_vpc, allow_all_outbound=True)
        security_group.add_ingress_rule(ec2.Peer.ipv4(default_vpc.vpc_cidr_block), ec2.Port.HTTPS, "Allow inbound HTTPS")

        # Create an OpenSearch cluster with smallest instance size avaiable to reudce the costs
        # In a real production environment i'd create a multi AZ instance with master / multiple data nodes for high availability
        opensearch_cluster = opensearch.Domain(
            self,
            "CodequestRAG",
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
            security_groups=[security_group],
            # TODO: Re-enable fine grained auth
            #fine_grained_access_control=AdvancedSecurityOptions(
            #    master_user_arn=tara_user_arn,
            #),
            #node_to_node_encryption=True,
            #encryption_at_rest=opensearch.EncryptionAtRestOptions(
            #    enabled=True
            #),
        )

        ingestion_role = Role.from_role_arn(self, "IngestionRole", Fn.import_value("IngestionFunctionIamRole"))
        opensearch_cluster.grant_write(ingestion_role)

        query_role = Role.from_role_arn(self, "QueryRole", Fn.import_value("QueryFunctionIamRole"))
        opensearch_cluster.grant_read(query_role)

        tara_user = User.from_user_arn(self, "TaraUser", tara_user_arn)
        opensearch_cluster.grant_read_write(tara_user)

        gcloud_key = secretsmanager.Secret(self, 'GCloudServiceAccountKey')
        gcloud_key.grant_read(ingestion_role)
        gcloud_key.grant_read(tara_user)

        CfnOutput(self, "OpensearchEndpoint", value=opensearch_cluster.domain_endpoint, export_name="OpensearchEndpointURL")
