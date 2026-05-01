# Handles interaction with the Discord Websocket gateway

import asyncio

import json
import logging
import websockets
from websockets.asyncio.client import ClientConnection, connect
from discordapi.gateway_client import DiscordGatewayClient
from discordapi.structures.discord_enums import DiscordGatewayEventType, DiscordGatewayOpcode, DiscordGatewayIntents, DiscordVoiceGatewayOpcode
from discordapi.structures.discord_payloads import DiscordGatewayEvent, DiscordHelloPayload, DiscordIdentifyPayload
from discordapi.structures.discord_voice_payloads import DiscordVoiceHeartbeatPayload, DiscordVoiceIdentifyPayload, DiscordVoiceReadyPayload, DiscordVoiceSelectProtocolPayload, DiscordVoiceSessionDescriptionPayload, DiscordVoiceStateObject, DiscordVoiceUpdatePayload, DiscordVoiceServerUpdatePayload
from utility.events import Event
from utility.error_log import add_error
from discordapi.voice_udp_client import run_udp_discovery, DiscordVoiceDatagramProtocol
from discordapi.opus_encoder import opus_encode_audio

_logger: logging.Logger = logging.getLogger(__name__)

class DiscordVoiceGatewayClient:

    PREFERRED_PROTOCOL = 'aead_aes256_gcm_rtpsize'
    DEFAULT_PROTOCOL = 'aead_xchacha20_poly1305_rtpsize'
    """aead_xchacha20_poly1305_rtpsize is guaranteed to be available"""

    #Partial gateway needs to be formatted with the url received from the server update
    _partial_gateway: str = None
    _gateway_url: str = None
    _session_id: str = None
    _guild_id: str = None
    _channel_id: str = None
    _token: str = None
    _bot_id: str = None
    _socket: ClientConnection = None
    _last_sequence:int = -1
    _last_hearbeat_nonce = -1
    _heartbeat_timer: asyncio.Task = None
    _heartbeat_interval = -1
    _heartbeat_ack: bool = True
    _heartbeat_is_active = False
    _config: any
    _cancel_flag = False
    message_callback: Event
    _waiting_for_server_details: bool = False
    _voiceStateUpdateReceived: bool = False
    _voiceServerUpdateReceived: bool = False
    _gateway_task: asyncio.Task[None] = None
    _voice_task: asyncio.Task[None] = None
    _ip_discovery_task: asyncio.Task[None] = None

    _udp_protocol: DiscordVoiceDatagramProtocol = None
    _udp_address: str = None
    _udp_port: int = -1
    _ssrc: int = -1
    _modes: list = None
    _secret: list = None

    _audio_sample_rate: int = -1
    _audio_channels: int = -1
    _audio_frame_duration: int = -1

    def __init__(self, config, gateway_client: DiscordGatewayClient):
        self._config = config
        self._partial_gateway = config["api"]["voice_gateway"]
        self._token = config['authentication']['token']
        self._bot_id = config['bot']['bot_id']
        self._audio_sample_rate = int(config['voip']['sample_rate'])
        self._audio_channels = int(config['voip']['channels'])
        self._audio_frame_duration = int(config['voip']['frame_duration'])
        #self.socket = connect(GATEWAY_URL)
        self.message_callback = Event()
        #VoiceGateway relies on receiving events from regular Gateway for initialization
        #TODO: Should this be decoupled?
        gateway_client.register_message_callback(self.on_gateway_event_received)
        _logger.debug(f"Init Voice Gateway Client")

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
                    if isinstance(message, str):
                    #message = self.socket.recv()
                    #print(f"Received: {message}")
                        _logger.debug(f"Received: {message}")
                        await self.handle_message(message)
                    elif isinstance(message, bytes):
                        _logger.debug(f"Received binary data: {message}")
                        #TODO: Handle binary data from Discord DAVE protocols
                    else:
                        _logger.warning("Received data of unknown type")
                except websockets.ConnectionClosedError as e:
                    #print(f"Webocket closed: {e}")
                    _logger.error(f"Websocket closed: {e}")
                    break
                finally:
                    #print("Connection closed")
                    pass

    async def handle_message(self, message):
        #print(f"JSON parsed: {data}")
        try:
            data = json.loads(message)
            _logger.debug(f"JSON parsed: {data}")
            _logger.debug("Handled message")
            event = DiscordGatewayEvent(**data)
            self._last_sequence = event.seq if event.seq else self._last_sequence
            await self.handle_opcode(event)
        except json.JSONDecodeError as e:
            #print(f"Error parsing gateway event:\n{e}")
            _logger.warning(f"Error JSON Decoding voice gateway event: {message}\n{e}")
        except Exception as e:
            #print(f"Caught exception in handle_message:{e}")
            _logger.warning(f"Caught exception in handle_message: {message}\n{e}")

    async def handle_opcode(self, event: DiscordGatewayEvent):
        _logger.debug(f"Handling opcode:{event.op}")
        match event.op:
            case DiscordVoiceGatewayOpcode.Ready:
                await self.handle_ready_payload(event)
                pass
            case DiscordVoiceGatewayOpcode.SessionDescription:
                await self.handle_session_description_payload(event)
                pass
            case DiscordVoiceGatewayOpcode.Speaking:
                pass
            case DiscordVoiceGatewayOpcode.HeartbeatAcknowledge:
                self._heartbeat_ack = True
                if int(event.d["t"]) != self._last_hearbeat_nonce:
                    _logger.warning(f"Mismatch with last sequence received.")
                print("Voice Heartbeat Acknowledged")
                pass
            case DiscordVoiceGatewayOpcode.Hello:
                #TODO: Handle 4006 - connection closed from websocket, which results in re-receiving Hello and Ready
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
                _logger.debug("Recieved Resumed event")
                pass
            case DiscordVoiceGatewayOpcode.ClientsConnect:
                _logger.debug("Recieved ClientsConnect event")
                pass
            case DiscordVoiceGatewayOpcode.ClientsDisconnect:
                _logger.debug("Recieved ClientsDisconnect event")
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
            #TODO: Handle DAVE protocol end-to-end encryption 
            payload = DiscordGatewayEvent(DiscordVoiceGatewayOpcode.Identify,
                        d=DiscordVoiceIdentifyPayload(self._guild_id,
                                                self._bot_id,
                                                self._session_id,
                                                self._token))
            await self._socket.send(payload.to_json())
        except BaseException as e:
            _logger.error(f"Failed to send identify payload: {e}")

    async def handle_ready_payload(self, event: DiscordGatewayEvent):
        try:
            payload = DiscordVoiceReadyPayload(**event.d)
            self._udp_address = payload.ip
            self._udp_port = payload.port
            self._ssrc = payload.ssrc
            self._modes = payload.modes
            _logger.debug(f"Handling Ready payload. IP={payload.ip}, Port={payload.port}, Modes={payload.modes}, SSRC={payload.ssrc}")
            #TODO: Connect to UDP socket
            if self._ip_discovery_task and not self._ip_discovery_task.done:
                self._ip_discovery_task.cancel()
                _logger.debug("Cancelling IP Discovery task")
            self._ip_discovery_task = asyncio.create_task(self.open_udp_socket())
        except BaseException as e:
            _logger.error(f"Failed to parse ready payload: {e}")

    async def handle_session_description_payload(self, event: DiscordGatewayEvent):
        try:
            payload = DiscordVoiceSessionDescriptionPayload(**event.d)
            self._modes = payload.mode
            self._secret = payload.secret_key
            #self._dave = payload.dave_protocol_version

            self._udp_protocol._srrc = self._ssrc
            self._udp_protocol._secret = self._secret
            _logger.debug(f"Received Session Description: {payload.to_json()}")
        except BaseException as e:
            _logger.error(f"Failed to parse session description payload: {e}")

    async def open_udp_socket(self):
        self._udp_address, self._udp_port, self._udp_protocol = await run_udp_discovery(self._udp_address, 
                                                                                        self._udp_port, 
                                                                                        self._ssrc)
        if not self._udp_protocol:
            _logger.warning("Failed to open udp connection")
            return
        print("UDP Discovery complete")
        mode = self.PREFERRED_PROTOCOL if self._modes.__contains__(self.PREFERRED_PROTOCOL) else self._modes[0]
        payload = DiscordVoiceSelectProtocolPayload(self._udp_address, self._udp_port, mode)
        event = DiscordGatewayEvent(DiscordVoiceGatewayOpcode.SelectProtocol, d=payload)
        await self._socket.send(event.to_json())    

    async def do_heartbeat(self, interval):
        try:
            self._heartbeat_is_active = True
            while self._heartbeat_is_active:
                if self._heartbeat_ack:
                    self._heartbeat_ack = False
                    payload = DiscordVoiceHeartbeatPayload(self._last_sequence)
                    event = DiscordGatewayEvent(op=DiscordVoiceGatewayOpcode.Heartbeat, 
                                                d=payload)
                    self._last_hearbeat_nonce = payload.t
                    data = event.to_json()
                    _logger.debug(f"Sending heartbeat data: {data}")
                    await self._socket.send(data)
                    await asyncio.sleep(interval)
                else:
                    #TODO: retry, log, disconnect
                    self._heartbeat_is_active = False
                    _logger.warning("Missed heartbeat_ack")
                    pass
        except BaseException as e:
            _logger.error(f"Caught exception in do_heartbeat: {e}")

    async def send_audio(self, filename, cancel = False):
        if self._ip_discovery_task and not self._ip_discovery_task.done:
            _logger.warning("Attempt to send audio before IP Discovery completed")
            return
        if not self._udp_protocol:
            _logger.warning("UDP Protocol has not been created")
            return
        if not self._voice_task or self._voice_task.done:
            self._voice_task = asyncio.create_task(self._udp_protocol.send_audio_file(filename,
                                                                                      self._audio_sample_rate,
                                                                                      self._audio_channels,
                                                                                      self._audio_frame_duration))
        #TODO:
        elif cancel:
            self._voice_task = asyncio.create_task(self._udp_protocol.send_audio_file(filename,
                                                                                      self._audio_sample_rate,
                                                                                      self._audio_channels,
                                                                                      self._audio_frame_duration))

    async def disconnect(self):
        await self._socket.close(websockets.CloseCode.NORMAL_CLOSURE, "Closed by application")
        self.do_heartbeat = False
        self._token = None
        self._gateway_task.cancel(msg="Cancelled by application")
        if self._ip_discovery_task:
                self._ip_discovery_task.cancel("Cancelled by application")
        self._waiting_for_server_details = False

    def cleanup(self):
        try:
            self._cancel_flag = True
            self._heartbeat_is_active = False
            if self._socket and self._socket.state != websockets.State.CLOSED:
                self._socket.close(websockets.CloseCode.NORMAL_CLOSURE, reason="Closed by application")
            if self._heartbeat_timer:
                self._heartbeat_timer.cancel() 
            if self._ip_discovery_task:
                self._ip_discovery_task.cancel()
            
        except BaseException as e:
            print(e)

    def debug_info(self):
        return f"""Gateway: {self._gateway_url if self._gateway_url else "null"}
            Session ID: {self._session_id if self._session_id else "null"}
            Channel ID: {self._channel_id}
            Last Sequence: {self._last_sequence}
            Heartbeat Active: {self._heartbeat_is_active}
            Waiting for Server Details: {self._waiting_for_server_details}
            UDP Protocol: {self._udp_protocol if self._udp_protocol else "null"}
            UDP Address: {self._udp_address if self._udp_protocol else "null"}
            UDP Port: {self._udp_port if self._udp_protocol else "null"}
            Modes: {self._modes}
            Audio Rate: {self._audio_sample_rate}, Channels: {self._audio_channels}, Frame: {self._audio_frame_duration}ms
            """