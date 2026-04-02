from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import command, admin
from discordapi.api_client import send_message

@command("Test")
@admin
def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    return CommandResult()