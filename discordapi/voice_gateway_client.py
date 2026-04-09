# Handles interaction with the Discord Websocket gateway

import asyncio

import websockets.asyncio.client
import json
import logging
#import config.app_config as app_config
#from ..config.app_config import get_config
from websockets.asyncio.client import ClientConnection, connect
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType, DiscordGatewayOpcode, DiscordGatewayIntents, DiscordVoiceGatewayOpcode
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordHelloPayload, DiscordIdentifyPayload, DiscordVoiceUpdatePayload
from utility.events import Event

_logger: logging.Logger = logging.getLogger(__name__)

class DiscordVoiceGatewayClient:

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
    message_callback: Event
    _waiting_for_server_details: bool = False

    def __init__(self, config, gateway_client: DiscordGatewayClient):
        self.config = config
        self.GATEWAY_URL = config["api"]["gateway"]
        self.token = config['authentication']['token']
        #self.socket = connect(GATEWAY_URL)
        self.message_callback = Event()
        #VoiceGateway relies on receiving events from regular Gateway for initialization
        #TODO: Should this be decoupled?
        gateway_client.register_message_callback(self.on_gateway_event_received)

    def on_gateway_event_received(self, data: DiscordGatewayEvent):
        if not self._waiting_for_server_details:
            return
        if (data.t == DiscordGatewayEventType.VOICE_STATE_UPDATE):
            pass
        if (data.t == DiscordGatewayEventType.VOICE_SERVER_UPDATE):
            pass
        pass

    async def listen(self):
        #while not self.cancel_flag:
        async with connect(self.GATEWAY_URL) as websocket:
            self.socket = websocket
            async for message in websocket:
                try:
                    #message = self.socket.recv()
                    #print(f"Received: {message}")
                    _logger.debug(f"Received: {message}")
                    await self.handle_message(message)
                except websockets.ConnectionClosedError as e:
                    #print(f"Webocket closed: {e}")
                    _logger.warning(f"Webocket closed: {e}")
                    break
                finally:
                    #print("Connection closed")
                    pass

    async def handle_message(self, message):
        data = json.loads(message)
        #print(f"JSON parsed: {data}")
        _logger.debug(f"JSON parsed: {data}")
        try:
            _logger.debug("Handled message")
            event = DiscordGatewayEvent(**data)
            self.last_sequence = event.s
            await self.handle_opcode(event)
        except json.JSONDecodeError as e:
            #print(f"Error parsing gateway event:\n{e}")
            _logger.warning(f"Error parsing gateway event:\n{e}")
        except Exception as e:
            #print(f"Caught exception in handle_message:{e}")
            _logger.warning(f"Caught exception in handle_message:{e}")

    async def handle_opcode(self, event: DiscordGatewayEvent):
        _logger.debug(f"Handling opcode:{event.op}")
        match event.op:
            case DiscordVoiceGatewayOpcode.Identify:
                pass
            case DiscordVoiceGatewayOpcode.SelectProtocol:
                pass
            case DiscordVoiceGatewayOpcode.Ready:
                pass
            case DiscordVoiceGatewayOpcode.Heartbeat:
                pass
            case DiscordVoiceGatewayOpcode.SessionDescription:
                pass
            case DiscordVoiceGatewayOpcode.Speaking:
                pass
            case DiscordVoiceGatewayOpcode.HeartbeatAcknowledge:
                self.heartbeat_ack = True
                pass
            case DiscordVoiceGatewayOpcode.Resume:
                pass
            case DiscordVoiceGatewayOpcode.Hello:
                _logger.debug(f"Handling Hello:{event.d}, of type: {type(event.d)}")
                #payload = json.loads(json.dumps(event.d))
                #print(f"Read Hello payload as JSON: {payload}")
                _logger.debug(f"Heartbeat: {event.d['heartbeat_interval']}")
                heartbeat = DiscordHelloPayload(event.d['heartbeat_interval'])
                await self.handle_hello_payload(event.d['heartbeat_interval'])
                #Set heartbeat interval
                #respond with indentify
                pass
            case DiscordVoiceGatewayOpcode.Resumed:
                pass
            case DiscordVoiceGatewayOpcode.ClientsConnect:
                pass
            case DiscordVoiceGatewayOpcode.ClientsDisconnect:
                pass
            case _:
                #TODO: Handle DAVE encoding if necessary
                _logger.warning(f"Received unhandled opcode:\n{event}")

    async def handle_hello_payload(self, heartbeat_interval):
        try:
            _logger.debug(f"Handling hello payload:{heartbeat_interval}")
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
            _logger.debug(f"Sending identify data: {data}")
            await self.socket.send(data)
        except BaseException as e:
            _logger.error(f"Caught exception in handle_hello_payload: {e}")
            print(f"Caught exception in handle_hello_payload: {e}")

    async def do_heartbeat(self, interval):
        self.heartbeat_is_active = True
        while self.heartbeat_is_active:
            if self.heartbeat_ack:
                self.heartbeat_ack = False
                payload = DiscordGatewayEvent(op=DiscordGatewayOpcode.Heartbeat, d=self.last_sequence)
                data = payload.to_json()
                _logger.debug(f"Sending heartbeat data: {data}")
                await self.socket.send(data)
                await asyncio.sleep(interval)
            else:
                #TODO: retry, log, disconnect
                self.heartbeat_is_active = False
                _logger.warning("Missed heartbeat_ack")
                pass

    async def connect_to_voice(self, guild_id:str, channel_id:str):
        payload = DiscordGatewayEvent(DiscordGatewayOpcode.VoiceStateUpdate,
                                      d=DiscordVoiceUpdatePayload(guild_id,
                                                                  channel_id,
                                                                  False,
                                                                  False))
        await self.socket.send(payload.to_json())
        pass

    def cleanup(self):
        try:
            self.cancel_flag = True
            self.heartbeat_is_active = False
            if self.socket and self.socket.state != websockets.State.CLOSED:
                self.socket.close(websockets.CloseCode.NORMAL_CLOSURE, reason="Closed by application")
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel() 
        except BaseException as e:
            print(e)