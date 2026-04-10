# Handles HTTP Requests, adhering to rate limits

import asyncio
import requests
import logging
import aiohttp
from asyncio import Queue, Semaphore
from requests_ratelimiter import LimiterSession
from time import time

RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_RESET_HEADER = "X-RateLimit-Reset"
RATE_RESET_AFTER_HEADER = "X-RateLimit-Reset-After"
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

    _session = None
    buckets = {}

    #NOTE - this will throw an exception if called outside an async function
    #aiohttp.ClientSession must be used in an async event loop
    @property
    def get_session(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # def post_message(self, endpoint, headers, content):
    #     bucket: RateBucket = self.buckets.get(endpoint)
    #     if bucket == None:
    #         _logger.debug("No bucket yet")
    #         response = self.get_session.post(endpoint, headers=headers, data=content)
    #         self.update_bucket(response)
    #         return response
    #     else:
    #         if bucket.limit_remaining > 0:
    #             response = self.get_session.post(endpoint, headers=headers, data=content)
    #             self.update_bucket(response)
    #             return response
    #         else:
    #             bucket.enqueue_request(lambda: self.get_session.post(endpoint, headers=headers, data=content))
    #             _logger.debug(f"Request enqueued: {content}")
    #     return None

    async def post_message_async(self, endpoint: str, headers: dict, content):
        bucket: RateBucket = self.buckets.get(endpoint)
        if bucket == None:
            _logger.debug(f"No bucket yet for {endpoint}")
            for k,v in self.buckets.items():
                _logger.debug(f"{k}: {v.rate_limit}, {v.bucket_id}\n{endpoint} is {str(k)}: {endpoint == str(k)}")
            response = await self.get_session.post(endpoint, headers=headers, data=content)
            if response.ok:
                self.update_bucket(response)
            elif response.status == 429:
                bucket = self.update_bucket(response)
                #Retry once after waiting
                await asyncio.sleep(bucket.reset_after)
                await bucket.semaphore.acquire()
                response = await self.get_session.post(endpoint, headers=headers, data=content)
                self.update_bucket(response)
                if not response.ok:
                    _logger.warning(f"post_message_async retry failed after 429 response.\n{endpoint}: {content}")
            return response
        else:
            _logger.debug(f"Awaiting semphore... Remaining: {bucket.semaphore._value}")
            await bucket.semaphore.acquire()
            response = await self.get_session.post(endpoint, headers=headers, data=content)
            self.update_bucket(response)
            if response.ok:
                self.update_bucket(response)
                _logger.debug(f"Bucket update: {bucket.limit_remaining}, Semaphore: {bucket.semaphore._value}")
            elif response.status == 429:
                bucket = self.update_bucket(response)
                #Retry once after waiting
                _logger.debug(f"Received 429 response, retrying after {bucket.reset_after} seconds")
                await asyncio.sleep(bucket.reset_after)
                await bucket.semaphore.acquire()
                response = await self.get_session.post(endpoint, headers=headers, data=content)
                self.update_bucket(response)
                if not response.ok:
                    _logger.warning(f"post_message_async retry failed after 429 response.\n{endpoint}: {content}")
            return response

    def update_bucket(self, response: aiohttp.ClientResponse):
        bucket: RateBucket = self.buckets.get(str(response.url))
        if bucket:
            _logger.debug(f"Updating bucket {bucket.bucket_id}: {response.url}\nHeaders: {response.headers}")
            bucket.update(response.headers)
        else:
            self.buckets[str(response.url)] = RateBucket(response.headers)
            _logger.debug(f"Bucket created: {response.url}\nHeaders: {response.headers}")
        return bucket

    def force_reset_bucket(self, endpoint):
        bucket: RateBucket = self.buckets.get(str(endpoint))
        if bucket:
            _logger.debug(f"Force reset bucket {bucket.bucket_id}: {endpoint}")
            bucket.reset()
            return bucket
        return None

class RateBucket:
    rate_limit: int
    limit_remaining: int
    reset_at: int
    reset_after: float
    bucket_id: str

    pending_requests = Queue()
    semaphore: Semaphore
    _timer_task = None

    def __init__(self, headers: dict):
        self.rate_limit = int(headers.get(RATE_LIMIT_HEADER))
        self.limit_remaining = int(headers.get(RATE_REMAINING_HEADER))
        self.reset_at = int(headers.get(RATE_RESET_HEADER))
        self.reset_after = float(headers.get(RATE_RESET_AFTER_HEADER))
        self.bucket_id = headers.get(RATE_BUCKET_HEADER)
        self.semaphore = Semaphore(self.limit_remaining)
        self.start_timer(self.reset_after)

    def update(self, headers: dict):
        self.rate_limit = int(headers.get(RATE_LIMIT_HEADER))
        self.limit_remaining = int(headers.get(RATE_REMAINING_HEADER))
        self.reset_after = float(headers.get(RATE_RESET_AFTER_HEADER))
        #Only update timer if reset timestamp has passed
        _logger.debug(f"Reset at: {self.reset_at}, time: {time()}")
        if self.reset_at < time():
            self.reset_at = int(headers.get(RATE_RESET_HEADER))
            self.start_timer(float(headers.get(RATE_RESET_AFTER_HEADER)))
        if self.limit_remaining != self.semaphore._value:
            _logger.warning(f"Desync detected between rate limit headers and semaphore: {self.limit_remaining} (header) vs {self.semaphore._value} (sem)")

    def start_timer(self, duration: float):
        if (not self._timer_task or self._timer_task.done()):
            _logger.debug(f"Timer {self.bucket_id} started: {duration} seconds")
            self._timer_task = asyncio.create_task(asyncio.sleep(duration))
            self._timer_task.add_done_callback(self.reset)

    def reset(self, *args):
        _logger.debug(f"Resetting bucket {self.bucket_id}, Remaining: {self.limit_remaining}")
        self.limit_remaining = self.rate_limit
        self.reset_after = 0
        #TODO: Fix desyncs with semaphore and header when multiple async requests are queued.
        # Semaphore needs to be updated with header values
        print(f"Resetting bucket {self.bucket_id}, Remaining: {self.limit_remaining}")
        for i in range(max(self.rate_limit - self.semaphore._value, 0)):
            self.semaphore.release()
            #self.do_request()
        _logger.debug(f"Semaphore release to {self.semaphore._value}, expected {self.rate_limit}")

    def do_request(self):
        request = self.pending_requests.get()
        _logger.debug(f"Execute pending request: {request}")
        request()
        self.update()

    def enqueue_request(self, request):
        self.pending_requests.put(request)