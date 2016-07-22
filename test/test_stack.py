import pytest
import httpretty
import json
from exosphere import stacks


@pytest.fixture(autouse=True, scope='function')
def mock_responses(request):
    def callback(http_request, uri, headers):
        httpretty.disable()
        response = testypie.get_response(uri, http_request.headers)
        headers.update({key.lower(): value for key, value in
                        response['headers'].iteritems()})
        httpretty.enable()
        return response['code'], headers, response['body'].encode('utf-8')

    httpretty.register_uri(
        httpretty.GET,
        'http://search-distillery-hmgiipkkqvhkhxcrzfqsgzyrgq.eu-west-1.es.amazonaws.com/distillery-0-0/features-raw/_search?search_type=scan&scroll=5m',
        body=json.dumps({
            "_scroll_id": "c2Nhbjs1OzExOkRPVDZFdzIxUjJHYmdzNkJCMktZdlE7MTM6RUhlUWs1S3RSZXFyVVIzVnltWjUtZzs5OnN6QVhqekRzUkNhRnhwXzZJaHI5ZkE7MTI6RE9UNkV3MjFSMkdiZ3M2QkIyS1l2UTsxNDpFSGVRazVLdFJlcXJVUjNWeW1aNS1nOzE7dG90YWxfaGl0czoyNzE2Mjs=",
            "took": 32, "timed_out": False, "_shards": {"total": 5, "successful": 5, "failed": 0},
            "hits": {"total": 27162, "max_score": 0.0, "hits": []}
        })
    )

    httpretty.enable()

    request.addfinalizer(httpretty.disable)


def test_create_stack():
    stacks.get('static_site').update()
