import logging
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import send_message

_logger = logging.getLogger(__name__)

