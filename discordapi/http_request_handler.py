import requests
from requests_ratelimiter import LimiterSession
from time import time


class HTTPRequestHandler:
    #Rate limit should be parsed from response headers
    RATE_LIMIT = 5

    session = {}

    def __init__(self):
        self.session = LimiterSession(per_second=self.RATE_LIMIT)

    def send_message(self, endpoint):
        self.session.get(endpoint)

    