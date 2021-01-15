import re
from urllib.parse import parse_qs

import httpretty
import pytest


@pytest.fixture(autouse=True, scope="function")
def mock_responses(request):
    def callback(http_request, uri, headers):
        httpretty.disable()
        response = testypie.get_response(uri, http_request.headers)
        headers.update(
            {
                key.lower(): value
                for key, value in response["headers"].iteritems()
            }
        )
        httpretty.enable()
        return response["code"], headers, response["body"].encode("utf-8")

    def cloudformation(request, uri, headers):
        q = parse_qs(request.querystring or request.body.decode("utf-8"))
        print(q)
        return (
            200,
            {},
            {
                "GET": {},
                "POST": {
                    "DescribeStacks": """<DescribeStacksResponse xmlns="http://cloudformation.amazonaws.com/doc/2010-05-15/">
  <DescribeStacksResult>
    <Stacks>
      <member>
        <StackName>MyStack</StackName>
        <StackId>arn:aws:cloudformation:us-east-1:123456789:stack/MyStack/aaf549a0-a413-11df-adb3-5081b3858e83</StackId>
        <CreationTime>2010-07-27T22:28:28Z</CreationTime>
        <StackStatus>CREATE_COMPLETE</StackStatus>
        <DisableRollback>false</DisableRollback>
        <Outputs>
          <member>
            <OutputKey>StartPage</OutputKey>
            <OutputValue>http://my-load-balancer.amazonaws.com:80/index.html</OutputValue>
          </member>
        </Outputs>
      </member>
    </Stacks>
  </DescribeStacksResult>
  <ResponseMetadata>
    <RequestId>b9b4b068-3a41-11e5-94eb-example</RequestId>
  </ResponseMetadata>
</DescribeStacksResponse>""",
                },
            }[request.method][q.get("Action", ["default"])[0]],
        )

    httpretty.register_uri(
        httpretty.GET,
        re.compile("https://cloudformation.eu-west-1.amazonaws.com.*"),
        body=cloudformation,
    )

    httpretty.register_uri(
        httpretty.POST,
        re.compile("https://cloudformation.eu-west-1.amazonaws.com.*"),
        body=cloudformation,
    )

    httpretty.enable()

    request.addfinalizer(httpretty.disable)


def test_create_stack():
    # stacks.static_site.update('example.com')
    pass
