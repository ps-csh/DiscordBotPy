import logging
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload

_commands: list = {}
_fallback: function = lambda: print("Fallback command not implemented!")
_logger = logging.getLogger(__name__)

def command(name):
    def wrapper(func):
        _commands[name] = (func)
        print(f"Added command: {func.__name__}")
        return func
    return wrapper

def register_command(name, func):
    _commands[name] = func

def register_fallback(func):
    _fallback = func

# @command(name="debug")
# def testCommand():
#     print("ex")
#     pass

def parse_command(payload: DiscordGatewayEvent):
    pass

def handle_command(command_string: str, command_args: str | None, payload: DiscordMessagePayload):
    if command_string in _commands:
        _commands[command_string](CommandData(command_string, command_args, payload, payload.channel_id))
    else:
        _fallback()

class CommandData:

    command_string: str
    command_args: list
    payload: DiscordMessagePayload
    channel: str

    def __init__(self, cmd, args, payload, channel = None):
        self.command_string = cmd
        self.command_args = args
        self.payload = payload
        self.channel = channel or payload.channel_id