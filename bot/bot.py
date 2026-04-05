#
import configparser
import json
import logging
import discordapi.api_client
import bot.commands.default_commands, bot.commands.db_commands
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordMessagePayload
from bot.command_registry import CommandData, CommandResult, handle_command

class Bot:

    _bot_id: int
    _command_identifiers: list
    _logger: logging.Logger

    def __init__(self, config):
        self._bot_id = config["bot"]["bot_id"]
        self._command_identifiers = config["bot"]["identifiers"]
        self._logger = logging.getLogger(__name__)

    def parse_command(self, data: DiscordGatewayEvent):
        try:
            self._logger.debug(f"Parsing command in: {data.to_json()}")
            self._logger.debug(f"data: {data.d}")
            if (data.t == DiscordGatewayEventType.MESSAGE_CREATE):
                payload = DiscordMessagePayload(**data.d)
                command_string = payload.content.strip()
                #Ignore messages from self
                if payload.author["id"] == self._bot_id:
                    return
                for id in self._command_identifiers:
                    if (command_string.startswith(id)):
                        cmd = self.split_command(id, command_string)
                        result: CommandResult = handle_command(cmd.lower(), command_string, payload)
                        self.handle_result(result, payload)
                        return
        except BaseException as e:
            self._logger.error(f"Exception while parsing command: {data}\n{e}")

    def split_command(self, identifier, command_string: str):
        message = command_string.removeprefix(identifier)
        substrings = message.split(maxsplit=1)
        self._logger.debug(f"Message: {message}")
        self._logger.debug(f"Substring: {substrings}")
        return substrings[0]
    
    def handle_result(self, result: CommandResult, payload: DiscordMessagePayload):
        if result == None:
            self._logger.warning(f"Command failed: {payload.content}")
        elif result.status == CommandResult.FAIL:
            self._logger.warning(f"Command failed: {payload.content}\nResult: {result.message}")
            discordapi.api_client.send_message(result.message, payload.channel_id)
        elif result.status == CommandResult.UNAUTHORIZED:
            discordapi.api_client.send_message(result.message, payload.channel_id)
        elif result.status == CommandResult.ERROR:
            self._logger.error(f"Received error handling command: {payload.content}\nMessage: {result.message}\nError: {result.result}")
            discordapi.api_client.send_message(result.message, payload.channel_id)