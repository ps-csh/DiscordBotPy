import discordapi.api_client
import asyncio
import sys
import configparser
import atexit
import logging
from discordapi.gateway_client import DiscordGatewayClient
import bot.command_registry
from bot.bot import Bot
#from config.app_config import get_config

gateway_client = None
command_handler = None
_bot: Bot = None

def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    logger = logging.getLogger("DiscordBot")
    logging.basicConfig(filename = config["logging"]["filename"],
                        format='%(asctime)s-[%(name)s][%(levelname)s]: %(message)s',
                        level= logging._nameToLevel[config["logging"]["level"]])
    logger.setLevel(logging.DEBUG)
    discordapi.api_client.init(config)
    gateway_client = DiscordGatewayClient(config)
    _bot = Bot(config=config)
    gateway_client.register_message_callback(_bot.parse_command)
    asyncio.run(gateway_client.listen())
    quit_flag = False
    while (not quit_flag):
        cmd = input("Type q to quit: ")
        if (cmd == 'q'):
            quit_flag = True
    gateway_client.close()

async def async_input():
    await asyncio.to_thread(sys.stdout.write, f'Waiting for command: ')
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip('\n')

def cleanup():
    gateway_client.close()

if __name__ == '__main__':
    print("Program start")
    atexit.register(cleanup)
    main()
    #asyncio.run(main())
