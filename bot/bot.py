#
import configparser
import json
import logging
import discordapi.api_client
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload
from bot.command_registry import CommandData, CommandResult, handle_command
from bot.commands.default_commands import Test

class Bot:

    _bot_id: int
    _command_identifiers: list
    _logger: logging.Logger

    def __init__(self, config):
        self._command_identifiers = config["bot"]["identifiers"]
        self._logger = logging.getLogger(__name__)

    def parse_command(self, data: DiscordGatewayEvent):
        try:
            self._logger.debug(f"Parsing command in: {data.to_json()}")
            self._logger.debug(f"data: {data.d}")
            if (data.t == DiscordGatewayEventType.MESSAGE_CREATE):
                payload = DiscordMessagePayload(**data.d)
                for id in self._command_identifiers:
                    if (payload.content.startswith(id)):
                        message = payload.content.removeprefix(id)
                        substrings = message.split(maxsplit=1)
                        self._logger.debug(f"Message: {message}")
                        self._logger.debug(f"Substring: {substrings}")
                        result: CommandResult = handle_command(substrings[0], 
                                       substrings[1] if len(substrings) > 1 else None,
                                       payload)
                        if result != None and result.status != CommandResult.SUCCESS:
                            self._logger.warning(f"Command failed: {payload.content}\Result: {result.message}")
                        elif result == None:
                            self._logger.warning(f"Command failed: {payload.content}")
        except BaseException as e:
            self._logger.error(f"Exception while parsing command: {data}\n{e}")
        pass