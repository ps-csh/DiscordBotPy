import asyncio
from logging.handlers import RotatingFileHandler
import sys
import configparser
import atexit
import logging
import shutil
import discordapi.api_client
import database.db_connection
import bot.command_registry
from bot.bot import Bot
from discordapi.gateway_client import DiscordGatewayClient
#from config.app_config import get_config

_gateway_client: DiscordGatewayClient
_command_handler = None
_bot: Bot = None
_config: configparser.ConfigParser
_logger: logging.Logger

def main():
    global _config, _logger
    _config = configparser.ConfigParser()
    _config.read("config.ini")
    _logger = logging.getLogger("DiscordBot")
    #handler = RotatingFileHandler(_config["logging"]["filename"], maxBytes=1048576, backupCount=5)
    logging.basicConfig(filename=_config["logging"]["filename"],
                        filemode='w',
                        format='%(asctime)s-[%(name)s][%(levelname)s]: %(message)s',
                        level= logging._nameToLevel[_config["logging"]["level"]])
    discordapi.api_client.init(_config)
    _gateway_client = DiscordGatewayClient(_config)
    database.db_connection.init(_config)
    _bot = Bot(config=_config)
    _gateway_client.register_message_callback(_bot.parse_command)
    asyncio.run(_gateway_client.listen())
    quit_flag = False
    while (not quit_flag):
        cmd = input("Type q to quit: ")
        if (cmd == 'q'):
            quit_flag = True
    _gateway_client.cleanup()
    database.db_connection.cleanup()
    shutil.copy2(_config["logging"]["filename"], "backup.log")

async def async_input():
    await asyncio.to_thread(sys.stdout.write, f'Waiting for command: ')
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip('\n')

def cleanup():
    global _gateway_client
    pass

if __name__ == '__main__':
    print("Program start")
    atexit.register(cleanup)
    main()
    #asyncio.run(main())
