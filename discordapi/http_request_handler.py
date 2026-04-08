import asyncio
import requests
import logging
import aiohttp
from asyncio import Queue, Semaphore
from requests_ratelimiter import LimiterSession
from time import time

RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_RESET_HEADER = "X-RateLimit-Reset-After"
RATE_BUCKET_HEADER = "X-RateLimit-Bucket"

_logger: logging.Logger = logging.getLogger(__name__)

class HTTPRequestHandler:
    #Rate limit should be parsed from response headers
    RATE_LIMIT = 5

    """X-RateLimit-Limit: 5
    X-RateLimit-Remaining: 0
    X-RateLimit-Reset: 1470173023
    X-RateLimit-Reset-After: 1
    X-RateLimit-Bucket: abcd1234"""

    session = {}
    buckets = {}

    def __init__(self):
        self.session = LimiterSession(per_second=self.RATE_LIMIT)

    def post_message(self, endpoint, headers, content):
        bucket: RateBucket = self.buckets.get(endpoint)
        if bucket == None:
            _logger.debug("No bucket yet")
            response = self.session.post(endpoint, headers=headers, data=content)
            return self.handle_response(response)
        else:
            if bucket.limit_remaining > 0:
                response = self.session.post(endpoint, headers=headers, data=content)
                return self.handle_response(response)
            else:
                bucket.enqueue_request(lambda: self.session.post(endpoint, headers=headers, data=content))
                _logger.debug(f"Request enqueued: {content}")
        return None

    async def post_message_async(self, endpoint, headers, content):
        bucket: RateBucket = self.buckets.get(endpoint)
        if bucket == None:
            _logger.debug(f"No bucket yet for {endpoint}")
            response = self.session.post(endpoint, headers=headers, data=content)
            return self.handle_response(response)
        else:
            bucket._semaphore.acquire()
            response = self.session.post(endpoint, headers=headers, data=content)
            return self.handle_response(response)

    def handle_response(self, response: requests.Response):
        if response.ok:
            bucket: RateBucket = self.buckets.get(response.url)
            if bucket != None:
                _logger.debug(f"Updating bucket {bucket.bucket_id}: {response.url}")
                bucket.update(response.headers)
            else:
                rate_limit = int(response.headers.get(RATE_LIMIT_HEADER))
                limit_remaining = int(response.headers.get(RATE_REMAINING_HEADER))
                reset_after = float(response.headers.get(RATE_RESET_HEADER))
                bucket_id = response.headers.get(RATE_BUCKET_HEADER)
                self.buckets[response.url] = RateBucket(rate_limit,
                                                        limit_remaining,
                                                        reset_after,
                                                        bucket_id)
                _logger.debug(f"Bucket created: {response.url}")
        return response


class RateBucket:
    rate_limit: int
    limit_remaining: int
    reset_after: float
    bucket_id: str

    pending_requests = Queue()
    _semaphore: Semaphore
    _timer_task = None

    def __init__(self, limit, remaining, reset, bucket):
        self.rate_limit = limit
        self.limit_remaining = remaining
        self.bucket_id = bucket
        self.reset_after = reset

    def update(self, headers: dict):
        self.rate_limit = int(headers.get(RATE_LIMIT_HEADER))
        self.limit_remaining = int(headers.get(RATE_REMAINING_HEADER))
        self.reset_after = float(headers.get(RATE_RESET_HEADER))
        self.start_timer(float(headers.get(RATE_RESET_HEADER)))

    def start_timer(self, duration: float):
        if (not self._timer_task or self._timer_task.done()):
            _logger.debug(f"Timer {self.bucket_id} started: {duration} seconds")
            self._timer_task = asyncio.create_task(asyncio.sleep(duration))
            self._timer_task.add_done_callback(self.reset)

    def reset(self, *args):
        _logger.debug(f"Resetting bucket {self.bucket_id}")
        print(f"Resetting bucket {self.bucket_id}")
        self.limit_remaining = self.rate_limit
        self.reset_after = -1
        for i in range(self.rate_limit - self.limit_remaining):
            self._semaphore.release()
            #self.do_request()

    def do_request(self):
        request = self.pending_requests.get()
        _logger.debug(f"Execute pending request: {request}")
        request()
        self.update()

    def enqueue_request(self, request):
        self.pending_requests.put(request)