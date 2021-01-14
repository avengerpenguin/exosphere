from __future__ import print_function
import sys

from troposphere import (
    Template,
    Ref,
    Output,
    Parameter,
    Join,
    GetAtt,
    FindInMap,
)
from troposphere.route53 import (
    RecordSetType,
    RecordSet,
    RecordSetGroup,
    AliasTarget,
    HostedZone,
)
from troposphere.s3 import (
    Bucket,
    PublicRead,
    BucketOwnerFullControl,
    WebsiteConfiguration,
    RedirectAllRequestsTo,
)

import boto3
import botocore


def update(domain, region="eu-west-2", subdomain=None):
    t = make(subdomain=subdomain)

    stack_name = domain.replace(".", "")
    if subdomain:
        stack_name = subdomain + stack_name

    client = boto3.client("cloudformation", region_name=region)

    try:
        response = client.describe_stacks(
            StackName=stack_name,
        )
    except botocore.exceptions.ClientError:
        client.create_stack(
            StackName=stack_name,
            TemplateBody=t.to_json(),
            Parameters=[
                {"ParameterKey": "HostedZoneName", "ParameterValue": domain},
            ],
            Capabilities=[
                "CAPABILITY_IAM",
            ],
        )
        waiter = client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)
        response = client.describe_stacks(
            StackName=stack_name,
        )

    try:
        client.update_stack(
            StackName=stack_name,
            TemplateBody=t.to_json(),
            Parameters=[
                {"ParameterKey": "HostedZoneName", "ParameterValue": domain},
            ],
            Capabilities=[
                "CAPABILITY_IAM",
            ],
        )
        waiter = client.get_waiter("stack_update_complete")
        waiter.wait(StackName=stack_name)
        response = client.describe_stacks(
            StackName=stack_name,
        )
    except Exception as e:
        print(e, file=sys.stderr)
        pass


def make(subdomain=None):
    t = Template()
    t.add_mapping(
        "RegionMap",
        {
            "us-east-1": {
                "S3hostedzoneID": "Z3AQBSTGFYJSTF",
                "websiteendpoint": "s3-website-us-east-1.amazonaws.com",
            },
            "us-west-1": {
                "S3hostedzoneID": "Z2F56UZL2M1ACD",
                "websiteendpoint": "s3-website-us-west-1.amazonaws.com",
            },
            "us-west-2": {
                "S3hostedzoneID": "Z3BJ6K6RIION7M",
                "websiteendpoint": "s3-website-us-west-2.amazonaws.com",
            },
            "eu-west-1": {
                "S3hostedzoneID": "Z1BKCTXD74EZPE",
                "websiteendpoint": "s3-website-eu-west-1.amazonaws.com",
            },
            "eu-west-2": {
                "S3hostedzoneID": "Z3GKZC51ZF0DB4",
                "websiteendpoint": "s3-website.eu-west-2.amazonaws.com",
            },
            "ap-southeast-1": {
                "S3hostedzoneID": "Z3O0J2DXBE1FTB",
                "websiteendpoint": "s3-website-ap-southeast-1.amazonaws.com",
            },
            "ap-southeast-2": {
                "S3hostedzoneID": "Z1WCIGYICN2BYD",
                "websiteendpoint": "s3-website-ap-southeast-2.amazonaws.com",
            },
            "ap-northeast-1": {
                "S3hostedzoneID": "Z2M4EHUR26P7ZW",
                "websiteendpoint": "s3-website-ap-northeast-1.amazonaws.com",
            },
            "sa-east-1": {
                "S3hostedzoneID": "Z31GFT0UA1I2HV",
                "websiteendpoint": "s3-website-sa-east-1.amazonaws.com",
            },
        },
    )
    hostedzone = t.add_parameter(
        Parameter(
            "HostedZoneName",
            Description="The DNS name of an existing Amazon Route 53 hosted zone",
            Type="String",
        )
    )

    if subdomain:
        t.add_resource(
            Bucket(
                "Bucket",
                BucketName=Join(".", [subdomain, Ref(hostedzone)]),
                AccessControl=PublicRead,
                WebsiteConfiguration=WebsiteConfiguration(
                    IndexDocument="index.html",
                    ErrorDocument="error.html",
                ),
            )
        )

        record = t.add_resource(
            RecordSetGroup(
                "RecordSetGroup",
                HostedZoneName=Join("", [Ref(hostedzone), "."]),
                RecordSets=[
                    RecordSet(
                        Name=Join(".", [subdomain, Ref(hostedzone)]),
                        Type="A",
                        AliasTarget=AliasTarget(
                            hostedzoneid=FindInMap(
                                "RegionMap",
                                Ref("AWS::Region"),
                                "S3hostedzoneID",
                            ),
                            dnsname=FindInMap(
                                "RegionMap",
                                Ref("AWS::Region"),
                                "websiteendpoint",
                            ),
                        ),
                    ),
                ],
            )
        )
    else:
        t.add_resource(HostedZone("HostedZone", Name=Ref(hostedzone)))
        root_bucket = t.add_resource(
            Bucket(
                "RootBucket",
                BucketName=Ref(hostedzone),
                AccessControl=PublicRead,
                WebsiteConfiguration=WebsiteConfiguration(
                    IndexDocument="index.html",
                    ErrorDocument="error.html",
                ),
            )
        )
        www_bucket = t.add_resource(
            Bucket(
                "WWWBucket",
                BucketName=Join(".", ["www", Ref(hostedzone)]),
                AccessControl=PublicRead,
                WebsiteConfiguration=WebsiteConfiguration(
                    RedirectAllRequestsTo=RedirectAllRequestsTo(
                        HostName=Ref(root_bucket)
                    )
                ),
            )
        )

        record = t.add_resource(
            RecordSetGroup(
                "RecordSetGroup",
                HostedZoneName=Join("", [Ref(hostedzone), "."]),
                RecordSets=[
                    RecordSet(
                        Name=Ref(hostedzone),
                        Type="A",
                        AliasTarget=AliasTarget(
                            hostedzoneid=FindInMap(
                                "RegionMap",
                                Ref("AWS::Region"),
                                "S3hostedzoneID",
                            ),
                            dnsname=FindInMap(
                                "RegionMap",
                                Ref("AWS::Region"),
                                "websiteendpoint",
                            ),
                        ),
                    ),
                    RecordSet(
                        Name=Join(".", ["www", Ref(hostedzone)]),
                        Type="CNAME",
                        TTL="900",
                        ResourceRecords=[
                            Join(
                                ".",
                                [
                                    "www",
                                    Ref(hostedzone),
                                    FindInMap(
                                        "RegionMap",
                                        Ref("AWS::Region"),
                                        "websiteendpoint",
                                    ),
                                ],
                            )
                        ],
                    ),
                ],
            )
        )
    return t
