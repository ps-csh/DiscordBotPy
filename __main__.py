import asyncio
import aioconsole
from logging.handlers import RotatingFileHandler
import sys
import configparser
import atexit
import logging
import shutil
import discordapi.api_client
import database.db_connection
import bot.command_registry
import bot.bot as Bot
from discordapi.gateway_client import DiscordGatewayClient
#TODO: Find where to import commands to avoid circular dependencies
import bot.commands.default_commands, bot.commands.db_commands
import bot.commands.debug_commands, bot.commands.voice_commands
#from config.app_config import get_config

_gateway_client: DiscordGatewayClient
_command_handler = None
_bot: Bot = None
_config: configparser.ConfigParser
_logger: logging.Logger

async def main():
    global _config, _logger
    _config = configparser.ConfigParser()
    _config.read("config.ini")
    shutil.copy2(_config["logging"]["filename"], "backup.log")
    _logger = logging.getLogger("DiscordBot")
    #handler = RotatingFileHandler(_config["logging"]["filename"], maxBytes=1048576, backupCount=5)
    logging.basicConfig(filename=_config["logging"]["filename"],
                        filemode='w',
                        format='%(asctime)s-[%(name)s][%(levelname)s]: %(message)s',
                        level= logging._nameToLevel[_config["logging"]["level"]])
    #_gateway_client = DiscordGatewayClient(_config)
    database.db_connection.init(_config)
    Bot.init(_config)
    #_gateway_client.register_message_callback(Bot.parse_command)
    await asyncio.gather(Bot.run(), async_input())
    database.db_connection.cleanup()

async def async_input():
    aioconsole.ainput
    active = True
    while (active):
        cmd = await aioconsole.ainput("Type q to quit: ")
        if (cmd == 'q'):
            active = False
    await cleanup()

async def cleanup():
    await Bot.cleanup()
    pass

#Wrap async function for atexit call
def exit_handler():
    asyncio.run(cleanup())

if __name__ == '__main__':
    print("Program start")
    atexit.register(exit_handler)
    #main()
    asyncio.run(main())
