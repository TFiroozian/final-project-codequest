from aws_cdk import (
    Stack,
    RemovalPolicy,
)
from constructs import Construct
from aws_cdk.aws_iam import PolicyStatement, PolicyDocument, Effect, Role, IRole, User, Policy
from aws_cdk import (
    aws_ec2 as ec2,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretsmanager,
)
from aws_cdk import Fn, CfnOutput


class codeQuestInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "VPC", max_azs=1, nat_gateways=1, subnet_configuration=[
            ec2.SubnetConfiguration(
                name="ingress",
                cidr_mask=24,
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            ec2.SubnetConfiguration(
                name="application",
                cidr_mask=24,
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            )
        ])

        subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets

        tara_user_arn = "arn:aws:iam::186495367013:user/tara"

        security_group = ec2.SecurityGroup(self, 'SecurityGroup', vpc=vpc, allow_all_outbound=True)
        security_group.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block), ec2.Port.HTTPS, "Allow inbound HTTPS")

        # Create an OpenSearch cluster with smallest instance size avaiable to reudce the costs
        # In a real production environment i'd create a multi AZ instance with master / multiple data nodes for high availability
        opensearch_cluster = opensearch.Domain(
            self,
            "CodequestRAGDB",
            version=opensearch.EngineVersion.OPENSEARCH_2_15,
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnets=subnets)],
            capacity=opensearch.CapacityConfig(
                data_nodes=1,
                data_node_instance_type="t3.small.search",
                multi_az_with_standby_enabled=False,
            ),
            ebs=opensearch.EbsOptions(volume_size=10),
            enforce_https=True,
            removal_policy=RemovalPolicy.DESTROY,
            security_groups=[security_group],
            use_unsigned_basic_auth=True,
        )

        ingestion_role = Role.from_role_arn(self, "IngestionRole", Fn.import_value("IngestionFunctionIamRole"))
        opensearch_cluster.grant_write(ingestion_role)
        self.allow_bedrock_call(ingestion_role, "IngestionRole")

        query_role = Role.from_role_arn(self, "QueryRole", Fn.import_value("QueryFunctionIamRole"))
        opensearch_cluster.grant_read(query_role)
        self.allow_bedrock_call(query_role, "QueryRole")

        tara_user = User.from_user_arn(self, "TaraUser", tara_user_arn)
        opensearch_cluster.grant_read_write(tara_user)

        gcloud_key = secretsmanager.Secret(self, 'GCloudServiceAccountKey')
        gcloud_key.grant_read(ingestion_role)
        gcloud_key.grant_read(tara_user)

        api_key = secretsmanager.Secret(self, 'APIKey')
        api_key.grant_read(query_role)

        CfnOutput(self, "OpensearchDBEndpoint", value=opensearch_cluster.domain_endpoint, export_name="OpensearchDBEndpointURL")

    
    def allow_bedrock_call(self, role: IRole, role_name: str):
        role.attach_inline_policy(Policy(
            self,
            f"Allow{role_name}ToCallTitan",
            document=PolicyDocument(
                statements=[PolicyStatement(
                    actions=["bedrock:InvokeModel"],
                    resources=["*"],
                    effect=Effect.ALLOW
                )]
            )
        ))

