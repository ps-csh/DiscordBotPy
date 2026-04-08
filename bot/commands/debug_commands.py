import logging
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordSendMessageStructure
from utility.error_log import get_error, last_error
from bot.command_registry import CommandData, CommandResult
from bot.command_decorators import args, command, admin
from discordapi.api_client import send_message, _http_handler
from discordapi.http_request_handler import HTTPRequestHandler, RateBucket

_logger = logging.getLogger(__name__)

@command("test")
@admin
async def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    return CommandResult()

@command("argstest1")
@admin
async def Test(cmd: CommandData):
    send_message(DiscordSendMessageStructure("Test").to_json(), cmd.channel)
    return CommandResult()


@command("argstest1")
@admin
@args(1)
async def ArgsTest(cmd: CommandData):
    send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}").to_json(), cmd.channel)
    return CommandResult()

@command("argstest2")
@admin
@args(2)
async def ArgsTest2(cmd: CommandData):
    send_message(DiscordSendMessageStructure(f"Success: {cmd.command_args[0]}, {cmd.command_args[1]}").to_json(), cmd.channel)
    return CommandResult()

@command("ratetest")
@admin
async def RateTest(cmd: CommandData):
    for i in range(15):
        send_message(DiscordSendMessageStructure(f"Rate Test: {i}").to_json(), cmd.channel)
    return CommandResult()

@command("bucketinfo")
@admin
async def BucketInfo(cmd: CommandData):
    output = "Buckets:\n"
    """rate_limit: int
    limit_remaining: int
    reset_after: float
    bucket_id: str"""
    for k,v in _http_handler.buckets.items():
        output += f"{k}, Limit: {v.rate_limit}. Remain: {v.limit_remaining}, Reset: {v.reset_after}, ID: {v.bucket_id}, Pending: {v.pending_requests.qsize()}\n"
    send_message(DiscordSendMessageStructure(f"Rate Test: {output}").to_json(), cmd.channel)
    return CommandResult()

@command("geterror")
@admin
@args(1)
async def GetError(cmd: CommandData):
    try:
        index = int(args[0])
        error: CommandResult = get_error(index)
        if error:
            send_message(f"{error.message}, {error.result}")
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, f"No error found for index {index}.")
    except BaseException as e:
        return CommandResult(CommandResult.ERROR, "Failed to get error.", e)
    
@command("lasterror")
@admin
async def LastError(cmd: CommandData):
    try:
        error: CommandResult = last_error()
        if error:
            send_message(f"{error.message}, {error.result}")
            return CommandResult()
        else:
            return CommandResult(CommandResult.FAIL, f"No error found.")
    except BaseException as e:
        return CommandResult(CommandResult.ERROR, "Failed to get error.", e)