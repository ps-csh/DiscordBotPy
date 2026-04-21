import logging
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from bot.bot import connect_to_voice, disconnect_from_voice, voice_client
from discordapi.api_client import send_message

_logger = logging.getLogger(__name__)

@command("joinvc")
@admin
async def JoinVoice(cmd: CommandData):
    await connect_to_voice(cmd.payload.guild_id, cmd.payload)
    return CommandResult()

@command("leavevc")
@admin
async def LeaveVoice(cmd: CommandData):
    await disconnect_from_voice(cmd.payload.guild_id, cmd.payload)
    return CommandResult()

@command("testaudio")
@admin
@args(1)
async def SendAudio(cmd: CommandData):
    if voice_client():
        await voice_client().send_audio(cmd.command_args[0], True)
    return CommandResult()