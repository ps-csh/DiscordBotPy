# Handles interaction with the Discord API, through HTTP requests

import requests
import logging
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

json_header = {}
multipart_header = {}
#http_handler = HTTPRequestHandler()
_logger = logging.getLogger(__name__)

def init(config):
    print("Init api_client")
    auth_config = config["authentication"]
    #json_header["Authorization"] = f"{auth_config["type"]} {auth_config["token"]}"
    #json_header["User-Agent"] = auth_config["useragent"]
    global json_header, multipart_header
    json_header = {
        "Authorization": f"{auth_config["type"]} {auth_config["token"]}",
        "User-Agent": auth_config["useragent"],
        "Content-Type": 'application/json'
    }
    multipart_header = {
        "Authorization": f"{auth_config["type"]} {auth_config["token"]}",
        "User-Agent": auth_config["useragent"],
        "Content-Type": 'multipart/form-data'
    }
    print(json_header)
    #send_message(10)

def send_message(content, channel):
    global json_header
    print(ENDPOINTS["message"].format(channel))
    _logger.debug(f"send_message with headers: {json_header}\ncontent: {content}\nendpoint: {ENDPOINTS["message"].format(channel)}")
    response = requests.post(ENDPOINTS["message"].format(channel), data=content, headers=json_header)
