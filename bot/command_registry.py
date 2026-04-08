import enum
import logging
import configparser
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload
from functools import wraps

_commands: dict = {}
_fallback: function = lambda: print("Fallback command not implemented!")
# _logger = logging.getLogger(__name__)
# _config = configparser.ConfigParser()
# _config.read("config.ini")

def register_command(name, func):
    print(f"Added command: {func.__name__}")
    _commands[name] = func

def register_fallback(func):
    global _fallback
    _fallback = func

def parse_command(payload: DiscordGatewayEvent):
    pass

def get_command(command_name: str):
    """
    returns: CommandResult | None
    """
    if command_name in _commands:
        return _commands[command_name]
    else:
        #TODO: Delete fallback
        _fallback()
        return None

class CommandData:

    command_string: str
    command_args: list
    payload: DiscordMessagePayload
    channel: str

    def __init__(self, cmd, payload, args = None, channel = None):
        self.command_string = cmd
        self.command_args = args,
        self.payload = payload
        self.channel = channel or payload.channel_id

class CommandResult:
    SUCCESS = 0
    FAIL = 1
    UNAUTHORIZED = 2
    ERROR = 3

    status: int
    message: str | None
    result: any | None

    def __init__(self, status:int = SUCCESS, message: str|None = None, result: any | None = None):
        self.status = status
        self.message = message
        self.result = result