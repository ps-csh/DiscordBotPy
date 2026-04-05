# Handles interaction with the Discord Websocket gateway

import asyncio

import websockets.asyncio.client
import json
import logging
#import config.app_config as app_config
#from ..config.app_config import get_config
from websockets.asyncio.client import ClientConnection, connect
from discordapi.structures.discord_enums import DiscordGatewayOpcode, DiscordGatewayIntents
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordHelloPayload, DiscordIdentifyPayload
from utility.events import Event

class DiscordGatewayClient:

    GATEWAY_URL = ""
    token = ""
    socket: ClientConnection
    last_sequence = None
    heartbeat_timer: asyncio.Task
    heartbeat_interval = -1
    heartbeat_ack: bool = True
    heartbeat_is_active = False
    config: any
    cancel_flag = False
    logger: logging.Logger
    message_callback: Event

    def __init__(self, config):
        self.config = config
        self.GATEWAY_URL = config["api"]["gateway"]
        self.token = config['authentication']['token']
        #self.socket = connect(GATEWAY_URL)
        self.message_callback = Event()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Init gateway_client")

    def register_message_callback(self, callback):
        self.message_callback.register_listener(callback)

    async def listen(self):
        #while not self.cancel_flag:
        async with connect(self.GATEWAY_URL) as websocket:
            self.socket = websocket
            async for message in websocket:
                try:
                    #message = self.socket.recv()
                    #print(f"Received: {message}")
                    self.logger.debug(f"Received: {message}")
                    await self.handle_message(message)
                except websockets.ConnectionClosedError as e:
                    #print(f"Webocket closed: {e}")
                    self.logger.warning(f"Webocket closed: {e}")
                    break
                finally:
                    #print("Connection closed")
                    pass

    async def handle_message(self, message):
        data = json.loads(message)
        #print(f"JSON parsed: {data}")
        self.logger.debug(f"JSON parsed: {data}")
        try:
            self.logger.debug("Handled message")
            event = DiscordGatewayEvent(**data)
            self.last_sequence = event.s
            await self.handle_opcode(event)
        except json.JSONDecodeError as e:
            #print(f"Error parsing gateway event:\n{e}")
            self.logger.warning(f"Error parsing gateway event:\n{e}")
        except Exception as e:
            #print(f"Caught exception in handle_message:{e}")
            self.logger.warning(f"Caught exception in handle_message:{e}")

    async def handle_opcode(self, event: DiscordGatewayEvent):
        self.logger.debug(f"Handling opcode:{event.op}")
        match event.op:
            case DiscordGatewayOpcode.Dispatch:
                self.message_callback.invoke(event)
                pass
            case DiscordGatewayOpcode.VoiceStateUpdate:
                pass
            case DiscordGatewayOpcode.Reconnect:
                pass
            case DiscordGatewayOpcode.InvalidSession:
                pass
            case DiscordGatewayOpcode.Hello:
                self.logger.debug(f"Handling Hello:{event.d}, of type: {type(event.d)}")
                #payload = json.loads(json.dumps(event.d))
                #print(f"Read Hello payload as JSON: {payload}")
                self.logger.debug(f"Heartbeat: {event.d['heartbeat_interval']}")
                heartbeat = DiscordHelloPayload(event.d['heartbeat_interval'])
                await self.handle_hello_payload(event.d['heartbeat_interval'])
                #Set heartbeat interval
                #respond with indentify
                pass
            case DiscordGatewayOpcode.HeartbeatAcknowledge:
                self.heartbeat_ack = True
                pass
            case _:
                self.logger.warning(f"Received unhandled opcode:\n{event}")

    async def handle_hello_payload(self, heartbeat_interval):
        try:
            self.logger.debug(f"Handling hello payload:{heartbeat_interval}")
            self.heartbeat_timer = asyncio.create_task(self.do_heartbeat(heartbeat_interval/1000))
            intents = (DiscordGatewayIntents.Guilds | 
                    DiscordGatewayIntents.GuildMembers |
                    DiscordGatewayIntents.GuildVoiceStates |
                    DiscordGatewayIntents.GuildPresences |
                    DiscordGatewayIntents.GuildMessages |
                    DiscordGatewayIntents.DirectMessages |
                    DiscordGatewayIntents.MessageContent)
            identify_payload = DiscordIdentifyPayload(token=self.token, 
                                            device='python',
                                            intents=intents)
            gateway_event = DiscordGatewayEvent(DiscordGatewayOpcode.Identify, d=identify_payload)
            data = gateway_event.to_json()
            self.logger.debug(f"Sending identify data: {data}")
            await self.socket.send(data)
        except BaseException as e:
            self.logger.error(f"Caught exception in handle_hello_payload: {e}")
            print(f"Caught exception in handle_hello_payload: {e}")

    async def do_heartbeat(self, interval):
        self.heartbeat_is_active = True
        while self.heartbeat_is_active:
            if self.heartbeat_ack:
                self.heartbeat_ack = False
                payload = DiscordGatewayEvent(op=DiscordGatewayOpcode.Heartbeat, d=self.last_sequence)
                data = payload.to_json()
                self.logger.debug(f"Sending heartbeat data: {data}")
                await self.socket.send(data)
                await asyncio.sleep(interval)
            else:
                #TODO: retry, log, disconnect
                self.heartbeat_is_active = False
                self.logger.warning("Missed heartbeat_ack")
                pass

    def cleanup(self):
        try:
            self.cancel_flag = True
            self.socket.close(websockets.CloseCode.NORMAL_CLOSURE, reason="Closed by application")
            self.heartbeat_is_active = False
            self.heartbeat_timer.cancel()
        except BaseException as e:
            print(e)