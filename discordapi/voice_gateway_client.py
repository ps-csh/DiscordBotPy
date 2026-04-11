# Handles interaction with the Discord Websocket gateway

import asyncio

import json
import logging
import websockets
from websockets.asyncio.client import ClientConnection, connect
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType, DiscordGatewayOpcode, DiscordGatewayIntents, DiscordVoiceGatewayOpcode
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordHelloPayload, DiscordIdentifyPayload
from discordapi.structures.discord_voice_payloads import DiscordVoiceHeartbeatPayload, DiscordVoiceIdentifyPayload, DiscordVoiceReadyPayload, DiscordVoiceStateObject, DiscordVoiceUpdatePayload, DiscordVoiceServerUpdatePayload
from utility.events import Event
from utility.error_log import add_error

_logger: logging.Logger = logging.getLogger(__name__)

class DiscordVoiceGatewayClient:

    #Partial gateway needs to be formatted with the url received from the server update
    _partial_gateway: str
    _gateway_url: str
    _session_id: str
    _guild_id: str
    _channel_id: str
    _token: str
    _bot_id: str
    _socket: ClientConnection
    _last_sequence:int = -1
    _last_hearbeat_nonce = -1
    _heartbeat_timer: asyncio.Task
    _heartbeat_interval = -1
    _heartbeat_ack: bool = True
    _heartbeat_is_active = False
    _config: any
    _cancel_flag = False
    message_callback: Event
    _waiting_for_server_details: bool = False
    _voiceStateUpdateReceived: bool = False
    _voiceServerUpdateReceived: bool = False
    _gateway_task = asyncio.Task[None]

    _udp_address: str
    _udp_port: int
    _ssrc: int

    def __init__(self, config, gateway_client: DiscordGatewayClient):
        self._config = config
        self._partial_gateway = config["api"]["voice_gateway"]
        self._token = config['authentication']['token']
        self._bot_id = config['bot']['bot_id']
        #self.socket = connect(GATEWAY_URL)
        self.message_callback = Event()
        #VoiceGateway relies on receiving events from regular Gateway for initialization
        #TODO: Should this be decoupled?
        gateway_client.register_message_callback(self.on_gateway_event_received)

    def wait_for_server_details(self):
        self._waiting_for_server_details = True
        self._voiceStateUpdateReceived = False
        self._voiceServerUpdateReceived = False

    def on_gateway_event_received(self, data: DiscordGatewayEvent):
        if self._waiting_for_server_details:
            try:
                if (data.t == DiscordGatewayEventType.VOICE_STATE_UPDATE):
                    voice_update = DiscordVoiceStateObject(**data.d)
                    if voice_update.user_id == self._bot_id:
                        self._voiceStateUpdateReceived = True
                        self._session_id = voice_update.session_id
                        self._channel_id = voice_update.channel_id
                elif (data.t == DiscordGatewayEventType.VOICE_SERVER_UPDATE):
                    voice_server_update = DiscordVoiceServerUpdatePayload(**data.d)
                    self._token = voice_server_update.token
                    self._guild_id = voice_server_update.guild_id
                    self._gateway_url = self._partial_gateway.format(voice_server_update.endpoint)
                    self._voiceServerUpdateReceived = True
                self.connect()
            except BaseException as e:
                _logger.error(f"Failed to parse voice update data: {e}")
        pass

    def connect(self):
        if (self._voiceStateUpdateReceived and self._voiceServerUpdateReceived):
            self._gateway_task = asyncio.create_task(self.listen())
            pass

    async def listen(self):
        #while not self.cancel_flag:
        async with connect(self._gateway_url) as websocket:
            self._socket = websocket
            await self.send_identify_payload()
            async for message in websocket:
                try:
                    #message = self.socket.recv()
                    #print(f"Received: {message}")
                    _logger.debug(f"Received: {message}")
                    await self.handle_message(message)
                except websockets.ConnectionClosedError as e:
                    #print(f"Webocket closed: {e}")
                    _logger.warning(f"Websocket closed: {e}")
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
            self._last_sequence = event.s
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
            case DiscordVoiceGatewayOpcode.Ready:
                await self.handle_ready_payload(event)
                pass
            case DiscordVoiceGatewayOpcode.SessionDescription:
                pass
            case DiscordVoiceGatewayOpcode.Speaking:
                pass
            case DiscordVoiceGatewayOpcode.HeartbeatAcknowledge:
                self._heartbeat_ack = True
                if int(event.d["t"]) != self._last_hearbeat_nonce:
                    _logger.warning(f"Mismatch with last sequence received.")
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
            self._heartbeat_timer = asyncio.create_task(self.do_heartbeat(heartbeat_interval/1000))
        except BaseException as e:
            _logger.error(f"Caught exception in handle_hello_payload: {e}")
            print(f"Caught exception in handle_hello_payload: {e}")

    async def send_identify_payload(self):
        try:
            payload = DiscordGatewayEvent(DiscordVoiceGatewayOpcode.Identify,
                        d=DiscordVoiceIdentifyPayload(self._guild_id,
                                                self._bot_id,
                                                self._session_id,
                                                self._token))
            self._socket.send(payload.to_json())
        except BaseException as e:
            _logger.error(f"Failed to send identify payload: {e}")

    async def handle_ready_payload(self, event: DiscordGatewayEvent):
        try:
            payload = DiscordVoiceReadyPayload(**event.d)
            self._udp_address = payload.ip
            self._udp_port = payload.port
            self._ssrc = payload.ssrc
            #TODO: Connect to UDP socket
        except BaseException as e:
            _logger.error(f"Failed to parse ready payload: {e}")

    async def do_heartbeat(self, interval):
        self._heartbeat_is_active = True
        while self._heartbeat_is_active:
            if self._heartbeat_ack:
                self._heartbeat_ack = False
                payload = DiscordVoiceHeartbeatPayload(self._last_sequence)
                event = DiscordGatewayEvent(op=DiscordGatewayOpcode.Heartbeat, 
                                              d=payload)
                self._last_hearbeat_nonce =  payload.t
                data = event.to_json()
                _logger.debug(f"Sending heartbeat data: {data}")
                await self._socket.send(data)
                await asyncio.sleep(interval)
            else:
                #TODO: retry, log, disconnect
                self._heartbeat_is_active = False
                _logger.warning("Missed heartbeat_ack")
                pass

    def disconnect(self):
        self._socket.close(websockets.CloseCode.NORMAL_CLOSURE, "Closed by application")
        self.do_heartbeat = False
        self._token = None
        self._gateway_task.cancel(msg="Cancelled by application")
        self._waiting_for_server_details = False

    def cleanup(self):
        try:
            self._cancel_flag = True
            self._heartbeat_is_active = False
            if self._socket and self._socket.state != websockets.State.CLOSED:
                self._socket.close(websockets.CloseCode.NORMAL_CLOSURE, reason="Closed by application")
            if self._heartbeat_timer:
                self._heartbeat_timer.cancel() 
        except BaseException as e:
            print(e)