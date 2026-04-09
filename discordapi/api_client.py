# Handles interaction with the Discord API, through HTTP requests

import asyncio

import requests
import logging

from discordapi.http_request_handler import HTTPRequestHandler
#import config.app_config as app_config
#from http_request_handler import HTTPRequestHandler

ENDPOINTS = {
    "base": "https://discordapp.com/api/",
    "channel": "https://discordapp.com/api/channels/{0}",
    "message": "https://discordapp.com/api/channels/{0}/messages",
    "guild": "https://discordapp.com/api/guild/{0}",
    "webhook": "https://discordapp.com/api/webhook/{0}",
    "user": "https://discordapp.com/api/users/{0}"
}

_json_header = {}
_multipart_header = {}
_http_handler: HTTPRequestHandler = HTTPRequestHandler()
_rate_buckets = {}
_logger = logging.getLogger(__name__)

def init(config):
    global _http_handler
    print("Init api_client")
    auth_config = config["authentication"]
    #json_header["Authorization"] = f"{auth_config["type"]} {auth_config["token"]}"
    #json_header["User-Agent"] = auth_config["useragent"]
    global _json_header, _multipart_header
    _json_header = {
        "Authorization": f"{auth_config["type"]} {auth_config["token"]}",
        "User-Agent": auth_config["useragent"],
        "Content-Type": 'application/json'
    }
    _multipart_header = {
        "Authorization": f"{auth_config["type"]} {auth_config["token"]}",
        "User-Agent": auth_config["useragent"],
        "Content-Type": 'multipart/form-data'
    }
    _logger.debug(_json_header)

#TODO: Move HTTP request to separate module
async def send_message(content: str, channel: str):
    global _json_header

    if content and not content.isspace():
        #print(ENDPOINTS["message"].format(channel))
        _logger.debug(f"send_message with headers: {_json_header}\ncontent: {content}\nendpoint: {ENDPOINTS["message"].format(channel)}")
        #response = requests.post(ENDPOINTS["message"].format(channel), data=content, headers=_json_header)
        response = await _http_handler.post_message_async(ENDPOINTS["message"].format(channel), headers=_json_header, content=content)
        if response and not response.ok:
            _logger.warning(f"send_message POST request failed: {response.status} {response.reason}")

async def send_message_async(content: str, channel: str):
    global _json_header

    if content and not content.isspace():
        #print(ENDPOINTS["message"].format(channel))
        _logger.debug(f"send_message with headers: {_json_header}\ncontent: {content}\nendpoint: {ENDPOINTS["message"].format(channel)}")
        #response = requests.post(ENDPOINTS["message"].format(channel), data=content, headers=_json_header)
        response = await _http_handler.post_message_async(ENDPOINTS["message"].format(channel), headers=_json_header, content=content)
        if response and not response.ok:
            _logger.warning(f"send_message POST request failed: {response.status} {response.reason}")