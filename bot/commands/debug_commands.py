import logging
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from utility.error_log import get_error, last_error
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import ENDPOINTS, send_message, _http_handler as HTTPHandler, send_message_simple
from discordapi.http_request_handler import HTTPRequestHandler, RateBucket
from bot.bot import voice_client, shutdown

_logger = logging.getLogger(__name__)

@command("shutdown")
@admin
async def debug_bot_shutdown(cmd: CommandData):
    shutdown()
    return CommandResult()

@command("test")
@admin
async def debug_test(cmd: CommandData):
    await send_message_simple("Test", cmd.channel)
    return CommandResult()

@command("argstest1")
@admin
@args(1)
async def debug_args_test_1(cmd: CommandData):
    await send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}").to_json(), cmd.channel)
    return CommandResult()

@command("argstest2")
@admin
@args(2)
async def debug_args_test_2(cmd: CommandData):
    await send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}, {cmd.command_args[1]}").to_json(), cmd.channel)
    return CommandResult()

@command("ratetest")
@admin
@args(1)
async def debug_rate_test(cmd: CommandData):
    try:
        for i in range(int(cmd.command_args[0])):
            await send_message(DiscordSendMessageStructure(f"Rate Test: {i}").to_json(), cmd.channel)
        return CommandResult()
    except ValueError as e:
        return CommandResult(CommandResult.ERROR, "Received incorrect argument type.", e)
    except Exception as e:
        return CommandResult(CommandResult.ERROR, "Failed to perform rate test.", e)

@command("bucketinfo")
@admin
async def debug_bucket_info(cmd: CommandData):
    output = "Buckets:\n"
    """rate_limit: int
    limit_remaining: int
    reset_after: float
    bucket_id: str"""
    for k,v in HTTPHandler.buckets.items():
        output += f"{k}, Limit: {v.rate_limit}. Remain: {v.limit_remaining}, Reset: {v.reset_after}, ID: {v.bucket_id}, Pending: {v.pending_requests.qsize()}\n"
    await send_message_simple(f"Rate Test: {output}", cmd.channel)
    return CommandResult()

@command("geterror")
@admin
@args(1)
async def debug_get_error_log(cmd: CommandData):
    try:
        index = int(args[0])
        error: CommandResult = get_error(index)
        if error:
            await send_message_simple(f"{error.message}, {error.result}", cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, f"No error found for index {index}.")
    except Exception as e:
        return CommandResult(CommandResult.ERROR, "Failed to get error.", e)
    
@command("lasterror")
@admin
async def debug_last_error_log(cmd: CommandData):
    try:
        error: CommandResult | None = last_error()
        if error:
            await send_message_simple(f"{error.message}, {error.result}", cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, f"No error found.")
    except Exception as e:
        return CommandResult(CommandResult.ERROR, "Failed to get error.", e)
    
@command("bucketreset")
@admin
async def debug_force_reset_bucket(cmd: CommandData):
    try:
        bucket = HTTPHandler.force_reset_bucket(ENDPOINTS["message"].format(cmd.channel))
        if bucket:
            await send_message_simple(f"Bucket reset {bucket.bucket_id}", cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, f"No bucket found.")
    except Exception as e:
        return CommandResult(CommandResult.ERROR, "Failed to reset bucket.", e)
    
@command("voicestate")
@admin
async def debug_get_voice_state(cmd: CommandData):
    try:
        client = voice_client()
        if client:
            await send_message_simple(client.debug_info(), cmd.channel)
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, "Voice Client has not been created yet.")
    except Exception as e:
        return CommandResult(CommandResult.ERROR, "Failed to get voice state.", e)