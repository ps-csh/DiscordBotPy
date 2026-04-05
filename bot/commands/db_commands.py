import random

from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import send_message
from database.db_connection import add_row, get_table_rows
from database.models import Quotes

@command("quote")
def random_quote(cmd: CommandData):
    try:
        quotes: list = get_table_rows(Quotes)
        if quotes and len(quotes) > 0:
            index = random.randint(0, len(quotes) - 1)
            send_message(DiscordSendMessageStructure(quotes[index].message).to_json(), cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, "No quotes found.")
    except BaseException as e:
        return CommandResult(CommandResult.ERROR, "Failed to get quote.", e)

@command("addquote")
@admin
@args(1)
def add_quote(cmd: CommandData):
    try:
        quote: str = cmd.command_args[0]
        if not quote or quote.isspace():
            return CommandResult(CommandResult.FAIL, "No quote string was provided.")
        dbObject = Quotes(message = quote)
        if add_row(dbObject):
            send_message(DiscordSendMessageStructure("Quote added.").to_json(), cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, "Failed to add quote")
    except BaseException as e:
        return CommandResult(CommandResult.ERROR, "Failed to add quote", e)