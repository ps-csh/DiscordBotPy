import random

from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import send_message
from database.db_connection import add_row, get_table_rows
from database.models import Quotes
import logging

_logger = logging.getLogger(__name__)

@command("quote")
async def random_quote(cmd: CommandData):
    try:
        quotes: list = get_table_rows(Quotes)
        if quotes and len(quotes) > 0:
            index = random.randint(0, len(quotes) - 1)
            _logger.debug(f"Debug quote: {quotes[index].message}")
            await send_message(DiscordSendMessageStructure(quotes[index].message).to_json(), cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, "No quotes found.")
    except Exception as e:
        #TODO: See if logging can be moved to this file
        _logger.error(f"Command failed: quote, Reason: {e}")
        return CommandResult(CommandResult.ERROR, "Failed to get quote.", e)

@command("addquote")
@admin
@args(1)
async def add_quote(cmd: CommandData):
    try:
        quote: str = cmd.command_args[0]
        if not quote or quote.isspace():
            return CommandResult(CommandResult.FAIL, "No quote string was provided.")
        dbObject = Quotes(message = quote)
        if add_row(dbObject):
            await send_message(DiscordSendMessageStructure("Quote added.").to_json(), cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, "Failed to add quote")
    except Exception as e:
        _logger.error(f"Command failed: addquote, Reason: {e}")
        return CommandResult(CommandResult.ERROR, "Failed to add quote", e)