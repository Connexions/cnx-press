import pretend
import requests
import requests_mock as rmock

from press.events import LegacyPublicationFinished
from press.subscribers.legacy_update_latest import legacy_update_latest

from tests.helpers import (
    retryable_timeout_request_mock_callback
)


def test(requests_mock):
    request_callback = pretend.call_recorder(
        lambda request, context: 'updated')
    # mock the request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    # stub out the logger
    logger_info = pretend.call_recorder(lambda *a, **kw: None)
    logger = pretend.stub(info=logger_info)
    # Create an event with a stub request
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]
    request = pretend.stub(domain='example.org', scheme='mock', log=logger)
    event = LegacyPublicationFinished(ids, request)

    # Call the subcriber
    legacy_update_latest(event)

    # Check for request calls
    assert len(request_callback.calls) == len(ids)
    known_base_url = 'mock://legacy.example.org'
    for i, (id, ver) in enumerate(sorted(ids)):
        url = (
            '{}/content/{}/latest'.format(known_base_url, id)
        )
        request, context = request_callback.calls[i].args
        assert url == request.url

    # Check for logging
    assert len(logger_info.calls) == len(ids)
    for i, (id, ver) in enumerate(sorted(ids)):
        assert id in logger_info.calls[i].args[0]


def test_failed_request_and_retry_failed(requests_mock):
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]

    def request_callback(request, context):
        if ids[1][0] in request.url:
            raise requests.exceptions.ConnectTimeout
        else:
            return 'updated'

    # mock a problem request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    # stub out the raven client
    captureException = pretend.call_recorder(lambda: None)
    raven_client = pretend.stub(captureException=captureException)
    # stub out the logger
    logger_info = pretend.call_recorder(lambda *a, **kw: None)
    logger_exception = pretend.call_recorder(lambda *a, **kw: None)
    logger = pretend.stub(
        info=logger_info,
        exception=logger_exception,
    )
    # Create an event with a stub request
    request = pretend.stub(domain='example.org', scheme='mock',
                           log=logger, raven_client=raven_client)
    event = LegacyPublicationFinished(ids, request)

    # Call the subcriber
    legacy_update_latest(event)

    # Check raven was used...
    assert captureException.calls

    # Check for logging
    assert logger_exception.calls == [
        pretend.call("problem fetching '{}'".format(ids[1][0])),
    ]
    assert len(logger_info.calls) == len(ids) - 1
    for i, (id, ver) in enumerate(sorted(ids)[:-1]):
        assert id in logger_info.calls[i].args[0]


def test_failed_request_and_retry_success(requests_mock):
    ids = [
        ('m12345', (2, None)),
        ('m54321', (4, None)),
        ('col32154', (5, 1)),
    ]

    @retryable_timeout_request_mock_callback
    def request_callback(request, context, tries):
        # fails at first but succeeds on the second try
        if ids[1][0] in request.url and tries < 2:
            raise requests.exceptions.ConnectTimeout
        return 'updated'

    # mock a problem request to enqueue
    requests_mock.register_uri('GET', rmock.ANY, text=request_callback)

    # stub out the raven client
    captureException = pretend.call_recorder(lambda: None)
    raven_client = pretend.stub(captureException=captureException)
    # stub out the logger
    logger_info = pretend.call_recorder(lambda *a, **kw: None)
    logger_exception = pretend.call_recorder(lambda *a, **kw: None)
    logger = pretend.stub(
        info=logger_info,
        exception=logger_exception,
    )
    # Create an event with a stub request
    request = pretend.stub(domain='example.org', scheme='mock',
                           log=logger, raven_client=raven_client)
    event = LegacyPublicationFinished(ids, request)

    # Call the subcriber
    legacy_update_latest(event)

    # Check raven was used...
    assert captureException.calls

    # Check for logging
    assert logger_exception.calls == []
