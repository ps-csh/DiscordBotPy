import discordapi.api_client
from discordapi.gateway_client import DiscordGatewayClient
import asyncio
import sys
import configparser
import atexit
#from config.app_config import get_config

gateway_client = None

def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
    #discordapi.api_client.init(config)
    gateway_client = DiscordGatewayClient(config)
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
