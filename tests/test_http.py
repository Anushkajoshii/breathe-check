import httpx
import pytest

from breathe_check.http import RateLimiter, get_with_retry


def client_from(responses):
    calls = iter(responses)
    return httpx.Client(transport=httpx.MockTransport(lambda request: next(calls)))


def test_retries_after_too_many_requests():
    waits = []
    client = client_from(
        [httpx.Response(429, headers={"x-ratelimit-reset": "3"}), httpx.Response(200, json={})]
    )
    response = get_with_retry(client, "https://x.test/a", sleep=waits.append)
    assert response.status_code == 200
    assert waits == [4.0]


def test_gives_up_after_max_tries():
    client = client_from([httpx.Response(503)] * 3)
    with pytest.raises(httpx.HTTPStatusError):
        get_with_retry(client, "https://x.test/a", tries=3, sleep=lambda s: None)


def test_client_errors_are_not_retried():
    client = client_from([httpx.Response(401)])
    with pytest.raises(httpx.HTTPStatusError):
        get_with_retry(client, "https://x.test/a", sleep=lambda s: None)


def test_rate_limiter_spaces_calls():
    now = [0.0]
    waits = []

    def sleep(seconds):
        waits.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(per_minute=60, clock=lambda: now[0], sleep=sleep)
    limiter.wait()
    now[0] += 0.25
    limiter.wait()
    assert waits == [pytest.approx(0.75)]
