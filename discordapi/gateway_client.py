# Handles interaction with the Discord Websocket gateway

import asyncio

import websockets.asyncio.client
import json
#import config.app_config as app_config
#from ..config.app_config import get_config
from websockets.asyncio.client import ClientConnection, connect
from utility.timer_callback import CallbackTimer
from discordapi.structures.discord_types import DiscordGatewayEvent, DiscordGatewayOpcode, DiscordGatewayIntents
from discordapi.structures.discord_payloads import DiscordHelloPayload, DiscordIdentifyPayload

class DiscordGatewayClient:

    GATEWAY_URL = ""
    socket: websockets.ClientConnection
    last_sequence = None
    heartbeat_timer: asyncio.Task
    heartbeat_interval = -1
    heartbeat_ack: bool = True
    heartbeat_is_active = False
    config: any
    cancel_flag = False

    def __init__(self, config):
        print("Init gateway_client")
        self.config = config
        self.GATEWAY_URL = config["api"]["gateway"]
        #self.socket = connect(GATEWAY_URL)
        pass

    async def listen(self):
        #while not self.cancel_flag:
        async with connect(self.GATEWAY_URL) as websocket:
            self.socket = websocket
            async for message in websocket:
                try:
                    #message = self.socket.recv()
                    print(f"Received: {message}")
                    await self.handle_message(message)
                except websockets.ConnectionClosedError as e:
                    print(f"Webocket closed: {e}")
                    break
                finally:
                    #print("Connection closed")
                    pass

    async def handle_message(self, message):
        data = json.loads(message)
        print(f"JSON parsed: {data}")
        try:
            print("Handled message")
            event = DiscordGatewayEvent(**data)
            self.last_sequence = event.s
            await self.handle_opcode(event)
        except json.JSONDecodeError as e:
            print(f"Error parsing gateway event:\n{e}")
        except Exception as e:
            print(f"Caught exception in handle_message:{e}")

    async def handle_opcode(self, event: DiscordGatewayEvent):
        print(f"Handling opcode:{event.op}")
        match event.op:
            case DiscordGatewayOpcode.Dispatch:
                #TODO: Handle message received
                pass
            case DiscordGatewayOpcode.VoiceStateUpdate:
                pass
            case DiscordGatewayOpcode.Reconnect:
                pass
            case DiscordGatewayOpcode.InvalidSession:
                pass
            case DiscordGatewayOpcode.Hello:
                print(f"Handling Hello:{event.d}, of type: {type(event.d)}")
                #payload = json.loads(json.dumps(event.d))
                #print(f"Read Hello payload as JSON: {payload}")
                print(f"Heartbeat: {event.d['heartbeat_interval']}")
                heartbeat = DiscordHelloPayload(event.d['heartbeat_interval'])
                await self.handle_hello_payload(event.d['heartbeat_interval'])
                #Set heartbeat interval
                #respond with indentify
                pass
            case DiscordGatewayOpcode.HeartbeatAcknowledge:
                pass
            case _:
                print(f"Received unhandled opcode:\n{event}")

    async def handle_hello_payload(self, heartbeat_interval):
        print(f"Handling hello payload:{heartbeat_interval}")
        self.heartbeat_timer = asyncio.create_task(self.do_heartbeat(heartbeat_interval/1000))
        intents = (DiscordGatewayIntents.Guilds | 
                DiscordGatewayIntents.GuildMembers |
                DiscordGatewayIntents.GuildVoiceStates |
                DiscordGatewayIntents.GuildPresences |
                DiscordGatewayIntents.GuildMessages |
                DiscordGatewayIntents.DirectMessages |
                DiscordGatewayIntents.MessageContent)
        identify_payload = DiscordIdentifyPayload(token=self.config['authentication']['token'], 
                                        device='python',
                                        intents=intents)
        gateway_event = DiscordGatewayEvent(DiscordGatewayOpcode.Identify, d=identify_payload)
        data = gateway_event.to_json()
        print(f"Sending identify data: {data}")
        await self.socket.send(data)

    async def do_heartbeat(self, interval):
        self.heartbeat_is_active = True
        while self.heartbeat_is_active:
            if self.heartbeat_ack:
                payload = DiscordGatewayEvent(op=DiscordGatewayOpcode.Heartbeat, d=self.last_sequence)
                data = payload.to_json()
                print(f"Sending heartbeat data: {data}")
                await self.socket.send(data)

                await asyncio.sleep(interval)
            else:
                #TODO: retry, log, disconnect
                self.heartbeat_is_active = False
                pass

    def close(self):
        self.cancel_flag = True
        self.socket.close(websockets.CloseCode.NORMAL_CLOSURE, reason="Closed by application")
        self.heartbeat_is_active = False
        self.heartbeat_timer.cancel()