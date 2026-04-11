#
import asyncio
import configparser
import json
import logging
import discordapi.api_client
from discordapi.api_client import send_message
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload
from discordapi.voice_gateway_client import DiscordVoiceGatewayClient
from bot.command_registry import CommandData, CommandResult, get_command
from utility.error_log import add_error


_logger: logging.Logger = logging.getLogger(__name__)
_bot_id: int
_command_identifiers: list
_gateway_client: DiscordGatewayClient
_voice_client: DiscordVoiceGatewayClient
_active: bool = True
_default_voice_channel: str

def init(config):
    global _bot_id, _command_identifiers, _gateway_client, _voice_client, _default_voice_channel
    _bot_id = config["bot"]["bot_id"]
    _command_identifiers = config["bot"]["identifiers"]
    _default_voice_channel = config["bot"]["voice_channel"]
    discordapi.api_client.init(config)
    _gateway_client = DiscordGatewayClient(config)
    _gateway_client.register_message_callback(parse_command)
    _voice_client = DiscordVoiceGatewayClient(config, _gateway_client)

async def run():
    #NOTE - asyncio.create_task only works in an async event loop
    await _gateway_client.listen()
    await cleanup()

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
                    cmd_name = split_command(id, command_string)
                    command = get_command(cmd_name.lower())
                    if command:
                        #Fire and forget command execution
                        asyncio.create_task(handle_command(command, command_string, payload))
                    else:
                        asyncio.create_task(send_message(f"Command not found: {cmd_name}", payload.channel_id))
                    return
    except BaseException as e:
        _logger.error(f"Exception while parsing command: {data}\n{e}")

def split_command(identifier, command_string: str):
    message = command_string.removeprefix(identifier)
    substrings = message.split(maxsplit=1)
    _logger.debug(f"Message: {message}")
    _logger.debug(f"Substring: {substrings}")
    return substrings[0]

async def handle_command(command: function, command_string: str, payload: DiscordMessagePayload):
    result: CommandResult = await command(CommandData(command_string, payload, channel=payload.channel_id))
    await handle_result(result, payload)

async def handle_result(result: CommandResult, payload: DiscordMessagePayload):
    if result == None:
        _logger.warning(f"Command failed: {payload.content}")
    elif result.status == CommandResult.FAIL:
        _logger.warning(f"Command failed: {payload.content}\nResult: {result.message}")
        await discordapi.api_client.send_message(result.message, payload.channel_id)
    elif result.status == CommandResult.UNAUTHORIZED:
        await discordapi.api_client.send_message(result.message, payload.channel_id)
    elif result.status == CommandResult.ERROR:
        add_error(result)
        await discordapi.api_client.send_message(result.message, payload.channel_id)

async def connect_to_voice(guild_id, payload: DiscordMessagePayload, channel_id: str | None = None):
    result = await _gateway_client.connect_to_voice(guild_id, channel_id if channel_id else _default_voice_channel)
    if result:
        _voice_client.wait_for_server_details()
    else:
        await discordapi.api_client.send_message("Failed to connect to voice channel", payload.channel_id)

async def disconnect_from_voice(guild_id, payload: DiscordMessagePayload):
    result = await _gateway_client.disconnect_from_voice(guild_id)
    _voice_client.disconnect()
    if not result:
        await discordapi.api_client.send_message("Failed to disconnect from voice", payload.channel_id)

def shutdown():
    global _active
    _active = False

async def cleanup():
    await _gateway_client.cleanup()
    if _voice_client:
        _voice_client.cleanup()