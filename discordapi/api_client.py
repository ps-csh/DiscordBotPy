# Handles interaction with the Discord API, through HTTP requests

import requests
#import config.app_config as app_config
#from http_request_handler import HTTPRequestHandler

ENDPOINTS = {
    "base": "https://discordapp.com/api/",
    "channel": "channels/{0}",
    "message": "channels/{0}/messages",
    "guild": "guild/{0}",
    "webhook": "webhook/{0}",
    "user": "users/{0}"
}

auth_header = {}
#http_handler = HTTPRequestHandler()

def init(config):
    print("Init api_client")
    auth_config = config["authentication"]
    auth_header["Authorization"] = f"{auth_config["type"]} {auth_config["token"]}"
    auth_header["User-Agent"] = auth_config["useragent"]
    print(auth_header)
    send_message(10)

def send_message(channel):
    print(ENDPOINTS["base"] + ENDPOINTS["message"].format(channel))
