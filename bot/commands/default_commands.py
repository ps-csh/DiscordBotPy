from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import command, CommandData
from discordapi.api_client import send_message

@command("Test")
def Test(cmd: CommandData):
    test = DiscordSendMessageStructure("Test")
    test_j = DiscordSendMessageStructure("Test").to_json()
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    pass