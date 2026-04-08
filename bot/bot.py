#
import configparser
import json
import logging
import discordapi.api_client
import bot.commands.default_commands, bot.commands.db_commands, bot.commands.debug_commands
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload
from bot.command_registry import CommandData, CommandResult, handle_command

MAX_ERRORS = 10

_logger: logging.Logger = logging.getLogger(__name__)
_bot_id: int
_command_identifiers: list
_errors: list

def init(config):
    global _bot_id, _command_identifiers
    _bot_id = config["bot"]["bot_id"]
    _command_identifiers = config["bot"]["identifiers"]

def parse_command(data: DiscordGatewayEvent):
    try:
        _logger.debug(f"Parsing command in: {data.to_json()}")
        _logger.debug(f"data: {data.d}")
        if (data.t == DiscordGatewayEventType.MESSAGE_CREATE):
            payload = DiscordMessagePayload(**data.d)
            command_string = payload.content.strip()
            #Ignore messages from self
            if payload.author["id"] == _bot_id:
                return
            for id in _command_identifiers:
                if (command_string.startswith(id)):
                    cmd = split_command(id, command_string)
                    result: CommandResult = handle_command(cmd.lower(), command_string, payload)
                    handle_result(result, payload)
                    return
    except BaseException as e:
        _logger.error(f"Exception while parsing command: {data}\n{e}")

def split_command(identifier, command_string: str):
    message = command_string.removeprefix(identifier)
    substrings = message.split(maxsplit=1)
    _logger.debug(f"Message: {message}")
    _logger.debug(f"Substring: {substrings}")
    return substrings[0]

def handle_result(result: CommandResult, payload: DiscordMessagePayload):
    if result == None:
        _logger.warning(f"Command failed: {payload.content}")
    elif result.status == CommandResult.FAIL:
        _logger.warning(f"Command failed: {payload.content}\nResult: {result.message}")
        discordapi.api_client.send_message(result.message, payload.channel_id)
    elif result.status == CommandResult.UNAUTHORIZED:
        discordapi.api_client.send_message(result.message, payload.channel_id)
    elif result.status == CommandResult.ERROR:
        add_error(result)
        discordapi.api_client.send_message(result.message, payload.channel_id)

def add_error(error_result: CommandResult):
    if len(_errors) >= MAX_ERRORS:
        del _errors[0]
    _errors.append(error_result)

def get_error(index: int):
    if index >= 0 and index < len(_errors):
        return _errors[index]
    return None

def last_error():
    count = len(_errors)
    return _errors[count - 1] if count > 0 else None