import requests
from requests_ratelimiter import LimiterSession
from time import time

RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_RESET_HEADER = "X-RateLimit-Reset-After"
RATE_BUCKET_HEADER = "X-RateLimit-Bucket"

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
            response = self.session.post(endpoint, headers=headers, data=content)
            self.handle_response(response)
        else:
            if bucket.limit_remaining > 0:
                response = self.session.post(endpoint, headers=headers, data=content)
                self.handle_response(response)
            else:
                bucket.pending_requests = lambda: self.session.post(endpoint, headers=headers, data=content)


    def handle_response(self, response: requests.Response):
        if response.ok:
            bucket = self.buckets.get(response.url)
            if bucket != None:
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


class RateBucket:
    rate_limit: int
    limit_remaining: int
    reset_after: float
    bucket_id: str

    pending_requests = []

    def __init__(self, limit, remaining, reset, bucket):
        self.rate_limit = limit
        self.limit_remaining = remaining
        self.bucket_id = bucket
        self.reset_after = reset

    def update(self, headers: dict):
        self.rate_limit = int(headers.get(RATE_LIMIT_HEADER))
        self.limit_remaining = int(headers.get(RATE_REMAINING_HEADER))
        self.reset_after = float(headers.get(RATE_RESET_HEADER))

    def reset(self):
        self.limit_remaining = self.rate_limit
        