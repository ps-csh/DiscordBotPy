from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import send_message

@command("test")
@admin
def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    return CommandResult()

@command("argstest1")
@admin
def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    return CommandResult()


@command("argstest1")
@admin
@args(1)
def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}").to_json(), cmd.channel)
    return CommandResult()

@command("argstest2")
@admin
@args(2)
def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}, {cmd.command_args[1]}").to_json(), cmd.channel)
    return CommandResult()
