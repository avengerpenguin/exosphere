import boto3
import botocore
import sys

from exosphere.stacks import static_site
from troposphere import (
    Parameter,
    Output,
    Ref,
    Join,
    GetAtt,
    Condition,
    s3,
    iam,
    awslambda,
)
from awacs import aws


def make():
    t = static_site.make()

    from_address = t.add_parameter(
        Parameter(
            "FromAddress",
            Description="The verified SES email address to send from",
            Type="String",
        )
    )
    forwarding_addresses = t.add_parameter(
        Parameter(
            "ForwardingAddresses",
            Description="The destination addresses to forward the email to",
            Type="CommaDelimitedList",
        )
    )

    function = t.add_resource(
        awslambda.Function(
            "SESACMForwarderLambda",
            Description="Function for forwarding mail from S3 buckets",
            Handler="index.handler",
            Timeout=60,
            MemorySize=128,
            Role=GetAtt("LambdaSESACMForwarderRole", "Arn"),
            Runtime="python2.7",
            Environment=awslambda.Environment(
                Variables={
                    "FromAddress": Ref(from_address),
                    "ForwardingAddresses": Join(
                        ",", Ref(forwarding_addresses)
                    ),
                }
            ),
            Code=awslambda.Code(
                ZipFile=r'''# coding: utf-8
import boto3
import email
import json
import logging
import os
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(event, context):
    logger.info("Collecting event record data...")
    record = event["Records"][0]
    try:
        logger.info("Looking for SES event...")
        bucket_name =  record["s3"]["bucket"]["name"]
        message_id =  record["s3"]["object"]["key"]
    except KeyError:
        logger.critical("There was a problem retrieving data "
                        "from the event record, {}".format(record))
        return("FAIL")

    s3_client = boto3.client('s3')
    logger.info("Fetching s3 object: {}/{}".format(bucket_name, message_id))
    mail_object = s3_client.get_object(Bucket = bucket_name, Key = message_id)
    logger.info("Decoding mail body...")
    email_data = mail_object["Body"].read().decode('utf-8')
    email_object = email.message_from_string(email_data)

    # Get env variables
    # We need to use a verified email address rather than relying on the source
    logger.info("Retrieving environment settings...")
    email_from = os.environ['FromAddress']
    forwarding_addresses = [address.strip() for address in os.environ['ForwardingAddresses'].split(",")]

    if 'From' in email_object:
        email_object['X-Original-From'] = email_object['From']
        del email_object['From']

    if 'Return-Path' in email_object:
        email_object['X-Original-Return-Path'] = email_object['Return-Path']
        del email_object['Return-Path']

    email_object['From'] = email_from

    logger.info("Connecting to SES client")
    ses_client = boto3.client('ses', region_name='eu-west-1')
    logger.debug('Destinations:' + '; '.join([
            'To: ' + address for address in forwarding_addresses
        ]))
    logger.debug('Message: ' + email_object.as_string())
    response = ses_client.send_raw_email(
        Destinations=forwarding_addresses,
        #Source=email_from,
        RawMessage={
            'Data': email_object.as_string()
        },
    )
    logger.info("Sent verification email successfully to {}".format(','.join(forwarding_addresses)))

    return "CONTINUE"'''
            ),
        )
    )

    bucket = t.add_resource(
        s3.Bucket(
            "SESACMS3Bucket",
            DependsOn="InvokePermission",
            BucketName=Join(".", ["mail", Ref("HostedZoneName")]),
            LifecycleConfiguration=s3.LifecycleConfiguration(
                Rules=[s3.LifecycleRule(ExpirationInDays=3, Status="Enabled")]
            ),
            NotificationConfiguration=s3.NotificationConfiguration(
                LambdaConfigurations=[
                    s3.LambdaConfigurations(
                        Event="s3:ObjectCreated:*",
                        Function=GetAtt("SESACMForwarderLambda", "Arn"),
                    )
                ],
            ),
        )
    )

    t.add_resource(
        awslambda.Permission(
            "InvokePermission",
            Action="lambda:InvokeFunction",
            FunctionName=GetAtt(function, "Arn"),
            Principal="s3.amazonaws.com",
            SourceAccount=Ref("AWS::AccountId"),
            SourceArn=Join(
                "",
                ["arn:aws:s3:::", Join(".", ["mail", Ref("HostedZoneName")])],
            ),
        )
    )

    t.add_resource(
        s3.BucketPolicy(
            "SESS3BucketPolicy",
            Bucket=Ref(bucket),
            PolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect="Allow",
                        Principal=aws.Principal(
                            "Service",
                            resources="ses.amazonaws.com",
                        ),
                        Action=[aws.Action("s3", action="PutObject")],
                        Resource=[
                            Join("", ["arn:aws:s3:::", Ref(bucket), "/*"])
                        ],
                        Condition=aws.Condition(
                            aws.StringEquals(
                                {"aws:Referer": Ref("AWS::AccountId")}
                            )
                        ),
                    ),
                ]
            ),
        )
    )
    t.add_resource(
        iam.Role(
            "LambdaSESACMForwarderRole",
            AssumeRolePolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect="Allow",
                        Principal=aws.Principal(
                            "Service",
                            resources="lambda.amazonaws.com",
                        ),
                        Action=[aws.Action("sts", action="AssumeRole")],
                    )
                ]
            ),
            Path="/",
            Policies=[
                iam.Policy(
                    PolicyName="ses-send-email",
                    PolicyDocument=aws.PolicyDocument(
                        Version="2012-10-17",
                        Statement=[
                            aws.Statement(
                                Effect="Allow",
                                Action=[
                                    aws.Action("ses", action="SendEmail"),
                                    aws.Action("ses", action="SendRawEmail"),
                                ],
                                Resource=["*"],
                            )
                        ],
                    ),
                ),
                iam.Policy(
                    PolicyName="lambda-cloudwatch-access",
                    PolicyDocument=aws.PolicyDocument(
                        Version="2012-10-17",
                        Statement=[
                            aws.Statement(
                                Effect="Allow",
                                Action=[
                                    aws.Action(
                                        "logs", action="CreateLogGroup"
                                    ),
                                    aws.Action(
                                        "logs", action="CreateLogStream"
                                    ),
                                    aws.Action("logs", action="PutLogEvents"),
                                ],
                                Resource=["arn:aws:logs:*:*:*"],
                            )
                        ],
                    ),
                ),
                iam.Policy(
                    PolicyName="lambda-s3-access",
                    PolicyDocument=aws.PolicyDocument(
                        Version="2012-10-17",
                        Statement=[
                            aws.Statement(
                                Effect="Allow",
                                Action=[
                                    aws.Action("s3", action="GetObject"),
                                ],
                                Resource=[
                                    Join(
                                        "",
                                        [
                                            "arn:aws:s3:::",
                                            Join(
                                                ".",
                                                [
                                                    "mail",
                                                    Ref("HostedZoneName"),
                                                ],
                                            ),
                                            "/*",
                                        ],
                                    )
                                ],
                            )
                        ],
                    ),
                ),
            ],
        )
    )

    t.add_output(
        Output(
            "SESACMS3BucketName",
            Description="The bucket that stores SES ACM mail",
            Value=Ref(bucket),
        )
    )
    t.add_output(
        Output(
            "SESACMFromAddress",
            Description="The address that sends SES mail",
            Value=Ref(from_address),
        )
    )
    t.add_output(
        Output(
            "SESACMToAddresses",
            Value=Join(",", Ref(forwarding_addresses)),
        )
    )

    return t


def update(domain, from_address, forwarding_addresses, region="eu-west-2"):
    t = make()

    stack_name = domain.replace(".", "")

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
                {
                    "ParameterKey": "FromAddress",
                    "ParameterValue": from_address,
                },
                {
                    "ParameterKey": "ForwardingAddresses",
                    "ParameterValue": forwarding_addresses,
                },
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
                {
                    "ParameterKey": "FromAddress",
                    "ParameterValue": from_address,
                },
                {
                    "ParameterKey": "ForwardingAddresses",
                    "ParameterValue": forwarding_addresses,
                },
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
